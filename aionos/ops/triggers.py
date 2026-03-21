"""
EchoWorks Ops Engine -- Playbook Trigger System
==================================================
Event-based and time-based triggers that auto-fire playbooks.

Trigger types:
  - event:   fires when a deal stage changes or an action is logged
  - time:    fires on a schedule (daily, weekly, monthly)
  - metric:  fires when a metric crosses a threshold

Usage:
    from aionos.ops.triggers import TriggerEngine
    engine = TriggerEngine()
    engine.check_all()                # run all trigger checks
    engine.fire_event("stage_change", prospect_id=5, new_stage="demo_scheduled")
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from aionos.ops.store import OpsStore, _get_current_week


_TRIGGERS_DB = os.path.join(os.path.dirname(__file__), "ops.db")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return date.today().isoformat()


class TriggerType:
    EVENT = "event"      # stage_change, deal_closed, prospect_added
    TIME = "time"        # daily, weekly, monthly
    METRIC = "metric"    # threshold crossing


class EventType:
    STAGE_CHANGE = "stage_change"
    DEAL_CLOSED_WON = "deal_closed_won"
    DEAL_CLOSED_LOST = "deal_closed_lost"
    PROSPECT_ADDED = "prospect_added"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    PROSPECT_STALE = "prospect_stale"


class TriggerEngine:
    """
    Watches for events and fires matching playbooks automatically.
    Stores trigger-to-playbook mappings and execution log in ops.db.
    """

    def __init__(self, ops: Optional[OpsStore] = None) -> None:
        self._ops = ops or OpsStore()
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        conn = self._ops._conn
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trigger_rules (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                trigger_type TEXT NOT NULL DEFAULT 'event',
                event_type   TEXT DEFAULT '',
                condition    TEXT DEFAULT '',
                playbook_id  INTEGER,
                action       TEXT DEFAULT '',
                enabled      INTEGER DEFAULT 1,
                created      TEXT NOT NULL,
                FOREIGN KEY (playbook_id) REFERENCES playbooks(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trigger_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id      INTEGER NOT NULL,
                event_type   TEXT NOT NULL,
                event_data   TEXT DEFAULT '',
                action_taken TEXT DEFAULT '',
                timestamp    TEXT NOT NULL,
                FOREIGN KEY (rule_id) REFERENCES trigger_rules(id)
            )
        """)
        conn.commit()

    # ── Rule Management ────────────────────────────────────────

    def add_rule(
        self,
        name: str,
        trigger_type: str,
        event_type: str = "",
        condition: str = "",
        playbook_id: Optional[int] = None,
        action: str = "",
    ) -> int:
        cur = self._ops._conn.execute(
            """INSERT INTO trigger_rules
               (name, trigger_type, event_type, condition, playbook_id, action, enabled, created)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
            (name, trigger_type, event_type, condition, playbook_id, action, _now()),
        )
        self._ops._conn.commit()
        return cur.lastrowid

    def list_rules(self, enabled_only: bool = True) -> List[Dict]:
        query = "SELECT * FROM trigger_rules"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY id"
        rows = self._ops._conn.execute(query).fetchall()
        return [dict(r) for r in rows]

    def disable_rule(self, rule_id: int) -> None:
        self._ops._conn.execute(
            "UPDATE trigger_rules SET enabled = 0 WHERE id = ?", (rule_id,)
        )
        self._ops._conn.commit()

    def enable_rule(self, rule_id: int) -> None:
        self._ops._conn.execute(
            "UPDATE trigger_rules SET enabled = 1 WHERE id = ?", (rule_id,)
        )
        self._ops._conn.commit()

    # ── Event Firing ───────────────────────────────────────────

    def fire_event(self, event_type: str, **event_data) -> List[str]:
        """
        Fire an event and execute all matching trigger rules.
        Returns list of actions taken.
        """
        rules = self._ops._conn.execute(
            """SELECT * FROM trigger_rules
               WHERE enabled = 1 AND trigger_type = 'event' AND event_type = ?""",
            (event_type,),
        ).fetchall()

        actions_taken = []
        for rule in rules:
            rule = dict(rule)
            if not self._condition_met(rule, event_data):
                continue

            action = self._execute_rule(rule, event_data)
            actions_taken.append(action)

            self._ops._conn.execute(
                """INSERT INTO trigger_log (rule_id, event_type, event_data, action_taken, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (rule["id"], event_type, json.dumps(event_data), action, _now()),
            )
        self._ops._conn.commit()
        return actions_taken

    def _condition_met(self, rule: Dict, event_data: Dict) -> bool:
        """Check if rule condition is satisfied by event data."""
        condition = rule.get("condition", "")
        if not condition:
            return True

        # Simple key=value conditions: "new_stage=demo_scheduled"
        for part in condition.split(","):
            part = part.strip()
            if "=" not in part:
                continue
            key, val = part.split("=", 1)
            if str(event_data.get(key.strip(), "")) != val.strip():
                return False
        return True

    def _execute_rule(self, rule: Dict, event_data: Dict) -> str:
        """Execute a trigger rule's action."""
        playbook_id = rule.get("playbook_id")
        action = rule.get("action", "")

        results = []

        # Reset and start associated playbook
        if playbook_id:
            pb = self._ops.get_playbook(playbook_id)
            if pb:
                if pb["status"] == "completed":
                    self._ops.reset_playbook(playbook_id)
                self._ops._conn.execute(
                    "UPDATE playbooks SET status = 'in_progress', updated = ? WHERE id = ?",
                    (_now(), playbook_id),
                )
                self._ops._conn.commit()
                results.append(f"Started playbook #{playbook_id}: {pb['name']}")

        # Custom action string (for logging, notifications)
        if action:
            results.append(f"Action: {action}")

        return "; ".join(results) if results else "No action"

    # ── Time-Based Checks ─────────────────────────────────────

    def check_time_triggers(self) -> List[str]:
        """Check which time-based triggers should fire today."""
        rules = self._ops._conn.execute(
            "SELECT * FROM trigger_rules WHERE enabled = 1 AND trigger_type = 'time'"
        ).fetchall()

        today = date.today()
        weekday = today.strftime("%A").lower()  # monday, tuesday...
        day_of_month = today.day
        actions = []

        for rule in rules:
            rule = dict(rule)
            schedule = rule.get("condition", "")

            should_fire = False
            if schedule == "daily":
                should_fire = True
            elif schedule == "weekday":
                should_fire = weekday not in ("saturday", "sunday")
            elif schedule == "weekly":
                should_fire = weekday == "monday"
            elif schedule == "monthly":
                should_fire = day_of_month == 1
            elif schedule.startswith("day="):
                should_fire = weekday == schedule.split("=")[1].strip().lower()

            if should_fire:
                # Check if already fired today
                already = self._ops._conn.execute(
                    """SELECT COUNT(*) FROM trigger_log
                       WHERE rule_id = ? AND timestamp LIKE ?""",
                    (rule["id"], f"{_today()}%"),
                ).fetchone()[0]
                if already > 0:
                    continue

                action = self._execute_rule(rule, {"schedule": schedule})
                actions.append(f"[{rule['name']}] {action}")
                self._ops._conn.execute(
                    """INSERT INTO trigger_log
                       (rule_id, event_type, event_data, action_taken, timestamp)
                       VALUES (?, ?, ?, ?, ?)""",
                    (rule["id"], "time_trigger", json.dumps({"schedule": schedule}),
                     action, _now()),
                )
        self._ops._conn.commit()
        return actions

    # ── Metric-Based Checks ───────────────────────────────────

    def check_metric_triggers(self) -> List[str]:
        """Check if any metrics have crossed thresholds."""
        rules = self._ops._conn.execute(
            "SELECT * FROM trigger_rules WHERE enabled = 1 AND trigger_type = 'metric'"
        ).fetchall()

        actions = []
        for rule in rules:
            rule = dict(rule)
            condition = rule.get("condition", "")
            # Format: "metric_name>threshold" or "metric_name<threshold"
            if ">" in condition:
                name, threshold = condition.split(">")
                op = ">"
            elif "<" in condition:
                name, threshold = condition.split("<")
                op = "<"
            else:
                continue

            name = name.strip()
            try:
                threshold = float(threshold.strip())
            except ValueError:
                continue

            # Get latest metric value
            latest = self._ops.metric_trend(name, last_n=1)
            if not latest:
                continue

            val = latest[0]["value"]
            crossed = (op == ">" and val > threshold) or (op == "<" and val < threshold)

            if crossed:
                already = self._ops._conn.execute(
                    """SELECT COUNT(*) FROM trigger_log
                       WHERE rule_id = ? AND timestamp LIKE ?""",
                    (rule["id"], f"{_today()}%"),
                ).fetchone()[0]
                if already > 0:
                    continue

                action = self._execute_rule(rule, {"metric": name, "value": val, "threshold": threshold})
                actions.append(f"[{rule['name']}] {name}={val} {op} {threshold} -> {action}")
                self._ops._conn.execute(
                    """INSERT INTO trigger_log
                       (rule_id, event_type, event_data, action_taken, timestamp)
                       VALUES (?, ?, ?, ?, ?)""",
                    (rule["id"], "metric_trigger",
                     json.dumps({"metric": name, "value": val}),
                     action, _now()),
                )
        self._ops._conn.commit()
        return actions

    # ── Full Check ────────────────────────────────────────────

    def check_all(self) -> str:
        """Run all trigger checks. Called by daily runner."""
        lines = ["  --- TRIGGER ENGINE ---"]

        time_actions = self.check_time_triggers()
        metric_actions = self.check_metric_triggers()

        if time_actions:
            lines.append(f"  Time triggers fired: {len(time_actions)}")
            for a in time_actions:
                lines.append(f"    >> {a}")
        if metric_actions:
            lines.append(f"  Metric triggers fired: {len(metric_actions)}")
            for a in metric_actions:
                lines.append(f"    >> {a}")
        if not time_actions and not metric_actions:
            lines.append("  No triggers fired.")

        return "\n".join(lines)

    # ── Trigger Log ───────────────────────────────────────────

    def recent_log(self, limit: int = 20) -> List[Dict]:
        rows = self._ops._conn.execute(
            """SELECT tl.*, tr.name as rule_name
               FROM trigger_log tl
               JOIN trigger_rules tr ON tl.rule_id = tr.id
               ORDER BY tl.timestamp DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
