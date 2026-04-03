"""
Sales Engine — Prospect Pipeline
==================================
SQLite-backed prospect tracker with deal stages,
message generation, daily action queue, and CSV export.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from aionos.sales.models import DealStage, VerticalID

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "pipeline.db")


def _get_db(db_path: str = _DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            company     TEXT NOT NULL,
            title       TEXT DEFAULT '',
            vertical    TEXT NOT NULL,
            stage       TEXT NOT NULL DEFAULT 'cold',
            email       TEXT DEFAULT '',
            linkedin    TEXT DEFAULT '',
            phone       TEXT DEFAULT '',
            notes       TEXT DEFAULT '',
            source      TEXT DEFAULT '',
            sequence_day INTEGER DEFAULT 0,
            last_action_date TEXT DEFAULT '',
            next_action_date TEXT DEFAULT '',
            created     TEXT NOT NULL,
            updated     TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            action      TEXT NOT NULL,
            channel     TEXT DEFAULT '',
            message     TEXT DEFAULT '',
            timestamp   TEXT NOT NULL,
            FOREIGN KEY (prospect_id) REFERENCES prospects(id)
        )
    """)
    conn.commit()
    return conn


class Pipeline:
    """
    Prospect pipeline backed by local SQLite.

    Usage:
        pipe = Pipeline()
        pid = pipe.add("John Smith", "Baker McKenzie", "Managing Partner",
                        "legal", email="jsmith@bakermckenzie.com")
        pipe.advance(pid, "engaged")
        pipe.log_action(pid, "Sent cold email", channel="email")
        today = pipe.daily_queue()
        pipe.export_csv("prospects.csv")
    """

    def __init__(self, db_path: str = _DEFAULT_DB) -> None:
        self._db_path = db_path
        self._conn = _get_db(db_path)

    # ── Add / Update ──────────────────────────────────────────────

    def add(
        self,
        name: str,
        company: str,
        title: str = "",
        vertical: str = "legal",
        email: str = "",
        linkedin: str = "",
        phone: str = "",
        notes: str = "",
        source: str = "",
    ) -> int:
        """Add a prospect. Returns prospect ID."""
        VerticalID(vertical)  # validate
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            """INSERT INTO prospects
               (name, company, title, vertical, stage, email, linkedin,
                phone, notes, source, sequence_day, created, updated)
               VALUES (?, ?, ?, ?, 'cold', ?, ?, ?, ?, ?, 0, ?, ?)""",
            (name, company, title, vertical, email, linkedin,
             phone, notes, source, now, now),
        )
        self._conn.commit()
        return cur.lastrowid

    def update(self, prospect_id: int, **fields) -> None:
        """Update arbitrary fields on a prospect."""
        allowed = {
            "name", "company", "title", "vertical", "email",
            "linkedin", "phone", "notes", "source",
        }
        to_set = {k: v for k, v in fields.items() if k in allowed}
        if not to_set:
            return
        to_set["updated"] = datetime.now(timezone.utc).isoformat()
        sets = ", ".join(f"{k} = ?" for k in to_set)
        vals = list(to_set.values()) + [prospect_id]
        self._conn.execute(
            f"UPDATE prospects SET {sets} WHERE id = ?", vals
        )
        self._conn.commit()

    def remove(self, prospect_id: int) -> None:
        """Remove a prospect and their activity log."""
        self._conn.execute(
            "DELETE FROM activity_log WHERE prospect_id = ?", (prospect_id,)
        )
        self._conn.execute(
            "DELETE FROM prospects WHERE id = ?", (prospect_id,)
        )
        self._conn.commit()

    # ── Stage management ──────────────────────────────────────────

    def advance(self, prospect_id: int, new_stage: str) -> None:
        """Move a prospect to a new deal stage."""
        DealStage(new_stage)  # validate
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE prospects SET stage = ?, updated = ? WHERE id = ?",
            (new_stage, now, prospect_id),
        )
        self.log_action(prospect_id, f"Stage → {new_stage}")
        self._conn.commit()

    def get(self, prospect_id: int) -> Optional[Dict]:
        """Get a single prospect by ID."""
        row = self._conn.execute(
            "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_all(
        self,
        vertical: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> List[Dict]:
        """List prospects, optionally filtered."""
        query = "SELECT * FROM prospects WHERE 1=1"
        params: list = []
        if vertical:
            query += " AND vertical = ?"
            params.append(vertical)
        if stage:
            query += " AND stage = ?"
            params.append(stage)
        query += " ORDER BY updated DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def count_by_stage(self) -> Dict[str, int]:
        """Pipeline summary: count per stage."""
        rows = self._conn.execute(
            "SELECT stage, COUNT(*) as cnt FROM prospects GROUP BY stage"
        ).fetchall()
        return {r["stage"]: r["cnt"] for r in rows}

    # ── Activity log ──────────────────────────────────────────────

    def log_action(
        self,
        prospect_id: int,
        action: str,
        channel: str = "",
        message: str = "",
    ) -> None:
        """Log an outbound action against a prospect."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT INTO activity_log
               (prospect_id, action, channel, message, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (prospect_id, action, channel, message, now),
        )
        # Update sequence tracking
        self._conn.execute(
            """UPDATE prospects SET
                last_action_date = ?,
                sequence_day = sequence_day + 1,
                updated = ?
               WHERE id = ?""",
            (now, now, prospect_id),
        )
        self._conn.commit()

    def get_history(self, prospect_id: int) -> List[Dict]:
        """Full action history for a prospect."""
        rows = self._conn.execute(
            "SELECT * FROM activity_log WHERE prospect_id = ? ORDER BY timestamp",
            (prospect_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def recent_actions(self, limit: int = 200) -> List[Dict]:
        """Recent actions across all prospects."""
        rows = self._conn.execute(
            """SELECT a.*, p.name, p.company
               FROM activity_log a
               LEFT JOIN prospects p ON a.prospect_id = p.id
               ORDER BY a.timestamp DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Daily action queue ────────────────────────────────────────

    def set_next_action(
        self, prospect_id: int, days_from_now: int = 1
    ) -> None:
        """Schedule next follow-up action."""
        target = (date.today() + timedelta(days=days_from_now)).isoformat()
        self._conn.execute(
            "UPDATE prospects SET next_action_date = ?, updated = ? WHERE id = ?",
            (target, datetime.now(timezone.utc).isoformat(), prospect_id),
        )
        self._conn.commit()

    def daily_queue(self, date: Optional[str] = None) -> List[Dict]:
        """
        Get all prospects with action due today (or specified date).
        Returns prospect records with their next action info.
        """
        if date is None:
            from datetime import date as _date
            date = _date.today().isoformat()
        rows = self._conn.execute(
            """SELECT * FROM prospects
               WHERE next_action_date <= ? AND stage NOT IN ('closed_won', 'closed_lost')
               ORDER BY vertical, next_action_date""",
            (date,),
        ).fetchall()
        return [dict(r) for r in rows]

    def stale_prospects(self, days: int = 7) -> List[Dict]:
        """Prospects with no action in N days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = self._conn.execute(
            """SELECT * FROM prospects
               WHERE (last_action_date < ? OR last_action_date = '')
               AND stage NOT IN ('closed_won', 'closed_lost')
               ORDER BY last_action_date""",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Import / Export ───────────────────────────────────────────

    def export_csv(self, filepath: Optional[str] = None) -> str:
        """
        Export all prospects to CSV.
        If filepath is given, writes to file and returns path.
        Otherwise returns CSV as a string.
        """
        rows = self._conn.execute(
            "SELECT * FROM prospects ORDER BY vertical, stage, company"
        ).fetchall()
        if not rows:
            return ""

        columns = rows[0].keys()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

        csv_text = output.getvalue()
        if filepath:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                f.write(csv_text)
            return filepath
        return csv_text

    def import_csv(self, filepath: str) -> int:
        """
        Import prospects from CSV. Returns count imported.
        CSV must have: name, company, vertical.
        Optional: title, email, linkedin, phone, notes, source.
        """
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("name") or not row.get("company"):
                    continue
                self.add(
                    name=row["name"],
                    company=row["company"],
                    title=row.get("title", ""),
                    vertical=row.get("vertical", "legal"),
                    email=row.get("email", ""),
                    linkedin=row.get("linkedin", ""),
                    phone=row.get("phone", ""),
                    notes=row.get("notes", ""),
                    source=row.get("source", "csv_import"),
                )
                count += 1
        return count

    def close(self) -> None:
        self._conn.close()
