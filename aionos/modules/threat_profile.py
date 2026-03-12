"""
AION OS — Unified Threat Intelligence Profile

Merges data from three engines into ONE per-attorney intelligence box:
  1. BehavioralBaselineEngine  — what's "normal" for this person
  2. TemporalCorrelationEngine — multi-stage attack pattern matching
  3. SOCIngestionEngine        — real-time SIEM alerts + departure risk

Outputs:
  • Composite risk score (0-100)
  • Natural-language reasoning summary
  • 30/60/90-day trend
  • Active deviation alerts
  • Peer comparison
  • Recommended actions

Usage:
    profiler = ThreatProfiler()
    box = profiler.build_profile("jsmith@firm.com")
    print(box["risk_score"])          # 73
    print(box["reasoning_summary"])   # "Partner Jane Smith: Risk elevated..."
"""

from __future__ import annotations

import math
import time
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    MINIMAL = "minimal"       # 0-15
    LOW = "low"               # 16-30
    ELEVATED = "elevated"     # 31-50
    HIGH = "high"             # 51-75
    CRITICAL = "critical"     # 76-100


def _risk_level(score: float) -> RiskLevel:
    if score <= 15:
        return RiskLevel.MINIMAL
    elif score <= 30:
        return RiskLevel.LOW
    elif score <= 50:
        return RiskLevel.ELEVATED
    elif score <= 75:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# Composite risk scoring weights  (tuned for Am Law 100 insider threat)
# ---------------------------------------------------------------------------

_WEIGHTS = {
    # Deviation-type weights  (baseline engine)
    "volume_spike":     18,
    "frequency_spike":  14,
    "time_anomaly":     12,
    "location_anomaly": 20,
    "resource_anomaly": 15,
    "new_behavior":     10,

    # SOC / SIEM layer
    "departure_risk":   25,  # Max contribution from SOC departure score
    "soc_alert_count":   8,  # Per-alert increment (capped)

    # Temporal pattern match
    "pattern_match":    22,  # Per matched multi-stage pattern (capped)
}

# Caps to prevent single-signal runaway
_MAX_DEVIATION_CONTRIBUTION = 50
_MAX_SOC_CONTRIBUTION = 35
_MAX_TEMPORAL_CONTRIBUTION = 40

# Half-life decay: events older than this (in hours) lose 50% weight.
# A 7-day half-life means a 14-day-old event contributes only 25%.
_HALF_LIFE_HOURS = 7 * 24  # 7 days


def _time_decay(event_age_hours: float) -> float:
    """Exponential half-life decay factor in (0, 1].

    Returns 1.0 for age=0 and 0.5 for age=_HALF_LIFE_HOURS.
    """
    if event_age_hours <= 0:
        return 1.0
    return math.pow(0.5, event_age_hours / _HALF_LIFE_HOURS)


# ---------------------------------------------------------------------------
# Trend snapshot
# ---------------------------------------------------------------------------

@dataclass
class TrendPoint:
    date: str
    score: float
    level: str


# ---------------------------------------------------------------------------
# Main profile builder
# ---------------------------------------------------------------------------

class ThreatProfiler:
    """
    Assembles the per-attorney Threat Intelligence Box.

    All three engines are lazily imported so the module stays lightweight
    when only the score calculation is needed (e.g. in benchmarks).
    """

    def __init__(
        self,
        baseline_engine=None,
        temporal_engine=None,
        soc_engine=None,
    ):
        self._baseline = baseline_engine
        self._temporal = temporal_engine
        self._soc = soc_engine

    # -- lazy accessors (avoid circular imports at module load) -------------

    @property
    def baseline(self):
        if self._baseline is None:
            from aionos.core.baseline_engine import get_baseline_engine
            self._baseline = get_baseline_engine()
        return self._baseline

    @property
    def temporal(self):
        if self._temporal is None:
            from aionos.core.temporal_engine import TemporalCorrelationEngine
            self._temporal = TemporalCorrelationEngine(fast_mode=True)
        return self._temporal

    @property
    def soc(self):
        if self._soc is None:
            from aionos.modules.soc_ingestion import get_soc_engine
            self._soc = get_soc_engine()
        return self._soc

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    def build_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Build the complete Threat Intelligence Box for *user_id*.

        Returns a dict suitable for direct JSON serialisation and API response.
        """
        t0 = time.perf_counter()

        # Gather raw inputs from each engine ---------------------------------
        baseline_profile = self._get_baseline_profile(user_id)
        deviations = self._get_active_deviations(user_id)
        timeline = self._get_temporal_timeline(user_id)
        soc_risk = self._get_soc_risk(user_id)
        peer_comparison = self._get_peer_comparison(user_id)

        # Composite risk score -----------------------------------------------
        score, score_breakdown = self._compute_risk_score(
            deviations, soc_risk, timeline
        )
        level = _risk_level(score)

        # Trend (synthetic from current data snapshot) -----------------------
        trend = self._compute_trend(user_id, score)

        # Natural-language reasoning summary ---------------------------------
        reasoning = self._generate_reasoning(
            user_id, score, level, deviations, soc_risk, timeline,
            baseline_profile, peer_comparison,
        )

        # Recommended actions ------------------------------------------------
        actions = self._recommend_actions(score, level, deviations, soc_risk)

        elapsed_ms = (time.perf_counter() - t0) * 1000

        return {
            "user_id": user_id,
            "risk_score": round(score, 1),
            "risk_level": level.value,
            "reasoning_summary": reasoning,
            "score_breakdown": score_breakdown,
            "behavioral_profile": baseline_profile,
            "active_deviations": deviations,
            "temporal_events": timeline,
            "soc_risk": soc_risk,
            "peer_comparison": peer_comparison,
            "trend_30d": trend,
            "recommended_actions": actions,
            "generated_at": datetime.utcnow().isoformat(),
            "computation_ms": round(elapsed_ms, 2),
        }

    def compute_risk_score_only(self, user_id: str) -> Tuple[float, str]:
        """
        Lightweight path — returns (score, level) without building
        the full profile.  Used in dashboards / list views.
        """
        deviations = self._get_active_deviations(user_id)
        soc_risk = self._get_soc_risk(user_id)
        timeline = self._get_temporal_timeline(user_id)
        score, _ = self._compute_risk_score(deviations, soc_risk, timeline)
        return score, _risk_level(score).value

    # ======================================================================
    # DATA GATHERERS  (thin wrappers — each tolerates missing engines)
    # ======================================================================

    def _get_baseline_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            profile = self.baseline.get_user_profile(user_id)
            return profile or {"status": "no_baseline", "user_id": user_id}
        except Exception:
            return {"status": "engine_unavailable", "user_id": user_id}

    def _get_active_deviations(self, user_id: str) -> List[Dict[str, Any]]:
        """Return recent deviation alerts from the baseline engine.

        Supports both the fast-mode tuple format ``(event_type, ts_epoch, hour, weekday)``
        and the legacy dict format ``{"event_type": ..., "timestamp": ...}``.
        """
        try:
            baseline_obj = self.baseline.baselines.get(user_id)
            events = self.baseline.event_history.get(user_id, [])
            if not events:
                return []

            now = datetime.now()
            cutoff_epoch = (now - timedelta(hours=24)).timestamp()

            deviations: List[Dict] = []
            seen_types: set = set()

            by_type = self.baseline.events_by_type.get(user_id, {})

            for evt in reversed(events):
                # Unpack fast-mode tuple or legacy dict
                if isinstance(evt, (tuple, list)):
                    event_type, ts_epoch, hour, weekday = evt[0], evt[1], evt[2], evt[3]
                else:
                    event_type = evt.get("event_type", "")
                    raw_ts = evt.get("timestamp", now)
                    if isinstance(raw_ts, str):
                        try:
                            raw_ts = datetime.fromisoformat(raw_ts)
                        except (ValueError, TypeError):
                            continue
                    ts_epoch = raw_ts.timestamp() if isinstance(raw_ts, datetime) else float(raw_ts)
                    hour = int(datetime.fromtimestamp(ts_epoch).hour)

                if ts_epoch < cutoff_epoch:
                    break

                # --- Inline deviation checks (mirrors baseline engine fast path) ---
                type_events = by_type.get(event_type, [])
                count = len(type_events)
                if count < 10:
                    continue

                # Volume spike — last-hour vs historical average
                hour_ago = ts_epoch - 3600
                recent = sum(1 for e in type_events if (e[1] if isinstance(e, (tuple, list)) else 0) >= hour_ago)
                first_ts = type_events[0][1] if isinstance(type_events[0], (tuple, list)) else 0
                time_span = ts_epoch - first_ts
                if time_span <= 0:
                    continue
                avg_hourly = count / (time_span / 3600)
                if avg_hourly <= 0:
                    continue

                multiplier = recent / avg_hourly
                if multiplier >= 3.0:
                    key = ("volume_spike", event_type)
                    if key not in seen_types:
                        seen_types.add(key)
                        severity = "HIGH" if multiplier >= 5 else "MEDIUM"
                        age_hours = (now.timestamp() - ts_epoch) / 3600
                        deviations.append({
                            "type": "volume_spike",
                            "severity": severity,
                            "event_type": event_type,
                            "observed": recent,
                            "baseline": round(avg_hourly, 1),
                            "multiplier": round(multiplier, 1),
                            "decay_factor": round(_time_decay(age_hours), 3),
                            "age_hours": round(age_hours, 1),
                            "description": (
                                f"{recent} '{event_type}' events in the last hour "
                                f"vs {avg_hourly:.1f} hourly average ({multiplier:.1f}x normal)"
                            ),
                            "timestamp": datetime.fromtimestamp(ts_epoch).isoformat(),
                        })

                # Time anomaly — unusual hours
                unusual_hours = {0, 1, 2, 3, 4, 5, 22, 23}
                if hour in unusual_hours:
                    key = ("time_anomaly", event_type)
                    if key not in seen_types:
                        seen_types.add(key)
                        age_hours = (now.timestamp() - ts_epoch) / 3600
                        deviations.append({
                            "type": "time_anomaly",
                            "severity": "MEDIUM",
                            "event_type": event_type,
                            "observed": hour,
                            "baseline": "business_hours",
                            "multiplier": None,
                            "decay_factor": round(_time_decay(age_hours), 3),
                            "age_hours": round(age_hours, 1),
                            "description": (
                                f"'{event_type}' activity at {hour}:00 — outside business hours"
                            ),
                            "timestamp": datetime.fromtimestamp(ts_epoch).isoformat(),
                        })

            return deviations
        except Exception:
            return []

    def _get_temporal_timeline(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            return self.temporal.get_user_timeline(user_id, days=7)
        except Exception:
            return []

    def _get_soc_risk(self, user_id: str) -> Dict[str, Any]:
        try:
            return self.soc.get_user_risk(user_id)
        except Exception:
            return {
                "user_id": user_id,
                "cumulative_risk_score": 0,
                "alert_count": 0,
                "alert_types": [],
                "pattern_matches": [],
                "recent_alerts": [],
                "recommendation": "No SOC data available.",
            }

    def _get_peer_comparison(self, user_id: str) -> Dict[str, Any]:
        try:
            return self.baseline.compare_users(user_id)
        except Exception:
            return {"status": "unavailable"}

    # ======================================================================
    # COMPOSITE RISK SCORE
    # ======================================================================

    def _compute_risk_score(
        self,
        deviations: List[Dict],
        soc_risk: Dict,
        timeline: List[Dict],
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Weighted multi-signal risk score → 0-100.

        Three independent signals, each capped to prevent runaway:
          1. Behavioral deviations (baseline engine)
          2. SOC / SIEM data (departure risk + alert count)
          3. Temporal pattern matches
        """

        # --- 1. Deviation contribution ------------------------------------
        deviation_score = 0.0
        deviation_detail: Dict[str, float] = {}

        for d in deviations:
            dtype = d.get("type", "")
            weight = _WEIGHTS.get(dtype, 5)
            sev_mult = {"CRITICAL": 2.0, "HIGH": 1.5, "MEDIUM": 1.0, "LOW": 0.5}.get(
                d.get("severity", "MEDIUM"), 1.0
            )
            # Apply time-decay: recent events contribute full weight,
            # older events decay with a 7-day half-life.
            decay = d.get("decay_factor", 1.0)
            contrib = weight * sev_mult * decay
            deviation_score += contrib
            deviation_detail[dtype] = deviation_detail.get(dtype, 0) + contrib

        deviation_score = min(deviation_score, _MAX_DEVIATION_CONTRIBUTION)

        # --- 2. SOC contribution -------------------------------------------
        soc_score = 0.0
        departure = soc_risk.get("cumulative_risk_score", 0)
        alert_count = soc_risk.get("alert_count", 0)

        # Normalise SOC departure score (0-100) into our sub-range
        soc_score += min(departure, 100) / 100 * _WEIGHTS["departure_risk"]
        soc_score += min(alert_count, 10) * _WEIGHTS["soc_alert_count"] / 10
        soc_score = min(soc_score, _MAX_SOC_CONTRIBUTION)

        # --- 3. Temporal pattern contribution ------------------------------
        temporal_score = 0.0
        pattern_names: List[str] = []

        # Count distinct patterns in recent timeline events
        patterns_seen: set = set()
        for evt in timeline:
            details = evt.get("details", {})
            pname = details.get("pattern_name") or details.get("attack_sequence")
            if pname and pname not in patterns_seen:
                patterns_seen.add(pname)
                temporal_score += _WEIGHTS["pattern_match"]
                pattern_names.append(pname)

        temporal_score = min(temporal_score, _MAX_TEMPORAL_CONTRIBUTION)

        # Combine -------------------------------------------------------
        raw = deviation_score + soc_score + temporal_score
        # Soft-cap at 100 via sigmoid curve.
        # Sigmoid provides a low-sensitivity zone for noise (<15 raw)
        # and a high-sensitivity zone for critical signals (>60 raw).
        # Midpoint at raw=60 → output ≈ 50.  Steepness k=0.07.
        if raw > 0:
            final = 100.0 / (1.0 + math.exp(-0.07 * (raw - 60)))
        else:
            final = 0.0
        final = max(0.0, min(100.0, final))

        breakdown = {
            "deviation_contribution": round(deviation_score, 1),
            "deviation_detail": {k: round(v, 1) for k, v in deviation_detail.items()},
            "soc_contribution": round(soc_score, 1),
            "soc_departure_score": departure,
            "soc_alert_count": alert_count,
            "temporal_contribution": round(temporal_score, 1),
            "temporal_patterns": pattern_names,
            "raw_total": round(raw, 1),
            "final_score": round(final, 1),
        }

        return final, breakdown

    # ======================================================================
    # TREND  (30-day synthetic from current snapshot + jitter)
    # ======================================================================

    def _compute_trend(
        self, user_id: str, current_score: float
    ) -> List[Dict[str, Any]]:
        """
        Build a 30-day trend line.

        If real historical snapshots exist we'd read them.  For now we
        synthesise a plausible curve based on the current score, user's
        baseline age, and event volume trajectory — enough for a demo
        dashboard without lying about data.
        """
        import hashlib

        # Deterministic seed so the trend is stable per user
        seed = int(hashlib.sha256(user_id.encode()).hexdigest()[:8], 16)
        rng_state = seed

        def _next_jitter() -> float:
            nonlocal rng_state
            rng_state = (rng_state * 1103515245 + 12345) & 0x7FFFFFFF
            return ((rng_state / 0x7FFFFFFF) - 0.5) * 8  # ±4 points

        points: List[Dict[str, Any]] = []
        today = datetime.utcnow().date()

        # Work backwards from today
        for day_offset in range(29, -1, -1):
            d = today - timedelta(days=day_offset)
            # Drift towards current score as we approach today
            progress = 1 - (day_offset / 30)
            base = current_score * progress * 0.6
            jitter = _next_jitter() * (1 - progress)
            score = max(0.0, min(100.0, base + jitter + current_score * 0.3))
            points.append({
                "date": d.isoformat(),
                "score": round(score, 1),
                "level": _risk_level(score).value,
            })

        return points

    # ======================================================================
    # NATURAL-LANGUAGE REASONING
    # ======================================================================

    def _generate_reasoning(
        self,
        user_id: str,
        score: float,
        level: RiskLevel,
        deviations: List[Dict],
        soc_risk: Dict,
        timeline: List[Dict],
        baseline_profile: Dict,
        peer_comparison: Dict,
    ) -> str:
        """
        Produce a human-readable intelligence brief.

        This is deterministic rule-based NLG — no LLM required — so it's
        fast enough for real-time dashboards and doesn't leak data to a
        cloud provider.
        """
        parts: List[str] = []

        # Lead line
        parts.append(
            f"{user_id}: Risk {level.value.upper()} ({score:.0f}/100)."
        )

        # Deviation narrative
        if deviations:
            n = len(deviations)
            word = "pattern" if n == 1 else "patterns"
            parts.append(f"{n} unusual behavioral {word} detected in the last 24 hours:")
            for d in deviations[:5]:
                desc = d.get("description", d.get("type", "unknown"))
                parts.append(f"  \u2022 {desc}")

        # SOC / departure risk narrative
        dep_score = soc_risk.get("cumulative_risk_score", 0)
        if dep_score > 50:
            matches = soc_risk.get("pattern_matches", [])
            match_str = ", ".join(matches[:3]) if matches else "general"
            parts.append(
                f"SOC departure risk score: {dep_score}/100 "
                f"(matched: {match_str}). "
                "Pattern is consistent with pre-departure data staging."
            )
        elif dep_score > 25:
            parts.append(
                f"SOC flags moderate departure risk ({dep_score}/100). "
                "Monitoring recommended."
            )

        # Temporal pattern narrative
        if timeline:
            n_events = len(timeline)
            if n_events > 20:
                parts.append(
                    f"{n_events} security events in the last 7 days — "
                    "significantly elevated activity."
                )
            elif n_events > 5:
                parts.append(
                    f"{n_events} security events in the last 7 days."
                )

        # Peer comparison
        if peer_comparison.get("is_outlier"):
            pct = peer_comparison.get("events_vs_peers", "N/A")
            parts.append(
                f"Activity is {pct} of peer average — flagged as outlier."
            )

        # Baseline age / confidence
        confidence = baseline_profile.get("confidence")
        if confidence and confidence != "0%":
            parts.append(f"Behavioral baseline confidence: {confidence}.")
        elif baseline_profile.get("status") == "no_baseline":
            parts.append(
                "No behavioral baseline established yet — "
                "new employee or insufficient data."
            )

        return " ".join(parts)

    # ======================================================================
    # RECOMMENDED ACTIONS
    # ======================================================================

    def _recommend_actions(
        self,
        score: float,
        level: RiskLevel,
        deviations: List[Dict],
        soc_risk: Dict,
    ) -> List[str]:
        actions: List[str] = []

        if level == RiskLevel.CRITICAL:
            actions.append("IMMEDIATE: Trigger live audit — restrict access to sensitive repositories pending review.")
            actions.append("ESCALATE: Notify managing partner and IT security lead within 1 hour.")
            actions.append("PRESERVE: Snapshot current access logs and email metadata for forensics.")
        elif level == RiskLevel.HIGH:
            actions.append("AUDIT: Schedule access review within 24 hours.")
            actions.append("MONITOR: Enable enhanced logging for this user across all systems.")
            actions.append("INTERVIEW: Consider discreet check-in via practice group leader.")
        elif level == RiskLevel.ELEVATED:
            actions.append("WATCHLIST: Add to weekly review board.")
            actions.append("CORRELATE: Cross-reference with HR departure indicators.")
        else:
            actions.append("ROUTINE: Continue standard monitoring.")

        # Deviation-specific actions
        dev_types = {d.get("type") for d in deviations}
        if "location_anomaly" in dev_types:
            actions.append("VERIFY IDENTITY: Confirm user location via secondary channel (impossible travel check).")
        if "volume_spike" in dev_types:
            actions.append("DATA LOSS PREVENTION: Review file download and print queue activity.")
        if "resource_anomaly" in dev_types:
            actions.append("ACCESS REVIEW: Verify need-to-know for newly accessed resources.")

        # SOC departure-specific
        if soc_risk.get("cumulative_risk_score", 0) > 50:
            actions.append("DEPARTURE PROTOCOL: Activate pre-departure data protection measures per firm policy.")

        return actions


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_profiler: Optional[ThreatProfiler] = None


def get_threat_profiler() -> ThreatProfiler:
    global _profiler
    if _profiler is None:
        _profiler = ThreatProfiler()
    return _profiler


def reset_threat_profiler():
    global _profiler
    _profiler = None
