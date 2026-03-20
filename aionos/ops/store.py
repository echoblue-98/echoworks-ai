"""
EchoWorks Ops Engine -- Core Store
=====================================
SQLite-backed storage for memos, playbooks, metrics, and reviews.
All local. Zero cloud. Zero dependency beyond stdlib.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from aionos.ops.models import (
    Memo, MemoCategory, MemoStatus,
    Playbook, PlaybookStatus,
    Metric, MetricType,
    WeeklyReview,
)

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "ops.db")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return date.today().isoformat()


def _get_db(db_path: str = _DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS memos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            category    TEXT NOT NULL DEFAULT 'strategy',
            status      TEXT NOT NULL DEFAULT 'draft',
            issue       TEXT DEFAULT '',
            strategy    TEXT DEFAULT '',
            tradeoffs   TEXT DEFAULT '',
            metrics     TEXT DEFAULT '',
            next_steps  TEXT DEFAULT '[]',
            created     TEXT NOT NULL,
            updated     TEXT NOT NULL,
            review_date TEXT DEFAULT ''
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS playbooks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            category    TEXT NOT NULL DEFAULT 'operations',
            description TEXT DEFAULT '',
            trigger     TEXT DEFAULT '',
            steps       TEXT DEFAULT '[]',
            status      TEXT NOT NULL DEFAULT 'not_started',
            owner       TEXT DEFAULT '',
            created     TEXT NOT NULL,
            updated     TEXT NOT NULL,
            last_run    TEXT DEFAULT '',
            run_count   INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            metric_type TEXT NOT NULL DEFAULT 'count',
            category    TEXT NOT NULL DEFAULT 'sales',
            value       REAL NOT NULL DEFAULT 0,
            target      REAL DEFAULT 0,
            period      TEXT NOT NULL,
            recorded    TEXT NOT NULL,
            notes       TEXT DEFAULT ''
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS weekly_reviews (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            week                TEXT NOT NULL UNIQUE,
            pipeline_summary    TEXT DEFAULT '',
            metrics_summary     TEXT DEFAULT '',
            wins                TEXT DEFAULT '',
            blockers            TEXT DEFAULT '',
            next_week_priorities TEXT DEFAULT '',
            created             TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


class OpsStore:
    """
    Local operations engine for EchoWorks AI.

    Stores memos, playbooks, metrics, and weekly reviews
    in a local SQLite database. Zero cloud dependency.
    """

    def __init__(self, db_path: str = _DEFAULT_DB) -> None:
        self._conn = _get_db(db_path)

    # ================================================================
    #  MEMOS
    # ================================================================

    def create_memo(
        self,
        title: str,
        category: str = "strategy",
        issue: str = "",
        strategy: str = "",
        tradeoffs: str = "",
        metrics: str = "",
        next_steps: Optional[List[Dict]] = None,
        review_date: str = "",
    ) -> int:
        """Create a structured operational memo. Returns memo ID."""
        MemoCategory(category)  # validate
        now = _now()
        steps_json = json.dumps(next_steps or [])
        cur = self._conn.execute(
            """INSERT INTO memos
               (title, category, status, issue, strategy, tradeoffs,
                metrics, next_steps, created, updated, review_date)
               VALUES (?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, category, issue, strategy, tradeoffs,
             metrics, steps_json, now, now, review_date),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_memo(self, memo_id: int) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT * FROM memos WHERE id = ?", (memo_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["next_steps"] = json.loads(d.get("next_steps", "[]"))
        return d

    def list_memos(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        query = "SELECT * FROM memos WHERE 1=1"
        params: list = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY updated DESC"
        rows = self._conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["next_steps"] = json.loads(d.get("next_steps", "[]"))
            result.append(d)
        return result

    def update_memo(self, memo_id: int, **fields) -> None:
        allowed = {
            "title", "category", "status", "issue", "strategy",
            "tradeoffs", "metrics", "review_date",
        }
        to_set = {k: v for k, v in fields.items() if k in allowed}
        if "next_steps" in fields:
            to_set["next_steps"] = json.dumps(fields["next_steps"])
        if not to_set:
            return
        to_set["updated"] = _now()
        sets = ", ".join(f"{k} = ?" for k in to_set)
        vals = list(to_set.values()) + [memo_id]
        self._conn.execute(
            f"UPDATE memos SET {sets} WHERE id = ?", vals
        )
        self._conn.commit()

    def activate_memo(self, memo_id: int) -> None:
        self.update_memo(memo_id, status="active")

    def archive_memo(self, memo_id: int) -> None:
        self.update_memo(memo_id, status="archived")

    def memos_due_for_review(self) -> List[Dict]:
        """Memos with review_date <= today."""
        today = _today()
        rows = self._conn.execute(
            """SELECT * FROM memos
               WHERE review_date <= ? AND review_date != ''
               AND status = 'active'
               ORDER BY review_date""",
            (today,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ================================================================
    #  PLAYBOOKS
    # ================================================================

    def create_playbook(
        self,
        name: str,
        category: str = "operations",
        description: str = "",
        trigger: str = "",
        steps: Optional[List[Dict]] = None,
        owner: str = "",
    ) -> int:
        """Create an executable playbook. Returns playbook ID."""
        now = _now()
        steps_json = json.dumps(steps or [])
        cur = self._conn.execute(
            """INSERT INTO playbooks
               (name, category, description, trigger, steps, status,
                owner, created, updated)
               VALUES (?, ?, ?, ?, ?, 'not_started', ?, ?, ?)""",
            (name, category, description, trigger, steps_json,
             owner, now, now),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_playbook(self, playbook_id: int) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT * FROM playbooks WHERE id = ?", (playbook_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["steps"] = json.loads(d.get("steps", "[]"))
        return d

    def list_playbooks(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        query = "SELECT * FROM playbooks WHERE 1=1"
        params: list = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY updated DESC"
        rows = self._conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["steps"] = json.loads(d.get("steps", "[]"))
            result.append(d)
        return result

    def complete_step(self, playbook_id: int, step_num: int, notes: str = "") -> None:
        """Mark a playbook step as completed."""
        pb = self.get_playbook(playbook_id)
        if not pb:
            return
        steps = pb["steps"]
        for s in steps:
            if s.get("step_num") == step_num:
                s["status"] = "completed"
                s["completed_date"] = _today()
                if notes:
                    s["notes"] = notes
                break
        # Check if all steps done
        all_done = all(s.get("status") == "completed" for s in steps)
        now = _now()
        self._conn.execute(
            """UPDATE playbooks SET steps = ?, status = ?, updated = ?,
               last_run = ?, run_count = run_count + ?
               WHERE id = ?""",
            (json.dumps(steps),
             "completed" if all_done else "in_progress",
             now, now if all_done else pb.get("last_run", ""),
             1 if all_done else 0,
             playbook_id),
        )
        self._conn.commit()

    def reset_playbook(self, playbook_id: int) -> None:
        """Reset a playbook for re-execution."""
        pb = self.get_playbook(playbook_id)
        if not pb:
            return
        steps = pb["steps"]
        for s in steps:
            s["status"] = "not_started"
            s["completed_date"] = ""
            s["notes"] = ""
        self._conn.execute(
            "UPDATE playbooks SET steps = ?, status = 'not_started', updated = ? WHERE id = ?",
            (json.dumps(steps), _now(), playbook_id),
        )
        self._conn.commit()

    # ================================================================
    #  METRICS
    # ================================================================

    def record_metric(
        self,
        name: str,
        value: float,
        period: str = "",
        metric_type: str = "count",
        category: str = "sales",
        target: float = 0.0,
        notes: str = "",
    ) -> int:
        """Record a KPI data point. Returns metric ID."""
        if not period:
            period = _get_current_week()
        cur = self._conn.execute(
            """INSERT INTO metrics
               (name, metric_type, category, value, target, period, recorded, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, metric_type, category, value, target, period, _now(), notes),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_metrics(
        self,
        name: Optional[str] = None,
        category: Optional[str] = None,
        period: Optional[str] = None,
    ) -> List[Dict]:
        query = "SELECT * FROM metrics WHERE 1=1"
        params: list = []
        if name:
            query += " AND name = ?"
            params.append(name)
        if category:
            query += " AND category = ?"
            params.append(category)
        if period:
            query += " AND period = ?"
            params.append(period)
        query += " ORDER BY recorded DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def metric_trend(self, name: str, last_n: int = 8) -> List[Dict]:
        """Get last N data points for a metric to see the trend."""
        rows = self._conn.execute(
            """SELECT * FROM metrics WHERE name = ?
               ORDER BY period DESC LIMIT ?""",
            (name, last_n),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def metrics_summary(self, period: Optional[str] = None) -> Dict[str, Dict]:
        """Aggregate metrics by name for a period."""
        if not period:
            period = _get_current_week()
        rows = self._conn.execute(
            """SELECT name, metric_type, SUM(value) as total,
                      MAX(target) as target, category
               FROM metrics WHERE period = ?
               GROUP BY name""",
            (period,),
        ).fetchall()
        result = {}
        for r in rows:
            d = dict(r)
            name = d.pop("name")
            result[name] = d
        return result

    # ================================================================
    #  WEEKLY REVIEWS
    # ================================================================

    def create_review(
        self,
        pipeline_summary: str = "",
        metrics_summary: str = "",
        wins: str = "",
        blockers: str = "",
        next_week_priorities: str = "",
        week: Optional[str] = None,
    ) -> int:
        """Create or update a weekly review."""
        if not week:
            week = _get_current_week()
        # Upsert
        existing = self._conn.execute(
            "SELECT id FROM weekly_reviews WHERE week = ?", (week,)
        ).fetchone()
        if existing:
            self._conn.execute(
                """UPDATE weekly_reviews SET
                   pipeline_summary = ?, metrics_summary = ?,
                   wins = ?, blockers = ?, next_week_priorities = ?
                   WHERE week = ?""",
                (pipeline_summary, metrics_summary, wins,
                 blockers, next_week_priorities, week),
            )
            self._conn.commit()
            return existing["id"]
        cur = self._conn.execute(
            """INSERT INTO weekly_reviews
               (week, pipeline_summary, metrics_summary, wins,
                blockers, next_week_priorities, created)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (week, pipeline_summary, metrics_summary, wins,
             blockers, next_week_priorities, _now()),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_review(self, week: Optional[str] = None) -> Optional[Dict]:
        if not week:
            week = _get_current_week()
        row = self._conn.execute(
            "SELECT * FROM weekly_reviews WHERE week = ?", (week,)
        ).fetchone()
        return dict(row) if row else None

    def list_reviews(self, last_n: int = 8) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM weekly_reviews ORDER BY week DESC LIMIT ?",
            (last_n,),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()


def _get_current_week() -> str:
    """Return ISO week string like '2026-W12'."""
    today = date.today()
    return f"{today.year}-W{today.isocalendar()[1]:02d}"
