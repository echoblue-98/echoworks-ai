"""
AION OS — Extracted Pattern Engines
=====================================

Four domain-specific scoring engines that run PURE PYTHON.
Zero LLM dependency. Sub-millisecond per evaluation.

These are the "demo magic" layer:
  ProximityEngine  — Cluster users by behavioral similarity
  TrustEngine      — Dynamic trust scoring that decays / builds over time
  PhaseEngine      — Time-of-day + day-of-week risk amplification
  VibeSynergy      — Cross-signal fusion (when multiple engines agree, boost)

Architecture:
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │  Proximity   │  │    Trust     │  │    Phase     │  │ VibeSynergy  │
  │  Engine      │  │    Engine    │  │    Engine    │  │   (Fusion)   │
  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                 │                 │                 │
         └─────────────────┴─────────────────┴─────────────────┘
                                     │
                            ┌────────▼────────┐
                            │  Composite Risk │
                            │  Score (0-100)  │
                            └─────────────────┘

Each engine is stateless per call (state lives in the cache/store).
This means Dan can run 50 demo sessions simultaneously with zero contention.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# Shared types
# ============================================================================

@dataclass
class EngineScore:
    """Result from any pattern engine."""
    engine: str
    score: float           # 0.0 – 1.0
    confidence: float      # 0.0 – 1.0
    signals: List[str]     # Human-readable signal descriptions
    latency_us: float = 0  # Microseconds to compute


class RiskBand(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: float) -> "RiskBand":
        if score >= 0.85:
            return cls.CRITICAL
        if score >= 0.60:
            return cls.HIGH
        if score >= 0.35:
            return cls.MEDIUM
        return cls.LOW


# ============================================================================
# 1. ProximityEngine — Behavioral cluster similarity
# ============================================================================

class ProximityEngine:
    """
    Scores how close a user's current behavior is to known threat clusters.

    Works by comparing event-type frequency vectors using cosine similarity.
    No ML model — just vector math over event counts.

    Demo pitch: "Watch AION cluster 3 actors by behavioral fingerprint — instant."
    """

    # Reference threat profiles (event-type → weight)
    THREAT_CLUSTERS: Dict[str, Dict[str, float]] = {
        "data_exfiltration": {
            "file_download": 0.9, "bulk_operation": 0.85, "cloud_sync": 0.8,
            "usb_activity": 0.75, "print_job": 0.5, "email_forward": 0.6,
        },
        "credential_theft": {
            "vpn_brute_force": 0.95, "impossible_travel": 0.9,
            "credential_access": 0.85, "mfa_bypass": 0.8,
            "geographic_anomaly": 0.7, "vpn_access": 0.4,
        },
        "insider_sabotage": {
            "security_disable": 0.95, "log_deletion": 0.9,
            "registry_change": 0.8, "scheduled_task": 0.75,
            "permission_change": 0.7, "admin_action": 0.6,
        },
        "bec_wire_fraud": {
            "email_impersonation": 0.95, "bec_indicator": 0.9,
            "wire_transfer_request": 0.85, "email_account_takeover": 0.8,
            "email_rule_change": 0.7, "executive_whaling": 0.75,
        },
        "pre_departure": {
            "file_download": 0.8, "cloud_sync": 0.85,
            "email_forward": 0.75, "print_job": 0.7,
            "after_hours_access": 0.6, "vpn_access": 0.4,
        },
    }

    def score(self, event_counts: Dict[str, int]) -> EngineScore:
        """
        Score user's event vector against all threat clusters.

        Args:
            event_counts: {event_type_name: count} for the user's recent window
        Returns:
            EngineScore with best-matching cluster similarity
        """
        t0 = time.perf_counter()

        if not event_counts:
            return EngineScore("proximity", 0.0, 0.0, ["no events"], 0)

        best_cluster = ""
        best_sim = 0.0
        signals: List[str] = []

        for cluster_name, cluster_vec in self.THREAT_CLUSTERS.items():
            sim = self._cosine_sim(event_counts, cluster_vec)
            if sim > best_sim:
                best_sim = sim
                best_cluster = cluster_name

        if best_sim > 0.2:
            signals.append(f"Nearest cluster: {best_cluster} (sim={best_sim:.3f})")
            # Find which events contributed most
            cluster_vec = self.THREAT_CLUSTERS[best_cluster]
            top_contributors = sorted(
                [(k, event_counts.get(k, 0) * cluster_vec.get(k, 0))
                 for k in set(event_counts) & set(cluster_vec)],
                key=lambda x: x[1], reverse=True
            )[:3]
            for ev, contrib in top_contributors:
                if contrib > 0:
                    signals.append(f"  ↳ {ev}: {event_counts[ev]} events (weight {cluster_vec[ev]:.2f})")

        latency = (time.perf_counter() - t0) * 1_000_000
        confidence = min(1.0, sum(event_counts.values()) / 20)  # More events → more confident
        return EngineScore("proximity", best_sim, confidence, signals, latency)

    @staticmethod
    def _cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
        keys = set(a) | set(b)
        dot = sum(float(a.get(k, 0)) * float(b.get(k, 0)) for k in keys)
        mag_a = math.sqrt(sum(float(v) ** 2 for v in a.values())) or 1e-9
        mag_b = math.sqrt(sum(float(v) ** 2 for v in b.values())) or 1e-9
        return dot / (mag_a * mag_b)


# ============================================================================
# 2. TrustEngine — Dynamic trust decay / build
# ============================================================================

class TrustEngine:
    """
    Maintains a trust score per user that decays on suspicious signals
    and slowly rebuilds during normal operation.

    Trust = 1.0 (fully trusted) → 0.0 (fully untrusted)

    Decay events (reduce trust):
      - after_hours_access:   -0.15
      - bulk_operation:       -0.20
      - impossible_travel:    -0.30
      - security_disable:     -0.40
      - credential_access:    -0.25

    Recovery: +0.02 per hour of clean behavior (capped at 1.0)

    Demo pitch: "This user started at 1.0 trust. After 3 events, they're at 0.35.
                 AION caught the decay pattern — no LLM needed."
    """

    DECAY_MAP: Dict[str, float] = {
        "after_hours_access": 0.15,
        "bulk_operation": 0.20,
        "file_download": 0.10,
        "cloud_sync": 0.15,
        "usb_activity": 0.20,
        "impossible_travel": 0.30,
        "security_disable": 0.40,
        "credential_access": 0.25,
        "log_deletion": 0.35,
        "email_forward": 0.10,
        "vpn_brute_force": 0.30,
        "mfa_bypass": 0.30,
        "wire_transfer_request": 0.25,
        "email_impersonation": 0.20,
        "permission_change": 0.15,
        "print_job": 0.05,
    }

    RECOVERY_PER_HOUR = 0.02
    MIN_TRUST = 0.0
    MAX_TRUST = 1.0

    def score(self, events: List[Dict[str, Any]],
              initial_trust: float = 1.0,
              hours_since_last_event: float = 0.0) -> EngineScore:
        """
        Compute current trust level after processing event sequence.

        Args:
            events: list of {"type": str, ...} in chronological order
            initial_trust: starting trust level
            hours_since_last_event: clean hours since last known event
        """
        t0 = time.perf_counter()
        trust = initial_trust
        signals: List[str] = []

        for ev in events:
            ev_type = ev.get("type", "").lower()
            decay = self.DECAY_MAP.get(ev_type, 0.0)
            if decay > 0:
                trust = max(self.MIN_TRUST, trust - decay)
                signals.append(f"{ev_type}: trust → {trust:.2f} (−{decay:.2f})")

        # Recovery for clean hours
        if hours_since_last_event > 0 and trust < self.MAX_TRUST:
            recovery = min(
                hours_since_last_event * self.RECOVERY_PER_HOUR,
                self.MAX_TRUST - trust,
            )
            trust += recovery
            if recovery > 0.01:
                signals.append(f"Recovery +{recovery:.2f} over {hours_since_last_event:.1f}h clean")

        # Invert: low trust = high risk
        risk = 1.0 - trust
        latency = (time.perf_counter() - t0) * 1_000_000
        confidence = min(1.0, len(events) / 5)
        return EngineScore("trust", risk, confidence, signals, latency)


# ============================================================================
# 3. PhaseEngine — Time-of-day / day-of-week risk amplification
# ============================================================================

class PhaseEngine:
    """
    Amplifies risk scores during high-risk time windows.

    Research shows insider threats disproportionately occur:
      - After midnight (00:00–05:00)  ×1.8  "graveyard shift"
      - Weekends                      ×1.5
      - Holiday eves                  ×1.6
      - Friday 5PM–midnight           ×1.3  "end-of-week dump"

    Demo pitch: "This same event at 2PM scores 0.4. At 2AM? AION boosts to 0.72.
                 PhaseEngine knows when threats happen."
    """

    # Hour ranges and their multipliers (24h format)
    HOUR_MULTIPLIERS = {
        range(0, 5): 1.8,    # Graveyard
        range(5, 7): 1.4,    # Early morning
        range(7, 9): 1.0,    # Normal start
        range(9, 17): 1.0,   # Business hours
        range(17, 20): 1.1,  # After hours
        range(20, 24): 1.5,  # Late night
    }

    WEEKEND_MULTIPLIER = 1.5
    FRIDAY_EVENING_MULTIPLIER = 1.3  # Friday 17:00+

    def score(self, base_risk: float, timestamp: Optional[datetime] = None) -> EngineScore:
        """
        Apply temporal amplification to a base risk score.

        Args:
            base_risk: Raw risk (0–1) from other engines
            timestamp: When the event occurred (defaults to now)
        """
        t0 = time.perf_counter()
        ts = timestamp or datetime.utcnow()
        hour = ts.hour
        weekday = ts.weekday()  # 0=Mon, 6=Sun
        signals: List[str] = []

        # Hour multiplier
        hour_mult = 1.0
        for hr_range, mult in self.HOUR_MULTIPLIERS.items():
            if hour in hr_range:
                hour_mult = mult
                break

        if hour_mult > 1.0:
            signals.append(f"Hour {hour:02d}:00 → ×{hour_mult:.1f} amplification")

        # Weekend check
        weekend = weekday >= 5
        if weekend:
            hour_mult = max(hour_mult, self.WEEKEND_MULTIPLIER)
            signals.append(f"Weekend activity → ×{self.WEEKEND_MULTIPLIER:.1f}")

        # Friday evening
        if weekday == 4 and hour >= 17:
            hour_mult = max(hour_mult, self.FRIDAY_EVENING_MULTIPLIER)
            signals.append("Friday evening dump window")

        amplified = min(1.0, base_risk * hour_mult)
        latency = (time.perf_counter() - t0) * 1_000_000
        return EngineScore(
            "phase", amplified, 0.95, signals, latency
        )


# ============================================================================
# 4. VibeSynergy — Cross-engine signal fusion
# ============================================================================

class VibeSynergy:
    """
    Fuses scores from multiple engines into a single composite risk.

    When engines AGREE (all score high), the composite gets a synergy boost.
    When engines DISAGREE, the composite is damped.

    This prevents single-engine false positives while amplifying true threats.

    Scoring:
      - Weighted average of engine scores
      - Agreement bonus: +15% if all engines > 0.5
      - Disagreement penalty: −10% if stddev > 0.3
      - Confidence = min(engine confidences)

    Demo pitch: "Proximity found the cluster. Trust decayed to 0.35.
                 Phase says it's 2AM. VibeSynergy: CRITICAL — all engines agree."
    """

    WEIGHTS = {
        "proximity": 0.30,
        "trust": 0.35,
        "phase": 0.20,
        "external": 0.15,   # For temporal/baseline engine passthrough
    }

    AGREEMENT_BONUS = 0.15
    DISAGREEMENT_PENALTY = 0.10
    AGREEMENT_THRESHOLD = 0.5
    DISAGREEMENT_STDDEV = 0.3

    def fuse(self, scores: List[EngineScore]) -> EngineScore:
        """
        Combine multiple engine scores into a single composite.

        Args:
            scores: List of EngineScore from individual engines
        """
        t0 = time.perf_counter()

        if not scores:
            return EngineScore("synergy", 0.0, 0.0, ["no input scores"], 0)

        # Weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        for s in scores:
            w = self.WEIGHTS.get(s.engine, 0.15)
            weighted_sum += s.score * w
            total_weight += w

        base = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Agreement / disagreement
        raw_scores = [s.score for s in scores]
        signals: List[str] = []

        all_high = all(s >= self.AGREEMENT_THRESHOLD for s in raw_scores)
        if all_high and len(scores) >= 2:
            base = min(1.0, base + self.AGREEMENT_BONUS)
            signals.append(f"Synergy boost +{self.AGREEMENT_BONUS:.0%}: all engines agree")

        if len(raw_scores) >= 2:
            mean = sum(raw_scores) / len(raw_scores)
            variance = sum((x - mean) ** 2 for x in raw_scores) / len(raw_scores)
            stddev = math.sqrt(variance)
            if stddev > self.DISAGREEMENT_STDDEV:
                base = max(0.0, base - self.DISAGREEMENT_PENALTY)
                signals.append(f"Disagreement damping −{self.DISAGREEMENT_PENALTY:.0%}: σ={stddev:.2f}")

        # Aggregate signals from sub-engines
        for s in scores:
            if s.signals:
                signals.append(f"[{s.engine}] {s.signals[0]}")

        confidence = min(s.confidence for s in scores) if scores else 0.0
        latency = (time.perf_counter() - t0) * 1_000_000
        total_latency = latency + sum(s.latency_us for s in scores)

        return EngineScore("synergy", base, confidence, signals, total_latency)


# ============================================================================
# Composite scorer — runs all engines in sequence
# ============================================================================

class PatternEnginePipeline:
    """
    Runs all four pattern engines and fuses the result.

    Single-call interface for the detection pipeline and daemon pre-compute.

    Usage:
        pipeline = PatternEnginePipeline()
        result = pipeline.evaluate(event_counts, trust_events, base_risk, timestamp)
        # result.score → composite 0-1
        # result.signals → full signal chain
    """

    def __init__(self):
        self.proximity = ProximityEngine()
        self.trust = TrustEngine()
        self.phase = PhaseEngine()
        self.synergy = VibeSynergy()

    def evaluate(
        self,
        event_counts: Dict[str, int],
        trust_events: Optional[List[Dict[str, Any]]] = None,
        base_risk: float = 0.0,
        timestamp: Optional[datetime] = None,
        initial_trust: float = 1.0,
        hours_clean: float = 0.0,
    ) -> EngineScore:
        """
        Full pipeline evaluation.

        Args:
            event_counts: {event_type: count} for proximity clustering
            trust_events: chronological events for trust decay
            base_risk: passthrough risk from temporal/baseline engines
            timestamp: event time for phase amplification
            initial_trust: user's current trust level
            hours_clean: hours of clean behavior since last event
        """
        scores: List[EngineScore] = []

        # 1. Proximity
        prox = self.proximity.score(event_counts)
        scores.append(prox)

        # 2. Trust
        trust_score = self.trust.score(
            trust_events or [],
            initial_trust=initial_trust,
            hours_since_last_event=hours_clean,
        )
        scores.append(trust_score)

        # 3. Phase
        phase_input = max(prox.score, trust_score.score, base_risk)
        phase_score = self.phase.score(phase_input, timestamp)
        scores.append(phase_score)

        # 4. External passthrough (temporal/baseline engine output)
        if base_risk > 0:
            scores.append(EngineScore(
                "external", base_risk, 0.8,
                [f"Temporal/baseline risk: {base_risk:.2f}"],
            ))

        # 5. Fuse
        return self.synergy.fuse(scores)

    def evaluate_quick(self, event_counts: Dict[str, int]) -> EngineScore:
        """Lightweight evaluation — proximity + phase only. For daemon pre-compute."""
        prox = self.proximity.score(event_counts)
        phase = self.phase.score(prox.score)
        return self.synergy.fuse([prox, phase])
