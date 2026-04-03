"""
EchoWorks — CRM Export
========================
Export pipeline data to CSV, JSON, and Google Sheets-ready format.
This IS the CRM — these exports let you share the data, back it up,
or import into external tools if needed.

Usage:
    python sell.py export              CSV to stdout
    python sell.py export --file       CSV to ~/Downloads/pipeline_export.csv
    python sell.py export --json       JSON export
    python sell.py export --sheets     Google Sheets-ready (tab-separated)
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from datetime import date, datetime, timezone
from typing import List, Optional

from aionos.sales.prospects import Pipeline
from aionos.sales.cadence import CadenceEngine
from aionos.sales.learner import SalesLearner

EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


class CRMExport:
    """Export pipeline and cadence data."""

    def __init__(self) -> None:
        self._pipe = Pipeline()
        self._cadence = CadenceEngine()
        self._learner = SalesLearner()

    def _enrich_prospects(self) -> List[dict]:
        """Get all prospects enriched with cadence data."""
        all_p = self._pipe.list_all()
        rows = []

        for p in all_p:
            row = dict(p)
            pid = row["id"]

            # Add cadence info
            enrollment = self._cadence.get_enrollment(pid)
            if enrollment:
                row["cadence"] = enrollment["sequence_name"]
                row["cadence_step"] = enrollment["current_step"]
                row["cadence_total_steps"] = enrollment["total_steps"]
                row["cadence_status"] = enrollment["status"]
                row["cadence_next_date"] = enrollment.get("next_step_date", "")
            else:
                row["cadence"] = ""
                row["cadence_step"] = ""
                row["cadence_total_steps"] = ""
                row["cadence_status"] = ""
                row["cadence_next_date"] = ""

            rows.append(row)

        return rows

    def to_csv(self, file_path: Optional[str] = None) -> str:
        """Export to CSV. Returns CSV string. Writes to file if path given."""
        rows = self._enrich_prospects()
        if not rows:
            return ""

        fields = [
            "id", "name", "company", "title", "email", "linkedin", "phone",
            "vertical", "stage", "source", "notes",
            "cadence", "cadence_step", "cadence_total_steps",
            "cadence_status", "cadence_next_date",
            "next_action_date", "last_action_date",
            "created", "updated",
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

        csv_str = output.getvalue()

        if file_path:
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_str)
            print(f"  Exported {len(rows)} prospects to {file_path}")

        return csv_str

    def to_json(self, file_path: Optional[str] = None) -> str:
        """Export to JSON."""
        rows = self._enrich_prospects()
        json_str = json.dumps(rows, indent=2, default=str)

        if file_path:
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"  Exported {len(rows)} prospects to {file_path}")

        return json_str

    def to_sheets(self, file_path: Optional[str] = None) -> str:
        """Export tab-separated for easy paste into Google Sheets."""
        rows = self._enrich_prospects()
        if not rows:
            return ""

        fields = [
            "id", "name", "company", "title", "email", "linkedin", "phone",
            "vertical", "stage", "cadence", "cadence_step",
            "cadence_status", "cadence_next_date", "notes",
        ]

        lines = ["\t".join(fields)]
        for row in rows:
            line = "\t".join(str(row.get(f, "")) for f in fields)
            lines.append(line)

        tsv_str = "\n".join(lines)

        if file_path:
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(tsv_str)
            print(f"  Exported {len(rows)} prospects to {file_path}")

        return tsv_str

    def activity_log(self, file_path: Optional[str] = None, limit: int = 200) -> str:
        """Export recent activity log as CSV."""
        logs = self._pipe.recent_actions(limit=limit)
        if not logs:
            print("  No activity log entries.")
            return ""

        output = io.StringIO()
        fields = ["id", "prospect_id", "action", "channel", "message", "created"]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in logs:
            writer.writerow(dict(row))

        csv_str = output.getvalue()

        if file_path:
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_str)
            print(f"  Exported {len(logs)} actions to {file_path}")

        return csv_str

    def summary(self) -> dict:
        """Quick pipeline summary dict."""
        counts = self._pipe.count_by_stage()
        total = sum(counts.values())
        won = counts.get("closed_won", 0)
        lost = counts.get("closed_lost", 0)
        active = total - won - lost
        stats = self._cadence.cadence_stats()

        return {
            "date": date.today().isoformat(),
            "total_prospects": total,
            "active": active,
            "closed_won": won,
            "closed_lost": lost,
            "mrr": won * 5000,
            "stages": counts,
            "cadences": stats,
        }


def main() -> None:
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="EchoWorks CRM Export")
    parser.add_argument("--json", action="store_true", help="Export as JSON")
    parser.add_argument("--sheets", action="store_true",
                        help="Tab-separated for Google Sheets")
    parser.add_argument("--file", action="store_true",
                        help="Write to ~/Downloads/ instead of stdout")
    parser.add_argument("--activity", action="store_true",
                        help="Export activity log")
    parser.add_argument("--summary", action="store_true",
                        help="Print pipeline summary")
    args = parser.parse_args()

    export = CRMExport()
    today = date.today().isoformat()

    if args.summary:
        s = export.summary()
        print(json.dumps(s, indent=2))
        return

    if args.activity:
        path = os.path.join(EXPORT_DIR, f"activity_log_{today}.csv") if args.file else None
        data = export.activity_log(file_path=path)
        if not args.file and data:
            print(data)
        return

    if args.json:
        path = os.path.join(EXPORT_DIR, f"pipeline_{today}.json") if args.file else None
        data = export.to_json(file_path=path)
        if not args.file:
            print(data)
    elif args.sheets:
        path = os.path.join(EXPORT_DIR, f"pipeline_{today}.tsv") if args.file else None
        data = export.to_sheets(file_path=path)
        if not args.file:
            print(data)
    else:
        path = os.path.join(EXPORT_DIR, f"pipeline_{today}.csv") if args.file else None
        data = export.to_csv(file_path=path)
        if not args.file:
            print(data)


if __name__ == "__main__":
    main()
