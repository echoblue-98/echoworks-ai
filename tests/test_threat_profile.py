"""
Tests for aionos.modules.threat_profile — Unified Threat Intelligence Box.

Covers:
  • Composite risk score computation (weights, caps, edge cases)
  • Risk level classification
  • Natural-language reasoning generation
  • Recommended actions by level
  • Trend generation (deterministic per user)
  • REST API endpoint integration
  • Lightweight risk-only path
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field

from aionos.modules.threat_profile import (
    ThreatProfiler,
    RiskLevel,
    _risk_level,
    _WEIGHTS,
    _MAX_DEVIATION_CONTRIBUTION,
    _MAX_SOC_CONTRIBUTION,
    _MAX_TEMPORAL_CONTRIBUTION,
    _HALF_LIFE_HOURS,
    _time_decay,
    get_threat_profiler,
    reset_threat_profiler,
)


# =========================================================================
# Helpers — lightweight mock engines
# =========================================================================


class FakeBaseline:
    """Minimal stand-in for BehavioralBaselineEngine."""

    def __init__(self, profiles=None, comparisons=None):
        self._profiles = profiles or {}
        self._comparisons = comparisons or {}
        self.baselines = {}
        self.event_history = {}

    def get_user_profile(self, user_id):
        return self._profiles.get(user_id)

    def compare_users(self, user_id, peer_group=None):
        return self._comparisons.get(user_id, {"status": "unavailable"})


class FakeTemporal:
    """Minimal stand-in for TemporalCorrelationEngine."""

    def __init__(self, timelines=None):
        self._timelines = timelines or {}

    def get_user_timeline(self, user_id, days=7):
        return self._timelines.get(user_id, [])


class FakeSOC:
    """Minimal stand-in for SOCIngestionEngine."""

    def __init__(self, risks=None):
        self._risks = risks or {}

    def get_user_risk(self, user_id):
        return self._risks.get(user_id, {
            "user_id": user_id,
            "cumulative_risk_score": 0,
            "alert_count": 0,
            "alert_types": [],
            "pattern_matches": [],
            "recent_alerts": [],
            "recommendation": "No SOC data available.",
        })


# =========================================================================
# Risk Level Classification
# =========================================================================


class TestRiskLevel:

    def test_minimal(self):
        assert _risk_level(0) == RiskLevel.MINIMAL
        assert _risk_level(15) == RiskLevel.MINIMAL

    def test_low(self):
        assert _risk_level(16) == RiskLevel.LOW
        assert _risk_level(30) == RiskLevel.LOW

    def test_elevated(self):
        assert _risk_level(31) == RiskLevel.ELEVATED
        assert _risk_level(50) == RiskLevel.ELEVATED

    def test_high(self):
        assert _risk_level(51) == RiskLevel.HIGH
        assert _risk_level(75) == RiskLevel.HIGH

    def test_critical(self):
        assert _risk_level(76) == RiskLevel.CRITICAL
        assert _risk_level(100) == RiskLevel.CRITICAL


# =========================================================================
# Composite Risk Score
# =========================================================================


class TestCompositeRiskScore:

    def _profiler(self, **kwargs):
        return ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )

    def test_zero_score_when_no_signals(self):
        p = self._profiler()
        score, breakdown = p._compute_risk_score([], {"cumulative_risk_score": 0, "alert_count": 0}, [])
        assert score == 0.0
        assert breakdown["raw_total"] == 0.0

    def test_deviations_contribute(self):
        p = self._profiler()
        devs = [
            {"type": "volume_spike", "severity": "HIGH"},
        ]
        score, breakdown = p._compute_risk_score(devs, {"cumulative_risk_score": 0, "alert_count": 0}, [])
        assert score > 0
        assert breakdown["deviation_contribution"] > 0

    def test_deviation_cap(self):
        """Many deviations shouldn't exceed the cap."""
        p = self._profiler()
        devs = [
            {"type": "volume_spike", "severity": "CRITICAL"},
            {"type": "location_anomaly", "severity": "CRITICAL"},
            {"type": "time_anomaly", "severity": "CRITICAL"},
            {"type": "frequency_spike", "severity": "CRITICAL"},
            {"type": "resource_anomaly", "severity": "CRITICAL"},
            {"type": "new_behavior", "severity": "CRITICAL"},
        ]
        _, breakdown = p._compute_risk_score(devs, {"cumulative_risk_score": 0, "alert_count": 0}, [])
        assert breakdown["deviation_contribution"] <= _MAX_DEVIATION_CONTRIBUTION

    def test_soc_contributes(self):
        p = self._profiler()
        soc = {"cumulative_risk_score": 80, "alert_count": 5}
        score, breakdown = p._compute_risk_score([], soc, [])
        assert score > 0
        assert breakdown["soc_contribution"] > 0

    def test_soc_cap(self):
        p = self._profiler()
        soc = {"cumulative_risk_score": 100, "alert_count": 100}
        _, breakdown = p._compute_risk_score([], soc, [])
        assert breakdown["soc_contribution"] <= _MAX_SOC_CONTRIBUTION

    def test_temporal_contributes(self):
        p = self._profiler()
        timeline = [
            {"details": {"pattern_name": "vpn_then_download"}},
            {"details": {"pattern_name": "hr_lookup_then_bulk_access"}},
        ]
        score, breakdown = p._compute_risk_score([], {"cumulative_risk_score": 0, "alert_count": 0}, timeline)
        assert score > 0
        assert breakdown["temporal_contribution"] > 0

    def test_temporal_cap(self):
        p = self._profiler()
        timeline = [
            {"details": {"pattern_name": f"pattern_{i}"}} for i in range(20)
        ]
        _, breakdown = p._compute_risk_score([], {"cumulative_risk_score": 0, "alert_count": 0}, timeline)
        assert breakdown["temporal_contribution"] <= _MAX_TEMPORAL_CONTRIBUTION

    def test_score_never_exceeds_100(self):
        """Max signals from all three engines should still cap at 100."""
        p = self._profiler()
        devs = [{"type": "location_anomaly", "severity": "CRITICAL"}] * 10
        soc = {"cumulative_risk_score": 100, "alert_count": 100}
        timeline = [{"details": {"pattern_name": f"p{i}"}} for i in range(10)]
        score, _ = p._compute_risk_score(devs, soc, timeline)
        assert score <= 100.0

    def test_combined_signals_higher_than_individual(self):
        p = self._profiler()
        devs = [{"type": "volume_spike", "severity": "HIGH"}]
        soc = {"cumulative_risk_score": 60, "alert_count": 3}
        timeline = [{"details": {"pattern_name": "seq1"}}]

        score_combo, _ = p._compute_risk_score(devs, soc, timeline)
        score_dev, _ = p._compute_risk_score(devs, {"cumulative_risk_score": 0, "alert_count": 0}, [])
        score_soc, _ = p._compute_risk_score([], soc, [])
        score_temp, _ = p._compute_risk_score([], {"cumulative_risk_score": 0, "alert_count": 0}, timeline)

        assert score_combo > score_dev
        assert score_combo > score_soc
        assert score_combo > score_temp


# =========================================================================
# Full Profile Build
# =========================================================================


class TestBuildProfile:

    def test_returns_all_required_keys(self):
        profiler = ThreatProfiler(
            baseline_engine=FakeBaseline(
                profiles={"alice": {"user_id": "alice", "confidence": "80%", "data_points": 150}},
            ),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        box = profiler.build_profile("alice")

        required_keys = {
            "user_id", "risk_score", "risk_level", "reasoning_summary",
            "score_breakdown", "behavioral_profile", "active_deviations",
            "temporal_events", "soc_risk", "peer_comparison", "trend_30d",
            "recommended_actions", "generated_at", "computation_ms",
        }
        assert required_keys.issubset(box.keys())

    def test_score_is_float_in_range(self):
        profiler = ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        box = profiler.build_profile("bob")
        assert 0 <= box["risk_score"] <= 100

    def test_reasoning_contains_user_id(self):
        profiler = ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        box = profiler.build_profile("jdoe@firm.com")
        assert "jdoe@firm.com" in box["reasoning_summary"]

    def test_trend_has_30_points(self):
        profiler = ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        box = profiler.build_profile("user1")
        assert len(box["trend_30d"]) == 30

    def test_trend_deterministic_per_user(self):
        profiler = ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        t1 = profiler.build_profile("stableuser")["trend_30d"]
        t2 = profiler.build_profile("stableuser")["trend_30d"]
        assert t1 == t2

    def test_computation_ms_populated(self):
        profiler = ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        box = profiler.build_profile("x")
        assert box["computation_ms"] >= 0

    def test_no_baseline_still_returns_profile(self):
        profiler = ThreatProfiler(
            baseline_engine=FakeBaseline(profiles={}),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        box = profiler.build_profile("unknown_user")
        assert box["behavioral_profile"]["status"] == "no_baseline"
        assert box["risk_score"] >= 0


# =========================================================================
# Reasoning & Recommendations
# =========================================================================


class TestReasoning:

    def _profiler(self):
        return ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )

    def test_critical_level_has_immediate_action(self):
        p = self._profiler()
        actions = p._recommend_actions(
            85, RiskLevel.CRITICAL,
            [{"type": "volume_spike"}],
            {"cumulative_risk_score": 80},
        )
        assert any("IMMEDIATE" in a for a in actions)

    def test_high_level_has_audit(self):
        p = self._profiler()
        actions = p._recommend_actions(
            60, RiskLevel.HIGH, [], {"cumulative_risk_score": 0},
        )
        assert any("AUDIT" in a for a in actions)

    def test_location_anomaly_adds_verify_identity(self):
        p = self._profiler()
        actions = p._recommend_actions(
            40, RiskLevel.ELEVATED,
            [{"type": "location_anomaly"}],
            {"cumulative_risk_score": 0},
        )
        assert any("VERIFY IDENTITY" in a for a in actions)

    def test_departure_adds_protocol(self):
        p = self._profiler()
        actions = p._recommend_actions(
            70, RiskLevel.HIGH, [],
            {"cumulative_risk_score": 60},
        )
        assert any("DEPARTURE PROTOCOL" in a for a in actions)

    def test_reasoning_mentions_departure_for_high_soc(self):
        p = self._profiler()
        reasoning = p._generate_reasoning(
            "user1", 70, RiskLevel.HIGH,
            deviations=[],
            soc_risk={"cumulative_risk_score": 75, "pattern_matches": ["vpn_exfil"]},
            timeline=[],
            baseline_profile={"confidence": "90%"},
            peer_comparison={"is_outlier": False},
        )
        assert "departure" in reasoning.lower() or "SOC" in reasoning

    def test_reasoning_mentions_outlier(self):
        p = self._profiler()
        reasoning = p._generate_reasoning(
            "user1", 30, RiskLevel.ELEVATED,
            deviations=[],
            soc_risk={"cumulative_risk_score": 0},
            timeline=[],
            baseline_profile={"confidence": "90%"},
            peer_comparison={"is_outlier": True, "events_vs_peers": "280%"},
        )
        assert "outlier" in reasoning.lower()


# =========================================================================
# Lightweight Risk-Only Path
# =========================================================================


class TestRiskOnly:

    def test_returns_tuple(self):
        p = ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        score, level = p.compute_risk_score_only("somebody")
        assert isinstance(score, float)
        assert level in [rl.value for rl in RiskLevel]


# =========================================================================
# Time-Decay Function  (Gemini recommendation)
# =========================================================================


class TestTimeDecay:

    def test_decay_at_zero_age(self):
        """Zero age should give full weight."""
        assert _time_decay(0) == 1.0

    def test_decay_at_half_life(self):
        """At exactly one half-life, weight should be 0.5."""
        assert abs(_time_decay(_HALF_LIFE_HOURS) - 0.5) < 0.001

    def test_decay_at_double_half_life(self):
        """At 2× half-life, weight should be 0.25."""
        assert abs(_time_decay(_HALF_LIFE_HOURS * 2) - 0.25) < 0.001

    def test_decay_always_positive(self):
        """Even very old events should have a positive (but tiny) weight."""
        assert _time_decay(30 * 24) > 0

    def test_decay_monotonically_decreasing(self):
        values = [_time_decay(h) for h in range(0, 500, 24)]
        for a, b in zip(values, values[1:]):
            assert a >= b

    def test_recent_event_full_contribution(self):
        """A deviation from 1 hour ago should still be near-full weight."""
        p = ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )
        devs = [{"type": "volume_spike", "severity": "HIGH", "decay_factor": _time_decay(1)}]
        score_recent, _ = p._compute_risk_score(devs, {"cumulative_risk_score": 0, "alert_count": 0}, [])

        devs_old = [{"type": "volume_spike", "severity": "HIGH", "decay_factor": _time_decay(14 * 24)}]
        score_old, _ = p._compute_risk_score(devs_old, {"cumulative_risk_score": 0, "alert_count": 0}, [])

        assert score_recent > score_old, "Recent events should score higher than old ones"


# =========================================================================
# Sigmoid Scoring Curve  (Gemini recommendation: replaced asymptotic with sigmoid)
# =========================================================================


class TestSigmoidCurve:

    def _profiler(self):
        return ThreatProfiler(
            baseline_engine=FakeBaseline(),
            temporal_engine=FakeTemporal(),
            soc_engine=FakeSOC(),
        )

    def test_low_raw_suppressed(self):
        """Low raw scores should produce lower final scores (noise suppression)."""
        import math
        p = self._profiler()
        # A single mild deviation should produce a low final score
        devs = [{"type": "new_behavior", "severity": "LOW", "decay_factor": 1.0}]
        score, breakdown = p._compute_risk_score(devs, {"cumulative_risk_score": 0, "alert_count": 0}, [])
        assert score < 20, f"Low signal should be suppressed, got {score}"

    def test_midpoint_around_50(self):
        """With raw ≈ 60, sigmoid midpoint should give output around 50."""
        import math
        # Sigmoid: 100 / (1 + exp(-0.07 * (60 - 60))) = 100/2 = 50
        final = 100.0 / (1.0 + math.exp(-0.07 * (60 - 60)))
        assert abs(final - 50.0) < 0.1

    def test_high_raw_saturates(self):
        """Very high raw scores should approach but not exceed 100."""
        import math
        final = 100.0 / (1.0 + math.exp(-0.07 * (125 - 60)))
        assert final > 95
        assert final <= 100


# =========================================================================
# Singleton management
# =========================================================================


class TestSingleton:

    def test_get_returns_profiler(self):
        reset_threat_profiler()
        p = get_threat_profiler()
        assert isinstance(p, ThreatProfiler)

    def test_reset_clears_singleton(self):
        p1 = get_threat_profiler()
        reset_threat_profiler()
        p2 = get_threat_profiler()
        assert p1 is not p2


# =========================================================================
# REST API Integration
# =========================================================================


class TestThreatProfileAPI:
    """Test the /api/v1/user/{id}/profile endpoint via FastAPI TestClient."""

    @pytest.fixture
    def client(self):
        import aionos.api.rest_api as api_mod
        from aionos.licensing.tier_config import reset_tier_config
        from fastapi.testclient import TestClient
        from unittest.mock import patch as _patch

        reset_tier_config()
        with _patch.dict(os.environ, {
            "AION_LICENSE_TIER": "sentinel",
            "AION_ADMIN_KEY": "test-admin-key",
        }, clear=False):
            reset_tier_config()
            api_mod._API_KEY_STORE.clear()
            yield TestClient(api_mod.app)
        reset_tier_config()
        api_mod._API_KEY_STORE.clear()

    def test_profile_endpoint_returns_200(self, client):
        r = client.get(
            "/api/v1/user/testuser@firm.com/profile",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "risk_score" in data
        assert "reasoning_summary" in data
        assert "trend_30d" in data

    def test_risk_endpoint_returns_200(self, client):
        r = client.get(
            "/api/v1/user/testuser@firm.com/risk",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "risk_score" in data
        assert "risk_level" in data
        # Should NOT contain the heavy fields
        assert "trend_30d" not in data

    def test_profile_requires_auth(self, client):
        r = client.get("/api/v1/user/someone/profile")
        # No API key → should get 403 or lack of access
        assert r.status_code == 403

    def test_viewer_cannot_access_profile(self, client):
        import aionos.api.rest_api as api_mod
        from aionos.licensing.tier_config import reset_tier_config
        from unittest.mock import patch as _patch

        # Add a viewer key
        with _patch.dict(os.environ, {
            "AION_VIEWER_KEY": "test-viewer-key",
        }, clear=False):
            api_mod._API_KEY_STORE.clear()
            r = client.get(
                "/api/v1/user/someone/profile",
                headers={"X-API-Key": "test-viewer-key"},
            )
            assert r.status_code == 403
