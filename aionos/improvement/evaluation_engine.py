"""
AION OS - Evaluation Engine
============================

Provides the "fitness function" for recursive self-improvement.

Collects outcomes for each alert and computes:
  - Precision: what fraction of alerts were correct?
  - Recall (approx): did we catch known-bad scenarios?
  - Time-to-detect: how fast from first event to alert?
  - Analyst effort: how long did triage take?
  - Noise ratio: what fraction got auto-closed or dismissed?

Also maintains synthetic + real test suites as a regression pack.
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict
from enum import Enum

logger = logging.getLogger("aionos.improvement.evaluation")

# =============================================================================
# PATHS
# =============================================================================

EVAL_DATA_DIR = Path(__file__).parent.parent / "knowledge" / "improvement"
OUTCOMES_FILE = EVAL_DATA_DIR / "alert_outcomes.jsonl"
METRICS_FILE = EVAL_DATA_DIR / "metrics_history.jsonl"
TEST_SUITE_FILE = EVAL_DATA_DIR / "test_suite.json"


# =============================================================================
# DATA MODELS
# =============================================================================

class OutcomeLabel(Enum):
    """How a human analyst labeled an alert outcome."""
    TRUE_POSITIVE = "true_positive"       # Correct alert, real threat
    FALSE_POSITIVE = "false_positive"     # Noise, not a real threat
    NEAR_MISS = "near_miss"               # Alert was close but missed key detail
    MISSED = "missed"                     # System failed to alert on real threat
    MIS_CATEGORIZED = "mis_categorized"   # Alert fired but wrong category/severity
    DUPLICATE = "duplicate"               # Duplicate of another alert
    PENDING = "pending"                   # Not yet reviewed


@dataclass
class AlertOutcome:
    """
    Recorded outcome for a single alert.

    Populated by analyst feedback or automated label propagation.
    """
    alert_id: str
    alert_type: str                       # Pattern name or category
    severity: str                         # P0-P4
    user_id: str                          # User who triggered the alert
    timestamp: str = ""                   # When alert was generated
    outcome: str = "pending"              # OutcomeLabel value
    analyst_id: Optional[str] = None      # Who reviewed it
    reviewed_at: Optional[str] = None     # When reviewed
    time_to_detect_seconds: Optional[float] = None  # First event → alert
    analyst_time_seconds: Optional[float] = None     # Time spent triaging
    notes: str = ""
    corrected_severity: Optional[str] = None         # If mis-categorized
    corrected_category: Optional[str] = None
    policy_version: Optional[int] = None  # Which policy was active

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AlertOutcome":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DetectionMetrics:
    """
    Aggregate detection quality metrics over a time window.

    This is the "fitness function" for evaluating policy changes.
    """
    window_start: str
    window_end: str
    policy_version: int

    # Core metrics
    total_alerts: int = 0
    true_positives: int = 0
    false_positives: int = 0
    near_misses: int = 0
    missed_threats: int = 0
    mis_categorized: int = 0
    duplicates: int = 0
    pending_review: int = 0

    # Derived metrics
    precision: float = 0.0         # TP / (TP + FP)
    recall_approx: float = 0.0    # TP / (TP + missed)
    f1_score: float = 0.0         # Harmonic mean of precision & recall
    noise_ratio: float = 0.0      # (FP + dup) / total

    # Time metrics
    avg_time_to_detect_seconds: float = 0.0
    p95_time_to_detect_seconds: float = 0.0
    avg_analyst_time_seconds: float = 0.0
    p95_analyst_time_seconds: float = 0.0

    # Coverage
    patterns_triggered: int = 0
    unique_users_alerted: int = 0
    categories_covered: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def score(self) -> float:
        """
        Composite fitness score (0-100).

        Weights:
          - 40% precision (reduce noise)
          - 30% recall (don't miss threats)
          - 15% speed (time to detect)
          - 15% efficiency (analyst time)
        """
        precision_score = self.precision * 40
        recall_score = self.recall_approx * 30

        # Speed score: <5min=perfect, >1hr=0
        if self.avg_time_to_detect_seconds > 0:
            speed = max(0, 1 - (self.avg_time_to_detect_seconds / 3600))
        else:
            speed = 0.5  # No data
        speed_score = speed * 15

        # Efficiency: <5min analyst time=perfect, >30min=0
        if self.avg_analyst_time_seconds > 0:
            efficiency = max(0, 1 - (self.avg_analyst_time_seconds / 1800))
        else:
            efficiency = 0.5
        efficiency_score = efficiency * 15

        return round(precision_score + recall_score + speed_score + efficiency_score, 2)


@dataclass
class TestScenario:
    """
    A synthetic or real test scenario for regression testing.

    Each scenario defines events and expected detection outcome.
    """
    id: str
    name: str
    description: str
    category: str
    severity: str  # Expected severity
    events: List[Dict[str, Any]]     # SecurityEvent-like dicts
    expected_alert: bool = True      # Should this trigger?
    expected_pattern: str = ""       # Which pattern should match?
    source: str = "synthetic"        # "synthetic", "real_anonymized"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TestScenario":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# =============================================================================
# EVALUATION ENGINE
# =============================================================================

class EvaluationEngine:
    """
    Computes detection quality metrics and manages test suites.

    Provides the "fitness function" that drives RSI:
    a candidate policy change is only promoted if it improves
    the composite score without violating safety constraints.
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = Path(data_dir) if data_dir else EVAL_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.outcomes_path = self.data_dir / "alert_outcomes.jsonl"
        self.metrics_path = self.data_dir / "metrics_history.jsonl"
        self.test_suite_path = self.data_dir / "test_suite.json"

        self._outcomes: List[AlertOutcome] = []
        self._test_suite: List[TestScenario] = []
        self._load()

    # -------------------------------------------------------------------------
    # Outcome recording
    # -------------------------------------------------------------------------

    def record_outcome(self, outcome: AlertOutcome):
        """Record an alert outcome (from analyst feedback)."""
        self._outcomes.append(outcome)
        self._append_outcome(outcome)
        logger.info(
            f"Recorded outcome for alert {outcome.alert_id}: "
            f"{outcome.outcome} (by {outcome.analyst_id})"
        )

    def get_outcomes(
        self,
        since: Optional[str] = None,
        policy_version: Optional[int] = None,
        outcome_filter: Optional[str] = None,
    ) -> List[AlertOutcome]:
        """Query outcomes with optional filters."""
        results = self._outcomes

        if since:
            results = [o for o in results if o.timestamp >= since]
        if policy_version is not None:
            results = [o for o in results if o.policy_version == policy_version]
        if outcome_filter:
            results = [o for o in results if o.outcome == outcome_filter]

        return results

    # -------------------------------------------------------------------------
    # Metrics computation
    # -------------------------------------------------------------------------

    def compute_metrics(
        self,
        window_days: int = 30,
        policy_version: Optional[int] = None
    ) -> DetectionMetrics:
        """
        Compute aggregate detection metrics over a time window.

        Args:
            window_days: Look back this many days.
            policy_version: If set, only consider outcomes under this policy.

        Returns:
            DetectionMetrics with precision, recall, speed, etc.
        """
        cutoff = (datetime.utcnow() - timedelta(days=window_days)).isoformat()
        outcomes = self.get_outcomes(
            since=cutoff, policy_version=policy_version
        )

        if not outcomes:
            return DetectionMetrics(
                window_start=cutoff,
                window_end=datetime.utcnow().isoformat(),
                policy_version=policy_version or 0,
            )

        # Count outcomes
        counts = defaultdict(int)
        detect_times = []
        analyst_times = []
        patterns = set()
        users = set()
        categories = set()

        for o in outcomes:
            counts[o.outcome] += 1
            if o.time_to_detect_seconds is not None:
                detect_times.append(o.time_to_detect_seconds)
            if o.analyst_time_seconds is not None:
                analyst_times.append(o.analyst_time_seconds)
            patterns.add(o.alert_type)
            users.add(o.user_id)
            if o.corrected_category:
                categories.add(o.corrected_category)
            categories.add(o.alert_type)

        tp = counts.get("true_positive", 0)
        fp = counts.get("false_positive", 0)
        missed = counts.get("missed", 0)
        total = sum(counts.values())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + missed) if (tp + missed) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)
               if (precision + recall) > 0 else 0.0)
        noise = (fp + counts.get("duplicate", 0)) / total if total > 0 else 0.0

        metrics = DetectionMetrics(
            window_start=cutoff,
            window_end=datetime.utcnow().isoformat(),
            policy_version=policy_version or 0,
            total_alerts=total,
            true_positives=tp,
            false_positives=fp,
            near_misses=counts.get("near_miss", 0),
            missed_threats=missed,
            mis_categorized=counts.get("mis_categorized", 0),
            duplicates=counts.get("duplicate", 0),
            pending_review=counts.get("pending", 0),
            precision=round(precision, 4),
            recall_approx=round(recall, 4),
            f1_score=round(f1, 4),
            noise_ratio=round(noise, 4),
            avg_time_to_detect_seconds=(
                round(statistics.mean(detect_times), 2) if detect_times else 0.0
            ),
            p95_time_to_detect_seconds=(
                round(sorted(detect_times)[int(len(detect_times) * 0.95)]
                      if detect_times else 0.0, 2)
            ),
            avg_analyst_time_seconds=(
                round(statistics.mean(analyst_times), 2) if analyst_times else 0.0
            ),
            p95_analyst_time_seconds=(
                round(sorted(analyst_times)[int(len(analyst_times) * 0.95)]
                      if analyst_times else 0.0, 2)
            ),
            patterns_triggered=len(patterns),
            unique_users_alerted=len(users),
            categories_covered=sorted(categories),
        )

        # Persist metrics snapshot
        self._append_metrics(metrics)

        logger.info(
            f"Computed metrics: precision={metrics.precision:.2%}, "
            f"recall={metrics.recall_approx:.2%}, "
            f"f1={metrics.f1_score:.2%}, "
            f"score={metrics.score()}/100"
        )
        return metrics

    # -------------------------------------------------------------------------
    # Test suite management
    # -------------------------------------------------------------------------

    def add_test_scenario(self, scenario: TestScenario):
        """Add a test scenario to the regression pack."""
        # Check for duplicate IDs
        existing_ids = {s.id for s in self._test_suite}
        if scenario.id in existing_ids:
            # Update existing
            self._test_suite = [
                s if s.id != scenario.id else scenario
                for s in self._test_suite
            ]
        else:
            self._test_suite.append(scenario)
        self._save_test_suite()
        logger.info(f"Added test scenario: {scenario.id} ({scenario.name})")

    def get_test_suite(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[TestScenario]:
        """Get test scenarios, optionally filtered."""
        results = self._test_suite
        if category:
            results = [s for s in results if s.category == category]
        if tags:
            tag_set = set(tags)
            results = [s for s in results if tag_set & set(s.tags)]
        return results

    def run_test_suite(
        self,
        engine_callback,
        policy_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run all test scenarios against a detection engine callback.

        Args:
            engine_callback: function(events: List[dict]) → List[alert_dict]
                The caller provides a function that ingests events and
                returns any alerts generated.
            policy_version: Tag results with this policy version.

        Returns:
            Dict with pass/fail counts and details.
        """
        results = {
            "policy_version": policy_version,
            "total": len(self._test_suite),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "details": [],
        }

        for scenario in self._test_suite:
            try:
                alerts = engine_callback(scenario.events)
                triggered = len(alerts) > 0

                passed = (triggered == scenario.expected_alert)

                # Check pattern match if specified
                if passed and scenario.expected_pattern and alerts:
                    pattern_names = [
                        a.get("pattern", a.get("alert_type", ""))
                        for a in alerts
                    ]
                    if scenario.expected_pattern not in pattern_names:
                        passed = False

                if passed:
                    results["passed"] += 1
                else:
                    results["failed"] += 1

                results["details"].append({
                    "scenario_id": scenario.id,
                    "name": scenario.name,
                    "passed": passed,
                    "expected_alert": scenario.expected_alert,
                    "actual_alert": triggered,
                    "alerts_generated": len(alerts),
                })

            except Exception as e:
                results["errors"] += 1
                results["details"].append({
                    "scenario_id": scenario.id,
                    "name": scenario.name,
                    "passed": False,
                    "error": str(e),
                })

        results["pass_rate"] = (
            results["passed"] / results["total"]
            if results["total"] > 0 else 0.0
        )

        logger.info(
            f"Test suite: {results['passed']}/{results['total']} passed "
            f"({results['pass_rate']:.0%})"
        )
        return results

    def initialize_default_test_suite(self):
        """
        Seed the test suite with AION's 5 core demo scenarios
        plus additional regression cases.
        """
        scenarios = [
            TestScenario(
                id="typhoon_insider_theft",
                name="Typhoon Advertising Data Theft",
                description=(
                    "Classic insider threat: VPN access → database queries → "
                    "bulk downloads → hard drive destruction over 4 weeks"
                ),
                category="insider_threat",
                severity="P0",
                events=[
                    {"event_type": "vpn_access", "user_id": "knowles",
                     "day_offset": 0, "details": {"location": "home"}},
                    {"event_type": "database_query", "user_id": "knowles",
                     "day_offset": 7, "details": {"tables": ["clients", "billing"]}},
                    {"event_type": "bulk_operation", "user_id": "knowles",
                     "day_offset": 14, "details": {"file_count": 2500}},
                    {"event_type": "file_download", "user_id": "knowles",
                     "day_offset": 20, "details": {"size_mb": 800}},
                    {"event_type": "usb_activity", "user_id": "knowles",
                     "day_offset": 21, "details": {"action": "write"}},
                ],
                expected_alert=True,
                expected_pattern="insider_data_theft",
                tags=["core", "insider", "regression"],
            ),
            TestScenario(
                id="bec_wire_fraud",
                name="Business Email Compromise",
                description=(
                    "CEO impersonation → urgent wire transfer request → "
                    "modified banking details"
                ),
                category="financial_fraud",
                severity="P0",
                events=[
                    {"event_type": "email_forward", "user_id": "cfo_office",
                     "day_offset": 0, "details": {"from": "ceo_lookalike@ext.com"}},
                    {"event_type": "email_forward", "user_id": "cfo_office",
                     "day_offset": 0, "details": {"subject": "urgent wire"}},
                ],
                expected_alert=True,
                expected_pattern="bec_wire_fraud",
                tags=["core", "bec", "regression"],
            ),
            TestScenario(
                id="attorney_departure_exfil",
                name="Attorney Departure Data Exfiltration",
                description=(
                    "Departing partner downloads client files, forwards emails "
                    "to personal account, prints sensitive documents"
                ),
                category="legal_compliance",
                severity="P1",
                events=[
                    {"event_type": "file_download", "user_id": "partner_smith",
                     "day_offset": 0, "details": {"file_type": "client_matter"}},
                    {"event_type": "email_forward", "user_id": "partner_smith",
                     "day_offset": 1, "details": {"to": "partner_smith@gmail.com"}},
                    {"event_type": "print_job", "user_id": "partner_smith",
                     "day_offset": 2, "details": {"pages": 500}},
                    {"event_type": "cloud_sync", "user_id": "partner_smith",
                     "day_offset": 3, "details": {"service": "dropbox"}},
                ],
                expected_alert=True,
                expected_pattern="attorney_departure_exfil",
                tags=["core", "legal", "regression"],
            ),
            TestScenario(
                id="vpn_brute_force_lateral",
                name="VPN Brute Force + Lateral Movement",
                description=(
                    "Failed VPN logins → successful login → internal scanning → "
                    "privilege escalation"
                ),
                category="network_attack",
                severity="P1",
                events=[
                    {"event_type": "vpn_brute_force", "user_id": "external_actor",
                     "day_offset": 0, "details": {"attempts": 50}},
                    {"event_type": "vpn_access", "user_id": "compromised_user",
                     "day_offset": 0, "details": {"source": "tor_exit_node"}},
                    {"event_type": "geographic_anomaly", "user_id": "compromised_user",
                     "day_offset": 0, "details": {"location": "unexpected_country"}},
                ],
                expected_alert=True,
                expected_pattern="vpn_brute_force_lateral",
                tags=["core", "network", "regression"],
            ),
            TestScenario(
                id="mfa_fatigue_attack",
                name="MFA Fatigue / Push Bombing",
                description="Attacker spams MFA prompts until user accepts",
                category="identity_attack",
                severity="P1",
                events=[
                    {"event_type": "vpn_mfa_bypass", "user_id": "target_user",
                     "day_offset": 0, "details": {"push_count": 15,
                                                   "accepted_after_fatigue": True}},
                    {"event_type": "vpn_access", "user_id": "target_user",
                     "day_offset": 0, "details": {"new_device": True}},
                ],
                expected_alert=True,
                tags=["core", "identity", "regression"],
            ),
            # Negative test: normal activity should NOT alert
            TestScenario(
                id="normal_daily_work",
                name="Normal Attorney Daily Work",
                description="Routine file access and email during business hours",
                category="baseline",
                severity="P4",
                events=[
                    {"event_type": "vpn_access", "user_id": "normal_user",
                     "day_offset": 0, "details": {"location": "office"}},
                    {"event_type": "file_download", "user_id": "normal_user",
                     "day_offset": 0, "details": {"file_count": 3}},
                ],
                expected_alert=False,
                tags=["negative", "baseline", "regression"],
            ),
        ]

        for s in scenarios:
            self.add_test_scenario(s)

        logger.info(f"Initialized test suite with {len(scenarios)} scenarios")

    # -------------------------------------------------------------------------
    # Comparison helpers (for shadow mode)
    # -------------------------------------------------------------------------

    def compare_metrics(
        self,
        baseline: DetectionMetrics,
        candidate: DetectionMetrics,
    ) -> Dict[str, Any]:
        """
        Compare two metrics snapshots and produce a before/after summary.

        Returns dict suitable for "show before/after stats" UI.
        """
        def delta(old, new, pct=False):
            diff = new - old
            if pct and old > 0:
                return {"old": old, "new": new, "delta": diff,
                        "pct_change": round(diff / old * 100, 1)}
            return {"old": old, "new": new, "delta": diff}

        return {
            "precision": delta(baseline.precision, candidate.precision, pct=True),
            "recall": delta(baseline.recall_approx, candidate.recall_approx, pct=True),
            "f1_score": delta(baseline.f1_score, candidate.f1_score, pct=True),
            "noise_ratio": delta(baseline.noise_ratio, candidate.noise_ratio, pct=True),
            "false_positives": delta(baseline.false_positives, candidate.false_positives),
            "missed_threats": delta(baseline.missed_threats, candidate.missed_threats),
            "avg_detect_time": delta(
                baseline.avg_time_to_detect_seconds,
                candidate.avg_time_to_detect_seconds
            ),
            "composite_score": delta(baseline.score(), candidate.score()),
            "improved": candidate.score() > baseline.score(),
            "summary": (
                f"False positives {'↓' if candidate.false_positives < baseline.false_positives else '↑'} "
                f"{abs(candidate.false_positives - baseline.false_positives)}, "
                f"no impact on known incidents"
                if candidate.missed_threats <= baseline.missed_threats
                else f"WARNING: missed threats {'↑' if candidate.missed_threats > baseline.missed_threats else '↓'} "
                     f"{abs(candidate.missed_threats - baseline.missed_threats)}"
            ),
        }

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def _load(self):
        """Load outcomes and test suite from disk."""
        # Load outcomes
        if self.outcomes_path.exists():
            try:
                with open(self.outcomes_path) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self._outcomes.append(
                                AlertOutcome.from_dict(json.loads(line))
                            )
            except Exception as e:
                logger.warning(f"Failed to load outcomes: {e}")

        # Load test suite
        if self.test_suite_path.exists():
            try:
                with open(self.test_suite_path) as f:
                    data = json.load(f)
                self._test_suite = [
                    TestScenario.from_dict(s) for s in data.get("scenarios", [])
                ]
            except Exception as e:
                logger.warning(f"Failed to load test suite: {e}")

    def _append_outcome(self, outcome: AlertOutcome):
        """Append a single outcome to the JSONL file."""
        with open(self.outcomes_path, "a") as f:
            f.write(json.dumps(outcome.to_dict(), default=str) + "\n")

    def _append_metrics(self, metrics: DetectionMetrics):
        """Append metrics snapshot to history."""
        with open(self.metrics_path, "a") as f:
            f.write(json.dumps(metrics.to_dict(), default=str) + "\n")

    def _save_test_suite(self):
        """Save the full test suite."""
        data = {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat(),
            "scenarios": [s.to_dict() for s in self._test_suite],
        }
        with open(self.test_suite_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
