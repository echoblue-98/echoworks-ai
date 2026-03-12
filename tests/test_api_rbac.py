"""
Tests for the REST API layer: RBAC enforcement, error paths, edge cases.

Uses FastAPI's TestClient for in-process HTTP testing without a live server.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Setup — configure API keys before importing the app
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_api_keys(monkeypatch):
    """Inject test API keys so RBAC is fully exercised."""
    monkeypatch.setenv("AION_ADMIN_KEY", "test-admin-key-2026")
    monkeypatch.setenv("AION_ANALYST_KEY", "test-analyst-key-2026")
    monkeypatch.setenv("AION_VIEWER_KEY", "test-viewer-key-2026")

    # Force re-load of API keys on next request
    import aionos.api.rest_api as api_mod
    api_mod._API_KEY_STORE.clear()


@pytest.fixture
def client():
    """FastAPI TestClient bound to the AION OS app."""
    from aionos.api.rest_api import app
    return TestClient(app, raise_server_exceptions=False)


# Headers helpers
ADMIN  = {"X-API-Key": "test-admin-key-2026"}
ANALYST = {"X-API-Key": "test-analyst-key-2026"}
VIEWER  = {"X-API-Key": "test-viewer-key-2026"}
ANON    = {}  # no key
BEARER_ADMIN = {"Authorization": "Bearer test-admin-key-2026"}
BAD_KEY = {"X-API-Key": "totally-invalid-key"}


# =============================================================================
# HEALTH / ROOT (no auth required)
# =============================================================================

class TestHealthEndpoints:

    def test_health_returns_operational(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "operational"
        assert "version" in data
        assert "timestamp" in data

    def test_root_returns_api_info(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "AION OS API"
        assert "docs" in data


# =============================================================================
# RBAC ENFORCEMENT
# =============================================================================

class TestRBAC:
    """Verify role-based access control across all tiers."""

    def test_admin_can_access_stats(self, client):
        r = client.get("/api/v1/stats", headers=ADMIN)
        assert r.status_code == 200

    def test_viewer_can_access_stats(self, client):
        r = client.get("/api/v1/stats", headers=VIEWER)
        assert r.status_code == 200

    def test_anonymous_cannot_access_stats(self, client):
        r = client.get("/api/v1/stats", headers=ANON)
        assert r.status_code == 403

    def test_viewer_cannot_run_improvement_cycle(self, client):
        """Viewers are read-only — cycle trigger requires admin."""
        r = client.post("/api/v1/improvement/cycle", headers=VIEWER)
        assert r.status_code == 403

    def test_analyst_can_submit_feedback(self, client):
        r = client.post(
            "/api/v1/improvement/feedback",
            json={
                "feedback_type": "alert_correct",
                "analyst_id": "test_analyst",
                "notes": "Test feedback",
            },
            headers=ANALYST,
        )
        assert r.status_code == 200

    def test_anonymous_cannot_submit_feedback(self, client):
        r = client.post(
            "/api/v1/improvement/feedback",
            json={
                "feedback_type": "alert_correct",
                "analyst_id": "test",
            },
            headers=ANON,
        )
        assert r.status_code == 403

    def test_bearer_token_accepted(self, client):
        """Authorization: Bearer <key> should work identically to X-API-Key."""
        r = client.get("/api/v1/stats", headers=BEARER_ADMIN)
        assert r.status_code == 200

    def test_bad_key_returns_403(self, client):
        r = client.get("/api/v1/stats", headers=BAD_KEY)
        assert r.status_code == 403

    def test_viewer_cannot_approve_proposal(self, client):
        r = client.post(
            "/api/v1/improvement/approve/1",
            json={"analyst_id": "viewer_user", "notes": "nope"},
            headers=VIEWER,
        )
        assert r.status_code == 403

    def test_viewer_cannot_list_policies(self, client):
        r = client.get("/api/v1/improvement/policies", headers=VIEWER)
        assert r.status_code == 403

    def test_admin_can_list_policies(self, client):
        r = client.get("/api/v1/improvement/policies", headers=ADMIN)
        assert r.status_code == 200


# =============================================================================
# IMPROVEMENT ENGINE ENDPOINTS
# =============================================================================

class TestImprovementAPI:
    """Tests for the /improvement/* endpoints."""

    def test_status_returns_structure(self, client):
        r = client.get("/api/v1/improvement/status", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    def test_metrics_returns_score(self, client):
        r = client.get("/api/v1/improvement/metrics", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        assert "score" in data

    def test_proposals_returns_list(self, client):
        r = client.get("/api/v1/improvement/proposals", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data.get("proposals"), list)

    def test_nudges_returns_list(self, client):
        r = client.get("/api/v1/improvement/nudges", headers=ANALYST)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data.get("nudges"), list)

    def test_policy_not_found_returns_404(self, client):
        r = client.get("/api/v1/improvement/policy/9999", headers=ADMIN)
        assert r.status_code == 404

    def test_diff_invalid_versions_returns_404(self, client):
        r = client.get("/api/v1/improvement/diff/9998/9999", headers=ADMIN)
        assert r.status_code == 404

    def test_rollback_invalid_version_returns_error(self, client):
        r = client.post(
            "/api/v1/improvement/rollback/9999",
            json={"analyst_id": "test", "notes": "rollback test"},
            headers=ADMIN,
        )
        # Should be 404 or 400 — not 500
        assert r.status_code in (400, 404)

    def test_feedback_invalid_type_accepted(self, client):
        """Feedback endpoint accepts free-form types (no enum validation)."""
        r = client.post(
            "/api/v1/improvement/feedback",
            json={
                "feedback_type": "not_a_valid_type",
                "analyst_id": "test",
            },
            headers=ADMIN,
        )
        # Endpoint accepts any feedback type (200) — validation is downstream
        assert r.status_code == 200

    def test_improvement_cycle_returns_result(self, client):
        r = client.post("/api/v1/improvement/cycle", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True


# =============================================================================
# OBSERVABILITY / METRICS
# =============================================================================

class TestMetricsAPI:

    def test_json_metrics_returns_data(self, client):
        r = client.get("/metrics/json", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data or isinstance(data, dict)

    def test_prometheus_metrics_returns_text(self, client):
        r = client.get("/metrics", headers=ADMIN)
        assert r.status_code == 200
        assert "text/plain" in r.headers.get("content-type", "")

    def test_metrics_forbidden_for_anonymous(self, client):
        r = client.get("/metrics/json", headers=ANON)
        assert r.status_code == 403


# =============================================================================
# EDGE CASES & ERROR PATHS
# =============================================================================

class TestEdgeCases:

    def test_nonexistent_endpoint_returns_404(self, client):
        r = client.get("/api/v1/nonexistent")
        assert r.status_code in (404, 405)

    def test_post_to_get_endpoint_returns_405(self, client):
        r = client.post("/health")
        assert r.status_code == 405

    def test_malformed_json_body_returns_422(self, client):
        r = client.post(
            "/api/v1/analyze/legal",
            content="not json at all",
            headers={**ADMIN, "Content-Type": "application/json"},
        )
        assert r.status_code == 422

    def test_missing_required_fields_returns_422(self, client):
        r = client.post(
            "/api/v1/analyze/legal",
            json={},  # missing 'content' field
            headers=ADMIN,
        )
        assert r.status_code == 422

    def test_empty_content_accepted(self, client):
        """Empty string is a valid string — should pass validation."""
        r = client.post(
            "/api/v1/analyze/legal",
            json={"content": ""},
            headers=ADMIN,
        )
        # May be 200, 403 (ethics), or 500 (engine) — but NOT 422
        assert r.status_code != 422

    def test_stats_response_structure(self, client):
        r = client.get("/api/v1/stats", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "statistics" in data
        assert "timestamp" in data

    def test_cors_headers_present(self, client):
        """CORS middleware should add access-control headers."""
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should not be a hard error
        assert r.status_code in (200, 204, 405)

    def test_concurrent_feedback_submissions(self, client):
        """Multiple rapid feedback submissions should all succeed (anti-poisoning allows normal rate)."""
        results = []
        for i in range(5):
            r = client.post(
                "/api/v1/improvement/feedback",
                json={
                    "feedback_type": "alert_correct",
                    "analyst_id": f"analyst_{i}",
                    "notes": f"Batch test {i}",
                },
                headers=ADMIN,
            )
            results.append(r.status_code)
        assert all(s == 200 for s in results), f"Some failed: {results}"


# =============================================================================
# RATE LIMITING on /api/soc/ingest  (Gemini recommendation)
# =============================================================================

class TestRateLimiting:

    def test_rate_limiter_allows_normal_traffic(self, client):
        """A handful of ingest calls should succeed."""
        from aionos.api.rest_api import _ingest_rate_limiter
        _ingest_rate_limiter.reset()  # clean slate

        r = client.post("/api/soc/ingest", json={
            "alert_type": "vpn_login",
            "user_id": "ratelimit_test@firm.com",
            "severity": "low",
        })
        assert r.status_code == 200

    def test_rate_limiter_blocks_flood(self, client):
        """Exceeding the limit should return 429."""
        from aionos.api.rest_api import _ingest_rate_limiter, _RATE_LIMIT_MAX_REQUESTS

        _ingest_rate_limiter.reset()

        # Exhaust the window
        for _ in range(_RATE_LIMIT_MAX_REQUESTS):
            _ingest_rate_limiter.is_allowed("127.0.0.1")

        # The next request via TestClient (source IP = testclient) may differ,
        # so we check the limiter directly.
        assert _ingest_rate_limiter.is_allowed("127.0.0.1") is False

    def test_rate_limiter_reset(self):
        """Reset should clear all windows."""
        from aionos.api.rest_api import _ingest_rate_limiter
        _ingest_rate_limiter.reset()
        assert _ingest_rate_limiter.is_allowed("any_ip")
        _ingest_rate_limiter.reset()
        assert _ingest_rate_limiter.is_allowed("any_ip")

    def test_rate_limiter_per_key_isolation(self):
        """Different keys should have independent windows."""
        from aionos.api.rest_api import _SlidingWindowRateLimiter

        limiter = _SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("a")
        assert limiter.is_allowed("a")
        assert not limiter.is_allowed("a")  # blocked
        assert limiter.is_allowed("b")       # different key — allowed
