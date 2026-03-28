"""
AION OS — Friction Reducer
Automatically classifies tasks by complexity and delegates appropriately,
minimizing unnecessary human involvement while preserving oversight where it matters.

"The real value may come from building something that reduces friction, simplifies
work, and helps people operate with less stress." — Rich, March 26 2026

Decision framework:
    1. Score task complexity (0.0-1.0) via heuristics
    2. Check agent trust against complexity
    3. Route: AUTONOMOUS → SUPERVISED → MANUAL
    4. Learn from outcomes to improve routing
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aionos.agents.friction")


# =============================================================================
# DELEGATION MODES
# =============================================================================

class DelegationMode(Enum):
    """How a task should be executed."""
    AUTONOMOUS = "autonomous"        # agent handles it entirely
    SUPERVISED = "supervised"        # agent acts, human reviews result
    MANUAL = "manual"                # human must perform, agent assists


# =============================================================================
# TASK CLASSIFICATION
# =============================================================================

@dataclass
class TaskProfile:
    """Friction analysis of a task."""
    task_id: str
    description: str
    complexity: float               # 0.0 = trivial, 1.0 = extremely complex
    repeatability: float            # 0.0 = unique, 1.0 = highly repeatable
    risk: float                     # 0.0 = zero-risk, 1.0 = catastrophic potential
    data_sensitivity: float         # 0.0 = public, 1.0 = classified/PII
    recommended_mode: DelegationMode = DelegationMode.SUPERVISED
    confidence: float = 0.0         # how confident the classification is
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Result of friction analysis."""
    task_id: str
    mode: DelegationMode
    reason: str
    trust_required: float
    estimated_savings_minutes: float   # human time saved by delegation
    decided_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FrictionMetric:
    """Tracks friction reduction outcomes."""
    task_id: str
    mode_used: DelegationMode
    success: bool
    human_time_saved_minutes: float
    recorded_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# FRICTION REDUCER
# =============================================================================

class FrictionReducer:
    """
    Routes tasks to the least-friction execution path that still meets
    trust and safety requirements.

    Usage:
        reducer = FrictionReducer(trust_gate=gate)
        decision = reducer.route("task-001", "Generate weekly SOC report",
                                  repeatable=True, risk="low")
        if decision.mode == DelegationMode.AUTONOMOUS:
            agent.execute(task)
    """

    # Complexity keywords (simple heuristic; real deployment would use ML)
    LOW_COMPLEXITY = {"read", "list", "check", "fetch", "get", "status", "report", "count", "summarize"}
    HIGH_COMPLEXITY = {"modify", "delete", "override", "deploy", "migrate", "terminate", "reconfigure"}

    # Risk mappings
    RISK_MAP = {"none": 0.0, "low": 0.15, "medium": 0.40, "high": 0.70, "critical": 0.95}

    # Thresholds for autonomous delegation
    AUTONOMOUS_MAX_COMPLEXITY = 0.35
    AUTONOMOUS_MAX_RISK = 0.25
    SUPERVISED_MAX_COMPLEXITY = 0.70
    SUPERVISED_MAX_RISK = 0.60

    def __init__(self, trust_gate=None, audit_callback: Optional[Callable] = None):
        self._trust_gate = trust_gate
        self._audit = audit_callback or self._default_audit
        self._history: List[FrictionMetric] = []
        self._lock = threading.Lock()

        # Learned adjustments: task patterns that were reclassified
        self._overrides: Dict[str, DelegationMode] = {}

    # --- ROUTING ---

    def route(
        self,
        task_id: str,
        description: str,
        repeatable: bool = False,
        risk: str = "medium",
        data_sensitivity: float = 0.0,
        agent_id: Optional[str] = None,
    ) -> RoutingDecision:
        """Analyze a task and decide the optimal delegation mode."""

        profile = self._classify(task_id, description, repeatable, risk, data_sensitivity)

        # Check for learned overrides
        desc_key = description.strip().lower()
        if desc_key in self._overrides:
            mode = self._overrides[desc_key]
            return RoutingDecision(
                task_id=task_id, mode=mode,
                reason=f"Override from learned routing: {mode.value}",
                trust_required=self._trust_for_mode(mode),
                estimated_savings_minutes=self._estimate_savings(profile, mode),
            )

        # Determine delegation mode from complexity + risk
        mode = self._select_mode(profile, agent_id)

        trust_req = self._trust_for_mode(mode)
        savings = self._estimate_savings(profile, mode)

        decision = RoutingDecision(
            task_id=task_id, mode=mode,
            reason=self._explain(profile, mode),
            trust_required=trust_req,
            estimated_savings_minutes=savings,
        )

        self._audit("friction_routed", {
            "task_id": task_id,
            "description": description[:80],
            "complexity": round(profile.complexity, 2),
            "risk": round(profile.risk, 2),
            "mode": mode.value,
            "savings_min": round(savings, 1),
        })

        return decision

    def batch_route(self, tasks: List[Dict]) -> List[RoutingDecision]:
        """Route multiple tasks at once. Each dict needs 'task_id' and 'description'."""
        return [self.route(**t) for t in tasks]

    # --- FEEDBACK & LEARNING ---

    def record_outcome(
        self,
        task_id: str,
        mode_used: DelegationMode,
        success: bool,
        human_time_saved: float = 0.0,
        description: Optional[str] = None,
    ) -> None:
        """Record how a delegation decision turned out, enabling learning."""
        with self._lock:
            metric = FrictionMetric(
                task_id=task_id, mode_used=mode_used,
                success=success, human_time_saved_minutes=human_time_saved,
            )
            self._history.append(metric)

            # Trim history
            if len(self._history) > 5000:
                self._history = self._history[-2500:]

            # Learn: if autonomous failed, escalate future similar tasks
            if not success and mode_used == DelegationMode.AUTONOMOUS and description:
                desc_key = description.strip().lower()
                self._overrides[desc_key] = DelegationMode.SUPERVISED
                logger.info("Learned: '%s' escalated to SUPERVISED after failure", desc_key[:60])

            # Learn: if manual succeeded easily, consider downgrading friction
            if success and mode_used == DelegationMode.MANUAL and description:
                desc_key = description.strip().lower()
                # After 3 successful manual completions, suggest supervised
                similar = [m for m in self._history
                           if m.success and m.mode_used == DelegationMode.MANUAL]
                if len(similar) >= 3 and desc_key not in self._overrides:
                    self._overrides[desc_key] = DelegationMode.SUPERVISED
                    logger.info("Learned: '%s' downgraded to SUPERVISED after repeated success", desc_key[:60])

    def set_override(self, description: str, mode: DelegationMode) -> None:
        """Human operator forces a routing rule."""
        self._overrides[description.strip().lower()] = mode

    # --- REPORTING ---

    def efficiency_report(self) -> Dict[str, Any]:
        """Summary of friction reduction performance."""
        if not self._history:
            return {"total_tasks": 0, "message": "No data yet"}

        total = len(self._history)
        successes = sum(1 for m in self._history if m.success)
        total_saved = sum(m.human_time_saved_minutes for m in self._history)

        by_mode = {}
        for mode in DelegationMode:
            mode_tasks = [m for m in self._history if m.mode_used == mode]
            if mode_tasks:
                by_mode[mode.value] = {
                    "count": len(mode_tasks),
                    "success_rate": round(sum(1 for m in mode_tasks if m.success) / len(mode_tasks), 2),
                    "time_saved_min": round(sum(m.human_time_saved_minutes for m in mode_tasks), 1),
                }

        return {
            "total_tasks": total,
            "success_rate": round(successes / total, 2) if total else 0,
            "total_human_time_saved_min": round(total_saved, 1),
            "total_human_time_saved_hours": round(total_saved / 60, 1),
            "by_mode": by_mode,
            "active_overrides": len(self._overrides),
        }

    # --- INTERNAL ---

    def _classify(
        self, task_id: str, description: str,
        repeatable: bool, risk: str, data_sensitivity: float,
    ) -> TaskProfile:
        words = set(description.lower().split())
        low_hits = len(words & self.LOW_COMPLEXITY)
        high_hits = len(words & self.HIGH_COMPLEXITY)

        # Complexity: weighted by keyword signals
        if high_hits > low_hits:
            complexity = min(0.5 + high_hits * 0.15, 1.0)
        elif low_hits > high_hits:
            complexity = max(0.5 - low_hits * 0.1, 0.05)
        else:
            complexity = 0.50  # ambiguous → middle

        # Longer descriptions often mean more complex tasks
        if len(description) > 200:
            complexity = min(complexity + 0.10, 1.0)

        risk_score = self.RISK_MAP.get(risk.lower(), 0.50)
        repeatability = 0.80 if repeatable else 0.30

        return TaskProfile(
            task_id=task_id, description=description,
            complexity=complexity, repeatability=repeatability,
            risk=risk_score, data_sensitivity=data_sensitivity,
        )

    def _select_mode(self, profile: TaskProfile, agent_id: Optional[str]) -> DelegationMode:
        # Check trust if trust gate is available
        agent_trust = 0.50
        if self._trust_gate and agent_id:
            agent_trust = self._trust_gate.get_score(agent_id)

        # High repeatability + low risk + low complexity → autonomous
        if (profile.complexity <= self.AUTONOMOUS_MAX_COMPLEXITY
                and profile.risk <= self.AUTONOMOUS_MAX_RISK
                and agent_trust >= 0.40):
            return DelegationMode.AUTONOMOUS

        # Moderate complexity/risk → supervised
        if (profile.complexity <= self.SUPERVISED_MAX_COMPLEXITY
                and profile.risk <= self.SUPERVISED_MAX_RISK
                and agent_trust >= 0.25):
            return DelegationMode.SUPERVISED

        # High complexity, high risk, or low trust → manual
        return DelegationMode.MANUAL

    def _trust_for_mode(self, mode: DelegationMode) -> float:
        return {
            DelegationMode.AUTONOMOUS: 0.40,
            DelegationMode.SUPERVISED: 0.25,
            DelegationMode.MANUAL: 0.0,
        }[mode]

    def _estimate_savings(self, profile: TaskProfile, mode: DelegationMode) -> float:
        """Estimate minutes of human time saved."""
        # Base time: complex = more time, repeatable = more aggregate savings
        base = 10 + profile.complexity * 30  # 10-40 min task
        multiplier = {
            DelegationMode.AUTONOMOUS: 0.95,    # saves 95% of human time
            DelegationMode.SUPERVISED: 0.60,    # saves 60%
            DelegationMode.MANUAL: 0.10,        # minimal savings (agent assistance)
        }[mode]
        return base * multiplier * (1 + profile.repeatability)

    def _explain(self, profile: TaskProfile, mode: DelegationMode) -> str:
        parts = []
        if profile.complexity <= 0.35:
            parts.append("low complexity")
        elif profile.complexity <= 0.70:
            parts.append("moderate complexity")
        else:
            parts.append("high complexity")

        if profile.risk <= 0.25:
            parts.append("low risk")
        elif profile.risk <= 0.60:
            parts.append("moderate risk")
        else:
            parts.append("high risk")

        if profile.repeatability >= 0.60:
            parts.append("highly repeatable")

        return f"{mode.value} — {', '.join(parts)}"

    @staticmethod
    def _default_audit(event: str, data: Dict) -> None:
        logger.info("FRICTION | %s | %s", event, data)
