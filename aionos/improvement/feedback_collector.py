"""
AION OS - Feedback Collector
==============================

Closes the human-in-the-loop cycle.

Surfaces improvement opportunities and collects analyst corrections:
  - "Mark this as mis-categorized"
  - "This is a near-miss"
  - "Alert was accurate"
  - "Reduce noise on this pattern"

Feeds corrections back into the evaluation pipeline so the
Improvement Engine can learn from human judgment.

UI integration hooks:
  - get_pending_reviews() → alerts awaiting feedback
  - submit_feedback() → record analyst correction
  - get_proposals_for_review() → policy changes awaiting approval
  - approve_proposal() / reject_proposal() → disposition decisions
"""

import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger("aionos.improvement.feedback")

FEEDBACK_DIR = Path(__file__).parent.parent / "knowledge" / "improvement" / "feedback"

# =============================================================================
# ANTI-POISONING CONFIGURATION
# =============================================================================
# Protects the improvement loop from adversarial feedback injection.
# An attacker could feed sustained "false positive" feedback to slowly
# erode detection thresholds until the system is blind to a pattern.

POISONING_GUARD_CONFIG = {
    # Rate limits (per analyst)
    "max_feedback_per_hour": 60,          # No analyst submits 60+ in an hour
    "max_feedback_per_day": 300,          # Hard daily cap per analyst
    "max_noisy_ratio": 0.85,             # If >85% of feedback is "noisy", flag it
    "noisy_window_hours": 24,            # Window for noisy ratio check

    # Pattern-targeted poisoning
    "max_noisy_per_pattern_per_day": 10,  # Max "noisy" votes on one pattern/day
    "min_analysts_for_consensus": 2,      # Need 2+ analysts agreeing before changes

    # Anomaly detection
    "burst_threshold": 10,                # 10+ feedback items in 5 minutes = burst
    "burst_window_minutes": 5,
}


# =============================================================================
# DATA MODELS
# =============================================================================

class FeedbackType(Enum):
    """Types of analyst feedback."""
    ALERT_CORRECT = "alert_correct"         # True positive confirmed
    ALERT_NOISY = "alert_noisy"             # False positive
    ALERT_MISSED = "alert_missed"           # Should have alerted but didn't
    ALERT_MIS_CATEGORIZED = "mis_categorized"  # Wrong category/severity
    ALERT_NEAR_MISS = "near_miss"           # Close but missed key detail
    ALERT_DUPLICATE = "duplicate"           # Duplicate of another alert
    PROPOSAL_APPROVE = "proposal_approve"   # Approve a proposed change
    PROPOSAL_REJECT = "proposal_reject"     # Reject a proposed change
    GENERAL_NOTE = "general_note"           # Free-form analyst note


@dataclass
class AnalystFeedback:
    """
    A single piece of analyst feedback.

    Can be attached to an alert (correction) or a proposal (disposition).
    """
    id: str = ""
    feedback_type: str = ""  # FeedbackType value
    analyst_id: str = ""
    timestamp: str = ""

    # Alert feedback
    alert_id: Optional[str] = None
    corrected_severity: Optional[str] = None   # e.g., "P2" → "P0"
    corrected_category: Optional[str] = None
    notes: str = ""

    # Proposal feedback
    proposal_id: Optional[str] = None
    policy_version: Optional[int] = None

    # Timing (for analyst effort metrics)
    triage_start: Optional[str] = None
    triage_end: Optional[str] = None
    triage_seconds: Optional[float] = None

    def __post_init__(self):
        if not self.id:
            self.id = f"fb_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AnalystFeedback":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ImprovementNudge:
    """
    A suggestion surfaced to the analyst in the UI.

    Example:
      "The system believes reducing noise on 'Departing Attorney' alerts
       is possible; review proposed rule changes?"
    """
    id: str
    title: str
    description: str
    category: str  # "noise_reduction", "coverage_gap", "prompt_quality"
    proposal_id: Optional[str] = None
    before_stats: Dict[str, Any] = field(default_factory=dict)
    after_stats: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    status: str = "pending"  # "pending", "reviewed", "acted_on", "dismissed"

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# FEEDBACK COLLECTOR
# =============================================================================

class FeedbackCollector:
    """
    Collects analyst feedback and surfaces improvement opportunities.

    Integration points:
      - REST API: POST /api/v1/improvement/feedback
      - SvelteKit UI: inline correction buttons on alert cards
      - CLI: `aionos feedback --alert-id <id> --type correct`
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = Path(data_dir) if data_dir else FEEDBACK_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.feedback_path = self.data_dir / "analyst_feedback.jsonl"
        self.nudges_path = self.data_dir / "improvement_nudges.json"

        self._feedback: List[AnalystFeedback] = []
        self._nudges: List[ImprovementNudge] = []

        # Anti-poisoning index: analyst_id -> list of timestamps (ISO strings)
        self._analyst_timestamps: Dict[str, List[str]] = defaultdict(list)

        self._load()

    # -------------------------------------------------------------------------
    # Alert feedback
    # -------------------------------------------------------------------------

    def submit_feedback(self, feedback: AnalystFeedback) -> AnalystFeedback:
        """
        Record analyst feedback for an alert or proposal.

        Includes anti-poisoning guards:
          - Rate limiting per analyst (hourly + daily)
          - Burst detection (flood of feedback in short window)
          - Pattern-targeted noisy-vote cap
          - Anomalous noisy ratio detection
        """
        # --- Anti-poisoning checks ---
        poisoning_flag = self._check_poisoning(feedback)
        if poisoning_flag:
            logger.warning(
                f"POISONING GUARD: {poisoning_flag} | "
                f"analyst={feedback.analyst_id} type={feedback.feedback_type}"
            )
            # Still record the feedback but tag it as suspicious
            feedback.notes = f"[FLAGGED: {poisoning_flag}] {feedback.notes}"

        # Calculate triage time if start/end provided
        if feedback.triage_start and feedback.triage_end:
            try:
                start = datetime.fromisoformat(feedback.triage_start)
                end = datetime.fromisoformat(feedback.triage_end)
                feedback.triage_seconds = (end - start).total_seconds()
            except Exception:
                pass

        self._feedback.append(feedback)
        self._append_feedback(feedback)

        # Update anti-poisoning index
        self._analyst_timestamps[feedback.analyst_id].append(feedback.timestamp)

        logger.info(
            f"Feedback {feedback.id}: {feedback.feedback_type} "
            f"by {feedback.analyst_id}"
            + (f" for alert {feedback.alert_id}" if feedback.alert_id else "")
            + (f" for proposal {feedback.proposal_id}" if feedback.proposal_id else "")
        )
        return feedback

    def _check_poisoning(self, feedback: AnalystFeedback) -> Optional[str]:
        """
        Anti-poisoning guard — detects adversarial feedback patterns.

        Uses indexed timestamps for O(1) analyst lookup instead of
        scanning all feedback. Returns a flag string if suspicious, None if clean.
        """
        now = datetime.utcnow()
        analyst = feedback.analyst_id
        cfg = POISONING_GUARD_CONFIG

        # Use indexed timestamps (fast)
        timestamps = self._analyst_timestamps.get(analyst, [])

        # --- Rate limit: per hour ---
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        hourly_count = sum(1 for ts in timestamps if ts >= one_hour_ago)
        if hourly_count >= cfg["max_feedback_per_hour"]:
            return f"RATE_LIMIT_HOURLY: {hourly_count}/{cfg['max_feedback_per_hour']}"

        # --- Rate limit: per day ---
        one_day_ago = (now - timedelta(days=1)).isoformat()
        daily_count = sum(1 for ts in timestamps if ts >= one_day_ago)
        if daily_count >= cfg["max_feedback_per_day"]:
            return f"RATE_LIMIT_DAILY: {daily_count}/{cfg['max_feedback_per_day']}"

        # --- Burst detection ---
        burst_cutoff = (now - timedelta(minutes=cfg["burst_window_minutes"])).isoformat()
        burst_count = sum(1 for ts in timestamps if ts >= burst_cutoff)
        if burst_count >= cfg["burst_threshold"]:
            return f"BURST_DETECTED: {burst_count} in {cfg['burst_window_minutes']}min"

        # --- Noisy ratio check (only when submitting a noisy vote) ---
        if feedback.feedback_type == FeedbackType.ALERT_NOISY.value:
            noisy_cutoff = (now - timedelta(hours=cfg["noisy_window_hours"])).isoformat()
            # Only scan this analyst's feedback (not all)
            analyst_recent = [
                fb for fb in self._feedback
                if fb.analyst_id == analyst and fb.timestamp >= noisy_cutoff
            ]
            if len(analyst_recent) >= 10:
                noisy_count = sum(
                    1 for fb in analyst_recent
                    if fb.feedback_type == FeedbackType.ALERT_NOISY.value
                )
                ratio = noisy_count / len(analyst_recent)
                if ratio > cfg["max_noisy_ratio"]:
                    return f"NOISY_RATIO_ANOMALY: {ratio:.0%} > {cfg['max_noisy_ratio']:.0%}"

        return None

    def get_poisoning_stats(self) -> Dict[str, Any]:
        """
        Get anti-poisoning statistics for audit/review.

        Returns flagged feedback count, analyst risk scores, etc.
        """
        flagged = [fb for fb in self._feedback if "[FLAGGED:" in fb.notes]
        analyst_flags: Dict[str, int] = defaultdict(int)
        for fb in flagged:
            analyst_flags[fb.analyst_id] += 1

        return {
            "total_feedback": len(self._feedback),
            "flagged_count": len(flagged),
            "flagged_ratio": len(flagged) / max(len(self._feedback), 1),
            "flagged_by_analyst": dict(analyst_flags),
            "guard_config": POISONING_GUARD_CONFIG,
        }

    def get_pending_reviews(
        self,
        limit: int = 50,
        alert_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get alerts that haven't received feedback yet.

        Returns lightweight dicts suitable for UI display.
        In production, this queries the alert store for unreviewed alerts.
        """
        # For now, return alerts without feedback from our records
        reviewed_alert_ids = {
            fb.alert_id for fb in self._feedback
            if fb.alert_id is not None
        }

        # Placeholder: in production, query TemporalCorrelationEngine
        # for recent alerts not in reviewed_alert_ids
        return {
            "reviewed_count": len(reviewed_alert_ids),
            "message": "Connect to alert store for pending reviews",
        }

    def get_feedback_stats(
        self,
        since: Optional[str] = None,
        analyst_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get statistics about feedback collected."""
        feedback = self._feedback

        if since:
            feedback = [f for f in feedback if f.timestamp >= since]
        if analyst_id:
            feedback = [f for f in feedback if f.analyst_id == analyst_id]

        type_counts = {}
        triage_times = []
        for fb in feedback:
            type_counts[fb.feedback_type] = type_counts.get(fb.feedback_type, 0) + 1
            if fb.triage_seconds is not None:
                triage_times.append(fb.triage_seconds)

        return {
            "total_feedback": len(feedback),
            "by_type": type_counts,
            "avg_triage_seconds": (
                round(sum(triage_times) / len(triage_times), 1)
                if triage_times else None
            ),
            "unique_analysts": len({f.analyst_id for f in feedback}),
        }

    # -------------------------------------------------------------------------
    # Improvement nudges
    # -------------------------------------------------------------------------

    def create_nudge(self, nudge: ImprovementNudge) -> ImprovementNudge:
        """Create an improvement nudge for the analyst UI."""
        self._nudges.append(nudge)
        self._save_nudges()

        logger.info(f"Created nudge: {nudge.title} ({nudge.category})")
        return nudge

    def get_active_nudges(self) -> List[ImprovementNudge]:
        """Get nudges that haven't been acted on."""
        return [n for n in self._nudges if n.status == "pending"]

    def dismiss_nudge(self, nudge_id: str, analyst_id: str):
        """Dismiss a nudge (analyst doesn't want to act on it)."""
        for nudge in self._nudges:
            if nudge.id == nudge_id:
                nudge.status = "dismissed"
                self._save_nudges()
                logger.info(f"Nudge {nudge_id} dismissed by {analyst_id}")
                return

    def act_on_nudge(self, nudge_id: str, analyst_id: str):
        """Mark a nudge as acted upon (analyst reviewed the proposal)."""
        for nudge in self._nudges:
            if nudge.id == nudge_id:
                nudge.status = "acted_on"
                self._save_nudges()
                logger.info(f"Nudge {nudge_id} acted on by {analyst_id}")
                return

    # -------------------------------------------------------------------------
    # Converting feedback to evaluation outcomes
    # -------------------------------------------------------------------------

    def to_alert_outcomes(self) -> List[Dict[str, Any]]:
        """
        Convert analyst feedback into AlertOutcome-compatible dicts.

        Used by the EvaluationEngine to compute metrics.
        """
        outcomes = []
        for fb in self._feedback:
            if fb.alert_id and fb.feedback_type in (
                FeedbackType.ALERT_CORRECT.value,
                FeedbackType.ALERT_NOISY.value,
                FeedbackType.ALERT_MISSED.value,
                FeedbackType.ALERT_MIS_CATEGORIZED.value,
                FeedbackType.ALERT_NEAR_MISS.value,
                FeedbackType.ALERT_DUPLICATE.value,
            ):
                # Map feedback type to outcome label
                type_to_outcome = {
                    FeedbackType.ALERT_CORRECT.value: "true_positive",
                    FeedbackType.ALERT_NOISY.value: "false_positive",
                    FeedbackType.ALERT_MISSED.value: "missed",
                    FeedbackType.ALERT_MIS_CATEGORIZED.value: "mis_categorized",
                    FeedbackType.ALERT_NEAR_MISS.value: "near_miss",
                    FeedbackType.ALERT_DUPLICATE.value: "duplicate",
                }

                outcomes.append({
                    "alert_id": fb.alert_id,
                    "outcome": type_to_outcome.get(fb.feedback_type, "pending"),
                    "analyst_id": fb.analyst_id,
                    "reviewed_at": fb.timestamp,
                    "analyst_time_seconds": fb.triage_seconds,
                    "corrected_severity": fb.corrected_severity,
                    "corrected_category": fb.corrected_category,
                    "notes": fb.notes,
                })

        return outcomes

    def get_recent_false_positives(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts marked as false positives (for candidate generation)."""
        fps = [
            fb.to_dict() for fb in self._feedback
            if fb.feedback_type == FeedbackType.ALERT_NOISY.value
        ]
        return fps[-limit:]

    def get_recent_missed_threats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent missed threats (for candidate generation)."""
        missed = [
            fb.to_dict() for fb in self._feedback
            if fb.feedback_type == FeedbackType.ALERT_MISSED.value
        ]
        return missed[-limit:]

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def _load(self):
        """Load feedback and nudges from disk."""
        if self.feedback_path.exists():
            try:
                with open(self.feedback_path) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self._feedback.append(
                                AnalystFeedback.from_dict(json.loads(line))
                            )
            except Exception as e:
                logger.warning(f"Failed to load feedback: {e}")

        if self.nudges_path.exists():
            try:
                with open(self.nudges_path) as f:
                    data = json.load(f)
                self._nudges = [
                    ImprovementNudge(**n) for n in data.get("nudges", [])
                ]
            except Exception as e:
                logger.warning(f"Failed to load nudges: {e}")

    def _append_feedback(self, feedback: AnalystFeedback):
        """Append feedback to JSONL file."""
        with open(self.feedback_path, "a") as f:
            f.write(json.dumps(feedback.to_dict(), default=str) + "\n")

    def _save_nudges(self):
        """Save nudges to JSON file."""
        data = {
            "updated_at": datetime.utcnow().isoformat(),
            "nudges": [n.to_dict() for n in self._nudges],
        }
        with open(self.nudges_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
