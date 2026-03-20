"""
AION OS -- Evolution Engine (Learner)
========================================
Self-improving feedback loop that runs after every deal close,
playbook completion, and weekly review cycle.

Analyzes operational data. Extracts patterns. Generates insights.
Feeds improvements back into the system.

All local. Zero cloud. Part of the AION OS ecosystem.

Usage:
    python -m aionos.ops.cli learn             # run full learning cycle
    python -m aionos.ops.cli learn deals        # analyze closed deals only
    python -m aionos.ops.cli learn playbooks    # analyze playbook efficiency
    python -m aionos.ops.cli learn velocity     # pipeline velocity analysis
    python -m aionos.ops.cli learn insights     # view stored insights
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from aionos.ops.store import OpsStore, _get_current_week


class EvolutionEngine:
    """
    AION OS self-improvement engine.

    After each sales cycle, playbook execution, or review period,
    the engine analyzes outcomes and generates actionable insights
    that feed back into the system.

    Think of it as AION learning from its own ops data.
    """

    def __init__(self, ops: Optional[OpsStore] = None) -> None:
        self._ops = ops or OpsStore()
        self._pipeline = None
        self._insights: List[Dict] = []

    def _get_pipeline(self):
        if self._pipeline is None:
            from aionos.sales.prospects import Pipeline
            self._pipeline = Pipeline()
        return self._pipeline

    # ================================================================
    #  DEAL ANALYSIS
    # ================================================================

    def analyze_deals(self) -> str:
        """
        Analyze all closed deals (won + lost).
        Extract: stage durations, winning patterns, failure points.
        """
        pipe = self._get_pipeline()
        lines = []
        lines.append("  --- DEAL PATTERN ANALYSIS ---")

        won = pipe.list_all(stage="closed_won")
        lost = pipe.list_all(stage="closed_lost")

        if not won and not lost:
            lines.append("  No closed deals yet. Skipping deal analysis.")
            return "\n".join(lines)

        # Analyze won deals
        if won:
            lines.append(f"\n  WINS: {len(won)} deals closed")
            won_data = self._analyze_deal_set(won, pipe)
            lines.extend(won_data["lines"])

            # Store insights
            for insight in won_data["insights"]:
                self._record_insight("deal_win", insight)

        # Analyze lost deals
        if lost:
            lines.append(f"\n  LOSSES: {len(lost)} deals lost")
            lost_data = self._analyze_deal_set(lost, pipe)
            lines.extend(lost_data["lines"])

            for insight in lost_data["insights"]:
                self._record_insight("deal_loss", insight)

        # Win rate
        total = len(won) + len(lost)
        if total > 0:
            rate = len(won) / total * 100
            lines.append(f"\n  WIN RATE: {rate:.0f}% ({len(won)}/{total})")
            self._record_insight(
                "conversion",
                f"Overall win rate: {rate:.0f}% ({len(won)} won, {len(lost)} lost)"
            )

        # Vertical breakdown
        vert_wins = defaultdict(int)
        vert_losses = defaultdict(int)
        for p in won:
            vert_wins[p["vertical"]] += 1
        for p in lost:
            vert_losses[p["vertical"]] += 1

        all_verts = set(list(vert_wins.keys()) + list(vert_losses.keys()))
        if all_verts:
            lines.append("\n  BY VERTICAL:")
            for v in sorted(all_verts):
                w = vert_wins.get(v, 0)
                l = vert_losses.get(v, 0)
                t = w + l
                r = w / t * 100 if t > 0 else 0
                lines.append(f"    {v:<14} {w}W / {l}L  ({r:.0f}% win rate)")
                if r >= 50 and t >= 2:
                    self._record_insight(
                        "vertical_strength",
                        f"{v} vertical converting at {r:.0f}% -- double down on outreach"
                    )
                elif r < 30 and t >= 3:
                    self._record_insight(
                        "vertical_weakness",
                        f"{v} vertical converting at {r:.0f}% -- review messaging or deprioritize"
                    )

        return "\n".join(lines)

    def _analyze_deal_set(self, prospects: List[Dict], pipe) -> Dict:
        """Analyze a set of deals (won or lost) for patterns."""
        lines = []
        insights = []
        touch_counts = []
        stage_times = defaultdict(list)

        for p in prospects:
            history = pipe.get_history(p["id"])
            if not history:
                continue

            touch_counts.append(len(history))

            # Calculate time between stage transitions
            stage_transitions = [
                h for h in history
                if h["action"].startswith("Stage")
            ]
            for i in range(1, len(stage_transitions)):
                prev = stage_transitions[i - 1]
                curr = stage_transitions[i]
                prev_stage = prev["action"].split("→")[-1].strip() if "→" in prev["action"] else "unknown"
                try:
                    t1 = datetime.fromisoformat(prev["timestamp"])
                    t2 = datetime.fromisoformat(curr["timestamp"])
                    days = (t2 - t1).total_seconds() / 86400
                    stage_times[prev_stage].append(days)
                except (ValueError, TypeError):
                    pass

        # Touch count stats
        if touch_counts:
            avg_touches = statistics.mean(touch_counts)
            lines.append(f"    Avg touches to close: {avg_touches:.1f}")
            if avg_touches > 10:
                insights.append(
                    f"Deals require {avg_touches:.0f} avg touches -- consider more aggressive follow-up cadence"
                )
            elif avg_touches <= 3:
                insights.append(
                    f"Deals closing in {avg_touches:.0f} touches -- messaging is landing well"
                )

        # Stage duration stats
        if stage_times:
            lines.append("    Stage durations (avg days):")
            for stage, durations in sorted(stage_times.items()):
                if durations:
                    avg = statistics.mean(durations)
                    lines.append(f"      {stage:<20} {avg:.1f} days")
                    if avg > 14:
                        insights.append(
                            f"Deals stalling at '{stage}' stage ({avg:.0f} days avg) -- needs intervention template"
                        )

        return {"lines": lines, "insights": insights}

    # ================================================================
    #  PLAYBOOK EFFICIENCY
    # ================================================================

    def analyze_playbooks(self) -> str:
        """
        Analyze playbook execution patterns.
        Find: bottleneck steps, completion rates, execution frequency.
        """
        lines = []
        lines.append("  --- PLAYBOOK EFFICIENCY ---")

        playbooks = self._ops.list_playbooks()
        if not playbooks:
            lines.append("  No playbooks found.")
            return "\n".join(lines)

        for pb in playbooks:
            lines.append(f"\n  #{pb['id']} {pb['name']} [{pb['category']}]")
            lines.append(f"    Status: {pb['status']}  |  Runs: {pb.get('run_count', 0)}")

            steps = pb.get("steps", [])
            if not steps:
                continue

            total = len(steps)
            done = sum(1 for s in steps if s.get("status") == "completed")
            lines.append(f"    Progress: {done}/{total} steps ({done/total*100:.0f}%)")

            # Find steps with notes (they carry operational knowledge)
            noted_steps = [s for s in steps if s.get("notes")]
            if noted_steps:
                lines.append(f"    Steps with notes: {len(noted_steps)}/{total} (institutional knowledge captured)")

            # Identify bottleneck (first incomplete step in an in_progress playbook)
            if pb["status"] == "in_progress":
                for s in steps:
                    if s.get("status") != "completed":
                        lines.append(f"    >> BOTTLENECK: Step {s['step_num']} -- {s['action'][:50]}")
                        self._record_insight(
                            "playbook_bottleneck",
                            f"Playbook '{pb['name']}' blocked at step {s['step_num']}: {s['action'][:80]}"
                        )
                        break

            # Suggest playbook improvements based on run count
            runs = pb.get("run_count", 0)
            if runs >= 3 and total > 6:
                self._record_insight(
                    "playbook_optimization",
                    f"'{pb['name']}' has run {runs}x with {total} steps -- consider splitting into sub-playbooks"
                )
            if runs == 0 and pb["status"] == "not_started":
                self._record_insight(
                    "playbook_unused",
                    f"'{pb['name']}' has never been executed -- activate or archive"
                )

        return "\n".join(lines)

    # ================================================================
    #  PIPELINE VELOCITY
    # ================================================================

    def analyze_velocity(self) -> str:
        """
        Analyze pipeline velocity -- how fast prospects move through stages.
        Identify stall points and acceleration opportunities.
        """
        pipe = self._get_pipeline()
        lines = []
        lines.append("  --- PIPELINE VELOCITY ---")

        all_prospects = pipe.list_all()
        if not all_prospects:
            lines.append("  No prospects in pipeline.")
            return "\n".join(lines)

        # Age analysis by stage
        stage_ages = defaultdict(list)
        now = datetime.now().isoformat()

        for p in all_prospects:
            created = p.get("created", "")
            if not created:
                continue
            try:
                created_dt = datetime.fromisoformat(created)
                age_days = (datetime.now() - created_dt).total_seconds() / 86400
                stage_ages[p["stage"]].append(age_days)
            except (ValueError, TypeError):
                pass

        if stage_ages:
            lines.append(f"\n  {'Stage':<20} {'Count':>5} {'Avg Age':>10} {'Oldest':>10}")
            lines.append(f"  {'-'*20} {'-'*5} {'-'*10} {'-'*10}")
            for stage in ["cold", "engaged", "demo_scheduled", "demo_completed",
                          "proposal_sent", "negotiation", "closed_won", "closed_lost"]:
                ages = stage_ages.get(stage, [])
                if ages:
                    avg = statistics.mean(ages)
                    oldest = max(ages)
                    lines.append(
                        f"  {stage:<20} {len(ages):>5} {avg:>8.1f}d {oldest:>8.1f}d"
                    )
                    # Flag stale buckets
                    if stage in ("engaged", "demo_scheduled", "demo_completed") and avg > 7:
                        self._record_insight(
                            "velocity_stall",
                            f"'{stage}' prospects averaging {avg:.0f} days -- need follow-up blitz"
                        )
                    if stage == "negotiation" and avg > 14:
                        self._record_insight(
                            "velocity_stall",
                            f"Negotiation stage averaging {avg:.0f} days -- add urgency or concession offer"
                        )

        # Cold prospect analysis
        cold = [p for p in all_prospects if p["stage"] == "cold"]
        engaged_or_beyond = [p for p in all_prospects if p["stage"] != "cold"]
        if all_prospects:
            activation_rate = len(engaged_or_beyond) / len(all_prospects) * 100
            lines.append(f"\n  ACTIVATION RATE: {activation_rate:.0f}% ({len(engaged_or_beyond)}/{len(all_prospects)} moved past cold)")
            if activation_rate < 10:
                self._record_insight(
                    "activation_low",
                    f"Only {activation_rate:.0f}% of prospects activated -- cold outreach needs improvement"
                )

        # Stale prospect count
        stale = pipe.stale_prospects(days=5)
        if stale:
            lines.append(f"  STALE (>5 days no contact): {len(stale)} prospects")
            if len(stale) > len(all_prospects) * 0.5:
                self._record_insight(
                    "pipeline_decay",
                    f"{len(stale)} of {len(all_prospects)} prospects are stale -- pipeline is decaying"
                )

        return "\n".join(lines)

    # ================================================================
    #  METRIC TRENDS
    # ================================================================

    def analyze_metrics(self) -> str:
        """
        Analyze metric trends over time.
        Detect improvements, regressions, and missed targets.
        """
        lines = []
        lines.append("  --- METRIC TREND ANALYSIS ---")

        # Get current week metrics
        summary = self._ops.metrics_summary()
        if not summary:
            lines.append("  No metrics recorded yet.")
            return "\n".join(lines)

        lines.append(f"\n  {'Metric':<24} {'Value':>10} {'Target':>10} {'Status':>10}")
        lines.append(f"  {'-'*24} {'-'*10} {'-'*10} {'-'*10}")

        for name, data in sorted(summary.items()):
            val = data.get("total", 0)
            target = data.get("target", 0)
            if target > 0:
                pct = val / target * 100
                if pct >= 100:
                    status = "HIT"
                elif pct >= 70:
                    status = "ON TRACK"
                elif pct >= 40:
                    status = "BEHIND"
                else:
                    status = "AT RISK"
            else:
                status = "-"

            mtype = data.get("metric_type", "count")
            if mtype == "currency":
                val_str = f"${val:,.0f}"
                tgt_str = f"${target:,.0f}" if target else "-"
            elif mtype == "percent":
                val_str = f"{val:.1f}%"
                tgt_str = f"{target:.1f}%" if target else "-"
            else:
                val_str = f"{val:.0f}"
                tgt_str = f"{target:.0f}" if target else "-"

            lines.append(f"  {name:<24} {val_str:>10} {tgt_str:>10} {status:>10}")

            if status == "AT RISK":
                self._record_insight(
                    "metric_risk",
                    f"'{name}' at {pct:.0f}% of target -- needs immediate attention"
                )
            elif status == "HIT":
                self._record_insight(
                    "metric_win",
                    f"'{name}' target hit ({val_str} / {tgt_str}) -- raise the bar next week"
                )

        return "\n".join(lines)

    # ================================================================
    #  INSIGHT ENGINE
    # ================================================================

    def _record_insight(self, category: str, insight: str) -> None:
        """Record an insight discovered during analysis."""
        self._insights.append({
            "category": category,
            "insight": insight,
            "discovered": date.today().isoformat(),
            "week": _get_current_week(),
        })

    def get_insights(self) -> List[Dict]:
        """Return all insights from this learning cycle."""
        return self._insights

    def format_insights(self) -> str:
        """Format insights into a readable report."""
        if not self._insights:
            return "  No new insights generated."

        lines = []
        lines.append("  --- AION OS EVOLUTION INSIGHTS ---")
        lines.append(f"  Generated: {date.today()} | Week: {_get_current_week()}")
        lines.append("")

        # Group by category
        by_cat = defaultdict(list)
        for i in self._insights:
            by_cat[i["category"]].append(i["insight"])

        # Priority order
        priority = [
            ("metric_risk", "URGENT -- Metrics at Risk"),
            ("pipeline_decay", "URGENT -- Pipeline Health"),
            ("velocity_stall", "ACTION -- Pipeline Velocity"),
            ("activation_low", "ACTION -- Outreach Effectiveness"),
            ("deal_loss", "LEARN -- Deal Losses"),
            ("playbook_bottleneck", "FIX -- Playbook Bottlenecks"),
            ("playbook_unused", "CLEAN -- Unused Playbooks"),
            ("vertical_weakness", "REVIEW -- Weak Verticals"),
            ("deal_win", "REINFORCE -- Winning Patterns"),
            ("metric_win", "CELEBRATE -- Targets Hit"),
            ("vertical_strength", "DOUBLE DOWN -- Strong Verticals"),
            ("conversion", "BENCHMARK -- Conversion"),
            ("playbook_optimization", "OPTIMIZE -- Playbook Efficiency"),
        ]

        for cat, label in priority:
            items = by_cat.get(cat, [])
            if items:
                lines.append(f"  [{label}]")
                for item in items:
                    lines.append(f"    -> {item}")
                lines.append("")

        # Catch any uncategorized
        known = {p[0] for p in priority}
        for cat, items in by_cat.items():
            if cat not in known:
                lines.append(f"  [{cat.upper()}]")
                for item in items:
                    lines.append(f"    -> {item}")
                lines.append("")

        return "\n".join(lines)

    def persist_insights(self) -> None:
        """
        Store insights as a memo so they're part of the ops record.
        This is how AION OS remembers what it learned.
        """
        if not self._insights:
            return

        week = _get_current_week()
        insight_text = "\n".join(
            f"- [{i['category']}] {i['insight']}"
            for i in self._insights
        )

        # Check if we already have a learning memo for this week
        existing = self._ops.list_memos(category="operations", status="active")
        for m in existing:
            if f"Evolution -- {week}" in m.get("title", ""):
                # Update the existing memo
                self._ops.update_memo(
                    m["id"],
                    issue=insight_text,
                    strategy=self._generate_recommendations(),
                )
                return

        # Create new evolution memo
        mid = self._ops.create_memo(
            title=f"AION OS Evolution -- {week}",
            category="operations",
            issue=insight_text,
            strategy=self._generate_recommendations(),
            metrics=f"{len(self._insights)} insights generated",
            review_date=(date.today() + timedelta(days=7)).isoformat(),
        )
        self._ops.activate_memo(mid)

    def _generate_recommendations(self) -> str:
        """
        Turn raw insights into concrete next actions.
        This is where AION OS tells you what to change.
        """
        recs = []

        by_cat = defaultdict(list)
        for i in self._insights:
            by_cat[i["category"]].append(i["insight"])

        if "metric_risk" in by_cat:
            recs.append("PRIORITY: Address at-risk metrics before next weekly review")

        if "pipeline_decay" in by_cat:
            recs.append("PRIORITY: Run mass outreach today -- pipeline is going stale")

        if "velocity_stall" in by_cat:
            recs.append("Schedule follow-up blitz for stalled prospects this week")

        if "activation_low" in by_cat:
            recs.append("Rewrite cold email subject lines -- current activation rate is too low")
            recs.append("Test new LinkedIn connection message variants")

        if "deal_loss" in by_cat:
            recs.append("Review lost deal patterns -- identify common objection or stall point")

        if "playbook_bottleneck" in by_cat:
            recs.append("Resolve blocked playbook steps or reassign to unblock")

        if "vertical_weakness" in by_cat:
            recs.append("Review messaging for underperforming verticals or reallocate effort")

        if "vertical_strength" in by_cat:
            recs.append("Increase outreach volume in high-converting verticals")

        if "metric_win" in by_cat:
            recs.append("Raise metric targets for next week -- current targets are too easy")

        if not recs:
            recs.append("No urgent actions. Continue current execution cadence.")

        return "\n".join(f"{i+1}. {r}" for i, r in enumerate(recs))

    # ================================================================
    #  FULL LEARNING CYCLE
    # ================================================================

    def run_full_cycle(self) -> str:
        """
        Run the complete AION OS evolution cycle.
        Analyzes everything, generates insights, persists learnings.
        Returns the full report.
        """
        self._insights = []  # reset

        lines = []
        lines.append("=" * 60)
        lines.append(f"  AION OS EVOLUTION ENGINE -- {date.today()}")
        lines.append(f"  Week: {_get_current_week()}")
        lines.append("=" * 60)
        lines.append("")

        # Run all analyses
        lines.append(self.analyze_deals())
        lines.append("")
        lines.append(self.analyze_playbooks())
        lines.append("")
        lines.append(self.analyze_velocity())
        lines.append("")
        lines.append(self.analyze_metrics())
        lines.append("")

        # Generate and display insights
        lines.append(self.format_insights())

        # Persist as a memo (AION remembers what it learned)
        self.persist_insights()
        if self._insights:
            lines.append(f"  >> {len(self._insights)} insights persisted to ops store")
            lines.append(f"  >> Learning memo created/updated for {_get_current_week()}")

        lines.append("")
        lines.append("-" * 60)
        lines.append("  AION OS learns from every cycle. Zero cloud. All local.")

        return "\n".join(lines)
