"""
AION OS — Trust-Gated Execution Layer
Capability-based security: agents can only act when trust thresholds are met.

"Security is not separate from the future of AI adoption. It is part of the
foundation that makes meaningful adoption possible." — Rich, March 26 2026

Trust model:
- Every action has a trust cost
- Agents accumulate trust through successful completions
- High-risk actions (policy changes, data writes, alerts) require higher trust
- Trust degrades on failures or anomalies
- Human override always available
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aionos.agents.trust_gate")


# =============================================================================
# TRUST LEVELS
# =============================================================================

class TrustLevel(Enum):
    """Graduated trust tiers with increasing autonomy."""
    UNTRUSTED = 0       # read-only, all actions require approval
    PROVISIONAL = 1     # can read & alert, writes need approval
    STANDARD = 2        # can read, write, alert autonomously
    ELEVATED = 3        # can modify policies, spawn agents
    AUTONOMOUS = 4      # full autonomy within safety invariants


# Map trust levels to numeric thresholds (0.0-1.0)
TRUST_THRESHOLDS = {
    TrustLevel.UNTRUSTED: 0.0,
    TrustLevel.PROVISIONAL: 0.25,
    TrustLevel.STANDARD: 0.50,
    TrustLevel.ELEVATED: 0.75,
    TrustLevel.AUTONOMOUS: 0.90,
}


# =============================================================================
# ACTION COSTS — what trust is required for each action type
# =============================================================================

ACTION_TRUST_COSTS = {
    "read_data": 0.0,             # anyone can read
    "read_logs": 0.0,
    "alert_human": 0.10,          # low bar
    "write_metrics": 0.20,
    "send_notification": 0.30,
    "write_data": 0.40,
    "modify_threshold": 0.55,
    "spawn_agent": 0.60,
    "modify_policy": 0.75,
    "terminate_agent": 0.75,
    "external_api_call": 0.50,
    "delete_data": 0.85,
    "override_safety": 1.0,       # only human-approved
}


# =============================================================================
# TRUST LEDGER
# =============================================================================

@dataclass
class TrustEvent:
    timestamp: datetime
    agent_id: str
    action: str
    delta: float          # positive = trust gained, negative = trust lost
    reason: str
    resulting_score: float


@dataclass
class TrustProfile:
    """Trust state for a single agent or operator."""
    entity_id: str
    score: float = 0.50                    # start at STANDARD
    level: TrustLevel = TrustLevel.STANDARD
    history: List[TrustEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_action: Optional[datetime] = None

    # Decay: trust erodes if unused (stale sessions)
    decay_rate_per_hour: float = 0.01      # lose 1% per hour of inactivity
    min_score: float = 0.0
    max_score: float = 1.0

    def apply_decay(self) -> None:
        if not self.last_action:
            return
        elapsed_hours = (datetime.utcnow() - self.last_action).total_seconds() / 3600
        decay = elapsed_hours * self.decay_rate_per_hour
        self.score = max(self.min_score, self.score - decay)
        self._update_level()

    def _update_level(self) -> None:
        for level in reversed(list(TrustLevel)):
            if self.score >= TRUST_THRESHOLDS[level]:
                self.level = level
                return
        self.level = TrustLevel.UNTRUSTED


# =============================================================================
# TRUST GATE
# =============================================================================

class TrustGate:
    """
    Decides whether an agent can perform an action based on trust score.

    Usage:
        gate = TrustGate()
        gate.register("agent-001")

        if gate.check("agent-001", "write_data"):
            do_write()
        else:
            request_human_approval()

        gate.record_success("agent-001", "write_data")  # trust goes up
        gate.record_failure("agent-001", "write_data")   # trust goes down
    """

    # Trust deltas
    SUCCESS_BONUS = 0.02
    FAILURE_PENALTY = -0.08         # failures cost 4x more than successes
    ANOMALY_PENALTY = -0.15         # anomalies are severe

    def __init__(self, audit_callback: Optional[Callable] = None):
        self._profiles: Dict[str, TrustProfile] = {}
        self._lock = threading.Lock()
        self._audit = audit_callback or self._default_audit
        self._approval_queue: List[Dict] = []

    # --- REGISTRATION ---

    def register(self, entity_id: str, initial_score: float = 0.50) -> TrustProfile:
        with self._lock:
            if entity_id in self._profiles:
                return self._profiles[entity_id]
            profile = TrustProfile(entity_id=entity_id, score=initial_score)
            profile._update_level()
            self._profiles[entity_id] = profile
            self._audit("trust_registered", {
                "entity": entity_id, "score": initial_score,
                "level": profile.level.name,
            })
            return profile

    # --- CHECK / ENFORCE ---

    def check(self, entity_id: str, action: str) -> bool:
        """Can this entity perform this action right now?"""
        profile = self._profiles.get(entity_id)
        if not profile:
            return False
        profile.apply_decay()
        required = ACTION_TRUST_COSTS.get(action, 1.0)  # unknown actions need max trust
        return profile.score >= required

    def enforce(self, entity_id: str, action: str) -> None:
        """Raise if not allowed. Use in agent code for hard enforcement."""
        if not self.check(entity_id, action):
            profile = self._profiles.get(entity_id)
            score = profile.score if profile else 0.0
            required = ACTION_TRUST_COSTS.get(action, 1.0)
            self._audit("trust_denied", {
                "entity": entity_id, "action": action,
                "score": round(score, 3), "required": required,
            })
            raise PermissionError(
                f"Trust insufficient: {entity_id} has {score:.2f}, "
                f"'{action}' requires {required:.2f}"
            )

    def get_level(self, entity_id: str) -> TrustLevel:
        profile = self._profiles.get(entity_id)
        if not profile:
            return TrustLevel.UNTRUSTED
        profile.apply_decay()
        return profile.level

    def get_score(self, entity_id: str) -> float:
        profile = self._profiles.get(entity_id)
        if not profile:
            return 0.0
        profile.apply_decay()
        return profile.score

    # --- FEEDBACK ---

    def record_success(self, entity_id: str, action: str) -> float:
        """Agent completed an action successfully — trust increases."""
        return self._adjust(entity_id, action, self.SUCCESS_BONUS, "success")

    def record_failure(self, entity_id: str, action: str) -> float:
        """Agent failed an action — trust decreases."""
        return self._adjust(entity_id, action, self.FAILURE_PENALTY, "failure")

    def record_anomaly(self, entity_id: str, description: str) -> float:
        """Anomalous behavior detected — significant trust hit."""
        return self._adjust(entity_id, "anomaly", self.ANOMALY_PENALTY, description)

    def human_override(self, entity_id: str, new_score: float, reason: str) -> float:
        """Human operator manually sets trust score."""
        with self._lock:
            profile = self._get_or_create(entity_id)
            old = profile.score
            profile.score = max(0.0, min(1.0, new_score))
            profile._update_level()
            profile.last_action = datetime.utcnow()
            event = TrustEvent(
                timestamp=datetime.utcnow(), agent_id=entity_id,
                action="human_override", delta=profile.score - old,
                reason=reason, resulting_score=profile.score,
            )
            profile.history.append(event)
            self._audit("trust_override", {
                "entity": entity_id, "old": round(old, 3),
                "new": round(profile.score, 3), "reason": reason,
            })
            return profile.score

    # --- APPROVAL QUEUE ---

    def request_approval(self, entity_id: str, action: str, context: Dict = None) -> str:
        """Queue an action for human approval when trust is insufficient."""
        request_id = f"apr_{entity_id}_{action}_{datetime.utcnow().timestamp()}"
        self._approval_queue.append({
            "request_id": request_id,
            "entity_id": entity_id,
            "action": action,
            "context": context or {},
            "requested_at": datetime.utcnow().isoformat(),
            "status": "pending",
        })
        self._audit("approval_requested", {
            "request_id": request_id, "entity": entity_id, "action": action,
        })
        return request_id

    def approve(self, request_id: str) -> bool:
        for req in self._approval_queue:
            if req["request_id"] == request_id:
                req["status"] = "approved"
                # Bump trust slightly for approved actions
                self._adjust(req["entity_id"], req["action"], 0.01, "approved_by_human")
                return True
        return False

    def pending_approvals(self) -> List[Dict]:
        return [r for r in self._approval_queue if r["status"] == "pending"]

    # --- REPORTING ---

    def summary(self) -> Dict[str, Any]:
        result = {}
        for eid, profile in self._profiles.items():
            profile.apply_decay()
            result[eid] = {
                "score": round(profile.score, 3),
                "level": profile.level.name,
                "actions": len(profile.history),
                "last_action": profile.last_action.isoformat() if profile.last_action else None,
            }
        return result

    # --- INTERNAL ---

    def _adjust(self, entity_id: str, action: str, delta: float, reason: str) -> float:
        with self._lock:
            profile = self._get_or_create(entity_id)
            old = profile.score
            profile.score = max(0.0, min(1.0, profile.score + delta))
            profile._update_level()
            profile.last_action = datetime.utcnow()

            event = TrustEvent(
                timestamp=datetime.utcnow(), agent_id=entity_id,
                action=action, delta=delta,
                reason=reason, resulting_score=profile.score,
            )
            profile.history.append(event)

            # Trim history to prevent unbounded growth
            if len(profile.history) > 1000:
                profile.history = profile.history[-500:]

            self._audit("trust_adjusted", {
                "entity": entity_id, "action": action,
                "delta": round(delta, 3), "old": round(old, 3),
                "new": round(profile.score, 3), "level": profile.level.name,
            })
            return profile.score

    def _get_or_create(self, entity_id: str) -> TrustProfile:
        if entity_id not in self._profiles:
            profile = TrustProfile(entity_id=entity_id, score=0.50)
            profile._update_level()
            self._profiles[entity_id] = profile
        return self._profiles[entity_id]

    @staticmethod
    def _default_audit(event: str, data: Dict) -> None:
        logger.info("TRUST | %s | %s", event, data)
