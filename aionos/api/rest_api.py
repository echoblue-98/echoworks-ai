"""
REST API - HTTP interface for AION OS

Provides REST endpoints for adversarial intelligence analysis.
"""

import collections
import time as _time

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json as _json
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uvicorn
import os
import hashlib
import hmac

from aionos.modules.legal_analyzer import LegalAnalyzer
from aionos.modules.security_redteam import SecurityRedTeam
from aionos.modules.soc_ingestion import get_soc_engine, ingest_alert, get_soc_status, verify_webhook_signature
from aionos.modules.threat_profile import get_threat_profiler
from aionos.core.adversarial_engine import IntensityLevel, AgentPerspective
from aionos.safety.audit_logger import AuditLogger
from aionos.safety.ethics_layer import EthicsLayer
from aionos.safety.invariants import InvariantChecker, IMMUTABLE_INVARIANTS as SAFETY_INVARIANTS
from aionos.improvement import ImprovementEngine
from aionos.improvement.feedback_collector import AnalystFeedback
from aionos.observability.metrics_exporter import get_metrics_exporter, get_metrics_registry
from aionos.security.idp import get_idp_validator, validate_bearer_token
from aionos.licensing import get_tier_config, LicenseTier, TIER_FEATURES


# =============================================================================
# SLIDING-WINDOW RATE LIMITER
# =============================================================================
# Prevents DoS against /api/soc/ingest and other high-throughput endpoints.
# Uses an in-memory sliding window per source IP (no Redis required).

_RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("AION_RATE_LIMIT_MAX", "200"))  # per window
_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("AION_RATE_LIMIT_WINDOW", "60"))


class _SlidingWindowRateLimiter:
    """Per-key sliding-window rate limiter (in-process, thread-safe enough for uvicorn)."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: Dict[str, collections.deque] = {}

    def is_allowed(self, key: str) -> bool:
        now = _time.monotonic()
        window = self._windows.get(key)
        if window is None:
            window = collections.deque()
            self._windows[key] = window

        # Evict expired entries
        cutoff = now - self.window_seconds
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= self.max_requests:
            return False

        window.append(now)
        return True

    def reset(self):
        self._windows.clear()


_ingest_rate_limiter = _SlidingWindowRateLimiter(
    _RATE_LIMIT_MAX_REQUESTS, _RATE_LIMIT_WINDOW_SECONDS
)


# =============================================================================
# RBAC — Role-Based Access Control
# =============================================================================

class UserRole(str, Enum):
    """API user roles with granular access tiers."""
    ADMIN = "admin"          # Full access: policies, attorney data, audit logs
    ANALYST = "analyst"      # SOC workflows: ingest, feedback, view alerts
    VIEWER = "viewer"        # Read-only: status, metrics, health
    ANONYMOUS = "anonymous"  # Unauthenticated: health + docs only


# Role → permitted endpoint prefixes / actions
ROLE_PERMISSIONS: Dict[str, set] = {
    UserRole.ADMIN: {
        "health", "legal_analysis", "security_analysis", "audit_logs",
        "stats", "soc_status", "soc_ingest", "soc_user_risk", "threat_profile",
        "improvement_status", "improvement_feedback", "improvement_metrics",
        "improvement_cycle", "improvement_proposals", "improvement_policies",
        "improvement_policy", "improvement_diff", "improvement_approve",
        "improvement_reject", "improvement_rollback", "improvement_nudges",
        "reason",
        "root",
    },
    UserRole.ANALYST: {
        "health", "legal_analysis", "security_analysis", "stats",
        "soc_status", "soc_ingest", "soc_user_risk", "threat_profile",
        "improvement_status", "improvement_feedback", "improvement_metrics",
        "improvement_proposals", "improvement_nudges",
        "reason",
        "root",
    },
    UserRole.VIEWER: {
        "health", "stats", "soc_status",
        "improvement_status", "improvement_metrics",
        "reason",
        "root",
    },
    UserRole.ANONYMOUS: {
        "health", "root",
    },
}

# API key → (user_id, role) mapping
# In production: backed by IdP (Okta/Azure AD) or encrypted key store
_API_KEY_STORE: Dict[str, Dict[str, str]] = {}


def _load_api_keys():
    """Load API keys from environment or config."""
    # Admin key
    admin_key = os.environ.get("AION_ADMIN_KEY")
    if admin_key:
        _API_KEY_STORE[admin_key] = {"user_id": "admin", "role": UserRole.ADMIN}

    # Analyst key
    analyst_key = os.environ.get("AION_ANALYST_KEY")
    if analyst_key:
        _API_KEY_STORE[analyst_key] = {"user_id": "analyst", "role": UserRole.ANALYST}

    # Viewer key
    viewer_key = os.environ.get("AION_VIEWER_KEY")
    if viewer_key:
        _API_KEY_STORE[viewer_key] = {"user_id": "viewer", "role": UserRole.VIEWER}


def resolve_role(api_key: Optional[str]) -> tuple:
    """Resolve an API key or IdP bearer token to (user_id, role). Returns anonymous if unrecognized."""
    if not _API_KEY_STORE:
        _load_api_keys()

    # Path 1: API key auth
    if api_key and api_key in _API_KEY_STORE:
        entry = _API_KEY_STORE[api_key]
        return entry["user_id"], UserRole(entry["role"])

    # Path 2: IdP bearer token (Okta / Azure AD / OIDC)
    if api_key:
        idp_context = validate_bearer_token(api_key)
        if idp_context:
            role_str = idp_context.get("role", "viewer")
            try:
                role = UserRole(role_str)
            except ValueError:
                role = UserRole.VIEWER
            return idp_context.get("user_id", "idp_user"), role

    # No keys configured = demo mode (admin access)
    if not _API_KEY_STORE:
        return "demo_user", UserRole.ADMIN

    return "anonymous", UserRole.ANONYMOUS


def require_role(action: str):
    """
    FastAPI dependency that enforces RBAC.

    Usage:
        @app.get("/endpoint")
        async def handler(auth=Depends(require_role("soc_status"))):
            user_id, role = auth
    """
    async def _check(
        x_api_key: Optional[str] = Header(None),
        authorization: Optional[str] = Header(None),
    ):
        # Accept key from X-API-Key header or Authorization: Bearer <key>
        key = x_api_key
        if not key and authorization and authorization.startswith("Bearer "):
            key = authorization[7:]

        user_id, role = resolve_role(key)

        if action not in ROLE_PERMISSIONS.get(role, set()):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role.value}' lacks permission for '{action}'. "
                       f"Required: admin or analyst key."
            )

        # Tier-based feature gate
        tier_config = get_tier_config()
        if not tier_config.is_endpoint_allowed(action):
            tier_name = tier_config.features["name"]
            raise HTTPException(
                status_code=403,
                detail=f"Endpoint '{action}' requires a higher license tier. "
                       f"Current: {tier_name} ({tier_config.tier.value}). "
                       f"Contact sales to upgrade."
            )

        return user_id, role

    return _check


# Initialize FastAPI app
app = FastAPI(
    title="AION OS API",
    description="Adversarial Intelligence Operating System - REST API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware — restrict origins in production via AION_CORS_ORIGINS
_cors_origins = os.environ.get("AION_CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
audit_logger = AuditLogger()
ethics_layer = EthicsLayer()


@app.on_event("startup")
async def prewarm_local_model() -> None:
    """
    Pre-warm the local LLM into VRAM on API startup so the first demo call
    has zero model-load latency. Combined with keep_alive=-1 on /reason calls,
    qwen stays resident until the API process is restarted.

    Fails silently if Ollama isn't reachable (sovereign-mode dev without LLM).
    """
    import httpx
    from aionos.core.reasoning_engine import _check_ollama

    if os.environ.get("AION_SKIP_PREWARM", "").lower() in ("1", "true", "yes"):
        return
    if not _check_ollama():
        return

    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            await client.post(
                ollama_url,
                json={
                    "model": ollama_model,
                    "prompt": "ok",
                    "stream": False,
                    "keep_alive": "-1",
                    "options": {"num_predict": 1},
                },
            )
    except Exception:
        # Best-effort — don't block startup if prewarm fails
        pass

# Initialize Improvement Engine (lazy — full init on first use)
_improvement_engine = None

def get_improvement_engine() -> ImprovementEngine:
    """Lazy-init the Improvement Engine singleton."""
    global _improvement_engine
    if _improvement_engine is None:
        provider = os.environ.get("AION_LLM_PROVIDER", "mock")
        _improvement_engine = ImprovementEngine(llm_provider=provider)
        _improvement_engine.initialize()
    return _improvement_engine


# Pydantic models for requests/responses
class AnalysisRequest(BaseModel):
    content: str = Field(..., description="Content to analyze")
    context: Optional[dict] = Field(default={}, description="Additional context")
    intensity: int = Field(default=3, ge=1, le=5, description="Adversarial intensity (1-5)")
    user_id: Optional[str] = Field(default="api_user", description="User identifier")


class LegalAnalysisRequest(AnalysisRequest):
    analysis_type: str = Field(default="brief", description="Type: brief, contract, argument")


class SecurityAnalysisRequest(AnalysisRequest):
    scan_type: str = Field(default="infrastructure", description="Type: infrastructure, posture, attack_chain")


class AnalysisResponse(BaseModel):
    success: bool
    analysis_id: str
    timestamp: str
    summary: dict
    critical_vulnerabilities: List[dict]
    formatted_output: str
    perspectives_used: List[str]
    intensity_level: int
    blocked: bool = False
    block_reason: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# Health check endpoint (no auth required)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health status"""
    return {
        "status": "operational",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# License / tier info endpoint
@app.get("/api/v1/license")
async def get_license_info(auth: tuple = Depends(require_role("stats"))):
    """
    Get current license tier and feature gates.

    Shows which engines, patterns, and endpoints are active
    for this deployment's tier.
    """
    tier_config = get_tier_config()
    return {
        "success": True,
        **tier_config.to_dict(),
        "features": tier_config.features,
    }


# Sovereign inference endpoint — proves local LLM, no frontier-lab egress
class ReasonRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    max_tokens: Optional[int] = Field(default=256, ge=1, le=4096)
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=2.0)


@app.post("/api/v1/reason")
async def sovereign_reason(
    request: ReasonRequest,
    auth: tuple = Depends(require_role("reason")),
):
    """
    Single-turn local inference proof.

    Calls the locally-running LLM (Ollama or LM Studio) with the supplied prompt.
    Returns model output plus provider, latency, and tokens/sec for demo verification.
    No frontier-lab egress — fails closed if no local provider is reachable.
    """
    import httpx
    from aionos.core.reasoning_engine import _check_ollama, _check_lmstudio

    started = _time.monotonic()
    provider = None
    model = None
    response_text = ""
    tokens = 0

    # Prefer LM Studio (OpenAI-compatible) if running
    if _check_lmstudio():
        lmstudio_url = os.environ.get(
            "LMSTUDIO_URL", "http://localhost:1234/v1/chat/completions"
        )
        try:
            resp = httpx.post(
                lmstudio_url,
                json={
                    "messages": [{"role": "user", "content": request.prompt}],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                },
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                response_text = data["choices"][0]["message"]["content"]
                usage = data.get("usage") or {}
                tokens = usage.get("completion_tokens", 0)
                model = data.get("model", "lmstudio-model")
                provider = "lmstudio"
        except Exception:
            pass

    # Fallback to Ollama
    if provider is None and _check_ollama():
        ollama_url = os.environ.get(
            "OLLAMA_URL", "http://localhost:11434/api/generate"
        )
        ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
        try:
            resp = httpx.post(
                ollama_url,
                json={
                    "model": ollama_model,
                    "prompt": request.prompt,
                    "stream": False,
                    "keep_alive": "-1",  # pin model in VRAM — eliminates cold-start on subsequent calls
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens,
                    },
                },
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                response_text = data.get("response", "")
                tokens = data.get("eval_count", 0)
                model = data.get("model", ollama_model)
                provider = "ollama"
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Ollama unreachable: {exc}")

    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="No local LLM provider reachable (Ollama on :11434 or LM Studio on :1234).",
        )

    latency_ms = int((_time.monotonic() - started) * 1000)
    tokens_per_sec = round(tokens / (latency_ms / 1000), 2) if latency_ms > 0 and tokens else 0.0

    return {
        "success": True,
        "provider": provider,
        "model": model,
        "response": response_text,
        "tokens": tokens,
        "latency_ms": latency_ms,
        "tokens_per_sec": tokens_per_sec,
        "sovereign": True,
        "frontier_lab_egress": False,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Sovereign inference STREAMING endpoint — same proof, dramatically better perceived latency.
# Emits NDJSON: one JSON object per line. Each chunk is either {"token": "..."} or a final
# {"done": true, ...metadata}. Browser reads via fetch + ReadableStream and renders tokens live.
# Ollama-only for now (M7's production provider). LM Studio path stays on the non-streaming endpoint.
@app.post("/api/v1/reason/stream")
async def sovereign_reason_stream(
    request: ReasonRequest,
    auth: tuple = Depends(require_role("reason")),
):
    """
    Streaming local inference proof.

    Returns NDJSON chunks as the local model generates tokens. Final line contains
    full metadata (provider, model, latency, tokens, tokens_per_sec, sovereign flag).
    No frontier-lab egress — fails closed if Ollama is unreachable.
    """
    import httpx
    from aionos.core.reasoning_engine import _check_ollama

    if not _check_ollama():
        raise HTTPException(
            status_code=503,
            detail="Ollama unreachable on :11434 — streaming endpoint requires Ollama.",
        )

    ollama_url = os.environ.get(
        "OLLAMA_URL", "http://localhost:11434/api/generate"
    )
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

    async def event_stream():
        started = _time.monotonic()
        tokens = 0
        accumulated = []
        model_name = ollama_model

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    ollama_url,
                    json={
                        "model": ollama_model,
                        "prompt": request.prompt,
                        "stream": True,
                        "keep_alive": "-1",  # pin model in VRAM — eliminates cold-start on subsequent calls
                        "options": {
                            "temperature": request.temperature,
                            "num_predict": request.max_tokens,
                        },
                    },
                ) as resp:
                    if resp.status_code != 200:
                        yield _json.dumps({
                            "error": f"Ollama returned status {resp.status_code}",
                            "done": True,
                        }) + "\n"
                        return

                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = _json.loads(line)
                        except _json.JSONDecodeError:
                            continue

                        piece = chunk.get("response", "")
                        if piece:
                            accumulated.append(piece)
                            yield _json.dumps({"token": piece, "done": False}) + "\n"

                        if chunk.get("done"):
                            tokens = chunk.get("eval_count", 0)
                            model_name = chunk.get("model", ollama_model)
                            break
        except Exception as exc:
            yield _json.dumps({
                "error": f"Stream interrupted: {exc}",
                "done": True,
            }) + "\n"
            return

        latency_ms = int((_time.monotonic() - started) * 1000)
        tokens_per_sec = (
            round(tokens / (latency_ms / 1000), 2) if latency_ms > 0 and tokens else 0.0
        )

        yield _json.dumps({
            "done": True,
            "success": True,
            "provider": "ollama",
            "model": model_name,
            "response": "".join(accumulated),
            "tokens": tokens,
            "latency_ms": latency_ms,
            "tokens_per_sec": tokens_per_sec,
            "sovereign": True,
            "frontier_lab_egress": False,
            "timestamp": datetime.utcnow().isoformat(),
        }) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Sovereign": "true",
            "X-Frontier-Lab-Egress": "false",
        },
    )


# Invariants endpoint — show the 9 immutable safety rules
@app.get("/api/v1/invariants")
async def get_invariants(auth: tuple = Depends(require_role("stats"))):
    """
    List the 9 immutable safety invariants.

    These are the constitutional constraints that the RSI engine
    can never violate, even with admin approval.
    """
    return {
        "success": True,
        **InvariantChecker.get_status(),
    }


# Legal analysis endpoint
@app.post("/api/v1/analyze/legal", response_model=AnalysisResponse)
async def analyze_legal(
    request: LegalAnalysisRequest,
    auth: tuple = Depends(require_role("legal_analysis")),
    use_gemini: bool = False,
    gemini_api_key: Optional[str] = None
):
    """
    Analyze legal document for weaknesses.
    
    Simulates opposing counsel to find vulnerabilities.
    """
    try:
        # Ethics check
        ethics_check = ethics_layer.check_query(
            query=request.content,
            context=request.context
        )
        
        if not ethics_check["allowed"]:
            audit_logger.log_ethical_violation(
                user_id=request.user_id,
                query=request.content,
                violation_type=ethics_check["violation"]["violation_type"],
                violation_message=ethics_check["message"],
                context=request.context
            )
            raise HTTPException(status_code=403, detail=ethics_check["message"])
        
        # Log query
        query_id = audit_logger.log_query(
            user_id=request.user_id,
            query=f"Legal analysis via API: {request.analysis_type}",
            context=request.context
        )
        
        # Run analysis
        analyzer = LegalAnalyzer(
            intensity=IntensityLevel(request.intensity),
            use_gemini=use_gemini,
            gemini_api_key=gemini_api_key
        )
        result = analyzer.analyze_brief(request.content, case_context=request.context)
        
        # Log analysis
        summary = result.get("summary", {})
        audit_logger.log_analysis(
            query_id=query_id,
            user_id=request.user_id,
            analysis_type="legal",
            perspectives_used=result.get("perspectives_used", []),
            vulnerabilities_found=summary.get("above_confidence_threshold", 0),
            critical_count=summary.get("critical_p0", 0) + summary.get("high_p1", 0),
            blocked=False
        )
        
        return {
            "success": True,
            "analysis_id": query_id,
            "timestamp": datetime.utcnow().isoformat(),
            **result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        audit_logger.log_system_event(
            event_type="api_error",
            message=str(e),
            severity="ERROR"
        )
        raise HTTPException(status_code=500, detail=str(e))


# Security analysis endpoint
@app.post("/api/v1/analyze/security", response_model=AnalysisResponse)
async def analyze_security(
    request: SecurityAnalysisRequest,
    auth: tuple = Depends(require_role("security_analysis")),
    use_gemini: bool = False,
    gemini_api_key: Optional[str] = None
):
    """
    Red team security infrastructure.
    
    Assumes breach mentality to find vulnerabilities.
    """
    try:
        # Ethics check
        ethics_check = ethics_layer.check_query(
            query=request.content,
            context={**request.context, "authorized_pen_test": True}
        )
        
        if not ethics_check["allowed"]:
            audit_logger.log_ethical_violation(
                user_id=request.user_id,
                query=request.content,
                violation_type=ethics_check["violation"]["violation_type"],
                violation_message=ethics_check["message"],
                context=request.context
            )
            raise HTTPException(status_code=403, detail=ethics_check["message"])
        
        # Log query
        query_id = audit_logger.log_query(
            user_id=request.user_id,
            query=f"Security analysis via API: {request.scan_type}",
            context=request.context
        )
        
        # Run analysis
        red_team = SecurityRedTeam(
            intensity=IntensityLevel(request.intensity),
            use_gemini=use_gemini,
            gemini_api_key=gemini_api_key
        )
        result = red_team.scan_infrastructure(request.content, context=request.context)
        
        # Log analysis
        summary = result.get("summary", {})
        audit_logger.log_analysis(
            query_id=query_id,
            user_id=request.user_id,
            analysis_type="security",
            perspectives_used=result.get("perspectives_used", []),
            vulnerabilities_found=summary.get("above_confidence_threshold", 0),
            critical_count=summary.get("critical_p0", 0) + summary.get("high_p1", 0),
            blocked=False
        )
        
        return {
            "success": True,
            "analysis_id": query_id,
            "timestamp": datetime.utcnow().isoformat(),
            **result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        audit_logger.log_system_event(
            event_type="api_error",
            message=str(e),
            severity="ERROR"
        )
        raise HTTPException(status_code=500, detail=str(e))


# Audit logs endpoint
@app.get("/api/v1/audit/logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    auth: tuple = Depends(require_role("audit_logs")),
):
    """Query audit logs"""
    logs = audit_logger.query_logs(
        user_id=user_id,
        event_type=event_type,
        limit=limit
    )
    
    return {
        "success": True,
        "count": len(logs),
        "logs": logs
    }


# Statistics endpoint
@app.get("/api/v1/stats")
async def get_statistics(auth: tuple = Depends(require_role("stats"))):
    """Get AION OS usage statistics"""
    stats = audit_logger.get_statistics()
    
    return {
        "success": True,
        "timestamp": datetime.utcnow().isoformat(),
        "statistics": stats
    }


# ============================================================================
# SOC (Security Operations Center) Endpoints
# ============================================================================

class SOCAlertRequest(BaseModel):
    """Incoming SOC alert"""
    id: Optional[str] = None
    timestamp: Optional[str] = None
    alert_type: str = Field(..., description="Type: vpn_anomaly, database_access, file_exfiltration, etc.")
    severity: str = Field(default="medium", description="low, medium, high, critical")
    user_id: str = Field(..., description="User identifier")
    user_email: Optional[str] = None
    source_ip: Optional[str] = None
    source_location: Optional[str] = None
    destination: Optional[str] = None
    action: str = Field(default="unknown", description="Action taken")
    details: Dict[str, Any] = Field(default={})


class SOCStatusResponse(BaseModel):
    """SOC status response"""
    status: str
    total_alerts: int
    high_risk_users: List[Dict]
    recent_alerts: List[Dict]
    pattern_detections: int


async def verify_internal_key(x_internal_key: Optional[str] = Header(None)):
    """Verify internal API key for SOC endpoints"""
    expected = os.environ.get("AION_INTERNAL_KEY")
    if expected and x_internal_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal key")
    return x_internal_key


@app.get("/api/soc/status", response_model=SOCStatusResponse)
async def soc_status(internal_key: str = Depends(verify_internal_key)):
    """
    Get SOC ingestion status.
    
    Returns: Alert counts, high-risk users, pattern detections.
    """
    return get_soc_status()


@app.post("/api/soc/ingest")
async def soc_ingest(
    request: Request,
    alert: Optional[SOCAlertRequest] = None,
    source: str = "generic",
    x_siem_signature: Optional[str] = Header(None)
):
    """
    Ingest security alert from SIEM.
    
    Accepts alerts from Splunk, Microsoft Sentinel, or generic JSON.
    Correlates with departure risk patterns for real-time detection.
    
    This is what would have caught the Typhoon VPN database theft.
    """
    # ---- Rate limiting (sliding window per client IP) --------------------
    client_ip = request.client.host if request.client else "unknown"
    if not _ingest_rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit exceeded: max {_RATE_LIMIT_MAX_REQUESTS} "
                f"requests per {_RATE_LIMIT_WINDOW_SECONDS}s. "
                "Retry after the window expires."
            ),
        )

    # Verify webhook signature if configured
    siem_secret = os.environ.get("SIEM_SECRET")
    if siem_secret and x_siem_signature:
        body = await request.body()
        if not verify_webhook_signature(body, x_siem_signature, siem_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Get alert data
    if alert:
        alert_data = alert.dict()
    else:
        alert_data = await request.json()
    
    # Ingest and analyze
    result = ingest_alert(alert_data, source)
    
    response = {
        "success": True,
        "alert_id": result.id,
        "departure_risk_score": result.departure_risk_score,
        "pattern_matches": result.pattern_matches,
        "severity": result.severity,
        "user_id": result.user_id
    }
    
    # Add warning if high risk
    if result.departure_risk_score > 50:
        response["warning"] = "HIGH DEPARTURE RISK - Recommend immediate audit"
    
    if result.pattern_matches:
        response["pattern_alert"] = f"Matches departure patterns: {', '.join(result.pattern_matches)}"
    
    # Include Security Attacker analysis if triggered
    if result.agent_analysis:
        response["agent_analysis"] = result.agent_analysis
        response["escalated"] = True
    
    return response


@app.get("/api/soc/user/{user_id}")
async def soc_user_risk(
    user_id: str,
    internal_key: str = Depends(verify_internal_key)
):
    """
    Get risk profile for specific user.
    
    Returns: Cumulative risk score, alert history, recommendations.
    """
    engine = get_soc_engine()
    return engine.get_user_risk(user_id)


# ============================================================================
# Threat Intelligence Profile — per-attorney "box"
# ============================================================================

@app.get("/api/v1/user/{user_id}/profile")
async def user_threat_profile(
    user_id: str,
    auth: tuple = Depends(require_role("threat_profile")),
):
    """
    Unified Threat Intelligence Box for a single attorney/employee.

    Merges behavioral baseline, temporal correlation, and SOC data
    into one composite risk score (0-100) with natural-language
    reasoning, 30-day trend, and recommended actions.
    """
    profiler = get_threat_profiler()
    return profiler.build_profile(user_id)


@app.get("/api/v1/user/{user_id}/risk")
async def user_risk_score(
    user_id: str,
    auth: tuple = Depends(require_role("threat_profile")),
):
    """
    Lightweight risk-only endpoint for list / dashboard views.

    Returns just the composite score and level — no full profile.
    """
    profiler = get_threat_profiler()
    score, level = profiler.compute_risk_score_only(user_id)
    return {
        "user_id": user_id,
        "risk_score": round(score, 1),
        "risk_level": level,
    }


# ============================================================================
# Improvement Engine Endpoints (Recursive Self-Improvement)
# ============================================================================

class FeedbackRequest(BaseModel):
    """Analyst feedback on an alert."""
    alert_id: Optional[str] = None
    feedback_type: str = Field(..., description="alert_correct, alert_noisy, alert_missed, mis_categorized, near_miss, duplicate")
    analyst_id: str = Field(..., description="Analyst identifier")
    corrected_severity: Optional[str] = None
    corrected_category: Optional[str] = None
    notes: str = ""
    triage_start: Optional[str] = None
    triage_end: Optional[str] = None


class ProposalActionRequest(BaseModel):
    """Approve or reject a policy proposal."""
    analyst_id: str = Field(..., description="Analyst identifier")
    notes: str = ""


@app.get("/api/v1/improvement/status")
async def improvement_status(auth: tuple = Depends(require_role("improvement_status"))):
    """
    Get Improvement Engine status.

    Returns: active policy, metrics, feedback stats, pending proposals.
    """
    engine = get_improvement_engine()
    return {"success": True, **engine.get_status()}


@app.post("/api/v1/improvement/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    auth: tuple = Depends(require_role("improvement_feedback")),
):
    """
    Submit analyst feedback on an alert.

    This drives the improvement loop — corrections are used to
    compute metrics and generate better detection policies.
    """
    engine = get_improvement_engine()
    feedback = AnalystFeedback(
        feedback_type=request.feedback_type,
        analyst_id=request.analyst_id,
        alert_id=request.alert_id,
        corrected_severity=request.corrected_severity,
        corrected_category=request.corrected_category,
        notes=request.notes,
        triage_start=request.triage_start,
        triage_end=request.triage_end,
    )
    result = engine.record_feedback(feedback)
    return {"success": True, "feedback_id": result.id}


@app.get("/api/v1/improvement/metrics")
async def improvement_metrics(
    window_days: int = 30,
    auth: tuple = Depends(require_role("improvement_metrics")),
):
    """
    Get detection quality metrics.

    Returns: precision, recall, F1, noise ratio, composite score.
    """
    engine = get_improvement_engine()
    metrics = engine.evaluation.compute_metrics(window_days=window_days)
    return {"success": True, "metrics": metrics.to_dict(), "score": metrics.score()}


@app.post("/api/v1/improvement/cycle")
async def run_improvement_cycle(auth: tuple = Depends(require_role("improvement_cycle"))):
    """
    Trigger one improvement cycle.

    Generates candidate changes, evaluates them, and surfaces
    proposals for human review. Does NOT auto-deploy.
    """
    engine = get_improvement_engine()
    result = engine.run_improvement_cycle()
    return {"success": True, **result}


@app.get("/api/v1/improvement/proposals")
async def get_proposals(auth: tuple = Depends(require_role("improvement_proposals"))):
    """Get pending policy proposals awaiting human review."""
    engine = get_improvement_engine()
    proposals = engine.get_pending_proposals()
    return {"success": True, "proposals": proposals}


@app.get("/api/v1/improvement/policies")
async def list_policies(auth: tuple = Depends(require_role("improvement_policies"))):
    """List all policy versions with metadata."""
    engine = get_improvement_engine()
    versions = engine.policy_store.list_versions()
    return {"success": True, "versions": versions}


@app.get("/api/v1/improvement/policy/{version}")
async def get_policy(version: int, auth: tuple = Depends(require_role("improvement_policy"))):
    """Get a specific policy version with full config."""
    engine = get_improvement_engine()
    policy = engine.policy_store.get_version(version)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy v{version} not found")
    return {"success": True, "policy": policy.to_dict()}


@app.get("/api/v1/improvement/diff/{from_version}/{to_version}")
async def policy_diff(
    from_version: int,
    to_version: int,
    auth: tuple = Depends(require_role("improvement_diff")),
):
    """
    Diff between two policy versions.

    Shows exactly what changed: "v17 → v18 changed MFA fatigue
    threshold from 3 to 5, and rewrote the BEC narrative prompt."
    """
    engine = get_improvement_engine()
    try:
        diff = engine.policy_store.diff(from_version, to_version)
        return {"success": True, "diff": diff.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/improvement/approve/{version}")
async def approve_proposal(
    version: int,
    request: ProposalActionRequest,
    auth: tuple = Depends(require_role("improvement_approve")),
):
    """
    Approve a proposed policy change and activate it.

    Human-in-the-loop: analyst reviews before/after stats and approves.
    """
    engine = get_improvement_engine()
    try:
        result = engine.approve_proposal(version, request.analyst_id, request.notes)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/improvement/reject/{version}")
async def reject_proposal(
    version: int,
    request: ProposalActionRequest,
    auth: tuple = Depends(require_role("improvement_reject")),
):
    """Reject a proposed policy change."""
    engine = get_improvement_engine()
    result = engine.reject_proposal(version, request.analyst_id, request.notes)
    return {"success": True, **result}


@app.post("/api/v1/improvement/rollback/{version}")
async def rollback_policy(
    version: int,
    request: ProposalActionRequest,
    auth: tuple = Depends(require_role("improvement_rollback")),
):
    """Roll back to a previous policy version."""
    engine = get_improvement_engine()
    try:
        result = engine.rollback_to(version, request.analyst_id, request.notes)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/improvement/nudges")
async def get_nudges(auth: tuple = Depends(require_role("improvement_nudges"))):
    """
    Get active improvement nudges.

    These are surfaced in the UI: "The system believes reducing noise
    on 'Departing Attorney' alerts is possible; review proposed rule changes?"
    """
    engine = get_improvement_engine()
    nudges = engine.feedback.get_active_nudges()
    return {"success": True, "nudges": [n.to_dict() for n in nudges]}


# =============================================================================
# OBSERVABILITY — Prometheus Metrics
# =============================================================================

@app.get("/metrics", tags=["observability"])
async def prometheus_metrics(auth=Depends(require_role("stats"))):
    """
    Prometheus-compatible metrics endpoint.

    Returns metrics in Prometheus text exposition format.
    Scrape this from your Prometheus/Grafana/Datadog stack.
    """
    from fastapi.responses import PlainTextResponse
    exporter = get_metrics_exporter()
    return PlainTextResponse(
        content=exporter.to_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/metrics/json", tags=["observability"])
async def json_metrics(auth=Depends(require_role("stats"))):
    """Metrics in JSON format for custom dashboards."""
    exporter = get_metrics_exporter()
    return exporter.to_json()


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "AION OS API",
        "version": "0.1.0",
        "description": "Adversarial Intelligence Operating System",
        "tagline": "The AI that prepares you for the fight",
        "docs": "/docs",
        "health": "/health"
    }


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
