"""
AION OS - Versioned Policy Store
=================================

First-class configuration/policy layer that is:
  - Declarative: correlation rules, thresholds, category mappings,
    and LLM prompts live in versioned config, not hard-coded.
  - Diffable: you can see "v17 → v18 changed MFA fatigue threshold
    from 3 to 5, and rewrote the BEC narrative prompt."
  - Rollback-able: one click to revert if something regresses.

RSI then becomes:
  "AION proposes a new policy version, tests it on past data,
   and you approve/deploy it."
"""

import json
import copy
import hashlib
import logging
import shutil
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger("aionos.improvement.policy")

# =============================================================================
# PATHS
# =============================================================================

POLICY_DIR = Path(__file__).parent.parent.parent / "config" / "policies"
POLICY_ARCHIVE_DIR = POLICY_DIR / "archive"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class DetectionThresholds:
    """Tunable thresholds for detection logic."""
    # Temporal correlation
    correlation_window_days: int = 14
    min_stages_to_alert: int = 2
    max_events_per_user: int = 10000
    event_ttl_days: int = 30

    # Behavioral baselines
    volume_spike_multiplier: float = 3.0
    frequency_spike_multiplier: float = 5.0
    new_behavior_min_days: int = 30
    baseline_confidence_threshold: float = 0.5

    # Hybrid engine
    gemini_batch_interval_seconds: int = 60
    gemini_min_events_to_analyze: int = 5
    probation_period_hours: int = 24
    probation_min_occurrences: int = 3
    probation_max_trigger_rate: float = 0.10

    # Alert severity
    mfa_fatigue_threshold: int = 3
    bulk_download_threshold_mb: int = 500
    after_hours_sensitivity: str = "medium"  # low, medium, high
    impossible_travel_min_distance_km: int = 500


@dataclass
class PatternWeight:
    """Weight/priority for a specific attack pattern."""
    pattern_name: str
    weight: float = 1.0
    enabled: bool = True
    min_confidence: float = 0.5
    auto_close_below: float = 0.2
    trigger_voice_above: float = 0.9


@dataclass
class TriageRule:
    """Rules for alert triage decisions."""
    category: str
    action: str  # "critical", "high", "auto_close", "escalate", "voice_alert"
    conditions: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class LLMPromptTemplate:
    """Versioned LLM prompt template."""
    name: str
    template: str
    purpose: str  # "report", "extraction", "severity_rubric", "narrative"
    model_target: str = "any"  # "claude", "gemini", "ollama", "any"
    max_tokens: int = 4096
    temperature: float = 0.3


@dataclass
class PolicyVersion:
    """
    A complete versioned policy snapshot.

    Contains ALL tunable parameters that RSI is allowed to modify.
    Core security logic (auth, input validation, memory bounds) is
    explicitly excluded — those require human code review.
    """
    version: int
    created_at: str = ""
    created_by: str = "system"  # "system", "llm_candidate", "human_analyst"
    description: str = ""
    parent_version: Optional[int] = None

    # Detection thresholds
    thresholds: DetectionThresholds = field(default_factory=DetectionThresholds)

    # Pattern weights (name → weight config)
    pattern_weights: Dict[str, PatternWeight] = field(default_factory=dict)

    # Triage rules
    triage_rules: List[TriageRule] = field(default_factory=list)

    # LLM prompt templates (name → template)
    prompt_templates: Dict[str, LLMPromptTemplate] = field(default_factory=dict)

    # Category mappings (event type → category, for grouping)
    category_mappings: Dict[str, str] = field(default_factory=dict)

    # Metadata
    status: str = "draft"  # "draft", "shadow", "approved", "active", "rolled_back"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    shadow_start: Optional[str] = None
    shadow_end: Optional[str] = None
    evaluation_score: Optional[float] = None
    notes: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def fingerprint(self) -> str:
        """Content hash for dedup/comparison."""
        content = json.dumps(self._config_only(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _config_only(self) -> dict:
        """Return only the tunable configuration (no metadata)."""
        d = asdict(self)
        for key in ("version", "created_at", "created_by", "description",
                     "parent_version", "status", "approved_by", "approved_at",
                     "shadow_start", "shadow_end", "evaluation_score", "notes"):
            d.pop(key, None)
        return d

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PolicyVersion":
        """Reconstruct from dict, handling nested dataclasses."""
        data = copy.deepcopy(data)
        if "thresholds" in data and isinstance(data["thresholds"], dict):
            data["thresholds"] = DetectionThresholds(**data["thresholds"])
        if "pattern_weights" in data:
            pw = {}
            for k, v in data["pattern_weights"].items():
                pw[k] = PatternWeight(**v) if isinstance(v, dict) else v
            data["pattern_weights"] = pw
        if "triage_rules" in data:
            data["triage_rules"] = [
                TriageRule(**r) if isinstance(r, dict) else r
                for r in data["triage_rules"]
            ]
        if "prompt_templates" in data:
            pt = {}
            for k, v in data["prompt_templates"].items():
                pt[k] = LLMPromptTemplate(**v) if isinstance(v, dict) else v
            data["prompt_templates"] = pt
        return cls(**data)


@dataclass
class PolicyDiff:
    """Human-readable diff between two policy versions."""
    from_version: int
    to_version: int
    changes: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# HARD INVARIANTS — these cannot be changed by RSI
# =============================================================================

IMMUTABLE_INVARIANTS = {
    "min_stages_to_alert": {"min": 2, "reason": "Never allow single-event alerts (too noisy)"},
    "max_events_per_user": {"min": 100, "max": 100000, "reason": "Memory safety bounds"},
    "event_ttl_days": {"min": 7, "max": 365, "reason": "Retention policy compliance"},
    "volume_spike_multiplier": {"min": 1.5, "reason": "Never go below 1.5x or everything alerts"},
    "baseline_confidence_threshold": {"min": 0.1, "max": 0.95, "reason": "Keep baseline functional"},
    "probation_period_hours": {"min": 1, "reason": "Minimum observation period for new patterns"},
    "probation_min_occurrences": {"min": 2, "reason": "Never promote single-instance patterns"},
    "mfa_fatigue_threshold": {"min": 2, "max": 20, "reason": "MFA fatigue detection guard"},
    "bulk_download_threshold_mb": {"min": 50, "reason": "Don't blind the system to large transfers"},
}

# =============================================================================
# ENTROPY / DIVERSITY INVARIANT (Gemini Recommendation)
# =============================================================================
# Prevents RSI from converging on a narrow subset of patterns.
# If the engine only "likes" 5 out of 69 patterns, it becomes blind.
# This invariant enforces minimum breadth of detection coverage.

PATTERN_COVERAGE_INVARIANTS = {
    "min_enabled_ratio": 0.75,        # At least 75% of patterns must stay enabled
    "max_disabled_per_cycle": 3,       # Max 3 patterns disabled in any single proposal
    "min_weight_floor": 0.1,           # No pattern weight can drop below 0.1
    "max_weight_ceiling": 5.0,         # No pattern weight can exceed 5.0
    "min_categories_active": 8,        # At least 8 of 15+ attack categories must be active
    "reason": "Entropy guard — prevents RSI from converging to detect only a subset",
}


# =============================================================================
# POLICY STORE
# =============================================================================

class PolicyStore:
    """
    Manages versioned detection policies.

    Provides:
      - Version history with full snapshots
      - Diff between any two versions
      - Rollback to any previous version
      - Invariant enforcement on every write
      - Disk-backed persistence in config/policies/
    """

    def __init__(self, policy_dir: Path = None):
        self.policy_dir = Path(policy_dir) if policy_dir else POLICY_DIR
        self.archive_dir = self.policy_dir / "archive"
        self.policy_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self._versions: Dict[int, PolicyVersion] = {}
        self._active_version: Optional[int] = None
        self._load_from_disk()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def get_active(self) -> Optional[PolicyVersion]:
        """Return the currently active policy version."""
        if self._active_version is not None:
            return self._versions.get(self._active_version)
        return None

    def get_version(self, version: int) -> Optional[PolicyVersion]:
        """Return a specific version."""
        return self._versions.get(version)

    def list_versions(self) -> List[Dict[str, Any]]:
        """List all versions with metadata (lightweight)."""
        result = []
        for v in sorted(self._versions.values(), key=lambda x: x.version):
            result.append({
                "version": v.version,
                "status": v.status,
                "created_at": v.created_at,
                "created_by": v.created_by,
                "description": v.description,
                "fingerprint": v.fingerprint(),
                "evaluation_score": v.evaluation_score,
            })
        return result

    def create_version(
        self,
        policy: PolicyVersion,
        validate: bool = True
    ) -> PolicyVersion:
        """
        Store a new policy version.

        Args:
            policy: The policy to store.
            validate: Whether to enforce invariants (default True).

        Returns:
            The stored policy (with version number assigned).

        Raises:
            ValueError: If invariants are violated.
        """
        if validate:
            violations = self._check_invariants(policy)
            if violations:
                raise ValueError(
                    f"Policy violates {len(violations)} invariant(s): "
                    + "; ".join(violations)
                )

        # Auto-assign version number
        if self._versions:
            next_version = max(self._versions.keys()) + 1
        else:
            next_version = 1

        policy.version = next_version
        policy.created_at = datetime.utcnow().isoformat()

        self._versions[next_version] = policy
        self._save_version(policy)

        logger.info(
            f"Created policy v{next_version} by {policy.created_by}: "
            f"{policy.description}"
        )
        return policy

    def activate_version(self, version: int, approved_by: str = "system") -> PolicyVersion:
        """
        Promote a version to active (production).

        Only one version can be active at a time.
        The previously active version gets status 'rolled_back'.
        """
        policy = self._versions.get(version)
        if not policy:
            raise ValueError(f"Version {version} not found")

        # Deactivate current
        if self._active_version is not None:
            old = self._versions[self._active_version]
            old.status = "rolled_back"
            self._save_version(old)

        # Activate new
        policy.status = "active"
        policy.approved_by = approved_by
        policy.approved_at = datetime.utcnow().isoformat()
        self._active_version = version
        self._save_version(policy)
        self._save_active_pointer()

        logger.info(f"Activated policy v{version} (approved by {approved_by})")
        return policy

    def rollback(self, to_version: int, reason: str = "") -> PolicyVersion:
        """Roll back to a specific previous version."""
        target = self._versions.get(to_version)
        if not target:
            raise ValueError(f"Version {to_version} not found")

        # Create a new version that's a copy of the target
        rolled_back = copy.deepcopy(target)
        rolled_back.description = (
            f"Rollback to v{to_version}"
            + (f": {reason}" if reason else "")
        )
        rolled_back.created_by = "rollback"
        rolled_back.parent_version = to_version
        rolled_back.status = "draft"

        new_policy = self.create_version(rolled_back, validate=True)
        return self.activate_version(new_policy.version, approved_by="rollback")

    def diff(self, from_version: int, to_version: int) -> PolicyDiff:
        """
        Compute human-readable diff between two versions.

        Returns a PolicyDiff with structured change records and a summary.
        """
        v_from = self._versions.get(from_version)
        v_to = self._versions.get(to_version)
        if not v_from or not v_to:
            raise ValueError(f"Version {from_version} or {to_version} not found")

        d_from = v_from._config_only()
        d_to = v_to._config_only()

        changes = self._compute_diff(d_from, d_to, path="")
        summary_parts = []
        for c in changes:
            summary_parts.append(
                f"{c['path']}: {c.get('old', '(none)')} → {c.get('new', '(none)')}"
            )

        return PolicyDiff(
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            summary=f"v{from_version} → v{to_version}: {len(changes)} change(s)\n"
                     + "\n".join(summary_parts)
        )

    def get_proposal_summary(self, version: int) -> Dict[str, Any]:
        """
        Generate a human-readable proposal summary for a draft version.

        Intended for the "review proposed rule changes?" UI nudge.
        """
        policy = self._versions.get(version)
        if not policy:
            raise ValueError(f"Version {version} not found")

        active = self.get_active()
        if active:
            diff = self.diff(active.version, version)
        else:
            diff = PolicyDiff(
                from_version=0, to_version=version,
                changes=[{"path": "initial", "type": "created"}],
                summary="Initial policy version"
            )

        return {
            "version": version,
            "status": policy.status,
            "description": policy.description,
            "created_by": policy.created_by,
            "evaluation_score": policy.evaluation_score,
            "diff": diff.to_dict(),
            "prompt": (
                f"The system believes this change will improve detection. "
                f"Review proposed rule changes?\n\n{diff.summary}"
            ),
        }

    # -------------------------------------------------------------------------
    # Invariant enforcement
    # -------------------------------------------------------------------------

    def _check_invariants(self, policy: PolicyVersion) -> List[str]:
        """
        Check hard invariants that RSI must never violate.

        Returns list of violation descriptions (empty = all OK).
        """
        violations = []
        thresholds = asdict(policy.thresholds)

        # --- Threshold invariants ---
        for param_name, bounds in IMMUTABLE_INVARIANTS.items():
            if param_name not in thresholds:
                continue
            value = thresholds[param_name]

            if "min" in bounds and value < bounds["min"]:
                violations.append(
                    f"{param_name}={value} < min {bounds['min']} "
                    f"({bounds['reason']})"
                )
            if "max" in bounds and value > bounds["max"]:
                violations.append(
                    f"{param_name}={value} > max {bounds['max']} "
                    f"({bounds['reason']})"
                )

        # --- Pattern coverage / entropy invariant ---
        if policy.pattern_weights:
            total_patterns = len(policy.pattern_weights)
            enabled = [pw for pw in policy.pattern_weights.values()
                       if (pw.enabled if isinstance(pw, PatternWeight) else pw.get("enabled", True))]
            disabled = total_patterns - len(enabled)

            # Min enabled ratio
            if total_patterns > 0:
                ratio = len(enabled) / total_patterns
                if ratio < PATTERN_COVERAGE_INVARIANTS["min_enabled_ratio"]:
                    violations.append(
                        f"Pattern coverage {ratio:.0%} < minimum {PATTERN_COVERAGE_INVARIANTS['min_enabled_ratio']:.0%} "
                        f"({PATTERN_COVERAGE_INVARIANTS['reason']})"
                    )

            # Max disabled per cycle
            if disabled > PATTERN_COVERAGE_INVARIANTS["max_disabled_per_cycle"]:
                # Only enforce if this is a proposal (not the initial policy)
                if policy.parent_version is not None:
                    violations.append(
                        f"{disabled} patterns disabled > max {PATTERN_COVERAGE_INVARIANTS['max_disabled_per_cycle']} per cycle "
                        f"({PATTERN_COVERAGE_INVARIANTS['reason']})"
                    )

            # Weight bounds
            for name, pw in policy.pattern_weights.items():
                weight = pw.weight if isinstance(pw, PatternWeight) else pw.get("weight", 1.0)
                if weight < PATTERN_COVERAGE_INVARIANTS["min_weight_floor"]:
                    violations.append(
                        f"Pattern '{name}' weight {weight} < floor {PATTERN_COVERAGE_INVARIANTS['min_weight_floor']} "
                        f"({PATTERN_COVERAGE_INVARIANTS['reason']})"
                    )
                if weight > PATTERN_COVERAGE_INVARIANTS["max_weight_ceiling"]:
                    violations.append(
                        f"Pattern '{name}' weight {weight} > ceiling {PATTERN_COVERAGE_INVARIANTS['max_weight_ceiling']} "
                        f"({PATTERN_COVERAGE_INVARIANTS['reason']})"
                    )

        return violations

    # -------------------------------------------------------------------------
    # Diff computation
    # -------------------------------------------------------------------------

    def _compute_diff(
        self, old: Any, new: Any, path: str
    ) -> List[Dict[str, Any]]:
        """Recursively compute structured diff between two dicts."""
        changes = []

        if isinstance(old, dict) and isinstance(new, dict):
            all_keys = set(old.keys()) | set(new.keys())
            for key in sorted(all_keys):
                sub_path = f"{path}.{key}" if path else key
                if key not in old:
                    changes.append({
                        "path": sub_path, "type": "added",
                        "new": new[key]
                    })
                elif key not in new:
                    changes.append({
                        "path": sub_path, "type": "removed",
                        "old": old[key]
                    })
                else:
                    changes.extend(
                        self._compute_diff(old[key], new[key], sub_path)
                    )
        elif isinstance(old, list) and isinstance(new, list):
            if old != new:
                changes.append({
                    "path": path, "type": "modified",
                    "old": old, "new": new
                })
        elif old != new:
            changes.append({
                "path": path, "type": "modified",
                "old": old, "new": new
            })

        return changes

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def _save_version(self, policy: PolicyVersion):
        """Save a single version to disk."""
        path = self.archive_dir / f"policy_v{policy.version}.json"
        with open(path, "w") as f:
            json.dump(policy.to_dict(), f, indent=2, default=str)

    def _save_active_pointer(self):
        """Save which version is currently active."""
        pointer_path = self.policy_dir / "active_version.json"
        with open(pointer_path, "w") as f:
            json.dump({"active_version": self._active_version}, f)

    def _load_from_disk(self):
        """Load all versions from disk."""
        for path in sorted(self.archive_dir.glob("policy_v*.json")):
            try:
                with open(path) as f:
                    data = json.load(f)
                policy = PolicyVersion.from_dict(data)
                self._versions[policy.version] = policy
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")

        # Load active pointer
        pointer_path = self.policy_dir / "active_version.json"
        if pointer_path.exists():
            try:
                with open(pointer_path) as f:
                    data = json.load(f)
                self._active_version = data.get("active_version")
            except Exception as e:
                logger.warning(f"Failed to load active pointer: {e}")

    def initialize_default_policy(self) -> PolicyVersion:
        """
        Create the initial default policy (v1) if no policies exist.

        This seeds the system with sensible defaults matching
        current hard-coded values in temporal_engine and baseline_engine.
        """
        if self._versions:
            return self.get_active() or next(iter(self._versions.values()))

        default = PolicyVersion(
            version=0,  # Will be reassigned
            created_by="system",
            description="Initial default policy — mirrors current hard-coded values",
            thresholds=DetectionThresholds(),
            pattern_weights={
                "insider_data_theft": PatternWeight(
                    pattern_name="insider_data_theft", weight=1.0,
                    trigger_voice_above=0.9
                ),
                "vpn_brute_force_lateral": PatternWeight(
                    pattern_name="vpn_brute_force_lateral", weight=1.0
                ),
                "bec_wire_fraud": PatternWeight(
                    pattern_name="bec_wire_fraud", weight=1.0,
                    trigger_voice_above=0.85
                ),
                "attorney_departure_exfil": PatternWeight(
                    pattern_name="attorney_departure_exfil", weight=1.2,
                    trigger_voice_above=0.8,
                    min_confidence=0.4
                ),
            },
            triage_rules=[
                TriageRule(
                    category="insider_threat",
                    action="critical",
                    conditions={"severity": "P0", "stages_matched": {"gte": 3}},
                    description="Multi-stage insider threat → immediate critical"
                ),
                TriageRule(
                    category="bec_wire_fraud",
                    action="voice_alert",
                    conditions={"confidence": {"gte": 0.85}},
                    description="High-confidence BEC → voice alert"
                ),
                TriageRule(
                    category="noise_vpn_login",
                    action="auto_close",
                    conditions={"severity": "P4", "confidence": {"lt": 0.3}},
                    description="Low-confidence VPN noise → auto-close"
                ),
            ],
            prompt_templates={
                "incident_report": LLMPromptTemplate(
                    name="incident_report",
                    template=(
                        "Generate a security incident report for the following "
                        "correlated events. Include: executive summary, timeline, "
                        "risk assessment (P0-P4), affected assets, recommended "
                        "immediate actions, and forensic preservation steps.\n\n"
                        "Events:\n{events}\n\n"
                        "User context:\n{user_context}\n\n"
                        "Pattern match:\n{pattern_match}"
                    ),
                    purpose="report",
                    max_tokens=4096,
                    temperature=0.2,
                ),
                "severity_rubric": LLMPromptTemplate(
                    name="severity_rubric",
                    template=(
                        "Classify the severity of the following security events "
                        "using this rubric:\n"
                        "P0 CRITICAL: Active data exfiltration, compromised admin, "
                        "confirmed APT\n"
                        "P1 HIGH: Multi-stage attack in progress, credential theft, "
                        "lateral movement\n"
                        "P2 MEDIUM: Suspicious access pattern, policy violation, "
                        "single anomaly\n"
                        "P3 LOW: Minor deviation, informational anomaly\n"
                        "P4 INFO: Baseline update, system event\n\n"
                        "Events:\n{events}"
                    ),
                    purpose="severity_rubric",
                    max_tokens=1024,
                    temperature=0.1,
                ),
            },
            category_mappings={
                "vpn_brute_force": "network_attack",
                "credential_stuffing": "network_attack",
                "insider_data_theft": "insider_threat",
                "attorney_departure": "legal_compliance",
                "bec_wire_fraud": "financial_fraud",
                "lateral_movement": "persistence",
            },
        )

        policy = self.create_version(default, validate=True)
        return self.activate_version(policy.version, approved_by="system_init")
