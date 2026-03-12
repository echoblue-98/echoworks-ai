"""
AION OS - Shadow Runner
========================

Runs candidate policy changes in "shadow mode":
  - Replays historical events with the candidate policy
  - Compares what WOULD have happened vs what DID happen
  - Produces before/after metrics without touching production

Also enforces hard guardrails that RSI must never violate.

Shadow mode workflow:
  1. Clone the detection engines with candidate policy applied
  2. Replay stored events through the shadow engines
  3. Collect shadow alerts (never sent to analysts)
  4. Compare shadow metrics against baseline metrics
  5. Enforce safety invariants
  6. Return pass/fail recommendation

Separate compute: shadow replay runs in the caller's thread,
isolated from the main correlation engine.
"""

import copy
import json
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from enum import Enum

from aionos.safety.invariants import InvariantChecker

logger = logging.getLogger("aionos.improvement.shadow")


# =============================================================================
# SAFETY INVARIANTS
# =============================================================================

class GuardrailViolation(Exception):
    """Raised when a candidate change violates hard invariants."""
    pass


# Things RSI must NEVER auto-change
PROTECTED_DOMAINS = frozenset([
    "auth",
    "authorization",
    "authentication",
    "input_validation",
    "sanitization",
    "resource_limits",
    "memory_bounds",
    "rate_limiting",
    "audit_logging",
    "compliance",
    "encryption",
    "tls",
    "api_keys",
    "secrets",
])

# Coverage invariants: never reduce coverage on these scenarios
HIGH_SEVERITY_SCENARIOS = frozenset([
    "insider_data_theft",
    "bec_wire_fraud",
    "attorney_departure_exfil",
    "vpn_brute_force_lateral",
    "credential_compromise",
    "ransomware_staging",
])


# =============================================================================
# DATA MODELS
# =============================================================================

class ShadowVerdict(Enum):
    """Outcome of a shadow run."""
    PASSED = "passed"                     # Safe to promote
    FAILED_METRICS = "failed_metrics"     # Metrics regressed
    FAILED_COVERAGE = "failed_coverage"   # Lost coverage on critical scenarios
    FAILED_GUARDRAIL = "failed_guardrail" # Violated hard invariant
    ERROR = "error"                       # Runtime error during replay


@dataclass
class ShadowResult:
    """
    Result of a shadow mode evaluation.

    Contains everything needed for the "review proposed changes" UI:
      - Before/after metrics
      - Test suite pass rate
      - Guardrail check results
      - Human-readable summary
    """
    proposal_id: str
    candidate_policy_version: int
    baseline_policy_version: int
    verdict: str = "pending"  # ShadowVerdict value
    started_at: str = ""
    completed_at: str = ""
    duration_seconds: float = 0.0

    # Metrics comparison
    baseline_score: float = 0.0
    candidate_score: float = 0.0
    score_delta: float = 0.0
    metrics_comparison: Dict[str, Any] = field(default_factory=dict)

    # Test suite results
    test_suite_pass_rate: float = 0.0
    test_suite_details: Dict[str, Any] = field(default_factory=dict)

    # Guardrail checks
    guardrail_violations: List[str] = field(default_factory=list)
    coverage_check: Dict[str, Any] = field(default_factory=dict)

    # Shadow alerts (what would have changed)
    new_alerts_count: int = 0
    removed_alerts_count: int = 0
    changed_severity_count: int = 0

    # Human-readable summary for UI
    summary: str = ""
    recommendation: str = ""  # "approve", "reject", "review_manually"

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# SHADOW RUNNER
# =============================================================================

class ShadowRunner:
    """
    Evaluates candidate policies in shadow mode.

    Runs on a separate logical path (not the main correlation thread).
    Never sends shadow alerts to analysts.
    Enforces all safety guardrails.
    """

    SHADOW_LOG_DIR = Path(__file__).parent.parent / "knowledge" / "improvement" / "shadow_runs"

    def __init__(self):
        self.SHADOW_LOG_DIR.mkdir(parents=True, exist_ok=True)

    def evaluate_candidate(
        self,
        proposal_id: str,
        candidate_policy: Dict[str, Any],
        baseline_policy: Dict[str, Any],
        historical_events: List[Dict[str, Any]],
        engine_factory: Callable,
        test_suite_runner: Optional[Callable] = None,
        baseline_metrics: Optional[Dict[str, Any]] = None,
    ) -> ShadowResult:
        """
        Run a full shadow evaluation of a candidate policy.

        Args:
            proposal_id: ID of the improvement proposal.
            candidate_policy: The proposed policy as dict.
            baseline_policy: The current active policy as dict.
            historical_events: Stored events to replay.
            engine_factory: Callable(policy_dict) → detection engine instance.
                The engine must have an `ingest(event)` method and
                an `get_alerts()` method.
            test_suite_runner: Optional callable(engine) → test results dict.
            baseline_metrics: Pre-computed baseline metrics (optional).

        Returns:
            ShadowResult with verdict and full comparison.
        """
        start_time = time.time()

        result = ShadowResult(
            proposal_id=proposal_id,
            candidate_policy_version=candidate_policy.get("version", 0),
            baseline_policy_version=baseline_policy.get("version", 0),
        )

        try:
            # Step 1: Check guardrails BEFORE any simulation
            violations = self.check_guardrails(candidate_policy, baseline_policy)

            # Also run the 9 immutable invariant checks
            invariant_violations = InvariantChecker.check_all(
                candidate_policy, baseline_policy
            )
            violations.extend(invariant_violations)

            if violations:
                result.verdict = ShadowVerdict.FAILED_GUARDRAIL.value
                result.guardrail_violations = violations
                result.summary = (
                    f"BLOCKED: {len(violations)} guardrail violation(s). "
                    + "; ".join(violations[:3])
                )
                result.recommendation = "reject"
                self._finalize_result(result, start_time)
                return result

            # Step 2: Replay historical events with BOTH policies
            baseline_alerts = self._replay_events(
                historical_events, baseline_policy, engine_factory
            )
            candidate_alerts = self._replay_events(
                historical_events, candidate_policy, engine_factory
            )

            # Step 3: Compare alerts
            alert_diff = self._diff_alerts(baseline_alerts, candidate_alerts)
            result.new_alerts_count = alert_diff["new"]
            result.removed_alerts_count = alert_diff["removed"]
            result.changed_severity_count = alert_diff["severity_changed"]

            # Step 4: Check coverage on critical scenarios
            coverage_check = self._check_coverage(
                candidate_alerts, baseline_alerts
            )
            result.coverage_check = coverage_check
            if not coverage_check["passed"]:
                result.verdict = ShadowVerdict.FAILED_COVERAGE.value
                result.summary = (
                    f"BLOCKED: Lost coverage on {coverage_check['lost_patterns']}. "
                    f"Rule: never reduce coverage on known high-severity scenarios."
                )
                result.recommendation = "reject"
                self._finalize_result(result, start_time)
                return result

            # Step 5: Run test suite if available
            if test_suite_runner:
                test_results = test_suite_runner(candidate_policy)
                result.test_suite_pass_rate = test_results.get("pass_rate", 0)
                result.test_suite_details = test_results

                if result.test_suite_pass_rate < 1.0:
                    # Some tests failed — flag but don't auto-reject
                    failed = [
                        d for d in test_results.get("details", [])
                        if not d.get("passed", True)
                    ]
                    logger.warning(
                        f"Shadow test suite: {len(failed)} test(s) failed"
                    )

            # Step 6: Compute metric comparison
            baseline_score = baseline_metrics.get("score", 50) if baseline_metrics else 50
            # Estimate candidate score from alert diff
            candidate_score = self._estimate_score(
                baseline_score, alert_diff, result.test_suite_pass_rate
            )
            result.baseline_score = baseline_score
            result.candidate_score = candidate_score
            result.score_delta = round(candidate_score - baseline_score, 2)

            result.metrics_comparison = {
                "baseline_alerts": len(baseline_alerts),
                "candidate_alerts": len(candidate_alerts),
                "alert_delta": len(candidate_alerts) - len(baseline_alerts),
                "new_detections": alert_diff["new"],
                "lost_detections": alert_diff["removed"],
                "score_improvement": result.score_delta,
            }

            # Step 7: Determine verdict
            if candidate_score < baseline_score:
                result.verdict = ShadowVerdict.FAILED_METRICS.value
                result.summary = (
                    f"Candidate score ({candidate_score:.1f}) < baseline "
                    f"({baseline_score:.1f}). Metrics regressed."
                )
                result.recommendation = "reject"
            elif result.test_suite_pass_rate < 1.0:
                result.verdict = ShadowVerdict.PASSED.value
                result.summary = (
                    f"Score improved ({baseline_score:.1f} → {candidate_score:.1f}) "
                    f"but {int((1 - result.test_suite_pass_rate) * 100)}% of tests "
                    f"failed. Manual review recommended."
                )
                result.recommendation = "review_manually"
            else:
                result.verdict = ShadowVerdict.PASSED.value
                result.summary = (
                    f"Score improved ({baseline_score:.1f} → {candidate_score:.1f}). "
                    f"All tests pass. Safe to promote."
                )
                result.recommendation = "approve"

        except Exception as e:
            result.verdict = ShadowVerdict.ERROR.value
            result.summary = f"Shadow evaluation error: {str(e)}"
            result.recommendation = "reject"
            logger.error(f"Shadow evaluation failed: {e}", exc_info=True)

        self._finalize_result(result, start_time)
        return result

    # -------------------------------------------------------------------------
    # Guardrail checks
    # -------------------------------------------------------------------------

    def check_guardrails(
        self,
        candidate: Dict[str, Any],
        baseline: Dict[str, Any],
    ) -> List[str]:
        """
        Enforce hard invariants that RSI must never violate.

        Returns list of violation descriptions (empty = all OK).
        """
        violations = []

        # Rule 1: Never auto-change protected domains
        # Compare top-level keys for unexpected additions
        candidate_keys = set(self._flatten_keys(candidate))
        for key in candidate_keys:
            for protected in PROTECTED_DOMAINS:
                if protected in key.lower():
                    # Check if the value changed from baseline
                    old_val = self._get_nested(baseline, key)
                    new_val = self._get_nested(candidate, key)
                    if old_val != new_val:
                        violations.append(
                            f"Protected domain modified: {key} "
                            f"({protected} is immutable without human review)"
                        )

        # Rule 2: Threshold bounds (delegated to PolicyStore invariants)
        thresholds = candidate.get("thresholds", {})
        from .policy_store import IMMUTABLE_INVARIANTS
        for param, bounds in IMMUTABLE_INVARIANTS.items():
            if param in thresholds:
                val = thresholds[param]
                if "min" in bounds and val < bounds["min"]:
                    violations.append(
                        f"{param}={val} < min {bounds['min']}: {bounds['reason']}"
                    )
                if "max" in bounds and val > bounds["max"]:
                    violations.append(
                        f"{param}={val} > max {bounds['max']}: {bounds['reason']}"
                    )

        # Rule 3: Never relax time bounds below safety minimum
        if thresholds.get("event_ttl_days", 30) < 7:
            violations.append(
                "event_ttl_days < 7: minimum retention for forensic analysis"
            )

        # Rule 4: Never disable all patterns
        weights = candidate.get("pattern_weights", {})
        if weights:
            enabled_count = sum(
                1 for w in weights.values()
                if (isinstance(w, dict) and w.get("enabled", True))
            )
            if enabled_count == 0:
                violations.append(
                    "All patterns disabled — system would be blind"
                )

        # Rule 5: Invariant Violation Scanner — detect prompt injection
        #   Catches RSI proposals that attempt to:
        #     (a) exempt specific users from detection
        #     (b) weaken thresholds for specific users
        #     (c) embed natural-language instructions in policy values
        violations.extend(self._scan_for_injection(candidate))

        return violations

    # -------------------------------------------------------------------------
    # Invariant Violation Scanner  (Gemini recommendation)
    # -------------------------------------------------------------------------

    # Patterns that indicate an injected instruction inside policy values
    _INJECTION_MARKERS = [
        "ignore",
        "skip",
        "exempt",
        "exclude",
        "whitelist",
        "bypass",
        "disable detection",
        "do not alert",
        "no alert",
        "update policy",
        "override invariant",
    ]

    def _scan_for_injection(self, policy: Dict[str, Any]) -> List[str]:
        """
        Walk every string value in the candidate policy and flag
        suspicious natural-language instructions that could originate
        from a recursive indirect injection attack.

        Also checks for per-user exemptions, which no automated
        proposal should ever contain.
        """
        violations: List[str] = []

        # --- Per-user exemption check ------------------------------------
        exemptions_keys = {"exempt_users", "excluded_users", "skip_users",
                           "whitelist_users", "whitelisted_users",
                           "allowed_users", "bypass_users"}
        for key in self._flatten_keys(policy):
            leaf = key.split(".")[-1].lower()
            if leaf in exemptions_keys:
                val = self._get_nested(policy, key)
                if val:  # non-empty exemption list
                    violations.append(
                        f"INJECTION: Policy contains per-user exemption "
                        f"list at '{key}' with {len(val) if isinstance(val, list) else 1} "
                        f"entries. Per-user exemptions are forbidden (I6)."
                    )

        # --- NL instruction scan -----------------------------------------
        for key in self._flatten_keys(policy):
            val = self._get_nested(policy, key)
            if not isinstance(val, str):
                continue
            val_lower = val.lower()
            for marker in self._INJECTION_MARKERS:
                if marker in val_lower:
                    violations.append(
                        f"INJECTION: Suspicious instruction detected in "
                        f"'{key}': contains '{marker}'. "
                        f"Value: '{val[:120]}'"
                    )
                    break  # one violation per key is enough

        return violations

    # -------------------------------------------------------------------------
    # Event replay
    # -------------------------------------------------------------------------

    def _replay_events(
        self,
        events: List[Dict[str, Any]],
        policy: Dict[str, Any],
        engine_factory: Callable,
    ) -> List[Dict[str, Any]]:
        """
        Replay events through a detection engine configured with a policy.

        Returns list of alerts generated.
        """
        try:
            engine = engine_factory(policy)
            alerts = []

            for event in events:
                try:
                    result = engine.ingest(event)
                    if result and isinstance(result, list):
                        alerts.extend(result)
                    elif result:
                        alerts.append(result)
                except Exception as e:
                    logger.debug(f"Event replay error: {e}")
                    continue

            return alerts

        except Exception as e:
            logger.error(f"Engine creation failed: {e}")
            return []

    # -------------------------------------------------------------------------
    # Alert comparison
    # -------------------------------------------------------------------------

    def _diff_alerts(
        self,
        baseline_alerts: List[Dict[str, Any]],
        candidate_alerts: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Compare two sets of alerts and count differences."""
        def alert_key(a):
            return (
                a.get("user_id", ""),
                a.get("alert_type", a.get("pattern", "")),
                a.get("event_type", ""),
            )

        baseline_keys = {alert_key(a) for a in baseline_alerts}
        candidate_keys = {alert_key(a) for a in candidate_alerts}

        new = candidate_keys - baseline_keys
        removed = baseline_keys - candidate_keys
        common = baseline_keys & candidate_keys

        # Check severity changes in common alerts
        severity_changed = 0
        baseline_by_key = {alert_key(a): a for a in baseline_alerts}
        candidate_by_key = {alert_key(a): a for a in candidate_alerts}
        for key in common:
            if key in baseline_by_key and key in candidate_by_key:
                if baseline_by_key[key].get("severity") != candidate_by_key[key].get("severity"):
                    severity_changed += 1

        return {
            "new": len(new),
            "removed": len(removed),
            "common": len(common),
            "severity_changed": severity_changed,
        }

    def _check_coverage(
        self,
        candidate_alerts: List[Dict[str, Any]],
        baseline_alerts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Verify that candidate doesn't lose coverage on critical scenarios.

        Rule: "Never reduce coverage on known high-severity scenarios."
        """
        def get_patterns(alerts):
            return {
                a.get("alert_type", a.get("pattern", ""))
                for a in alerts
            }

        baseline_patterns = get_patterns(baseline_alerts)
        candidate_patterns = get_patterns(candidate_alerts)

        # Check critical patterns
        lost = []
        for pattern in HIGH_SEVERITY_SCENARIOS:
            if pattern in baseline_patterns and pattern not in candidate_patterns:
                lost.append(pattern)

        return {
            "passed": len(lost) == 0,
            "baseline_patterns": sorted(baseline_patterns),
            "candidate_patterns": sorted(candidate_patterns),
            "lost_patterns": lost,
            "new_patterns": sorted(candidate_patterns - baseline_patterns),
        }

    def _estimate_score(
        self,
        baseline_score: float,
        alert_diff: Dict[str, int],
        test_pass_rate: float,
    ) -> float:
        """
        Estimate composite score from alert diff and test results.

        In production, this would recompute full metrics from replay.
        For now, use a heuristic adjustment.
        """
        score = baseline_score

        # Reducing false alerts (removed) improves precision
        if alert_diff["removed"] > 0:
            score += min(alert_diff["removed"] * 0.5, 10)

        # New detections improve recall
        if alert_diff["new"] > 0:
            score += min(alert_diff["new"] * 1.0, 15)

        # Failed tests penalize
        if test_pass_rate < 1.0:
            score -= (1 - test_pass_rate) * 20

        return round(max(0, min(100, score)), 2)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _flatten_keys(self, d: Dict, prefix: str = "") -> List[str]:
        """Recursively flatten dict keys to dot-notation paths."""
        keys = []
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.append(full_key)
            if isinstance(v, dict):
                keys.extend(self._flatten_keys(v, full_key))
        return keys

    def _get_nested(self, d: Dict, key: str) -> Any:
        """Get a nested value by dot-notation path."""
        parts = key.split(".")
        current = d
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _finalize_result(self, result: ShadowResult, start_time: float):
        """Set timing and persist the result."""
        result.completed_at = datetime.utcnow().isoformat()
        result.duration_seconds = round(time.time() - start_time, 3)

        # Save to disk
        path = self.SHADOW_LOG_DIR / f"shadow_{result.proposal_id}.json"
        with open(path, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

        logger.info(
            f"Shadow run {result.proposal_id}: {result.verdict} "
            f"(score delta: {result.score_delta:+.1f}, "
            f"duration: {result.duration_seconds:.1f}s)"
        )
