"""
AION OS — Campaign Engine
============================
Action-driven outreach automation organized by campaign.

No dashboards. No charts. Just: who's next, what to say, did you send it.

Usage:
    python -m aionos.sales.campaign run          # Execute today's actions
    python -m aionos.sales.campaign status        # One-line campaign status
    python -m aionos.sales.campaign create legal  # Create a new campaign
    python -m aionos.sales.campaign outcomes      # Log replies and results

Architecture:
    Campaign = a named, categorized outreach sequence targeting a segment.
    Each campaign auto-selects prospects matching its filters, generates
    messages per the vertical playbook, and walks the operator through
    execution one action at a time.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from aionos.sales.prospects import Pipeline
from aionos.sales.messages import MessageGenerator
from aionos.sales.learner import SalesLearner
from aionos.sales.models import DealStage, VerticalID

_DB = os.path.join(os.path.dirname(__file__), "campaigns.db")


# ── Database ──────────────────────────────────────────────

def _get_db(path: str = _DB) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            vertical    TEXT NOT NULL,
            target_stage TEXT NOT NULL DEFAULT 'cold',
            channel     TEXT NOT NULL DEFAULT 'linkedin',
            batch_size  INTEGER DEFAULT 10,
            active      INTEGER DEFAULT 1,
            created     TEXT NOT NULL,
            updated     TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign_actions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            prospect_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            message     TEXT DEFAULT '',
            status      TEXT NOT NULL DEFAULT 'pending',
            scheduled   TEXT NOT NULL,
            executed    TEXT DEFAULT '',
            result      TEXT DEFAULT '',
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
            UNIQUE(campaign_id, prospect_id, scheduled)
        )
    """)
    conn.commit()
    return conn


# ── Campaign class ────────────────────────────────────────

class CampaignEngine:
    """
    Campaign-based outreach automation.

    Campaigns auto-populate with matching prospects.
    The operator runs through actions one at a time.
    """

    def __init__(self) -> None:
        self._db = _get_db()
        self._pipe = Pipeline()
        self._gen = MessageGenerator()
        self._learner = SalesLearner()
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        """Create default campaigns if none exist."""
        existing = self._db.execute("SELECT COUNT(*) as c FROM campaigns").fetchone()["c"]
        if existing > 0:
            return

        now = datetime.now(timezone.utc).isoformat()
        defaults = [
            ("Legal — New Connections",   "legal",      "cold",    "linkedin", 10),
            ("Legal — Follow-Ups",        "legal",      "engaged", "linkedin", 10),
            ("Legal — Demo Outreach",     "legal",      "cold",    "email",    10),
            ("Healthcare — New Connections", "healthcare", "cold",  "linkedin", 10),
            ("Healthcare — Follow-Ups",   "healthcare", "engaged", "linkedin", 10),
            ("Real Estate — New Connections", "realestate", "cold", "linkedin", 10),
        ]
        for name, vert, stage, channel, batch in defaults:
            self._db.execute(
                """INSERT OR IGNORE INTO campaigns
                   (name, vertical, target_stage, channel, batch_size, active, created, updated)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (name, vert, stage, channel, batch, now, now),
            )
        self._db.commit()

    # ── Campaign CRUD ─────────────────────────────────────

    def list_campaigns(self) -> List[dict]:
        rows = self._db.execute(
            "SELECT * FROM campaigns WHERE active = 1 ORDER BY vertical, target_stage"
        ).fetchall()
        return [dict(r) for r in rows]

    def create_campaign(
        self, name: str, vertical: str, target_stage: str = "cold",
        channel: str = "linkedin", batch_size: int = 10,
    ) -> int:
        VerticalID(vertical)
        now = datetime.now(timezone.utc).isoformat()
        cur = self._db.execute(
            """INSERT INTO campaigns (name, vertical, target_stage, channel, batch_size, active, created, updated)
               VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
            (name, vertical, target_stage, channel, batch_size, now, now),
        )
        self._db.commit()
        return cur.lastrowid

    # ── Populate actions ──────────────────────────────────

    def populate(self, campaign_id: int) -> int:
        """
        Auto-populate a campaign with pending actions for matching prospects.
        Returns number of new actions created.
        """
        campaign = dict(
            self._db.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        )
        vert = campaign["vertical"]
        stage = campaign["target_stage"]
        channel = campaign["channel"]
        batch = campaign["batch_size"]
        today = date.today().isoformat()

        # Get matching prospects not already actioned in this campaign today
        prospects = self._pipe.list_all(vertical=vert, stage=stage)
        already = set(
            r["prospect_id"]
            for r in self._db.execute(
                "SELECT prospect_id FROM campaign_actions WHERE campaign_id = ? AND scheduled = ?",
                (campaign_id, today),
            ).fetchall()
        )

        count = 0
        for p in prospects:
            if count >= batch:
                break
            pid = p["id"]
            if pid in already:
                continue

            # Generate message
            try:
                msgs = self._gen.generate(
                    name=p["name"], company=p["company"],
                    title=p.get("title") or "Partner", vertical=vert,
                )
                msg = msgs.get("linkedin_request", "") if channel == "linkedin" else msgs.get("cold_email", "")
            except Exception:
                msg = ""

            action_type = f"{channel}_outreach"
            self._db.execute(
                """INSERT OR IGNORE INTO campaign_actions
                   (campaign_id, prospect_id, action_type, message, status, scheduled)
                   VALUES (?, ?, ?, ?, 'pending', ?)""",
                (campaign_id, pid, action_type, msg, today),
            )
            count += 1

        self._db.commit()
        return count

    # ── Get today's queue ─────────────────────────────────

    def todays_actions(self, campaign_id: Optional[int] = None) -> List[dict]:
        """Get all pending actions for today, optionally filtered by campaign."""
        today = date.today().isoformat()
        if campaign_id:
            rows = self._db.execute(
                """SELECT ca.*, c.name as campaign_name, c.vertical, c.channel
                   FROM campaign_actions ca
                   JOIN campaigns c ON ca.campaign_id = c.id
                   WHERE ca.scheduled <= ? AND ca.status = 'pending' AND ca.campaign_id = ?
                   ORDER BY ca.id""",
                (today, campaign_id),
            ).fetchall()
        else:
            rows = self._db.execute(
                """SELECT ca.*, c.name as campaign_name, c.vertical, c.channel
                   FROM campaign_actions ca
                   JOIN campaigns c ON ca.campaign_id = c.id
                   WHERE ca.scheduled <= ? AND ca.status = 'pending'
                   ORDER BY c.vertical, ca.id""",
                (today,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Execute single action ─────────────────────────────

    def mark_sent(self, action_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        action = dict(self._db.execute(
            "SELECT * FROM campaign_actions WHERE id = ?", (action_id,)
        ).fetchone())
        pid = action["prospect_id"]
        campaign = dict(self._db.execute(
            "SELECT * FROM campaigns WHERE id = ?", (action["campaign_id"],)
        ).fetchone())

        # Update action
        self._db.execute(
            "UPDATE campaign_actions SET status = 'sent', executed = ? WHERE id = ?",
            (now, action_id),
        )
        self._db.commit()

        # Log in pipeline
        channel = campaign["channel"]
        self._pipe.log_action(pid, f"Campaign: {campaign['name']}", channel=channel)
        self._learner.record_outreach(pid, template=f"{campaign['vertical']}_{channel}", channel=channel)
        self._pipe.set_next_action(pid, 3)

    def mark_skipped(self, action_id: int) -> None:
        self._db.execute(
            "UPDATE campaign_actions SET status = 'skipped' WHERE id = ?",
            (action_id,),
        )
        self._db.commit()

    # ── Stats (one-liner, not dashboard) ──────────────────

    def campaign_status(self) -> List[dict]:
        """One-line status per campaign: name, pending, sent, skipped."""
        campaigns = self.list_campaigns()
        result = []
        for c in campaigns:
            cid = c["id"]
            counts = {}
            for status in ("pending", "sent", "skipped"):
                row = self._db.execute(
                    "SELECT COUNT(*) as n FROM campaign_actions WHERE campaign_id = ? AND status = ?",
                    (cid, status),
                ).fetchone()
                counts[status] = row["n"]
            result.append({
                "campaign": c["name"],
                "vertical": c["vertical"],
                "stage": c["target_stage"],
                "pending": counts["pending"],
                "sent": counts["sent"],
                "skipped": counts["skipped"],
            })
        return result


# ── CLI Runner ────────────────────────────────────────────

def _run(engine: CampaignEngine) -> None:
    """The main action loop. No fluff — just execute."""
    campaigns = engine.list_campaigns()
    if not campaigns:
        print("  No active campaigns. Create one first.")
        return

    # Auto-populate all campaigns for today
    total_new = 0
    for c in campaigns:
        n = engine.populate(c["id"])
        total_new += n

    actions = engine.todays_actions()
    if not actions:
        print("\n  Nothing to send today. All caught up.\n")
        return

    # Group by campaign for categorical flow
    by_campaign = defaultdict(list)
    for a in actions:
        by_campaign[a["campaign_name"]].append(a)

    total_sent = 0
    total_skipped = 0

    for camp_name, camp_actions in by_campaign.items():
        print(f"\n  ━━━ {camp_name} ({len(camp_actions)} queued) ━━━\n")

        skip_rest = False
        for i, action in enumerate(camp_actions, 1):
            if skip_rest:
                break

            pid = action["prospect_id"]
            prospect = engine._pipe.get(pid)
            if not prospect:
                continue
            prospect = dict(prospect)

            name = prospect["name"]
            company = prospect["company"]
            title = prospect.get("title", "")
            msg = action["message"]

            # Show the action
            print(f"  [{i}/{len(camp_actions)}]  #{pid} {name} — {company}")
            if title:
                print(f"          {title}")
            print()

            if msg:
                # Show message in a copy-friendly format
                print(f"  MESSAGE ({len(msg)} chars):")
                print(f"  ┌{'─' * 58}")
                for line in msg.split("\n"):
                    print(f"  │ {line}")
                print(f"  └{'─' * 58}")
            print()

            resp = input("  [s]ent  [k]skip  [n]ext campaign  [q]uit → ").strip().lower()

            if resp == "s":
                engine.mark_sent(action["id"])
                total_sent += 1
                print(f"  ✓ Logged.\n")
            elif resp == "n":
                print(f"  → Skipping rest of {camp_name}\n")
                skip_rest = True
            elif resp == "q":
                print(f"\n  Done. Sent: {total_sent} | Skipped: {total_skipped}\n")
                return
            else:
                engine.mark_skipped(action["id"])
                total_skipped += 1
                print(f"  — Skipped.\n")

    print(f"\n  Session complete. Sent: {total_sent} | Skipped: {total_skipped}")
    print(f"  Follow-ups auto-scheduled 3 days out.\n")


def _status(engine: CampaignEngine) -> None:
    """One-line-per-campaign status. Not a dashboard."""
    stats = engine.campaign_status()
    if not stats:
        print("  No campaigns yet.")
        return
    print(f"\n  {'Campaign':<38} {'Pend':>5} {'Sent':>5} {'Skip':>5}")
    print(f"  {'─' * 38} {'─' * 5} {'─' * 5} {'─' * 5}")
    for s in stats:
        print(f"  {s['campaign']:<38} {s['pending']:>5} {s['sent']:>5} {s['skipped']:>5}")
    print()


def _create(engine: CampaignEngine) -> None:
    """Create a new campaign interactively."""
    print()
    name = input("  Campaign name: ").strip()
    if not name:
        return
    print("  Vertical: [1] legal  [2] healthcare  [3] realestate")
    v = input("  → ").strip()
    vert = {"1": "legal", "2": "healthcare", "3": "realestate"}.get(v, "legal")
    print("  Target stage: [1] cold  [2] engaged")
    s = input("  → ").strip()
    stage = {"1": "cold", "2": "engaged"}.get(s, "cold")
    print("  Channel: [1] linkedin  [2] email")
    ch = input("  → ").strip()
    channel = {"1": "linkedin", "2": "email"}.get(ch, "linkedin")
    bs = input("  Batch size [10]: ").strip()
    batch = int(bs) if bs.isdigit() else 10

    cid = engine.create_campaign(name, vert, stage, channel, batch)
    print(f"\n  Campaign #{cid} created: {name}\n")


def _outcomes(engine: CampaignEngine) -> None:
    """Log outcomes — replies, meetings, closes."""
    print("\n  Log outcomes. Type 'done' to finish.")
    print("  Options: replied | meeting_booked | demo_completed | closed_won | closed_lost | no_reply\n")

    pipe = engine._pipe
    learner = engine._learner

    while True:
        raw = input("  Prospect # (or 'done'): ").strip()
        if raw.lower() == "done":
            break
        try:
            pid = int(raw)
        except ValueError:
            print("  Invalid.")
            continue

        p = pipe.get(pid)
        if not p:
            print(f"  #{pid} not found.")
            continue

        print(f"  #{pid} {p['name']} — {p['company']} ({p['stage']})")
        outcome = input("  Outcome: ").strip().lower()
        if not outcome:
            continue

        learner.record_outcome(pid, outcome)

        advance_map = {
            "replied": "engaged",
            "meeting_booked": "demo_scheduled",
            "demo_completed": "demo_completed",
            "closed_won": "closed_won",
            "closed_lost": "closed_lost",
        }
        new_stage = advance_map.get(outcome)
        if new_stage and p["stage"] != new_stage:
            pipe.advance(pid, new_stage)
            print(f"  → {p['stage']} → {new_stage}")
        else:
            print(f"  Recorded: {outcome}")
        print()


def main() -> None:
    engine = CampaignEngine()

    if len(sys.argv) < 2:
        # Default: run
        _run(engine)
        return

    cmd = sys.argv[1].lower()
    if cmd == "run":
        _run(engine)
    elif cmd == "status":
        _status(engine)
    elif cmd == "create":
        _create(engine)
    elif cmd == "outcomes":
        _outcomes(engine)
    else:
        print(f"  Unknown command: {cmd}")
        print("  Commands: run | status | create | outcomes")


if __name__ == "__main__":
    main()
