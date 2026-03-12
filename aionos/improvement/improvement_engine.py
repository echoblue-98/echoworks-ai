"""
AION OS - Improvement Engine (Main Orchestrator)
==================================================

The top-level module that ties together:
  - PolicyStore: versioned, diffable, rollback-able config
  - EvaluationEngine: metrics, test suites, fitness function
  - CandidateGenerator: LLM-powered change proposals
  - ShadowRunner: replay-based evaluation with guardrails
  - FeedbackCollector: human-in-the-loop corrections

Workflow:
  ┌──────────────────────────────────────────────────────────────┐
  │  1. Feedback flows in  (analyst corrections, outcome labels) │
  │  2. Metrics computed   (precision, recall, speed)            │
  │  3. Candidates generated  (LLM proposes changes offline)     │
  │  4. Shadow evaluation  (replay historical data)              │
  │  5. Proposal surfaced  (nudge analyst in UI)                 │
  │  6. Human approves     (review before/after stats)           │
  │  7. Policy promoted    (new version goes active)             │
  │  8. Repeat             (continuous improvement loop)         │
  └──────────────────────────────────────────────────────────────┘

This is recursive self-improvement at the SYSTEM level,
grounded in human feedback and replay, not a model rewriting
its own code in the dark.
"""

import copy
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from .policy_store import PolicyStore, PolicyVersion
from .evaluation_engine import (
    EvaluationEngine, DetectionMetrics, AlertOutcome, TestScenario
)
from .candidate_generator import CandidateGenerator, CandidateChange, CandidateProposal
from .shadow_runner import ShadowRunner, ShadowResult, ShadowVerdict
from .feedback_collector import (
    FeedbackCollector, AnalystFeedback, ImprovementNudge, FeedbackType
)
from aionos.safety.invariants import InvariantChecker

logger = logging.getLogger("aionos.improvement")

# =============================================================================
# CONFIGURATION
# =============================================================================

# Minimum score improvement required to auto-recommend promotion
MIN_SCORE_IMPROVEMENT = 2.0

# Minimum shadow period before considering promotion (hours)
MIN_SHADOW_HOURS = 24

# Maximum number of changes per proposal
MAX_CHANGES_PER_PROPOSAL = 5

# How often to auto-generate candidates (hours)
AUTO_GENERATE_INTERVAL_HOURS = 168  # Weekly


# =============================================================================
# IMPROVEMENT ENGINE
# =============================================================================

class ImprovementEngine:
    """
    Orchestrates the recursive self-improvement cycle for AION OS.

    Usage:
        engine = ImprovementEngine()
        engine.initialize()

        # Analyst provides feedback
        engine.record_feedback(AnalystFeedback(...))

        # System generates + evaluates improvements
        result = engine.run_improvement_cycle()

        # Analyst reviews proposal in UI
        proposals = engine.get_pending_proposals()
        engine.approve_proposal(proposal_id, analyst_id="alice")

    Safety guarantees:
        - No change reaches production without human approval
        - All changes run in shadow mode first
        - Hard invariants enforced at every stage
        - Full audit trail
    """

    def __init__(
        self,
        policy_dir: Path = None,
        data_dir: Path = None,
        llm_provider: str = "mock",
    ):
        """
        Initialize the Improvement Engine.

        Args:
            policy_dir: Where to store versioned policies.
            data_dir: Where to store evaluation data, feedback, etc.
            llm_provider: LLM backend for candidate generation.
                "mock" (testing), "local" (Ollama/LMStudio), "claude"
        """
        self.policy_store = PolicyStore(policy_dir)
        self.evaluation = EvaluationEngine(data_dir)
        self.generator = CandidateGenerator(llm_provider)
        self.shadow = ShadowRunner()
        self.feedback = FeedbackCollector(
            data_dir / "feedback" if data_dir else None
        )

        self._initialized = False

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def initialize(self):
        """
        Initialize the engine with default policy and test suite.

        Call this once on first run, or when resetting.
        """
        # Create default policy if none exists
        active = self.policy_store.get_active()
        if not active:
            self.policy_store.initialize_default_policy()
            logger.info("Initialized default policy")

        # Create default test suite if empty
        if not self.evaluation.get_test_suite():
            self.evaluation.initialize_default_test_suite()
            logger.info("Initialized default test suite")

        self._initialized = True
        logger.info("Improvement Engine initialized")

    # -------------------------------------------------------------------------
    # Feedback recording
    # -------------------------------------------------------------------------

    def record_feedback(self, feedback: AnalystFeedback) -> AnalystFeedback:
        """
        Record analyst feedback and propagate to evaluation engine.

        This is the primary input that drives improvement.
        """
        # Record in feedback collector
        result = self.feedback.submit_feedback(feedback)

        # Convert to alert outcome and record in evaluation engine
        if feedback.alert_id and feedback.feedback_type in (
            FeedbackType.ALERT_CORRECT.value,
            FeedbackType.ALERT_NOISY.value,
            FeedbackType.ALERT_MISSED.value,
            FeedbackType.ALERT_MIS_CATEGORIZED.value,
            FeedbackType.ALERT_NEAR_MISS.value,
            FeedbackType.ALERT_DUPLICATE.value,
        ):
            type_to_outcome = {
                FeedbackType.ALERT_CORRECT.value: "true_positive",
                FeedbackType.ALERT_NOISY.value: "false_positive",
                FeedbackType.ALERT_MISSED.value: "missed",
                FeedbackType.ALERT_MIS_CATEGORIZED.value: "mis_categorized",
                FeedbackType.ALERT_NEAR_MISS.value: "near_miss",
                FeedbackType.ALERT_DUPLICATE.value: "duplicate",
            }

            active_policy = self.policy_store.get_active()
            outcome = AlertOutcome(
                alert_id=feedback.alert_id,
                alert_type=feedback.corrected_category or "",
                severity=feedback.corrected_severity or "",
                user_id="",
                outcome=type_to_outcome.get(feedback.feedback_type, "pending"),
                analyst_id=feedback.analyst_id,
                reviewed_at=feedback.timestamp,
                analyst_time_seconds=feedback.triage_seconds,
                corrected_severity=feedback.corrected_severity,
                corrected_category=feedback.corrected_category,
                notes=feedback.notes,
                policy_version=active_policy.version if active_policy else None,
            )
            self.evaluation.record_outcome(outcome)

        return result

    # -------------------------------------------------------------------------
    # Main improvement cycle
    # -------------------------------------------------------------------------

    def run_improvement_cycle(
        self,
        historical_events: Optional[List[Dict[str, Any]]] = None,
        engine_factory: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Run one full improvement cycle:
          1. Compute current metrics
          2. Generate candidate changes
          3. Build candidate policy
          4. Run shadow evaluation
          5. Surface a nudge if improvement found

        Args:
            historical_events: Events to replay in shadow mode.
                If None, uses events from evaluation data.
            engine_factory: Callable(policy_dict) → detection engine.
                Required for shadow mode replay.

        Returns:
            Dict with cycle results, proposal, and recommendation.
        """
        cycle_id = f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting improvement cycle {cycle_id}")

        # Step 1: Compute current metrics
        active_policy = self.policy_store.get_active()
        if not active_policy:
            return {"error": "No active policy. Run initialize() first."}

        metrics = self.evaluation.compute_metrics(
            policy_version=active_policy.version
        )

        # Step 2: Gather feedback for candidate generation
        recent_fps = self.feedback.get_recent_false_positives(limit=20)
        recent_fns = self.feedback.get_recent_missed_threats(limit=20)

        if not recent_fps and not recent_fns:
            return {
                "cycle_id": cycle_id,
                "status": "no_feedback",
                "message": "No feedback data yet. Collect analyst corrections first.",
                "metrics": metrics.to_dict(),
            }

        # Step 3: Generate candidate changes
        proposal = self.generator.generate_from_metrics(
            metrics=metrics.to_dict(),
            recent_fps=recent_fps,
            recent_fns=recent_fns,
            current_policy=active_policy.to_dict(),
        )

        if not proposal.changes:
            return {
                "cycle_id": cycle_id,
                "status": "no_candidates",
                "message": "LLM did not propose any changes.",
                "metrics": metrics.to_dict(),
            }

        # Step 4: Build candidate policy from proposal
        candidate_policy = self._apply_changes_to_policy(
            active_policy, proposal.changes
        )
        candidate_policy.description = proposal.description
        candidate_policy.created_by = "llm_candidate"
        candidate_policy.status = "shadow"
        candidate_policy.shadow_start = datetime.utcnow().isoformat()

        try:
            # Run the 9 immutable invariant checks before policy creation
            invariant_violations = InvariantChecker.check_all(
                candidate_policy.to_dict(),
                baseline_policy=active_policy.to_dict(),
            )
            if invariant_violations:
                return {
                    "cycle_id": cycle_id,
                    "status": "invariant_violation",
                    "message": f"{len(invariant_violations)} invariant(s) violated",
                    "violations": invariant_violations,
                    "proposal": proposal.to_dict(),
                }

            candidate_policy = self.policy_store.create_version(
                candidate_policy, validate=True
            )
        except ValueError as e:
            return {
                "cycle_id": cycle_id,
                "status": "invariant_violation",
                "message": str(e),
                "proposal": proposal.to_dict(),
            }

        proposal.target_policy_version = candidate_policy.version

        # Step 5: Run shadow evaluation
        shadow_result = None
        if historical_events and engine_factory:
            shadow_result = self.shadow.evaluate_candidate(
                proposal_id=proposal.id,
                candidate_policy=candidate_policy.to_dict(),
                baseline_policy=active_policy.to_dict(),
                historical_events=historical_events,
                engine_factory=engine_factory,
                test_suite_runner=lambda p: self.evaluation.run_test_suite(
                    engine_callback=lambda events: engine_factory(p).ingest_batch(events),
                    policy_version=candidate_policy.version,
                ),
                baseline_metrics=metrics.to_dict(),
            )

            # Update policy with evaluation score
            if shadow_result:
                candidate_policy.evaluation_score = shadow_result.candidate_score
                self.policy_store._save_version(candidate_policy)

        # Step 6: Surface nudge if improvement found
        if shadow_result and shadow_result.verdict == ShadowVerdict.PASSED.value:
            diff = self.policy_store.diff(
                active_policy.version, candidate_policy.version
            )
            self.feedback.create_nudge(ImprovementNudge(
                id=f"nudge_{proposal.id}",
                title=f"Detection improvement available (v{candidate_policy.version})",
                description=shadow_result.summary,
                category="noise_reduction" if recent_fps else "coverage_gap",
                proposal_id=proposal.id,
                before_stats={
                    "score": shadow_result.baseline_score,
                    "false_positives": metrics.false_positives,
                },
                after_stats={
                    "score": shadow_result.candidate_score,
                    "false_positives": metrics.false_positives - len(recent_fps),
                },
            ))

        return {
            "cycle_id": cycle_id,
            "status": "completed",
            "metrics": metrics.to_dict(),
            "proposal": proposal.to_dict(),
            "candidate_version": candidate_policy.version,
            "shadow_result": shadow_result.to_dict() if shadow_result else None,
            "recommendation": (
                shadow_result.recommendation if shadow_result
                else "shadow_required"
            ),
        }

    # -------------------------------------------------------------------------
    # Proposal management
    # -------------------------------------------------------------------------

    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """Get all proposals awaiting human review."""
        proposals = []
        for version_info in self.policy_store.list_versions():
            if version_info["status"] in ("draft", "shadow"):
                summary = self.policy_store.get_proposal_summary(
                    version_info["version"]
                )
                proposals.append(summary)
        return proposals

    def approve_proposal(
        self,
        policy_version: int,
        analyst_id: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Approve a proposed policy change and activate it.

        Args:
            policy_version: Version to approve.
            analyst_id: Who is approving.
            notes: Optional notes.

        Returns:
            Activation result.
        """
        # Record approval feedback
        self.feedback.submit_feedback(AnalystFeedback(
            feedback_type=FeedbackType.PROPOSAL_APPROVE.value,
            analyst_id=analyst_id,
            policy_version=policy_version,
            notes=notes,
        ))

        # Activate the version
        policy = self.policy_store.activate_version(
            policy_version, approved_by=analyst_id
        )

        logger.info(
            f"Proposal v{policy_version} approved by {analyst_id}: "
            f"{policy.description}"
        )

        return {
            "status": "approved",
            "version": policy.version,
            "approved_by": analyst_id,
            "description": policy.description,
        }

    def reject_proposal(
        self,
        policy_version: int,
        analyst_id: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        """Reject a proposed policy change."""
        policy = self.policy_store.get_version(policy_version)
        if policy:
            policy.status = "rejected"
            policy.notes = reason
            self.policy_store._save_version(policy)

        self.feedback.submit_feedback(AnalystFeedback(
            feedback_type=FeedbackType.PROPOSAL_REJECT.value,
            analyst_id=analyst_id,
            policy_version=policy_version,
            notes=reason,
        ))

        logger.info(
            f"Proposal v{policy_version} rejected by {analyst_id}: {reason}"
        )

        return {
            "status": "rejected",
            "version": policy_version,
            "rejected_by": analyst_id,
            "reason": reason,
        }

    def rollback_to(
        self,
        version: int,
        analyst_id: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        """Roll back to a previous policy version."""
        new_policy = self.policy_store.rollback(version, reason)

        logger.info(
            f"Rolled back to v{version} by {analyst_id}: {reason}"
        )

        return {
            "status": "rolled_back",
            "new_version": new_policy.version,
            "rolled_back_to": version,
            "reason": reason,
        }

    # -------------------------------------------------------------------------
    # Status & reporting
    # -------------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status for the dashboard."""
        active_policy = self.policy_store.get_active()
        versions = self.policy_store.list_versions()
        metrics = self.evaluation.compute_metrics(
            policy_version=active_policy.version if active_policy else None
        )
        feedback_stats = self.feedback.get_feedback_stats()
        nudges = self.feedback.get_active_nudges()

        return {
            "initialized": self._initialized,
            "active_policy": {
                "version": active_policy.version if active_policy else None,
                "description": active_policy.description if active_policy else None,
                "fingerprint": active_policy.fingerprint() if active_policy else None,
            },
            "policy_versions": len(versions),
            "metrics": {
                "precision": metrics.precision,
                "recall": metrics.recall_approx,
                "f1_score": metrics.f1_score,
                "noise_ratio": metrics.noise_ratio,
                "composite_score": metrics.score(),
            },
            "feedback": feedback_stats,
            "pending_nudges": len(nudges),
            "pending_proposals": len(self.get_pending_proposals()),
        }

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _apply_changes_to_policy(
        self,
        base_policy: PolicyVersion,
        changes: List[CandidateChange],
    ) -> PolicyVersion:
        """
        Create a new PolicyVersion by applying candidate changes to a base.

        Only modifies tunable parameters — never touches protected domains.
        """
        new_policy = copy.deepcopy(base_policy)
        new_policy.parent_version = base_policy.version

        policy_dict = new_policy.to_dict()

        for change in changes:
            target = change.target
            new_value = change.new_value

            if new_value is None:
                continue

            # Navigate to the target path and set the value
            parts = target.split(".")
            current = policy_dict
            for part in parts[:-1]:
                if part in current and isinstance(current[part], dict):
                    current = current[part]
                else:
                    break
            else:
                if parts[-1] in current:
                    current[parts[-1]] = new_value

        # Reconstruct PolicyVersion from modified dict
        return PolicyVersion.from_dict(policy_dict)
