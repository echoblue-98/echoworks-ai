"""
EchoWorks Ops Engine -- Daily Runner
=======================================
Automated daily operations that run locally:
  - Pipeline health check
  - Stale prospect alerts
  - Memo review reminders
  - Auto-record sales metrics
  - Weekly review generation

Run daily: python -m aionos.ops.runner
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from typing import Dict, List, Optional

from aionos.ops.store import OpsStore, _get_current_week


class OpsRunner:
    """
    Daily operations automation for EchoWorks AI.
    All local. No cloud. No API calls.
    """

    def __init__(self, ops: Optional[OpsStore] = None) -> None:
        self._ops = ops or OpsStore()
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            from aionos.sales.prospects import Pipeline
            self._pipeline = Pipeline()
        return self._pipeline

    def run_daily(self) -> str:
        """Run all daily ops checks. Returns report string."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  ECHOWORKS OPS -- DAILY REPORT -- {date.today()}")
        lines.append("=" * 60)
        lines.append("")

        # 1. Pipeline health
        lines.append(self._pipeline_health())
        lines.append("")

        # 2. Today's action queue
        lines.append(self._action_queue_summary())
        lines.append("")

        # 3. Stale prospects
        lines.append(self._stale_alerts())
        lines.append("")

        # 4. Memo review reminders
        lines.append(self._memo_reviews())
        lines.append("")

        # 5. Active playbooks
        lines.append(self._playbook_status())
        lines.append("")

        # 6. This week's metrics
        lines.append(self._weekly_metrics())
        lines.append("")

        # 7. Auto-record pipeline metrics
        self._auto_record_metrics()

        lines.append("-" * 60)
        lines.append("  Run: python -m aionos.ops.runner")
        lines.append("  All data stored locally. Zero cloud.")
        lines.append("")

        return "\n".join(lines)

    def _pipeline_health(self) -> str:
        try:
            pipe = self._get_pipeline()
            counts = pipe.count_by_stage()
            total = sum(counts.values())
            lines = ["  --- PIPELINE HEALTH ---"]
            for stage, count in sorted(counts.items()):
                pct = (count / total * 100) if total else 0
                bar = "#" * min(count, 40)
                lines.append(f"  {stage:<16} {count:>3} ({pct:4.1f}%)  {bar}")
            lines.append(f"  {'TOTAL':<16} {total:>3}")
            return "\n".join(lines)
        except Exception:
            return "  --- PIPELINE HEALTH ---\n  (No pipeline data)"

    def _action_queue_summary(self) -> str:
        try:
            pipe = self._get_pipeline()
            queue = pipe.daily_queue()
            count = len(queue)
            lines = [f"  --- TODAY'S QUEUE: {count} prospects ---"]
            if count > 0:
                by_vertical = {}
                for p in queue:
                    v = p.get("vertical", "unknown")
                    by_vertical[v] = by_vertical.get(v, 0) + 1
                for v, c in sorted(by_vertical.items()):
                    lines.append(f"  {v:<16} {c} due")
                lines.append(f"  Run: python -m aionos.sales.cli queue")
            else:
                lines.append("  No actions due today.")
            return "\n".join(lines)
        except Exception:
            return "  --- TODAY'S QUEUE ---\n  (No pipeline data)"

    def _stale_alerts(self) -> str:
        try:
            pipe = self._get_pipeline()
            stale = pipe.stale_prospects(days=5)
            lines = [f"  --- STALE ALERTS: {len(stale)} prospects ---"]
            if stale:
                for p in stale[:5]:
                    last = p.get("last_action_date", "never")[:10] or "never"
                    lines.append(
                        f"  #{p['id']:>3} {p['name']:<20} "
                        f"{p['company']:<20} last: {last}"
                    )
                if len(stale) > 5:
                    lines.append(f"  ... and {len(stale) - 5} more")
                lines.append(f"  Run: python -m aionos.sales.cli stale")
            else:
                lines.append("  All prospects contacted within 5 days.")
            return "\n".join(lines)
        except Exception:
            return "  --- STALE ALERTS ---\n  (No pipeline data)"

    def _memo_reviews(self) -> str:
        memos = self._ops.memos_due_for_review()
        lines = [f"  --- MEMO REVIEWS DUE: {len(memos)} ---"]
        if memos:
            for m in memos:
                lines.append(
                    f"  #{m['id']:>3} [{m['category']}] {m['title']}"
                    f"  (due: {m['review_date']})"
                )
            lines.append(f"  Run: python -m aionos.ops.cli memo show <id>")
        else:
            lines.append("  No memos due for review.")
        return "\n".join(lines)

    def _playbook_status(self) -> str:
        playbooks = self._ops.list_playbooks(status="in_progress")
        lines = [f"  --- ACTIVE PLAYBOOKS: {len(playbooks)} ---"]
        if playbooks:
            for pb in playbooks:
                steps = pb.get("steps", [])
                done = sum(1 for s in steps if s.get("status") == "completed")
                total = len(steps)
                lines.append(
                    f"  #{pb['id']:>3} {pb['name']:<30} "
                    f"{done}/{total} steps done"
                )
            lines.append(f"  Run: python -m aionos.ops.cli playbook show <id>")
        else:
            lines.append("  No playbooks in progress.")
        return "\n".join(lines)

    def _weekly_metrics(self) -> str:
        week = _get_current_week()
        summary = self._ops.metrics_summary(week)
        lines = [f"  --- METRICS THIS WEEK ({week}) ---"]
        if summary:
            for name, data in summary.items():
                total = data.get("total", 0)
                target = data.get("target", 0)
                mtype = data.get("metric_type", "count")
                if mtype == "currency":
                    val_str = f"${total:,.0f}"
                    tgt_str = f"/ ${target:,.0f}" if target else ""
                elif mtype == "percent":
                    val_str = f"{total:.1f}%"
                    tgt_str = f"/ {target:.1f}%" if target else ""
                else:
                    val_str = f"{total:.0f}"
                    tgt_str = f"/ {target:.0f}" if target else ""
                lines.append(f"  {name:<28} {val_str} {tgt_str}")
        else:
            lines.append("  No metrics recorded this week.")
            lines.append("  Run: python -m aionos.ops.cli metric record ...")
        return "\n".join(lines)

    def _auto_record_metrics(self) -> None:
        """Auto-record pipeline metrics for the current week."""
        try:
            pipe = self._get_pipeline()
            counts = pipe.count_by_stage()
            week = _get_current_week()
            total = sum(counts.values())
            engaged = sum(
                counts.get(s, 0) for s in
                ["engaged", "demo_scheduled", "demo_completed",
                 "proposal_sent", "negotiation", "closed_won"]
            )
            won = counts.get("closed_won", 0)

            self._ops.record_metric(
                "total_prospects", total, period=week,
                category="sales", metric_type="count",
            )
            self._ops.record_metric(
                "engaged_prospects", engaged, period=week,
                category="sales", metric_type="count",
            )
            self._ops.record_metric(
                "closed_won", won, period=week,
                category="sales", metric_type="count",
            )
        except Exception:
            pass

    def generate_weekly_review(self) -> str:
        """Generate and store a weekly review from current data."""
        week = _get_current_week()

        # Pipeline summary
        pipeline = self._pipeline_health()

        # Metrics
        metrics = self._weekly_metrics()

        # Active memos
        active = self._ops.list_memos(status="active")
        memo_summary = "\n".join(
            f"  - [{m['category']}] {m['title']}" for m in active
        ) or "  No active memos."

        # Playbooks
        pb_summary = self._playbook_status()

        review_text = (
            f"WEEKLY REVIEW -- {week}\n"
            f"{'=' * 40}\n\n"
            f"{pipeline}\n\n"
            f"{metrics}\n\n"
            f"  --- ACTIVE MEMOS ---\n{memo_summary}\n\n"
            f"{pb_summary}"
        )

        self._ops.create_review(
            pipeline_summary=pipeline,
            metrics_summary=metrics,
            week=week,
        )

        return review_text


def main():
    """Run daily ops report."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    runner = OpsRunner()
    report = runner.run_daily()
    print(report)


if __name__ == "__main__":
    main()
