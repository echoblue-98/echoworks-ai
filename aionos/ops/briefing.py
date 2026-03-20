"""
AION OS -- Daily Briefing Engine
===================================
Generates a structured executive briefing that a tech sales person
can read to the founder in under 2 minutes.

Three outputs:
  1. Terminal briefing (CLI)
  2. Markdown file (saved to aionos/ops/briefs/)
  3. One-liner summary for toast notifications

All local. Zero cloud. Part of the AION OS ecosystem.

Usage:
    python -m aionos.ops.cli brief           # display briefing
    python -m aionos.ops.cli brief --save    # save to file
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from aionos.ops.store import OpsStore, _get_current_week
from aionos.ops.learner import EvolutionEngine


_BRIEF_DIR = os.path.join(os.path.dirname(__file__), "briefs")


class Briefing:
    """
    Generates a complete daily briefing for EchoWorks AI.

    This is what a sales person reads to the founder every morning:
      - Pipeline snapshot (10 seconds)
      - Urgent actions (20 seconds)
      - What happened since last brief (20 seconds)
      - Key metrics vs targets (15 seconds)
      - Evolution insights (15 seconds)
      - Today's execution plan (15 seconds)
    """

    def __init__(self, ops: Optional[OpsStore] = None) -> None:
        self._ops = ops or OpsStore()
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            from aionos.sales.prospects import Pipeline
            self._pipeline = Pipeline()
        return self._pipeline

    def generate(self) -> Dict:
        """
        Generate the full briefing. Returns a dict with:
          - text: full briefing string
          - summary: one-liner for notifications
          - urgency: 'green' | 'yellow' | 'red'
          - urgent_count: number of urgent items
          - file_path: path if saved
        """
        sections = []
        urgent_items = []
        today = date.today()
        week = _get_current_week()

        # ── HEADER ──
        sections.append("=" * 60)
        sections.append(f"  AION OS DAILY BRIEFING -- {today.strftime('%A, %B %d, %Y')}")
        sections.append(f"  Week: {week}")
        sections.append("=" * 60)
        sections.append("")

        # ── 1. PIPELINE SNAPSHOT ──
        pipe = self._get_pipeline()
        stages = pipe.count_by_stage()
        total = sum(stages.values())
        sections.append("  [1] PIPELINE SNAPSHOT")
        sections.append(f"  Total prospects: {total}")

        active_stages = ["engaged", "demo_scheduled", "demo_completed",
                         "proposal_sent", "negotiation"]
        active = sum(stages.get(s, 0) for s in active_stages)
        won = stages.get("closed_won", 0)
        cold = stages.get("cold", 0)
        sections.append(f"  Active deals: {active}  |  Won: {won}  |  Cold: {cold}")

        if total > 0 and cold / total > 0.9:
            urgent_items.append("90%+ of pipeline is cold -- need outbound blitz")

        sections.append("")

        # ── 2. URGENT ACTIONS ──
        sections.append("  [2] URGENT ACTIONS")

        # Stale prospects
        stale = pipe.stale_prospects(days=5)
        if stale:
            sections.append(f"  >> {len(stale)} prospects have gone stale (no contact >5 days)")
            if len(stale) > 10:
                urgent_items.append(f"{len(stale)} stale prospects")

        # Memos due for review
        due_memos = self._ops.memos_due_for_review()
        if due_memos:
            sections.append(f"  >> {len(due_memos)} memos due for review:")
            for m in due_memos[:3]:
                sections.append(f"     - #{m['id']} {m['title']}")
            urgent_items.append(f"{len(due_memos)} memos overdue for review")

        # Blocked playbooks
        playbooks = self._ops.list_playbooks(status="in_progress")
        blocked_steps = []
        for pb in playbooks:
            steps = pb.get("steps", [])
            for s in steps:
                if s.get("status") != "completed":
                    blocked_steps.append((pb["name"], s["step_num"], s["action"][:50]))
                    break
        if blocked_steps:
            sections.append(f"  >> {len(blocked_steps)} playbooks need next step:")
            for name, step, action in blocked_steps[:3]:
                sections.append(f"     - {name}: Step {step} -- {action}")

        # Today's queue
        queue = pipe.daily_queue()
        if queue:
            by_vert = defaultdict(int)
            for p in queue:
                by_vert[p["vertical"]] += 1
            queue_str = ", ".join(f"{v} {c}" for v, c in sorted(by_vert.items()))
            sections.append(f"  >> Today's outbound queue: {len(queue)} prospects ({queue_str})")

        if not stale and not due_memos and not blocked_steps and not queue:
            sections.append("  No urgent actions.")

        sections.append("")

        # ── 3. KEY METRICS ──
        sections.append("  [3] KEY METRICS")
        summary = self._ops.metrics_summary()
        if summary:
            for name, data in sorted(summary.items()):
                val = data.get("total", 0)
                target = data.get("target", 0)
                mtype = data.get("metric_type", "count")

                if mtype == "currency":
                    val_str = f"${val:,.0f}"
                    tgt_str = f"${target:,.0f}" if target else "-"
                else:
                    val_str = f"{val:.0f}"
                    tgt_str = f"{target:.0f}" if target else "-"

                if target > 0:
                    pct = val / target * 100
                    bar_len = min(int(pct / 5), 20)
                    bar = "#" * bar_len + "." * (20 - bar_len)
                    sections.append(f"  {name:<20} {val_str:>8} / {tgt_str:<8} [{bar}] {pct:.0f}%")
                    if pct < 40:
                        urgent_items.append(f"{name} at {pct:.0f}% of target")
                else:
                    sections.append(f"  {name:<20} {val_str:>8}")
        else:
            sections.append("  No metrics recorded this week.")

        sections.append("")

        # ── 4. EVOLUTION INSIGHTS ──
        sections.append("  [4] AION OS LEARNING")
        evolution_memos = [
            m for m in self._ops.list_memos(category="operations", status="active")
            if "Evolution" in m.get("title", "")
        ]
        if evolution_memos:
            latest = evolution_memos[0]
            strategy = latest.get("strategy", "")
            if strategy:
                sections.append("  Latest recommendations:")
                for line in strategy.split("\n")[:5]:
                    sections.append(f"    {line}")
            insights_text = latest.get("issue", "")
            insight_count = insights_text.count("\n") + 1 if insights_text else 0
            sections.append(f"  ({insight_count} insights from last evolution cycle)")
        else:
            sections.append("  No evolution data yet. Run: python -m aionos.ops.cli learn")

        sections.append("")

        # ── 5. TODAY'S EXECUTION PLAN ──
        sections.append("  [5] TODAY'S PLAN")
        # Active playbooks with next step
        active_pbs = self._ops.list_playbooks(status="in_progress")
        if active_pbs:
            for pb in active_pbs:
                steps = pb.get("steps", [])
                for s in steps:
                    if s.get("status") != "completed":
                        sections.append(f"  [ ] {pb['name']}: Step {s['step_num']} -- {s['action'][:60]}")
                        break
        # Not-started playbooks (suggest activating)
        not_started = self._ops.list_playbooks(status="not_started")
        if not_started:
            sections.append(f"  {len(not_started)} playbooks ready to start:")
            for pb in not_started[:2]:
                sections.append(f"    > {pb['name']} ({len(pb.get('steps', []))} steps)")

        if queue:
            sections.append(f"  [ ] Send outbound to {min(len(queue), 10)} prospects")
        sections.append(f"  [ ] Record today's metrics before EOD")
        sections.append(f"  [ ] Run: python -m aionos.ops.cli learn (end of day)")

        sections.append("")

        # ── FOOTER ──
        sections.append("-" * 60)

        # Determine urgency
        if len(urgent_items) >= 3:
            urgency = "red"
        elif len(urgent_items) >= 1:
            urgency = "yellow"
        else:
            urgency = "green"

        urgency_label = {"green": "ALL CLEAR", "yellow": "NEEDS ATTENTION", "red": "URGENT"}
        sections.append(f"  STATUS: {urgency_label[urgency]} -- {len(urgent_items)} item(s) flagged")
        sections.append("  All data local. Zero cloud. AION OS ecosystem.")

        # Build summary for notifications
        if urgent_items:
            summary_text = f"AION OS: {len(urgent_items)} urgent -- {urgent_items[0]}"
        else:
            summary_text = f"AION OS: Pipeline {total} prospects, {won} won, {active} active. All clear."

        return {
            "text": "\n".join(sections),
            "summary": summary_text[:200],
            "urgency": urgency,
            "urgent_count": len(urgent_items),
            "urgent_items": urgent_items,
        }

    def save(self) -> str:
        """Generate and save briefing to file. Returns file path."""
        result = self.generate()
        os.makedirs(_BRIEF_DIR, exist_ok=True)
        today = date.today().isoformat()
        path = os.path.join(_BRIEF_DIR, f"brief_{today}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        result["file_path"] = path
        return path
