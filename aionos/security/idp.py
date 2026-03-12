"""
AION OS - Identity Provider (IdP) Integration
===============================================

Gemini Finding: "No IdP integration — production law firm deployments
require SSO via Okta, Azure AD, or equivalent."

Provides JWT-based authentication middleware that validates tokens
from enterprise identity providers. Integrates with existing RBAC
in rest_api.py as an alternative auth path alongside API keys.

Supported IdPs:
  - Okta (OpenID Connect / OAuth 2.0)
  - Azure AD / Entra ID (Microsoft identity platform v2.0)
  - Generic OIDC (any provider with .well-known/openid-configuration)

Architecture:
  - JWKS keys cached with configurable TTL (default 1h)
  - Token validation: signature, issuer, audience, expiry, not-before
  - Role mapping via configurable claim → AION role map
  - Falls back to API key auth when IdP is not configured

Configuration (env vars):
  AION_IDP_PROVIDER    = "okta" | "azure_ad" | "oidc"
  AION_IDP_ISSUER      = "https://dev-xxxx.okta.com/oauth2/default"
  AION_IDP_AUDIENCE     = "api://aion-os"
  AION_IDP_JWKS_URI    = "https://dev-xxxx.okta.com/.../keys" (auto-discovered if omitted)
  AION_IDP_ROLE_CLAIM  = "groups" | "roles" | "aion_role"
  AION_IDP_ADMIN_GROUP = "AION-Admins"
  AION_IDP_ANALYST_GROUP = "AION-Analysts"

Usage:
    from aionos.security.idp import get_idp_validator, validate_bearer_token

    # In FastAPI endpoint:
    validator = get_idp_validator()
    if validator.is_configured():
        claims = validator.validate_token(token)
        role = validator.map_role(claims)
"""

import os
import json
import time
import base64
import hashlib
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Set
from urllib.request import urlopen, Request as URLRequest
from urllib.error import URLError

logger = logging.getLogger("aionos.security.idp")

# Try to import PyJWT for proper JWT validation
try:
    import jwt as pyjwt
    from jwt import PyJWKClient
    PYJWT_AVAILABLE = True
except ImportError:
    PYJWT_AVAILABLE = False
    logger.info("PyJWT not installed — using stdlib JWT validation")


# =============================================================================
# DATA CLASSES
# =============================================================================

class IdPProvider(str, Enum):
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    OIDC = "oidc"  # Generic OpenID Connect
    NONE = "none"


@dataclass
class IdPConfig:
    """Configuration for an identity provider."""
    provider: IdPProvider = IdPProvider.NONE
    issuer: str = ""
    audience: str = ""
    jwks_uri: str = ""
    role_claim: str = "groups"          # JWT claim containing role info
    admin_groups: Set[str] = field(default_factory=lambda: {"AION-Admins"})
    analyst_groups: Set[str] = field(default_factory=lambda: {"AION-Analysts"})
    viewer_groups: Set[str] = field(default_factory=lambda: {"AION-Viewers"})
    jwks_cache_ttl: int = 3600          # Cache JWKS keys for 1 hour
    clock_skew_seconds: int = 30        # Tolerance for clock differences
    required_scopes: Set[str] = field(default_factory=set)


@dataclass
class TokenClaims:
    """Validated token claims."""
    subject: str                    # User identifier (sub claim)
    email: str = ""                 # User email
    name: str = ""                  # Display name
    groups: List[str] = field(default_factory=list)  # Group memberships
    roles: List[str] = field(default_factory=list)    # Role claims
    scopes: List[str] = field(default_factory=list)   # Granted scopes
    issuer: str = ""                # Token issuer
    audience: str = ""              # Token audience
    issued_at: float = 0.0         # iat claim
    expires_at: float = 0.0        # exp claim
    raw_claims: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


# =============================================================================
# JWKS CACHE
# =============================================================================

class JWKSCache:
    """
    Caches JSON Web Key Sets from IdP with TTL.

    Supports auto-refresh on signature verification failure
    (handles IdP key rotation).
    """

    def __init__(self, jwks_uri: str, ttl: int = 3600):
        self._jwks_uri = jwks_uri
        self._ttl = ttl
        self._keys: Dict[str, Dict] = {}
        self._last_fetched: float = 0.0
        self._lock = threading.Lock()

    def get_key(self, kid: str) -> Optional[Dict]:
        """Get a signing key by Key ID. Fetches JWKS if cache expired."""
        if self._is_stale() or kid not in self._keys:
            self._refresh()
        return self._keys.get(kid)

    def force_refresh(self):
        """Force JWKS refresh (e.g., after signature failure)."""
        self._refresh()

    @property
    def cached_key_ids(self) -> List[str]:
        return list(self._keys.keys())

    def _is_stale(self) -> bool:
        return time.time() - self._last_fetched > self._ttl

    def _refresh(self):
        """Fetch JWKS from IdP endpoint."""
        with self._lock:
            # Double-check after acquiring lock
            if not self._is_stale() and self._keys:
                return

            try:
                req = URLRequest(
                    self._jwks_uri,
                    headers={"Accept": "application/json"},
                )
                with urlopen(req, timeout=10) as resp:
                    jwks = json.loads(resp.read())

                new_keys = {}
                for key_data in jwks.get("keys", []):
                    kid = key_data.get("kid")
                    if kid:
                        new_keys[kid] = key_data

                self._keys = new_keys
                self._last_fetched = time.time()
                logger.info(
                    f"JWKS refreshed from {self._jwks_uri}: "
                    f"{len(new_keys)} keys loaded"
                )
            except (URLError, json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to fetch JWKS from {self._jwks_uri}: {e}")
                # Keep stale keys rather than clearing


# =============================================================================
# JWT VALIDATOR
# =============================================================================

class JWTValidator:
    """
    Validates JWT tokens from enterprise identity providers.

    Checks:
      - Signature (via JWKS public keys)
      - Issuer (iss claim)
      - Audience (aud claim)
      - Expiration (exp claim)
      - Not-before (nbf claim)
      - Clock skew tolerance
    """

    def __init__(self, config: IdPConfig):
        self._config = config
        self._jwks_cache: Optional[JWKSCache] = None
        self._pyjwk_client = None

        if config.jwks_uri:
            self._jwks_cache = JWKSCache(config.jwks_uri, config.jwks_cache_ttl)
            if PYJWT_AVAILABLE:
                try:
                    self._pyjwk_client = PyJWKClient(config.jwks_uri)
                except Exception:
                    pass

    def validate(self, token: str) -> TokenClaims:
        """
        Validate a JWT token and return parsed claims.

        Raises ValueError on validation failure.
        """
        if PYJWT_AVAILABLE and self._pyjwk_client:
            return self._validate_pyjwt(token)
        return self._validate_stdlib(token)

    def _validate_pyjwt(self, token: str) -> TokenClaims:
        """Validate using PyJWT library (recommended for production)."""
        try:
            signing_key = self._pyjwk_client.get_signing_key_from_jwt(token)
            decoded = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "RS384", "RS512", "ES256", "ES384"],
                audience=self._config.audience or None,
                issuer=self._config.issuer or None,
                leeway=self._config.clock_skew_seconds,
                options={
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iss": bool(self._config.issuer),
                    "verify_aud": bool(self._config.audience),
                },
            )
            return self._extract_claims(decoded)
        except Exception as e:
            raise ValueError(f"JWT validation failed: {e}")

    def _validate_stdlib(self, token: str) -> TokenClaims:
        """
        Validate JWT using stdlib only (limited — no signature verification).

        WARNING: For demo/development only. Install PyJWT for production.
        Checks: structure, expiry, issuer, audience.
        Does NOT check cryptographic signature.
        """
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format: expected 3 parts")

        try:
            # Decode header
            header = self._b64_decode_json(parts[0])
            # Decode payload
            payload = self._b64_decode_json(parts[1])
        except Exception as e:
            raise ValueError(f"Failed to decode JWT: {e}")

        logger.warning(
            "JWT signature NOT verified (PyJWT not installed). "
            "Install PyJWT + cryptography for production."
        )

        # Check expiration
        now = time.time()
        exp = payload.get("exp", 0)
        if exp and now > exp + self._config.clock_skew_seconds:
            raise ValueError(f"Token expired at {exp}, current time {now}")

        # Check not-before
        nbf = payload.get("nbf", 0)
        if nbf and now < nbf - self._config.clock_skew_seconds:
            raise ValueError(f"Token not valid before {nbf}")

        # Check issuer
        if self._config.issuer:
            iss = payload.get("iss", "")
            if iss != self._config.issuer:
                raise ValueError(f"Issuer mismatch: expected '{self._config.issuer}', got '{iss}'")

        # Check audience
        if self._config.audience:
            aud = payload.get("aud", "")
            if isinstance(aud, list):
                if self._config.audience not in aud:
                    raise ValueError(f"Audience '{self._config.audience}' not in {aud}")
            elif aud != self._config.audience:
                raise ValueError(f"Audience mismatch: expected '{self._config.audience}', got '{aud}'")

        return self._extract_claims(payload)

    def _extract_claims(self, payload: Dict[str, Any]) -> TokenClaims:
        """Extract standardized claims from JWT payload."""
        return TokenClaims(
            subject=payload.get("sub", "unknown"),
            email=payload.get("email", payload.get("preferred_username", "")),
            name=payload.get("name", payload.get("given_name", "")),
            groups=payload.get(self._config.role_claim, []),
            roles=payload.get("roles", []),
            scopes=payload.get("scp", "").split() if isinstance(payload.get("scp"), str)
                   else payload.get("scp", []),
            issuer=payload.get("iss", ""),
            audience=str(payload.get("aud", "")),
            issued_at=payload.get("iat", 0),
            expires_at=payload.get("exp", 0),
            raw_claims=payload,
        )

    @staticmethod
    def _b64_decode_json(segment: str) -> Dict:
        """Decode a base64url-encoded JWT segment."""
        # Add padding
        padding = 4 - len(segment) % 4
        if padding != 4:
            segment += "=" * padding
        decoded = base64.urlsafe_b64decode(segment)
        return json.loads(decoded)


# =============================================================================
# IdP INTEGRATION
# =============================================================================

class IdPIntegration:
    """
    Main IdP integration class. Maps IdP tokens to AION roles.

    Usage in FastAPI:
        idp = get_idp_validator()
        if token and idp.is_configured():
            claims = idp.validate_token(token)
            role = idp.map_role(claims)
    """

    def __init__(self, config: IdPConfig):
        self._config = config
        self._validator: Optional[JWTValidator] = None

        if config.provider != IdPProvider.NONE and config.issuer:
            # Auto-discover JWKS URI if not set
            if not config.jwks_uri:
                config.jwks_uri = self._discover_jwks_uri(config)
            self._validator = JWTValidator(config)
            logger.info(
                f"IdP integration configured: provider={config.provider.value}, "
                f"issuer={config.issuer}"
            )
        else:
            logger.info("IdP integration not configured — using API key auth only")

    def is_configured(self) -> bool:
        """Whether IdP auth is active."""
        return self._validator is not None

    def validate_token(self, token: str) -> TokenClaims:
        """
        Validate a bearer token and return claims.

        Raises ValueError if token is invalid or IdP not configured.
        """
        if not self._validator:
            raise ValueError("IdP not configured")
        return self._validator.validate(token)

    def map_role(self, claims: TokenClaims) -> str:
        """
        Map IdP claims to an AION role.

        Checks group memberships and role claims against configured
        admin/analyst/viewer group names.

        Returns: "admin", "analyst", "viewer", or "anonymous"
        """
        all_groups = set(claims.groups + claims.roles)

        # Check admin groups
        if all_groups & self._config.admin_groups:
            return "admin"

        # Check analyst groups
        if all_groups & self._config.analyst_groups:
            return "analyst"

        # Check viewer groups
        if all_groups & self._config.viewer_groups:
            return "viewer"

        # Authenticated but no matching group → viewer (least privilege)
        if claims.subject and claims.subject != "unknown":
            logger.warning(
                f"User {claims.subject} authenticated but no matching group. "
                f"Groups: {all_groups}. Defaulting to viewer."
            )
            return "viewer"

        return "anonymous"

    def get_user_context(self, claims: TokenClaims) -> Dict[str, Any]:
        """
        Build AION user context from IdP claims for audit logging.
        """
        return {
            "user_id": claims.subject,
            "email": claims.email,
            "name": claims.name,
            "role": self.map_role(claims),
            "issuer": claims.issuer,
            "groups": claims.groups,
            "auth_method": "idp",
            "token_issued_at": claims.issued_at,
            "token_expires_at": claims.expires_at,
        }

    @staticmethod
    def _discover_jwks_uri(config: IdPConfig) -> str:
        """
        Auto-discover JWKS URI from OpenID Connect well-known endpoint.

        Standard: /.well-known/openid-configuration → jwks_uri
        """
        issuer = config.issuer.rstrip("/")

        discovery_urls = []
        if config.provider == IdPProvider.AZURE_AD:
            # Azure AD v2.0 discovery
            discovery_urls = [
                f"{issuer}/v2.0/.well-known/openid-configuration",
                f"{issuer}/.well-known/openid-configuration",
            ]
        elif config.provider == IdPProvider.OKTA:
            # Okta discovery
            discovery_urls = [
                f"{issuer}/.well-known/openid-configuration",
            ]
        else:
            # Generic OIDC
            discovery_urls = [
                f"{issuer}/.well-known/openid-configuration",
            ]

        for url in discovery_urls:
            try:
                req = URLRequest(url, headers={"Accept": "application/json"})
                with urlopen(req, timeout=10) as resp:
                    oidc_config = json.loads(resp.read())
                    jwks_uri = oidc_config.get("jwks_uri", "")
                    if jwks_uri:
                        logger.info(f"Discovered JWKS URI: {jwks_uri}")
                        return jwks_uri
            except (URLError, json.JSONDecodeError, OSError):
                continue

        logger.warning(f"Could not discover JWKS URI for issuer {issuer}")
        return ""


# =============================================================================
# FACTORY / SINGLETON
# =============================================================================

_global_idp: Optional[IdPIntegration] = None


def load_idp_config_from_env() -> IdPConfig:
    """Load IdP configuration from environment variables."""
    provider_str = os.environ.get("AION_IDP_PROVIDER", "none").lower()
    try:
        provider = IdPProvider(provider_str)
    except ValueError:
        provider = IdPProvider.NONE

    config = IdPConfig(
        provider=provider,
        issuer=os.environ.get("AION_IDP_ISSUER", ""),
        audience=os.environ.get("AION_IDP_AUDIENCE", ""),
        jwks_uri=os.environ.get("AION_IDP_JWKS_URI", ""),
        role_claim=os.environ.get("AION_IDP_ROLE_CLAIM", "groups"),
    )

    # Admin groups (comma-separated)
    admin_groups = os.environ.get("AION_IDP_ADMIN_GROUP", "AION-Admins")
    config.admin_groups = {g.strip() for g in admin_groups.split(",") if g.strip()}

    # Analyst groups (comma-separated)
    analyst_groups = os.environ.get("AION_IDP_ANALYST_GROUP", "AION-Analysts")
    config.analyst_groups = {g.strip() for g in analyst_groups.split(",") if g.strip()}

    # Viewer groups (comma-separated)
    viewer_groups = os.environ.get("AION_IDP_VIEWER_GROUP", "AION-Viewers")
    config.viewer_groups = {g.strip() for g in viewer_groups.split(",") if g.strip()}

    return config


def get_idp_validator() -> IdPIntegration:
    """
    Get the IdP integration singleton.

    Configuration via environment variables:
      AION_IDP_PROVIDER = "okta" | "azure_ad" | "oidc" | "none"
      AION_IDP_ISSUER   = "https://your-issuer.example.com"
      AION_IDP_AUDIENCE  = "api://aion-os"

    When AION_IDP_PROVIDER is "none" (default), IdP auth is disabled
    and the system falls back to API key authentication.
    """
    global _global_idp
    if _global_idp is None:
        config = load_idp_config_from_env()
        _global_idp = IdPIntegration(config)
    return _global_idp


def validate_bearer_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function: validate bearer token and return user context.

    Returns None if IdP not configured or token invalid.
    """
    idp = get_idp_validator()
    if not idp.is_configured():
        return None
    try:
        claims = idp.validate_token(token)
        return idp.get_user_context(claims)
    except ValueError as e:
        logger.warning(f"Bearer token validation failed: {e}")
        return None
