"""
Sales Engine — Self-Improvement Loop
=======================================
Tracks outreach outcomes, computes conversion rates by
segment/template/persona, and surfaces winning patterns.

The loop:
  1. You send outreach → log it with tags (persona, template, tier)
  2. Prospect replies or doesn't → log outcome
  3. Engine computes: which segments convert? which templates work?
  4. Next batch prioritizes winners, deprioritizes losers

Usage:
    from aionos.sales.learner import SalesLearner
    learner = SalesLearner()
    learner.record_outreach(prospect_id=35, template="legal_cold_email",
                            channel="email", persona="managing_partner")
    learner.record_outcome(prospect_id=35, outcome="replied")
    report = learner.performance_report()
    winners = learner.top_segments()
"""

from __future__ import annotations

import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from aionos.sales.prospects import Pipeline

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "pipeline.db")


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Create outreach tracking tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outreach_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            template    TEXT DEFAULT '',
            channel     TEXT DEFAULT '',
            persona     TEXT DEFAULT '',
            tier        TEXT DEFAULT '',
            vertical    TEXT DEFAULT '',
            outcome     TEXT DEFAULT 'pending',
            sent_at     TEXT NOT NULL,
            outcome_at  TEXT DEFAULT '',
            FOREIGN KEY (prospect_id) REFERENCES prospects(id)
        )
    """)
    # Segment weights — learned over time
    conn.execute("""
        CREATE TABLE IF NOT EXISTS segment_weights (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            segment_type TEXT NOT NULL,
            segment_value TEXT NOT NULL,
            weight      REAL DEFAULT 1.0,
            total_sent  INTEGER DEFAULT 0,
            total_replied INTEGER DEFAULT 0,
            total_demo  INTEGER DEFAULT 0,
            total_closed INTEGER DEFAULT 0,
            updated     TEXT NOT NULL,
            UNIQUE(segment_type, segment_value)
        )
    """)
    conn.commit()


class SalesLearner:
    """
    Self-improving outreach engine.

    Tracks which segments, templates, personas, and tiers
    produce replies, demos, and closed deals. Adjusts weights
    so the next outreach batch prioritizes winners.
    """

    # Outcome ladder (higher = better)
    OUTCOMES = {
        "pending": 0,
        "no_reply": 1,
        "bounced": 1,
        "unsubscribed": 1,
        "replied": 2,
        "objection": 2,
        "meeting_booked": 3,
        "demo_completed": 4,
        "proposal_sent": 5,
        "closed_won": 6,
        "closed_lost": 3,
    }

    def __init__(self, db_path: str = _DEFAULT_DB) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        _ensure_tables(self._conn)
        self._pipe = Pipeline(db_path)

    def close(self) -> None:
        self._conn.close()

    # ═══════════════════════════════════════════════════════════
    #  RECORD OUTREACH
    # ═══════════════════════════════════════════════════════════

    def record_outreach(
        self,
        prospect_id: int,
        template: str = "",
        channel: str = "email",
        persona: str = "",
        tier: str = "",
    ) -> int:
        """Log that an outreach was sent. Returns outreach_log ID."""
        prospect = self._pipe.get(prospect_id)
        vertical = prospect["vertical"] if prospect else ""

        # Auto-detect tier from notes if not provided
        if not tier and prospect:
            notes = prospect.get("notes", "").lower()
            for t in ["tier a", "tier b", "tier c", "tier d"]:
                if t in notes:
                    tier = t.replace("tier ", "").upper()
                    break

        # Auto-detect persona from title if not provided
        if not persona and prospect:
            title = prospect.get("title", "").lower()
            if "managing partner" in title:
                persona = "managing_partner"
            elif "cio" in title or "it director" in title:
                persona = "technical_buyer"
            elif "general counsel" in title or "ethics" in title:
                persona = "influencer"

        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            """INSERT INTO outreach_log
               (prospect_id, template, channel, persona, tier, vertical,
                outcome, sent_at)
               VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (prospect_id, template, channel, persona, tier, vertical, now),
        )
        self._conn.commit()
        return cur.lastrowid

    # ═══════════════════════════════════════════════════════════
    #  RECORD OUTCOME
    # ═══════════════════════════════════════════════════════════

    def record_outcome(
        self,
        prospect_id: int,
        outcome: str,
    ) -> None:
        """
        Record the outcome of outreach to a prospect.
        Updates the most recent pending outreach for that prospect.

        Outcomes: replied, no_reply, bounced, meeting_booked,
                  demo_completed, proposal_sent, closed_won, closed_lost
        """
        if outcome not in self.OUTCOMES:
            raise ValueError(f"Unknown outcome: {outcome}. "
                             f"Valid: {', '.join(self.OUTCOMES.keys())}")

        now = datetime.now(timezone.utc).isoformat()

        # Update most recent pending outreach for this prospect
        row = self._conn.execute(
            """SELECT id FROM outreach_log
               WHERE prospect_id = ? AND outcome = 'pending'
               ORDER BY sent_at DESC LIMIT 1""",
            (prospect_id,),
        ).fetchone()

        if row:
            self._conn.execute(
                "UPDATE outreach_log SET outcome = ?, outcome_at = ? WHERE id = ?",
                (outcome, now, row["id"]),
            )
        else:
            # No pending — update the most recent one regardless
            self._conn.execute(
                """UPDATE outreach_log SET outcome = ?, outcome_at = ?
                   WHERE prospect_id = ?
                   ORDER BY sent_at DESC LIMIT 1""",
                (outcome, now, prospect_id),
            )

        self._conn.commit()

        # Recompute segment weights
        self._recompute_weights()

    # ═══════════════════════════════════════════════════════════
    #  WEIGHT COMPUTATION
    # ═══════════════════════════════════════════════════════════

    def _recompute_weights(self) -> None:
        """Recompute segment weights from outreach outcomes."""
        rows = self._conn.execute(
            "SELECT * FROM outreach_log WHERE outcome != 'pending'"
        ).fetchall()

        if not rows:
            return

        # Aggregate by segment dimensions
        segments: Dict[Tuple[str, str], Dict] = defaultdict(
            lambda: {"sent": 0, "replied": 0, "demo": 0, "closed": 0}
        )

        for r in rows:
            outcome = r["outcome"]
            is_reply = outcome in ("replied", "objection", "meeting_booked",
                                   "demo_completed", "proposal_sent",
                                   "closed_won")
            is_demo = outcome in ("demo_completed", "proposal_sent", "closed_won")
            is_closed = outcome == "closed_won"

            dims = [
                ("persona", r["persona"]),
                ("tier", r["tier"]),
                ("template", r["template"]),
                ("channel", r["channel"]),
                ("vertical", r["vertical"]),
            ]

            for seg_type, seg_val in dims:
                if not seg_val:
                    continue
                seg = segments[(seg_type, seg_val)]
                seg["sent"] += 1
                if is_reply:
                    seg["replied"] += 1
                if is_demo:
                    seg["demo"] += 1
                if is_closed:
                    seg["closed"] += 1

        # Write weights
        now = datetime.now(timezone.utc).isoformat()
        for (seg_type, seg_val), stats in segments.items():
            reply_rate = stats["replied"] / stats["sent"] if stats["sent"] else 0
            demo_rate = stats["demo"] / stats["sent"] if stats["sent"] else 0

            # Weight formula: reply_rate * 0.6 + demo_rate * 0.4
            # Normalized to 0.1 - 2.0 range
            weight = max(0.1, min(2.0,
                                  (reply_rate * 0.6 + demo_rate * 0.4) * 4.0 + 0.5))

            # Minimum sample: need 5+ sends to adjust weight
            if stats["sent"] < 5:
                weight = 1.0

            self._conn.execute(
                """INSERT INTO segment_weights
                      (segment_type, segment_value, weight, total_sent,
                       total_replied, total_demo, total_closed, updated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(segment_type, segment_value)
                   DO UPDATE SET
                      weight = excluded.weight,
                      total_sent = excluded.total_sent,
                      total_replied = excluded.total_replied,
                      total_demo = excluded.total_demo,
                      total_closed = excluded.total_closed,
                      updated = excluded.updated""",
                (seg_type, seg_val, weight, stats["sent"],
                 stats["replied"], stats["demo"], stats["closed"], now),
            )

        self._conn.commit()

    # ═══════════════════════════════════════════════════════════
    #  PRIORITIZED PROSPECT LIST
    # ═══════════════════════════════════════════════════════════

    def prioritize_prospects(self, vertical: str = "legal", limit: int = 10) -> List[Dict]:
        """
        Return prospects sorted by weighted priority.
        Combines lead score with learned segment weights.

        Higher weight = this segment converts better = prioritize.
        """
        from aionos.sales.funnel import FunnelEngine
        funnel = FunnelEngine(self._pipe)
        scored = funnel.score_all()

        # Load segment weights
        weights = {}
        rows = self._conn.execute("SELECT * FROM segment_weights").fetchall()
        for r in rows:
            weights[(r["segment_type"], r["segment_value"])] = r["weight"]

        prioritized = []
        for p in scored:
            if vertical and p.get("vertical") != vertical:
                continue
            if p.get("stage") in ("closed_won", "closed_lost"):
                continue

            # Base score from funnel
            base = p.get("lead_score", 5)

            # Apply segment multipliers
            title = p.get("title", "").lower()
            persona = "managing_partner" if "managing partner" in title else \
                      "technical_buyer" if ("cio" in title or "it director" in title) else \
                      "influencer" if ("general counsel" in title or "ethics" in title) else ""

            notes = p.get("notes", "").lower()
            tier = ""
            for t in ["tier a", "tier b", "tier c", "tier d"]:
                if t in notes:
                    tier = t.replace("tier ", "").upper()
                    break

            persona_w = weights.get(("persona", persona), 1.0)
            tier_w = weights.get(("tier", tier), 1.0)

            # Weighted priority score
            priority = base * persona_w * tier_w
            prioritized.append({**p, "priority": round(priority, 1),
                                "persona_weight": persona_w,
                                "tier_weight": tier_w})

        prioritized.sort(key=lambda x: x["priority"], reverse=True)
        return prioritized[:limit]

    # ═══════════════════════════════════════════════════════════
    #  TOP SEGMENTS
    # ═══════════════════════════════════════════════════════════

    def top_segments(self) -> List[Dict]:
        """Return segments sorted by performance (reply rate)."""
        rows = self._conn.execute(
            """SELECT * FROM segment_weights
               WHERE total_sent >= 3
               ORDER BY weight DESC"""
        ).fetchall()

        return [
            {
                "segment": f"{r['segment_type']}={r['segment_value']}",
                "weight": round(r["weight"], 2),
                "sent": r["total_sent"],
                "replied": r["total_replied"],
                "demos": r["total_demo"],
                "closed": r["total_closed"],
                "reply_rate": f"{r['total_replied']/r['total_sent']*100:.0f}%"
                              if r["total_sent"] else "0%",
            }
            for r in rows
        ]

    # ═══════════════════════════════════════════════════════════
    #  PERFORMANCE REPORT
    # ═══════════════════════════════════════════════════════════

    def performance_report(self) -> str:
        """Generate a self-improvement report showing what's working."""
        lines = []
        lines.append("=" * 60)
        lines.append("  OUTREACH PERFORMANCE — SELF-IMPROVEMENT REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Overall stats
        total = self._conn.execute(
            "SELECT COUNT(*) as c FROM outreach_log"
        ).fetchone()["c"]
        resolved = self._conn.execute(
            "SELECT COUNT(*) as c FROM outreach_log WHERE outcome != 'pending'"
        ).fetchone()["c"]
        replied = self._conn.execute(
            "SELECT COUNT(*) as c FROM outreach_log WHERE outcome IN "
            "('replied','objection','meeting_booked','demo_completed','proposal_sent','closed_won')"
        ).fetchone()["c"]
        demos = self._conn.execute(
            "SELECT COUNT(*) as c FROM outreach_log WHERE outcome IN "
            "('demo_completed','proposal_sent','closed_won')"
        ).fetchone()["c"]
        closed = self._conn.execute(
            "SELECT COUNT(*) as c FROM outreach_log WHERE outcome = 'closed_won'"
        ).fetchone()["c"]

        lines.append("  --- OVERALL ---")
        lines.append(f"  Total outreach sent:  {total}")
        lines.append(f"  Outcomes recorded:    {resolved}")
        lines.append(f"  Replies:              {replied}  "
                     f"({replied/total*100:.0f}%)" if total else "")
        lines.append(f"  Demos booked:         {demos}  "
                     f"({demos/total*100:.0f}%)" if total else "")
        lines.append(f"  Closed won:           {closed}")
        lines.append("")

        if total == 0:
            lines.append("  No outreach logged yet. Start logging to enable self-improvement.")
            lines.append("")
            lines.append("  Quick start:")
            lines.append("    python -m aionos.sales.cli outreach 35 --template legal_cold_email")
            lines.append("    python -m aionos.sales.cli outcome 35 replied")
            return "\n".join(lines)

        # Segment performance
        segments = self.top_segments()
        if segments:
            lines.append("  --- SEGMENT PERFORMANCE (sorted by weight) ---")
            lines.append(f"  {'Segment':<35} {'Wt':>4} {'Sent':>5} {'Reply':>5} "
                         f"{'Demo':>5} {'Rate':>6}")
            lines.append(f"  {'-'*35} {'-'*4} {'-'*5} {'-'*5} {'-'*5} {'-'*6}")
            for s in segments:
                lines.append(
                    f"  {s['segment']:<35} {s['weight']:>4} {s['sent']:>5} "
                    f"{s['replied']:>5} {s['demos']:>5} {s['reply_rate']:>6}")
            lines.append("")

        # Recommendations
        lines.append("  --- RECOMMENDATIONS ---")
        if not segments:
            lines.append("  Not enough data yet. Need 5+ outreaches per segment to tune.")
        else:
            winners = [s for s in segments if s["weight"] > 1.2]
            losers = [s for s in segments if s["weight"] < 0.8]

            if winners:
                lines.append("  INCREASE:")
                for w in winners[:3]:
                    lines.append(f"    + {w['segment']} — {w['reply_rate']} reply rate (weight: {w['weight']})")
            if losers:
                lines.append("  DECREASE:")
                for l in losers[:3]:
                    lines.append(f"    - {l['segment']} — {l['reply_rate']} reply rate (weight: {l['weight']})")

            if not winners and not losers:
                lines.append("  All segments performing evenly. Keep logging to find winners.")

        lines.append("")

        # Next batch recommendation
        lines.append("  --- NEXT BATCH PRIORITY ---")
        priority = self.prioritize_prospects(limit=5)
        if priority:
            for p in priority:
                lines.append(
                    f"  #{p['id']:>3} {p['name']:<20} {p['company']:<25} "
                    f"priority: {p['priority']}"
                )
        else:
            lines.append("  Run: python -m aionos.sales.cli outreach <id> to start logging")

        lines.append("")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════
    #  OUTREACH HISTORY
    # ═══════════════════════════════════════════════════════════

    def outreach_stats(self) -> Dict:
        """Quick stats for integration into daily reports."""
        total = self._conn.execute(
            "SELECT COUNT(*) as c FROM outreach_log"
        ).fetchone()["c"]
        pending = self._conn.execute(
            "SELECT COUNT(*) as c FROM outreach_log WHERE outcome = 'pending'"
        ).fetchone()["c"]
        replied = self._conn.execute(
            "SELECT COUNT(*) as c FROM outreach_log WHERE outcome IN "
            "('replied','objection','meeting_booked','demo_completed',"
            "'proposal_sent','closed_won')"
        ).fetchone()["c"]

        return {
            "total_sent": total,
            "pending": pending,
            "replied": replied,
            "reply_rate": f"{replied/total*100:.0f}%" if total else "0%",
        }
