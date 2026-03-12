"""
Tests for the license tier feature gate system and the 9 immutable invariants.

Covers:
  - Tier configuration loading from env var
  - Pattern gating per tier
  - Endpoint gating per tier
  - API tier enforcement (403 on gated endpoints)
  - All 9 invariants: positive enforcement + violation detection
  - InvariantChecker.check_all() comprehensive coverage
"""

import os
import pytest
from unittest.mock import patch

from aionos.licensing.tier_config import (
    LicenseTier,
    TierConfig,
    get_tier_config,
    reset_tier_config,
    get_tier_patterns,
    TIER_ENGINE_LAYERS,
    TIER_ENDPOINT_GATES,
    TIER_FEATURES,
    BASELINE_PATTERN_IDS,
    LEGAL_SPECIFIC_PATTERN_IDS,
    ALL_PATTERN_IDS,
)
from aionos.safety.invariants import (
    InvariantChecker,
    InvariantViolation,
    IMMUTABLE_INVARIANTS,
    INVARIANT_BY_ID,
    INVARIANT_COUNT,
)


# =============================================================================
# TIER CONFIG TESTS
# =============================================================================

class TestTierConfig:

    def setup_method(self):
        reset_tier_config()

    def teardown_method(self):
        reset_tier_config()

    def test_exactly_three_tiers(self):
        assert len(LicenseTier) == 3
        assert set(LicenseTier) == {
            LicenseTier.BASELINE,
            LicenseTier.INTELLIGENCE,
            LicenseTier.SENTINEL,
        }

    def test_default_tier_is_sentinel(self):
        """Dev default should be full access (sentinel)."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AION_LICENSE_TIER", None)
            config = get_tier_config()
            assert config.tier == LicenseTier.SENTINEL

    def test_env_var_loads_baseline(self):
        with patch.dict(os.environ, {"AION_LICENSE_TIER": "baseline"}):
            config = get_tier_config()
            assert config.tier == LicenseTier.BASELINE

    def test_env_var_loads_intelligence(self):
        with patch.dict(os.environ, {"AION_LICENSE_TIER": "intelligence"}):
            config = get_tier_config()
            assert config.tier == LicenseTier.INTELLIGENCE

    def test_invalid_tier_defaults_sentinel(self):
        with patch.dict(os.environ, {"AION_LICENSE_TIER": "imaginary"}):
            config = get_tier_config()
            assert config.tier == LicenseTier.SENTINEL

    def test_tier_config_to_dict(self):
        config = TierConfig(tier=LicenseTier.BASELINE)
        d = config.to_dict()
        assert d["tier"] == "baseline"
        assert d["tier_name"] == "Core Baseline"
        assert isinstance(d["engines_enabled"], list)
        assert isinstance(d["endpoint_gates"], dict)


class TestTierPatterns:

    def test_baseline_has_40_patterns(self):
        assert len(BASELINE_PATTERN_IDS) == 40

    def test_legal_specific_has_29_patterns(self):
        assert len(LEGAL_SPECIFIC_PATTERN_IDS) == 29

    def test_total_is_69_patterns(self):
        assert len(ALL_PATTERN_IDS) == 69

    def test_no_overlap(self):
        overlap = BASELINE_PATTERN_IDS & LEGAL_SPECIFIC_PATTERN_IDS
        assert len(overlap) == 0, f"Overlapping patterns: {overlap}"

    def test_baseline_tier_gets_40(self):
        patterns = get_tier_patterns(LicenseTier.BASELINE)
        assert len(patterns) == 40

    def test_intelligence_tier_gets_all_69(self):
        patterns = get_tier_patterns(LicenseTier.INTELLIGENCE)
        assert len(patterns) == 69

    def test_sentinel_tier_gets_all_69(self):
        patterns = get_tier_patterns(LicenseTier.SENTINEL)
        assert len(patterns) == 69


class TestTierEngineGating:

    def test_baseline_has_temporal_and_baseline_engines(self):
        engines = TIER_ENGINE_LAYERS[LicenseTier.BASELINE]
        assert "temporal_engine" in engines
        assert "baseline_engine" in engines

    def test_baseline_lacks_hybrid(self):
        engines = TIER_ENGINE_LAYERS[LicenseTier.BASELINE]
        assert "hybrid_engine" not in engines

    def test_intelligence_has_hybrid(self):
        engines = TIER_ENGINE_LAYERS[LicenseTier.INTELLIGENCE]
        assert "hybrid_engine" in engines
        assert "attorney_departure" in engines
        assert "lateral_hire_gem" in engines
        assert "feedback_collector" in engines

    def test_intelligence_lacks_rsi(self):
        engines = TIER_ENGINE_LAYERS[LicenseTier.INTELLIGENCE]
        assert "improvement_engine" not in engines
        assert "adversarial_engine" not in engines

    def test_sentinel_has_everything(self):
        engines = TIER_ENGINE_LAYERS[LicenseTier.SENTINEL]
        assert "improvement_engine" in engines
        assert "adversarial_engine" in engines
        assert "quantum_adversarial" in engines
        assert "document_intelligence" in engines
        assert "shadow_runner" in engines

    def test_each_tier_is_superset_of_previous(self):
        baseline = TIER_ENGINE_LAYERS[LicenseTier.BASELINE]
        intel = TIER_ENGINE_LAYERS[LicenseTier.INTELLIGENCE]
        sentinel = TIER_ENGINE_LAYERS[LicenseTier.SENTINEL]
        assert baseline.issubset(intel)
        assert intel.issubset(sentinel)


class TestTierEndpointGating:

    def test_health_available_at_baseline(self):
        config = TierConfig(tier=LicenseTier.BASELINE)
        assert config.is_endpoint_allowed("health")
        assert config.is_endpoint_allowed("stats")
        assert config.is_endpoint_allowed("soc_status")

    def test_legal_analysis_requires_intelligence(self):
        baseline = TierConfig(tier=LicenseTier.BASELINE)
        intel = TierConfig(tier=LicenseTier.INTELLIGENCE)
        assert not baseline.is_endpoint_allowed("legal_analysis")
        assert intel.is_endpoint_allowed("legal_analysis")

    def test_improvement_cycle_requires_sentinel(self):
        baseline = TierConfig(tier=LicenseTier.BASELINE)
        intel = TierConfig(tier=LicenseTier.INTELLIGENCE)
        sentinel = TierConfig(tier=LicenseTier.SENTINEL)
        assert not baseline.is_endpoint_allowed("improvement_cycle")
        assert not intel.is_endpoint_allowed("improvement_cycle")
        assert sentinel.is_endpoint_allowed("improvement_cycle")

    def test_security_analysis_requires_sentinel(self):
        intel = TierConfig(tier=LicenseTier.INTELLIGENCE)
        sentinel = TierConfig(tier=LicenseTier.SENTINEL)
        assert not intel.is_endpoint_allowed("security_analysis")
        assert sentinel.is_endpoint_allowed("security_analysis")

    def test_ungated_endpoints_always_allowed(self):
        config = TierConfig(tier=LicenseTier.BASELINE)
        # Endpoints not in the gate map should be allowed
        assert config.is_endpoint_allowed("nonexistent_endpoint")


# =============================================================================
# API TIER ENFORCEMENT TESTS
# =============================================================================

class TestAPITierEnforcement:
    """Test that the REST API enforces tier gates via HTTP."""

    @pytest.fixture
    def baseline_client(self):
        """FastAPI test client with BASELINE tier."""
        import aionos.api.rest_api as api_mod
        from fastapi.testclient import TestClient
        reset_tier_config()
        with patch.dict(os.environ, {
            "AION_LICENSE_TIER": "baseline",
            "AION_ADMIN_KEY": "test-admin-key",
        }, clear=False):
            reset_tier_config()
            api_mod._API_KEY_STORE.clear()
            yield TestClient(api_mod.app)
        reset_tier_config()
        api_mod._API_KEY_STORE.clear()

    @pytest.fixture
    def sentinel_client(self):
        """FastAPI test client with SENTINEL tier (full access)."""
        import aionos.api.rest_api as api_mod
        from fastapi.testclient import TestClient
        reset_tier_config()
        with patch.dict(os.environ, {
            "AION_LICENSE_TIER": "sentinel",
            "AION_ADMIN_KEY": "test-admin-key",
        }, clear=False):
            reset_tier_config()
            api_mod._API_KEY_STORE.clear()
            yield TestClient(api_mod.app)
        reset_tier_config()
        api_mod._API_KEY_STORE.clear()

    def test_baseline_can_access_health(self, baseline_client):
        r = baseline_client.get("/health")
        assert r.status_code == 200

    def test_baseline_can_access_soc_status(self, baseline_client):
        r = baseline_client.get("/api/soc/status",
                                headers={"X-API-Key": "test-admin-key"})
        assert r.status_code == 200

    def test_baseline_blocked_from_legal_analysis(self, baseline_client):
        r = baseline_client.post(
            "/api/v1/analyze/legal",
            json={"content": "test brief", "intensity": 1},
            headers={"X-API-Key": "test-admin-key"},
        )
        assert r.status_code == 403
        assert "higher license tier" in r.json()["detail"]

    def test_baseline_blocked_from_improvement_cycle(self, baseline_client):
        r = baseline_client.post(
            "/api/v1/improvement/cycle",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert r.status_code == 403

    def test_sentinel_can_access_everything(self, sentinel_client):
        r = sentinel_client.get("/health")
        assert r.status_code == 200
        r = sentinel_client.get(
            "/api/v1/improvement/status",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert r.status_code == 200

    def test_license_endpoint_returns_tier_info(self, sentinel_client):
        r = sentinel_client.get(
            "/api/v1/license",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["tier"] == "sentinel"
        assert data["tier_name"] == "Enterprise Sentinel"
        assert "endpoint_gates" in data

    def test_invariants_endpoint(self, sentinel_client):
        r = sentinel_client.get(
            "/api/v1/invariants",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["invariant_count"] == 9
        assert len(data["invariants"]) == 9


# =============================================================================
# INVARIANT TESTS
# =============================================================================

class TestInvariantDefinitions:

    def test_exactly_9_invariants(self):
        assert INVARIANT_COUNT == 9

    def test_invariant_ids_are_I1_through_I9(self):
        ids = [inv.id for inv in IMMUTABLE_INVARIANTS]
        assert ids == [f"I{i}" for i in range(1, 10)]

    def test_all_invariants_have_all_fields(self):
        for inv in IMMUTABLE_INVARIANTS:
            assert inv.id
            assert inv.name
            assert inv.description
            assert inv.enforcement
            assert inv.severity == "critical"

    def test_invariant_lookup_by_id(self):
        assert INVARIANT_BY_ID["I1"].name == "Human-in-the-Loop"
        assert INVARIANT_BY_ID["I9"].name == "Data Sovereignty"

    def test_invariant_to_dict(self):
        d = INVARIANT_BY_ID["I3"].to_dict()
        assert d["id"] == "I3"
        assert d["name"] == "Coverage Floor"
        assert "75%" in d["description"]


class TestInvariantChecker:

    def test_clean_policy_passes(self):
        """A minimal valid policy should pass all checks."""
        policy = {
            "thresholds": {
                "min_stages_to_alert": 3,
                "event_ttl_days": 30,
                "volume_spike_multiplier": 2.0,
            },
        }
        violations = InvariantChecker.check_all(policy)
        assert violations == []

    # --- I1: Human-in-the-Loop ---

    def test_i1_auto_promote_without_analyst_blocked(self):
        violations = InvariantChecker.check_all(
            {}, context={"auto_promote": True}
        )
        assert any("[I1]" in v for v in violations)

    def test_i1_auto_promote_with_analyst_passes(self):
        violations = InvariantChecker.check_all(
            {}, context={"auto_promote": True, "analyst_id": "alice"}
        )
        assert not any("[I1]" in v for v in violations)

    # --- I2: Privilege Sanctity ---

    def test_i2_content_analysis_enabled_blocked(self):
        policy = {"content_analysis": {"enabled": True}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I2]" in v for v in violations)

    def test_i2_full_text_index_blocked(self):
        policy = {"content_analysis": {"index_full_text": True}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I2]" in v for v in violations)

    # --- I3: Coverage Floor ---

    def test_i3_coverage_below_75_percent_blocked(self):
        # 10 patterns, only 5 enabled = 50%
        weights = {f"p_{i}": {"enabled": i < 5} for i in range(10)}
        policy = {"pattern_weights": weights}
        violations = InvariantChecker.check_all(policy)
        assert any("[I3]" in v for v in violations)

    def test_i3_coverage_at_80_percent_passes(self):
        weights = {f"p_{i}": {"enabled": i < 8} for i in range(10)}
        policy = {"pattern_weights": weights}
        violations = InvariantChecker.check_all(policy)
        assert not any("[I3]" in v for v in violations)

    def test_i3_more_than_3_disabled_per_cycle_blocked(self):
        baseline_weights = {f"p_{i}": {"enabled": True} for i in range(20)}
        candidate_weights = {f"p_{i}": {"enabled": i >= 4} for i in range(20)}
        violations = InvariantChecker.check_all(
            {"pattern_weights": candidate_weights},
            baseline_policy={"pattern_weights": baseline_weights},
        )
        assert any("[I3]" in v and "disabled" in v for v in violations)

    # --- I4: Encryption Mandate ---

    def test_i4_non_aes_algorithm_blocked(self):
        policy = {"encryption": {"algorithm": "DES"}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I4]" in v for v in violations)

    def test_i4_encryption_disabled_blocked(self):
        policy = {"encryption": {"enabled": False}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I4]" in v for v in violations)

    def test_i4_aes256gcm_passes(self):
        policy = {"encryption": {"algorithm": "AES-256-GCM"}}
        violations = InvariantChecker.check_all(policy)
        assert not any("[I4]" in v for v in violations)

    # --- I5: Audit Continuity ---

    def test_i5_audit_disabled_blocked(self):
        policy = {"audit": {"enabled": False}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I5]" in v for v in violations)

    def test_i5_retention_below_7_days_blocked(self):
        policy = {"audit": {"retention_days": 3}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I5]" in v for v in violations)

    # --- I6: Threshold Bounds ---

    def test_i6_min_stages_below_2_blocked(self):
        policy = {"thresholds": {"min_stages_to_alert": 1}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I6]" in v for v in violations)

    def test_i6_event_ttl_below_7_blocked(self):
        policy = {"thresholds": {"event_ttl_days": 3}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I6]" in v for v in violations)

    def test_i6_valid_thresholds_pass(self):
        policy = {"thresholds": {"min_stages_to_alert": 3, "event_ttl_days": 90}}
        violations = InvariantChecker.check_all(policy)
        assert not any("[I6]" in v for v in violations)

    # --- I7: No Self-Modification ---

    def test_i7_exec_in_policy_blocked(self):
        policy = {"description": "exec('malicious code')"}
        violations = InvariantChecker.check_all(policy)
        assert any("[I7]" in v for v in violations)

    def test_i7_import_in_policy_blocked(self):
        policy = {"config": {"webhook": "import os"}}
        violations = InvariantChecker.check_all(policy)
        assert any("[I7]" in v for v in violations)

    def test_i7_normal_text_passes(self):
        policy = {"description": "Reduced MFA fatigue threshold from 5 to 3"}
        violations = InvariantChecker.check_all(policy)
        assert not any("[I7]" in v for v in violations)

    # --- I9: Data Sovereignty ---

    def test_i9_external_endpoints_blocked(self):
        policy = {"external_endpoints": ["https://evil.com/exfil"]}
        violations = InvariantChecker.check_all(policy)
        assert any("[I9]" in v for v in violations)

    def test_i9_no_external_endpoints_passes(self):
        policy = {"external_endpoints": []}
        violations = InvariantChecker.check_all(policy)
        assert not any("[I9]" in v for v in violations)

    # --- Combined ---

    def test_multiple_violations_reported(self):
        """A policy violating several invariants should report all of them."""
        policy = {
            "content_analysis": {"enabled": True},        # I2
            "encryption": {"enabled": False},              # I4
            "audit": {"enabled": False},                   # I5
            "external_endpoints": ["http://bad.com"],      # I9
        }
        violations = InvariantChecker.check_all(policy)
        violated_ids = {v.split("]")[0].replace("[", "") for v in violations}
        assert "I2" in violated_ids
        assert "I4" in violated_ids
        assert "I5" in violated_ids
        assert "I9" in violated_ids

    def test_get_all_invariants(self):
        invs = InvariantChecker.get_all_invariants()
        assert len(invs) == 9
        assert invs[0]["id"] == "I1"

    def test_get_status(self):
        status = InvariantChecker.get_status()
        assert status["invariant_count"] == 9
        assert status["status"] == "all_enforced"
        assert len(status["enforcement_points"]) >= 4
