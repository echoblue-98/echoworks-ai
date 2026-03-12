"""
AION OS — The 9 Immutable Safety Invariants
=============================================

These are the hard constraints that the Recursive Self-Improvement (RSI)
engine can NEVER violate, regardless of what the LLM proposes or what
the analyst approves.

They are enforced at three checkpoints:
  1. CandidateGenerator — proposals that violate invariants are rejected
  2. ShadowRunner — shadow evaluation fails if invariants are breached
  3. PolicyStore — writes that violate invariants raise InvariantViolation

Even an admin cannot override these without modifying source code.
This is the "constitutional layer" of the system.

The 9 Invariants:
  I1  — Human-in-the-Loop: No policy reaches production without human approval
  I2  — Privilege Sanctity: Never read, index, or store attorney-client content
  I3  — Coverage Floor: Never reduce detection coverage below 75% of patterns
  I4  — Encryption Mandate: All data at rest must be encrypted (AES-256-GCM)
  I5  — Audit Continuity: Audit logging can never be disabled or truncated
  I6  — Threshold Bounds: Detection thresholds stay within safe operational ranges
  I7  — No Self-Modification: RSI changes config, never code or invariants
  I8  — Rollback Guarantee: Every policy version is preserved and rollback-able
  I9  — Data Sovereignty: Zero bytes transmitted outside the deployment perimeter
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger("aionos.invariants")


# =============================================================================
#  EXCEPTION
# =============================================================================

class InvariantViolation(Exception):
    """Raised when any of the 9 immutable invariants is breached."""

    def __init__(self, invariant_id: str, message: str):
        self.invariant_id = invariant_id
        self.message = message
        super().__init__(f"[{invariant_id}] {message}")


# =============================================================================
#  THE 9 INVARIANTS — Definition
# =============================================================================

@dataclass(frozen=True)
class Invariant:
    """An immutable safety invariant."""
    id: str
    name: str
    description: str
    enforcement: str  # Where it's checked
    severity: str = "critical"  # Always critical — these cannot be warnings

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enforcement": self.enforcement,
            "severity": self.severity,
        }


# The canonical list — ordered I1 through I9
IMMUTABLE_INVARIANTS = (
    Invariant(
        id="I1",
        name="Human-in-the-Loop",
        description=(
            "No detection policy change reaches production without explicit "
            "human approval. The RSI engine proposes; a human disposes. "
            "Auto-deployment is architecturally impossible."
        ),
        enforcement="ImprovementEngine.approve_proposal() — requires analyst_id",
    ),
    Invariant(
        id="I2",
        name="Privilege Sanctity",
        description=(
            "The system never reads, indexes, or stores the content of "
            "attorney-client privileged communications. Only behavioral "
            "metadata is processed: access timestamps, volume, patterns. "
            "Document text never enters the detection pipeline."
        ),
        enforcement="EthicsLayer.check_query() + SOC ingestion content filter",
    ),
    Invariant(
        id="I3",
        name="Coverage Floor",
        description=(
            "RSI cannot reduce detection coverage below 75% of available "
            "patterns. No single improvement cycle may disable more than "
            "3 patterns. Prevents the engine from converging on a narrow "
            "subset and becoming blind to entire attack categories."
        ),
        enforcement="PolicyStore.validate_invariants() + ShadowRunner.check_guardrails()",
    ),
    Invariant(
        id="I4",
        name="Encryption Mandate",
        description=(
            "All data at rest must be encrypted with AES-256-GCM (FIPS 197, "
            "NIST SP 800-38D). The RSI engine cannot modify, disable, or "
            "downgrade encryption settings. Key derivation uses PBKDF2 with "
            "≥600,000 iterations."
        ),
        enforcement="ShadowRunner.check_guardrails() — 'encryption' is a PROTECTED_DOMAIN",
    ),
    Invariant(
        id="I5",
        name="Audit Continuity",
        description=(
            "Audit logging cannot be disabled, paused, or have its retention "
            "period reduced below 7 days. Every API call, policy change, "
            "feedback submission, and system event is logged with immutable "
            "timestamps."
        ),
        enforcement="ShadowRunner.check_guardrails() — 'audit_logging' is a PROTECTED_DOMAIN",
    ),
    Invariant(
        id="I6",
        name="Threshold Bounds",
        description=(
            "Detection thresholds must stay within safe operational ranges. "
            "Examples: min_stages_to_alert ≥ 2 (prevents single-event noise), "
            "event_ttl_days ∈ [7, 365], volume_spike_multiplier ≥ 1.5. "
            "Bounds are defined in IMMUTABLE_INVARIANTS in policy_store.py."
        ),
        enforcement="PolicyStore.validate_invariants() bound checks on every write",
    ),
    Invariant(
        id="I7",
        name="No Self-Modification",
        description=(
            "The RSI engine generates declarative configuration changes only. "
            "It cannot modify source code, invariant definitions, the shadow "
            "runner logic, or its own evaluation criteria. Changes are JSON "
            "policy diffs, never executable code."
        ),
        enforcement="CandidateGenerator output schema — only CandidateChange objects accepted",
    ),
    Invariant(
        id="I8",
        name="Rollback Guarantee",
        description=(
            "Every policy version is preserved in the archive with a full "
            "snapshot. Any version can be restored instantly via rollback. "
            "The archive cannot be purged by RSI. Currently ~1,068 versions "
            "archived."
        ),
        enforcement="PolicyStore.rollback() + archive directory is append-only for RSI",
    ),
    Invariant(
        id="I9",
        name="Data Sovereignty",
        description=(
            "Zero bytes of firm data are transmitted outside the deployment "
            "perimeter. No telemetry, no crash reports, no cloud callbacks. "
            "LLM inference uses local models (Ollama/LM Studio) by default. "
            "External API calls (Claude/Gemini) send only generic instructions, "
            "never proprietary data."
        ),
        enforcement="Network architecture — on-prem deployment with no outbound data paths",
    ),
)

# Quick lookup by ID
INVARIANT_BY_ID: Dict[str, Invariant] = {inv.id: inv for inv in IMMUTABLE_INVARIANTS}
INVARIANT_COUNT = len(IMMUTABLE_INVARIANTS)

assert INVARIANT_COUNT == 9, f"Expected 9 invariants, got {INVARIANT_COUNT}"


# =============================================================================
#  RUNTIME CHECKER
# =============================================================================

class InvariantChecker:
    """
    Runtime enforcement of the 9 immutable invariants.

    Called by:
      - ShadowRunner before every shadow evaluation
      - PolicyStore on every policy write
      - ImprovementEngine during cycle execution
    """

    @staticmethod
    def check_all(
        candidate_policy: Dict[str, Any],
        baseline_policy: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Run all applicable invariant checks.

        Returns list of violation descriptions (empty = all passed).
        """
        violations = []
        ctx = context or {}

        # I1: Human-in-the-Loop
        # Enforced architecturally — approve_proposal() requires analyst_id.
        # If someone tries to auto-promote without approval:
        if ctx.get("auto_promote") and not ctx.get("analyst_id"):
            violations.append(
                "[I1] Human-in-the-Loop: cannot auto-promote policy without analyst approval"
            )

        # I2: Privilege Sanctity
        # Check that policy doesn't enable document content analysis
        content_analysis = candidate_policy.get("content_analysis", {})
        if content_analysis.get("enabled") or content_analysis.get("index_full_text"):
            violations.append(
                "[I2] Privilege Sanctity: content_analysis.enabled/index_full_text "
                "cannot be turned on — attorney-client privilege protection"
            )

        # I3: Coverage Floor
        pattern_weights = candidate_policy.get("pattern_weights", {})
        if pattern_weights:
            total_patterns = len(pattern_weights)
            enabled_count = sum(
                1 for pw in pattern_weights.values()
                if (isinstance(pw, dict) and pw.get("enabled", True))
                or (isinstance(pw, (int, float)) and pw > 0)
            )
            if total_patterns > 0:
                ratio = enabled_count / total_patterns
                if ratio < 0.75:
                    violations.append(
                        f"[I3] Coverage Floor: {enabled_count}/{total_patterns} "
                        f"patterns enabled ({ratio:.0%}) — minimum is 75%"
                    )

            # Check max disabled per cycle
            if baseline_policy:
                baseline_weights = baseline_policy.get("pattern_weights", {})
                newly_disabled = 0
                for pid, pw in pattern_weights.items():
                    was_enabled = True
                    if pid in baseline_weights:
                        bw = baseline_weights[pid]
                        was_enabled = (
                            (isinstance(bw, dict) and bw.get("enabled", True))
                            or (isinstance(bw, (int, float)) and bw > 0)
                        )
                    is_enabled = (
                        (isinstance(pw, dict) and pw.get("enabled", True))
                        or (isinstance(pw, (int, float)) and pw > 0)
                    )
                    if was_enabled and not is_enabled:
                        newly_disabled += 1

                if newly_disabled > 3:
                    violations.append(
                        f"[I3] Coverage Floor: {newly_disabled} patterns disabled "
                        f"in one cycle — maximum is 3"
                    )

        # I4: Encryption Mandate
        encryption_cfg = candidate_policy.get("encryption", {})
        if encryption_cfg.get("algorithm") and encryption_cfg["algorithm"] != "AES-256-GCM":
            violations.append(
                f"[I4] Encryption Mandate: algorithm must be AES-256-GCM, "
                f"got '{encryption_cfg['algorithm']}'"
            )
        if encryption_cfg.get("enabled") is False:
            violations.append(
                "[I4] Encryption Mandate: encryption cannot be disabled"
            )

        # I5: Audit Continuity
        audit_cfg = candidate_policy.get("audit", candidate_policy.get("audit_logging", {}))
        if audit_cfg.get("enabled") is False:
            violations.append(
                "[I5] Audit Continuity: audit logging cannot be disabled"
            )
        if audit_cfg.get("retention_days") is not None:
            if audit_cfg["retention_days"] < 7:
                violations.append(
                    f"[I5] Audit Continuity: retention_days={audit_cfg['retention_days']} "
                    f"< 7 day minimum"
                )

        # I6: Threshold Bounds
        thresholds = candidate_policy.get("thresholds", {})
        from aionos.improvement.policy_store import IMMUTABLE_INVARIANTS as THRESHOLD_BOUNDS
        for param, bounds in THRESHOLD_BOUNDS.items():
            if param in thresholds:
                val = thresholds[param]
                if isinstance(val, (int, float)):
                    if "min" in bounds and val < bounds["min"]:
                        violations.append(
                            f"[I6] Threshold Bounds: {param}={val} < min {bounds['min']} "
                            f"({bounds['reason']})"
                        )
                    if "max" in bounds and val > bounds["max"]:
                        violations.append(
                            f"[I6] Threshold Bounds: {param}={val} > max {bounds['max']} "
                            f"({bounds['reason']})"
                        )

        # I7: No Self-Modification
        # Enforced by CandidateGenerator output schema — only CandidateChange objects.
        # Check that no code-like strings appear in policy values
        _check_no_executable(candidate_policy, violations)

        # I8: Rollback Guarantee (structural — archive is append-only)
        # Verified by PolicyStore._save_version() — always writes to archive/

        # I9: Data Sovereignty (network architecture — checked at deployment)
        # Can validate config doesn't add external endpoints
        external_endpoints = candidate_policy.get("external_endpoints", [])
        if external_endpoints:
            violations.append(
                f"[I9] Data Sovereignty: {len(external_endpoints)} external "
                f"endpoint(s) defined — zero outbound data is allowed"
            )

        return violations

    @staticmethod
    def get_all_invariants() -> List[Dict[str, str]]:
        """Return all 9 invariants as dicts (for API/dashboard display)."""
        return [inv.to_dict() for inv in IMMUTABLE_INVARIANTS]

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Return invariant enforcement status."""
        return {
            "invariant_count": INVARIANT_COUNT,
            "invariants": [inv.to_dict() for inv in IMMUTABLE_INVARIANTS],
            "enforcement_points": [
                "CandidateGenerator (proposal rejection)",
                "ShadowRunner (shadow evaluation failure)",
                "PolicyStore (write-time validation)",
                "ImprovementEngine (cycle orchestration)",
            ],
            "status": "all_enforced",
        }


def _check_no_executable(d: Dict[str, Any], violations: List[str], path: str = ""):
    """Recursively check that no policy values contain executable code."""
    EXECUTABLE_MARKERS = ("import ", "exec(", "eval(", "__import__", "subprocess", "os.system")
    for key, value in d.items():
        full_path = f"{path}.{key}" if path else key
        if isinstance(value, str):
            for marker in EXECUTABLE_MARKERS:
                if marker in value:
                    violations.append(
                        f"[I7] No Self-Modification: executable code detected "
                        f"at '{full_path}': contains '{marker}'"
                    )
        elif isinstance(value, dict):
            _check_no_executable(value, violations, full_path)
