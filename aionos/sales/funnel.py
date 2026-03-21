"""
EchoWorks Sales Engine -- Funnel Automation
==============================================
Lead scoring, deal health monitoring, auto-advance,
stuck deal detection, and funnel analytics.

Usage:
    from aionos.sales.funnel import FunnelEngine
    engine = FunnelEngine()
    engine.score_all()        # score every prospect
    engine.health_check()     # flag stuck/at-risk deals
    engine.auto_advance()     # advance deals based on signals
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from aionos.sales.prospects import Pipeline
from aionos.sales.models import DealStage


# ── Scoring weights ──────────────────────────────────────────

_SCORE_WEIGHTS = {
    # Activity-based
    "has_email": 10,
    "has_linkedin": 5,
    "has_phone": 5,
    "has_title": 5,
    "has_notes": 3,

    # Engagement signals
    "action_contacted": 8,
    "action_replied": 20,
    "action_demo_booked": 30,
    "action_proposal_requested": 25,

    # Stage progression
    "stage_engaged": 15,
    "stage_demo_scheduled": 25,
    "stage_demo_completed": 35,
    "stage_proposal_sent": 45,
    "stage_negotiation": 60,

    # Recency
    "contacted_last_3_days": 10,
    "contacted_last_7_days": 5,

    # Penalties
    "stale_7_days": -15,
    "stale_14_days": -25,
    "stale_30_days": -40,
}

# Max days in stage before flagged as stuck
_STAGE_VELOCITY = {
    "cold": 14,
    "engaged": 10,
    "demo_scheduled": 7,
    "demo_completed": 7,
    "proposal_sent": 14,
    "negotiation": 21,
}


class DealHealth:
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    STUCK = "stuck"
    DEAD = "dead"


class FunnelEngine:
    """
    Automated sales funnel intelligence:
    - Lead scoring (0-100)
    - Deal health monitoring
    - Auto-advance on engagement signals
    - Stuck deal alerts
    - Funnel analytics
    """

    def __init__(self, pipeline: Optional[Pipeline] = None) -> None:
        self._pipe = pipeline or Pipeline()

    # ═══════════════════════════════════════════════════════════
    #  LEAD SCORING
    # ═══════════════════════════════════════════════════════════

    def score_prospect(self, prospect: Dict) -> int:
        """Score a single prospect 0-100 based on data quality + engagement."""
        score = 0

        # Data completeness
        if prospect.get("email"):
            score += _SCORE_WEIGHTS["has_email"]
        if prospect.get("linkedin"):
            score += _SCORE_WEIGHTS["has_linkedin"]
        if prospect.get("phone"):
            score += _SCORE_WEIGHTS["has_phone"]
        if prospect.get("title"):
            score += _SCORE_WEIGHTS["has_title"]
        if prospect.get("notes"):
            score += _SCORE_WEIGHTS["has_notes"]

        # Stage progression
        stage = prospect.get("stage", "cold")
        stage_key = f"stage_{stage}"
        if stage_key in _SCORE_WEIGHTS:
            score += _SCORE_WEIGHTS[stage_key]

        # Activity history
        pid = prospect.get("id")
        if pid:
            history = self._pipe.get_history(pid)
            for entry in history:
                action = entry.get("action", "").lower()
                if "replied" in action or "responded" in action:
                    score += _SCORE_WEIGHTS["action_replied"]
                elif "demo" in action and "book" in action:
                    score += _SCORE_WEIGHTS["action_demo_booked"]
                elif "proposal" in action:
                    score += _SCORE_WEIGHTS["action_proposal_requested"]
                elif "contacted" in action or "sent" in action:
                    score += _SCORE_WEIGHTS["action_contacted"]

        # Recency
        last_action = prospect.get("last_action_date", "")
        if last_action:
            try:
                last_dt = datetime.fromisoformat(last_action.replace("Z", "+00:00"))
                days_ago = (datetime.now(last_dt.tzinfo or None) - last_dt).days
            except (ValueError, TypeError):
                days_ago = 999

            if days_ago <= 3:
                score += _SCORE_WEIGHTS["contacted_last_3_days"]
            elif days_ago <= 7:
                score += _SCORE_WEIGHTS["contacted_last_7_days"]

            # Penalties for stale
            if days_ago >= 30:
                score += _SCORE_WEIGHTS["stale_30_days"]
            elif days_ago >= 14:
                score += _SCORE_WEIGHTS["stale_14_days"]
            elif days_ago >= 7:
                score += _SCORE_WEIGHTS["stale_7_days"]

        return max(0, min(100, score))

    def score_all(self) -> List[Dict]:
        """Score all active prospects. Returns sorted list."""
        prospects = self._pipe.list_all()
        scored = []
        for p in prospects:
            stage = p.get("stage", "cold")
            if stage in ("closed_won", "closed_lost"):
                continue
            score = self.score_prospect(p)
            scored.append({**p, "lead_score": score})
        scored.sort(key=lambda x: x["lead_score"], reverse=True)
        return scored

    # ═══════════════════════════════════════════════════════════
    #  DEAL HEALTH
    # ═══════════════════════════════════════════════════════════

    def assess_health(self, prospect: Dict) -> Tuple[str, str]:
        """
        Assess deal health for a single prospect.
        Returns (health_status, reason).
        """
        stage = prospect.get("stage", "cold")

        if stage in ("closed_won", "closed_lost"):
            return (DealHealth.HEALTHY, "Closed")

        last_action = prospect.get("last_action_date", "")
        if not last_action:
            return (DealHealth.AT_RISK, "No contact recorded")

        try:
            last_dt = datetime.fromisoformat(last_action.replace("Z", "+00:00"))
            days_since = (datetime.now(last_dt.tzinfo or None) - last_dt).days
        except (ValueError, TypeError):
            days_since = 999

        max_days = _STAGE_VELOCITY.get(stage, 14)

        if days_since > max_days * 3:
            return (DealHealth.DEAD, f"No activity for {days_since} days in {stage}")
        elif days_since > max_days * 2:
            return (DealHealth.STUCK, f"Stuck in {stage} for {days_since} days (max: {max_days})")
        elif days_since > max_days:
            return (DealHealth.AT_RISK, f"Overdue in {stage}: {days_since}/{max_days} days")
        else:
            return (DealHealth.HEALTHY, f"On track: {days_since}/{max_days} days in {stage}")

    def health_check(self) -> Dict[str, List[Dict]]:
        """Run health check on entire pipeline. Returns categorized results."""
        prospects = self._pipe.list_all()
        results = {
            DealHealth.HEALTHY: [],
            DealHealth.AT_RISK: [],
            DealHealth.STUCK: [],
            DealHealth.DEAD: [],
        }

        for p in prospects:
            stage = p.get("stage", "cold")
            if stage in ("closed_won", "closed_lost"):
                continue
            health, reason = self.assess_health(p)
            results[health].append({**p, "health": health, "health_reason": reason})

        return results

    # ═══════════════════════════════════════════════════════════
    #  AUTO-ADVANCE
    # ═══════════════════════════════════════════════════════════

    def auto_advance(self) -> List[str]:
        """
        Check activity logs for engagement signals and
        auto-advance prospects that qualify.
        Returns list of actions taken.
        """
        actions = []
        prospects = self._pipe.list_all()

        for p in prospects:
            pid = p["id"]
            stage = p.get("stage", "cold")

            if stage in ("closed_won", "closed_lost"):
                continue

            history = self._pipe.get_history(pid)
            if not history:
                continue

            new_stage = self._infer_stage(stage, history)
            if new_stage and new_stage != stage:
                self._pipe.advance(pid, new_stage)
                action = f"Auto-advanced #{pid} {p['name']} ({p['company']}): {stage} -> {new_stage}"
                actions.append(action)

        return actions

    def _infer_stage(self, current_stage: str, history: List[Dict]) -> Optional[str]:
        """Infer the correct stage from activity history."""
        actions_lower = [h.get("action", "").lower() for h in history]
        all_text = " ".join(actions_lower)

        # Stage ladder -- only advance forward
        stage_order = [
            "cold", "engaged", "demo_scheduled", "demo_completed",
            "proposal_sent", "negotiation", "closed_won",
        ]

        try:
            current_idx = stage_order.index(current_stage)
        except ValueError:
            return None

        inferred = current_stage

        # Cold -> Engaged: replied, responded, connected, accepted
        if current_idx < stage_order.index("engaged"):
            engagement_signals = ["replied", "responded", "connected", "accepted", "interested"]
            if any(sig in all_text for sig in engagement_signals):
                inferred = "engaged"

        # Engaged -> Demo Scheduled: demo booked, meeting scheduled, calendar
        if stage_order.index(inferred) < stage_order.index("demo_scheduled"):
            demo_signals = ["demo booked", "demo scheduled", "meeting scheduled", "calendar sent"]
            if any(sig in all_text for sig in demo_signals):
                inferred = "demo_scheduled"

        # Demo Scheduled -> Demo Completed: demo completed, demo done, presented
        if stage_order.index(inferred) < stage_order.index("demo_completed"):
            completed_signals = ["demo completed", "demo done", "presented", "showed demo"]
            if any(sig in all_text for sig in completed_signals):
                inferred = "demo_completed"

        # Demo Completed -> Proposal Sent: proposal sent, quote sent, pricing sent
        if stage_order.index(inferred) < stage_order.index("proposal_sent"):
            proposal_signals = ["proposal sent", "quote sent", "pricing sent", "sow sent"]
            if any(sig in all_text for sig in proposal_signals):
                inferred = "proposal_sent"

        # Proposal -> Negotiation: negotiating, counteroffer, discussing terms
        if stage_order.index(inferred) < stage_order.index("negotiation"):
            neg_signals = ["negotiat", "counteroffer", "discussing terms", "reviewing proposal"]
            if any(sig in all_text for sig in neg_signals):
                inferred = "negotiation"

        # Negotiation -> Closed Won: signed, contract executed, payment received
        if stage_order.index(inferred) < stage_order.index("closed_won"):
            win_signals = ["signed", "contract executed", "payment received", "closed won", "deal closed"]
            if any(sig in all_text for sig in win_signals):
                inferred = "closed_won"

        return inferred if inferred != current_stage else None

    # ═══════════════════════════════════════════════════════════
    #  FUNNEL ANALYTICS
    # ═══════════════════════════════════════════════════════════

    def funnel_report(self) -> str:
        """Generate a full funnel analytics report."""
        scored = self.score_all()
        health = self.health_check()

        lines = []
        lines.append("=" * 60)
        lines.append("  SALES FUNNEL REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Stage distribution
        stage_counts = {}
        for p in scored:
            s = p.get("stage", "cold")
            stage_counts[s] = stage_counts.get(s, 0) + 1

        lines.append("  --- PIPELINE BY STAGE ---")
        stage_order = ["cold", "engaged", "demo_scheduled", "demo_completed",
                       "proposal_sent", "negotiation"]
        total = len(scored)
        for stage in stage_order:
            count = stage_counts.get(stage, 0)
            pct = (count / total * 100) if total else 0
            bar = "#" * min(int(pct), 40)
            lines.append(f"  {stage:<18} {count:>3} ({pct:4.1f}%)  {bar}")
        lines.append(f"  {'TOTAL':<18} {total:>3}")
        lines.append("")

        # Conversion funnel
        lines.append("  --- CONVERSION FUNNEL ---")
        prev = total
        for stage in stage_order[1:]:
            count = stage_counts.get(stage, 0)
            for later in stage_order[stage_order.index(stage) + 1:]:
                count += stage_counts.get(later, 0)
            conv = (count / prev * 100) if prev else 0
            lines.append(f"  {stage_order[stage_order.index(stage) - 1]:<16} -> {stage:<16} {conv:5.1f}%")
            prev = count if count else prev
        lines.append("")

        # Deal health summary
        lines.append("  --- DEAL HEALTH ---")
        for status in [DealHealth.HEALTHY, DealHealth.AT_RISK, DealHealth.STUCK, DealHealth.DEAD]:
            count = len(health[status])
            icon = {"healthy": "[OK]", "at_risk": "[!!]", "stuck": "[XX]", "dead": "[--]"}[status]
            lines.append(f"  {icon} {status:<12} {count}")
        lines.append("")

        # Top scored prospects
        lines.append("  --- TOP PROSPECTS (by lead score) ---")
        for p in scored[:10]:
            health_status, _ = self.assess_health(p)
            h_icon = {"healthy": "+", "at_risk": "!", "stuck": "X", "dead": "-"}.get(health_status, "?")
            lines.append(
                f"  [{h_icon}] #{p['id']:>3} {p['name']:<20} {p['company']:<20} "
                f"Score:{p['lead_score']:>3} Stage:{p['stage']}"
            )
        lines.append("")

        # At-risk deals needing action
        at_risk = health[DealHealth.AT_RISK] + health[DealHealth.STUCK]
        if at_risk:
            lines.append("  --- DEALS NEEDING ACTION ---")
            for p in at_risk[:10]:
                lines.append(
                    f"  >> #{p['id']:>3} {p['name']:<20} {p['company']:<20} "
                    f"[{p['health']}] {p['health_reason']}"
                )
            lines.append("")

        # Vertical breakdown
        lines.append("  --- BY VERTICAL ---")
        v_counts = {}
        for p in scored:
            v = p.get("vertical", "unknown")
            v_counts[v] = v_counts.get(v, 0) + 1
        for v, c in sorted(v_counts.items()):
            lines.append(f"  {v:<16} {c}")
        lines.append("")

        lines.append("-" * 60)
        lines.append("  All data local. Zero cloud. AION OS sales intelligence.")
        return "\n".join(lines)
