"""
EchoWorks — Cadence Engine
=============================
Multi-step outreach sequences with automatic scheduling.

This is the core missing piece. It tracks:
  - Which sequence each prospect is enrolled in
  - Which step they're on
  - What channel/message is due next
  - Auto-schedules next step when current step is marked done

Usage:
    from aionos.sales.cadence import CadenceEngine
    ce = CadenceEngine()
    ce.enroll(prospect_id=35, sequence="cold_legal")
    due = ce.due_today()  # [(prospect, step_info), ...]
    ce.complete_step(prospect_id=35)  # auto-schedules next step
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from aionos.sales.prospects import Pipeline
from aionos.sales.learner import SalesLearner

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "pipeline.db")


# ═══════════════════════════════════════════════════════════════
#  SEQUENCE DEFINITIONS
# ═══════════════════════════════════════════════════════════════
# Each sequence is a list of steps. Each step defines:
#   day: relative day from enrollment (Day 0 = enrollment day)
#   channels: list of actions to take on this step
#   Each channel action: channel, template_key, action description

SEQUENCES = {
    "cold_legal": {
        "name": "Law Firm Cold Outreach",
        "description": "12-day cold sequence for law firm prospects",
        "steps": [
            {
                "step": 1,
                "day": 0,
                "channels": [
                    {
                        "channel": "linkedin",
                        "template_key": "linkedin_request",
                        "action": "Send LinkedIn connection request",
                    },
                    {
                        "channel": "email",
                        "template_key": "cold_email",
                        "action": "Send cold email",
                    },
                ],
            },
            {
                "step": 2,
                "day": 3,
                "channels": [
                    {
                        "channel": "linkedin",
                        "template_key": "follow_up_1",
                        "action": "LinkedIn follow-up (if accepted) or email follow-up",
                    },
                ],
            },
            {
                "step": 3,
                "day": 5,
                "channels": [
                    {
                        "channel": "email",
                        "template_key": "follow_up_1",
                        "action": "Send 3-min demo recording link",
                    },
                ],
            },
            {
                "step": 4,
                "day": 8,
                "channels": [
                    {
                        "channel": "linkedin",
                        "template_key": "follow_up_2",
                        "action": "Share relevant insight or article",
                    },
                ],
            },
            {
                "step": 5,
                "day": 12,
                "channels": [
                    {
                        "channel": "email",
                        "template_key": "follow_up_3",
                        "action": "Breakup email — final touch",
                    },
                ],
            },
        ],
    },

    "engaged_legal": {
        "name": "Law Firm Demo Booking",
        "description": "Book a demo with engaged prospects",
        "steps": [
            {
                "step": 1,
                "day": 0,
                "channels": [
                    {
                        "channel": "email",
                        "template_key": "demo_booking",
                        "action": "Send demo recording + booking link",
                    },
                ],
            },
            {
                "step": 2,
                "day": 3,
                "channels": [
                    {
                        "channel": "linkedin",
                        "template_key": "demo_nudge",
                        "action": "Quick LinkedIn nudge — did you see the demo?",
                    },
                ],
            },
            {
                "step": 3,
                "day": 7,
                "channels": [
                    {
                        "channel": "email",
                        "template_key": "demo_last_touch",
                        "action": "Final demo booking attempt",
                    },
                ],
            },
        ],
    },

    "proposal_legal": {
        "name": "Law Firm Proposal Follow-Up",
        "description": "Follow up after proposal sent",
        "steps": [
            {
                "step": 1,
                "day": 0,
                "channels": [
                    {
                        "channel": "email",
                        "template_key": "proposal_sent",
                        "action": "Send one-pager + demo recording + follow-up",
                    },
                ],
            },
            {
                "step": 2,
                "day": 3,
                "channels": [
                    {
                        "channel": "email",
                        "template_key": "proposal_check_in",
                        "action": "Quick check-in — any questions from the team?",
                    },
                ],
            },
            {
                "step": 3,
                "day": 7,
                "channels": [
                    {
                        "channel": "phone",
                        "template_key": "proposal_call",
                        "action": "Phone call follow-up",
                    },
                ],
            },
            {
                "step": 4,
                "day": 14,
                "channels": [
                    {
                        "channel": "email",
                        "template_key": "proposal_last_touch",
                        "action": "Final follow-up — keep the door open",
                    },
                ],
            },
        ],
    },
}

# Map: pipeline stage → which sequence to auto-enroll into
STAGE_SEQUENCE_MAP = {
    "cold": "cold_legal",
    "engaged": "engaged_legal",
    "proposal_sent": "proposal_legal",
}


# ═══════════════════════════════════════════════════════════════
#  STEP-SPECIFIC MESSAGE TEMPLATES
# ═══════════════════════════════════════════════════════════════
# These override the generic templates with step-aware messaging.

def get_step_message(
    step_num: int,
    sequence_name: str,
    channel: str,
    first_name: str,
    company: str,
    template_key: str,
    generated_msgs: Dict[str, str],
) -> str:
    """
    Get the right message for a specific cadence step.
    Uses generated_msgs from MessageGenerator as base, with step-specific overrides.
    """
    # Step-specific overrides for cold_legal
    if sequence_name == "cold_legal":
        if step_num == 1 and channel == "linkedin":
            return generated_msgs.get("linkedin_request", "")
        if step_num == 1 and channel == "email":
            return generated_msgs.get("cold_email", "")
        if step_num == 2:
            return (
                f"{first_name},\n\n"
                f"Sent a note a few days ago about how law firms are catching "
                f"attorney departure theft before the resignation letter.\n\n"
                f"The short version: we detect the full exfiltration chain — "
                f"matter access, bulk export, personal email forward, cloud "
                f"upload — in under 3 seconds. 100% on-premise.\n\n"
                f"Worth a quick look? I have a 3-minute demo recording.\n\n"
                f"Moe"
            )
        if step_num == 3:
            return (
                f"Subject: Quick demo — attorney departure detection\n\n"
                f"{first_name},\n\n"
                f"I put together a 3-minute recording of our system detecting "
                f"a full attorney departure chain at a firm like {company}.\n\n"
                f"It shows: matter access → bulk DMS export → personal email "
                f"forward → cloud upload — all caught in real time.\n\n"
                f"Here's the link: [ATTACH DEMO]\n\n"
                f"If it's relevant, happy to do a live walkthrough.\n\n"
                f"Moe"
            )
        if step_num == 4:
            return (
                f"{first_name},\n\n"
                f"Quick stat that might be relevant for {company}:\n\n"
                f"The average time to detect insider data theft at a law firm "
                f"is 77 days (Ponemon Institute). Departing attorneys typically "
                f"start staging files 2-4 weeks before the resignation letter.\n\n"
                f"That's a window where client files, billing data, and "
                f"privileged documents walk out quietly.\n\n"
                f"Let me know if you'd like to see how we close that gap.\n\n"
                f"Moe"
            )
        if step_num == 5:
            return generated_msgs.get("follow_up_3", "")

    # Step-specific overrides for engaged_legal
    if sequence_name == "engaged_legal":
        if step_num == 1:
            return (
                f"Subject: Demo + what we detect — EchoWorks AI\n\n"
                f"{first_name},\n\n"
                f"Thanks for connecting. I put together a 3-minute recording "
                f"of our detection system catching a full attorney departure "
                f"chain — matter access, bulk export, personal email forward, "
                f"cloud upload.\n\n"
                f"Worth a look if {company} handles lateral moves or has "
                f"attorneys with portable client books.\n\n"
                f"Happy to do a live 15-minute walkthrough if it's relevant.\n\n"
                f"Moe"
            )
        if step_num == 2:
            return (
                f"{first_name} — just checking in. Did you get a chance to "
                f"look at the demo recording I sent? Happy to answer any "
                f"questions or do a quick live walkthrough.\n\n"
                f"Moe"
            )
        if step_num == 3:
            return (
                f"Subject: Last note on this — EchoWorks AI\n\n"
                f"{first_name},\n\n"
                f"I'll keep this short. Our system detects attorney departure "
                f"theft in under 3 seconds, runs 100% on {company}'s hardware, "
                f"and comes with a 90-day guarantee.\n\n"
                f"If the timing isn't right, no worries at all. But if "
                f"protecting client files during lateral moves is on your "
                f"radar, I'm here.\n\n"
                f"Moe"
            )

    # Step-specific overrides for proposal_legal
    if sequence_name == "proposal_legal":
        if step_num == 1:
            return (
                f"Subject: Demo + One-Pager — EchoWorks AI\n\n"
                f"{first_name},\n\n"
                f"Great talking with you. I put together two things:\n\n"
                f"1. A short demo walkthrough (3 min) — shows exactly what "
                f"the system sees when an attorney starts moving files.\n\n"
                f"2. A one-pager you can share with the team — covers what "
                f"we detect, how it deploys, and the 90-day guarantee.\n\n"
                f"Both attached.\n\n"
                f"No rush. When the team is ready to discuss, happy to jump "
                f"on a call.\n\n"
                f"Moe"
            )
        if step_num == 2:
            return (
                f"Subject: Re: EchoWorks AI\n\n"
                f"{first_name},\n\n"
                f"Just checking in — did the team get a chance to review "
                f"the one-pager and demo? Happy to answer any questions "
                f"or hop on a quick call with the group.\n\n"
                f"Moe"
            )
        if step_num == 3:
            return (
                f"[PHONE CALL]\n\n"
                f"\"Hey {first_name}, it's Moe from EchoWorks. Just wanted "
                f"to check in on the proposal — did the partners get a "
                f"chance to look it over? Happy to answer anything that "
                f"came up.\""
            )
        if step_num == 4:
            return (
                f"Subject: Keeping the door open\n\n"
                f"{first_name},\n\n"
                f"I know timing doesn't always align. If attorney departure "
                f"detection becomes a priority for {company}, the offer "
                f"stands — $5,000/month, on-premise, 90-day guarantee.\n\n"
                f"No hard feelings either way. Just wanted to make sure "
                f"you have everything you need.\n\n"
                f"Moe"
            )

    # Fallback: use generated messages
    return generated_msgs.get(template_key, f"[No template for {template_key}]")


# ═══════════════════════════════════════════════════════════════
#  CADENCE ENGINE (database layer)
# ═══════════════════════════════════════════════════════════════

class CadenceEngine:
    """
    Tracks multi-step outreach sequences per prospect.

    Each prospect can be enrolled in one active sequence at a time.
    The engine knows which step they're on, what's due today,
    and auto-schedules the next step when you mark one complete.
    """

    def __init__(self, db_path: str = _DEFAULT_DB) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout = 5000")
        self._ensure_tables()
        self._pipe = Pipeline(db_path)
        self._learner = SalesLearner(db_path)

    def _ensure_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cadence_enrollments (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id     INTEGER NOT NULL,
                sequence_name   TEXT NOT NULL,
                current_step    INTEGER NOT NULL DEFAULT 1,
                total_steps     INTEGER NOT NULL,
                enrolled_date   TEXT NOT NULL,
                next_step_date  TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'active',
                completed_date  TEXT DEFAULT '',
                FOREIGN KEY (prospect_id) REFERENCES prospects(id)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cadence_step_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                enrollment_id   INTEGER NOT NULL,
                prospect_id     INTEGER NOT NULL,
                step_number     INTEGER NOT NULL,
                sequence_name   TEXT NOT NULL,
                channel         TEXT NOT NULL,
                action          TEXT NOT NULL,
                completed_at    TEXT NOT NULL,
                FOREIGN KEY (enrollment_id) REFERENCES cadence_enrollments(id)
            )
        """)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ── Enrollment ─────────────────────────────────────────────

    def enroll(
        self,
        prospect_id: int,
        sequence_name: str,
        start_date: Optional[str] = None,
    ) -> int:
        """
        Enroll a prospect in a cadence sequence.
        Cancels any existing active enrollment first.
        Returns enrollment ID.
        """
        seq = SEQUENCES.get(sequence_name)
        if not seq:
            raise ValueError(f"Unknown sequence: {sequence_name}")

        # Cancel existing active enrollments for this prospect
        self._conn.execute(
            """UPDATE cadence_enrollments
               SET status = 'replaced'
               WHERE prospect_id = ? AND status = 'active'""",
            (prospect_id,),
        )

        today = start_date or date.today().isoformat()
        total_steps = len(seq["steps"])
        # First step is due on enrollment day (day 0) or today
        first_step = seq["steps"][0]
        next_date = today

        cur = self._conn.execute(
            """INSERT INTO cadence_enrollments
               (prospect_id, sequence_name, current_step, total_steps,
                enrolled_date, next_step_date, status)
               VALUES (?, ?, 1, ?, ?, ?, 'active')""",
            (prospect_id, sequence_name, total_steps, today, next_date),
        )

        # Commit our writes before Pipeline writes through its own connection
        self._conn.commit()

        # Also update the pipeline's next_action_date
        self._pipe.set_next_action(prospect_id, 0)

        return cur.lastrowid

    def enroll_by_stage(self, prospect_id: int) -> Optional[int]:
        """Auto-enroll based on the prospect's current pipeline stage."""
        prospect = self._pipe.get(prospect_id)
        if not prospect:
            return None
        stage = prospect["stage"]
        seq_name = STAGE_SEQUENCE_MAP.get(stage)
        if not seq_name:
            return None
        return self.enroll(prospect_id, seq_name)

    def bulk_enroll_cold(self, limit: int = 0) -> int:
        """
        Enroll all cold legal prospects that aren't already in a cadence.
        Returns count enrolled.
        """
        # Get all cold legal prospects
        cold = self._pipe.list_all(vertical="legal", stage="cold")
        enrolled_ids = set(
            r["prospect_id"]
            for r in self._conn.execute(
                "SELECT prospect_id FROM cadence_enrollments WHERE status = 'active'"
            ).fetchall()
        )

        count = 0
        for p in cold:
            if p["id"] in enrolled_ids:
                continue
            self.enroll(p["id"], "cold_legal")
            count += 1
            if limit and count >= limit:
                break

        return count

    # ── Status ─────────────────────────────────────────────────

    def get_enrollment(self, prospect_id: int) -> Optional[Dict]:
        """Get active enrollment for a prospect."""
        row = self._conn.execute(
            """SELECT * FROM cadence_enrollments
               WHERE prospect_id = ? AND status = 'active'
               ORDER BY id DESC LIMIT 1""",
            (prospect_id,),
        ).fetchone()
        return dict(row) if row else None

    def is_enrolled(self, prospect_id: int) -> bool:
        return self.get_enrollment(prospect_id) is not None

    # ── Due Today ──────────────────────────────────────────────

    def due_today(self, target_date: Optional[str] = None) -> List[Dict]:
        """
        Get all prospects with cadence steps due today.
        Returns list of dicts with prospect info + step details.
        """
        today = target_date or date.today().isoformat()
        rows = self._conn.execute(
            """SELECT e.*, p.name, p.company, p.title, p.email,
                      p.linkedin, p.vertical, p.stage, p.notes, p.source
               FROM cadence_enrollments e
               JOIN prospects p ON e.prospect_id = p.id
               WHERE e.status = 'active'
                 AND e.next_step_date <= ?
                 AND p.stage NOT IN ('closed_won', 'closed_lost')
               ORDER BY e.next_step_date ASC""",
            (today,),
        ).fetchall()

        result = []
        for row in rows:
            r = dict(row)
            seq = SEQUENCES.get(r["sequence_name"], {})
            steps = seq.get("steps", [])
            current = r["current_step"]
            step_info = None
            for s in steps:
                if s["step"] == current:
                    step_info = s
                    break

            r["step_info"] = step_info
            r["sequence_label"] = seq.get("name", r["sequence_name"])
            result.append(r)

        return result

    # ── Complete Step ──────────────────────────────────────────

    def complete_step(
        self,
        prospect_id: int,
        channel: str = "",
    ) -> Dict:
        """
        Mark the current step as complete for a prospect.
        Auto-schedules the next step.

        Returns dict with:
          - completed_step: step number just completed
          - next_step: next step number (or None if sequence done)
          - next_date: when next step is due
          - sequence_complete: True if all steps done
        """
        enrollment = self.get_enrollment(prospect_id)
        if not enrollment:
            raise ValueError(f"Prospect #{prospect_id} not enrolled in any cadence")

        seq = SEQUENCES[enrollment["sequence_name"]]
        steps = seq["steps"]
        current_step = enrollment["current_step"]
        now = datetime.now(timezone.utc).isoformat()

        # Find current step info
        step_info = None
        for s in steps:
            if s["step"] == current_step:
                step_info = s
                break

        if not step_info:
            raise ValueError(f"Step {current_step} not found in sequence")

        # Log completion for each channel action in this step
        channel_log = []
        for ch in step_info["channels"]:
            used_channel = channel or ch["channel"]
            self._conn.execute(
                """INSERT INTO cadence_step_log
                   (enrollment_id, prospect_id, step_number,
                    sequence_name, channel, action, completed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (enrollment["id"], prospect_id, current_step,
                 enrollment["sequence_name"], used_channel,
                 ch["action"], now),
            )
            channel_log.append((used_channel, ch["action"], ch["template_key"]))

        # Commit own writes BEFORE touching Pipeline/Learner connections
        self._conn.commit()

        # Now safe to write through other connections
        for used_channel, action, template_key in channel_log:
            self._pipe.log_action(
                prospect_id,
                f"Cadence step {current_step}: {action}",
                channel=used_channel,
            )
            self._learner.record_outreach(
                prospect_id,
                template=template_key,
                channel=used_channel,
                tier=f"step_{current_step}",
            )

        # Determine next step
        next_step_num = current_step + 1
        next_step_info = None
        for s in steps:
            if s["step"] == next_step_num:
                next_step_info = s
                break

        if next_step_info:
            # Calculate days until next step
            days_gap = next_step_info["day"] - step_info["day"]
            next_date = (date.today() + timedelta(days=days_gap)).isoformat()

            self._conn.execute(
                """UPDATE cadence_enrollments
                   SET current_step = ?, next_step_date = ?
                   WHERE id = ?""",
                (next_step_num, next_date, enrollment["id"]),
            )
            self._conn.commit()
            self._pipe.set_next_action(prospect_id, days_gap)

            return {
                "completed_step": current_step,
                "next_step": next_step_num,
                "next_date": next_date,
                "sequence_complete": False,
            }
        else:
            # Sequence complete
            self._conn.execute(
                """UPDATE cadence_enrollments
                   SET status = 'completed', completed_date = ?
                   WHERE id = ?""",
                (now, enrollment["id"]),
            )
            self._conn.commit()

            return {
                "completed_step": current_step,
                "next_step": None,
                "next_date": None,
                "sequence_complete": True,
            }

    # ── Reply / Stage Change ───────────────────────────────────

    def prospect_replied(self, prospect_id: int) -> None:
        """
        Mark that a prospect replied. Pauses cadence
        (they're now in conversation, manual handling).
        """
        enrollment = self.get_enrollment(prospect_id)
        if enrollment:
            self._conn.execute(
                """UPDATE cadence_enrollments
                   SET status = 'replied'
                   WHERE id = ?""",
                (enrollment["id"],),
            )
            self._conn.commit()

        # Record outcome in learner
        self._learner.record_outcome(prospect_id, "replied")

    def prospect_advanced(self, prospect_id: int, new_stage: str) -> None:
        """
        When a prospect moves to a new stage, cancel old cadence
        and auto-enroll in the new stage's sequence (if one exists).
        """
        # Cancel current cadence
        enrollment = self.get_enrollment(prospect_id)
        if enrollment:
            self._conn.execute(
                """UPDATE cadence_enrollments
                   SET status = 'stage_changed'
                   WHERE id = ?""",
                (enrollment["id"],),
            )
            self._conn.commit()

        # Auto-enroll in new stage's sequence
        seq_name = STAGE_SEQUENCE_MAP.get(new_stage)
        if seq_name:
            self.enroll(prospect_id, seq_name)

    # ── Analytics ──────────────────────────────────────────────

    def cadence_stats(self) -> Dict:
        """Cadence performance metrics."""
        rows = self._conn.execute(
            """SELECT sequence_name, status, COUNT(*) as cnt
               FROM cadence_enrollments
               GROUP BY sequence_name, status"""
        ).fetchall()

        stats = {}
        for r in rows:
            seq = r["sequence_name"]
            if seq not in stats:
                stats[seq] = {"active": 0, "completed": 0, "replied": 0, "total": 0}
            stats[seq][r["status"]] = stats[seq].get(r["status"], 0) + r["cnt"]
            stats[seq]["total"] += r["cnt"]

        # Reply rate per sequence
        for seq, data in stats.items():
            total = data["total"]
            replied = data.get("replied", 0)
            data["reply_rate"] = f"{replied / max(total, 1) * 100:.1f}%"

        return stats

    def step_performance(self) -> List[Dict]:
        """Which steps get the most replies?"""
        rows = self._conn.execute(
            """SELECT sequence_name, step_number,
                      COUNT(*) as total_completed
               FROM cadence_step_log
               GROUP BY sequence_name, step_number
               ORDER BY sequence_name, step_number"""
        ).fetchall()
        return [dict(r) for r in rows]
