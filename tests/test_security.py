"""
Tests for security modules: encryption, IdP integration, RBAC.
"""

import json
import time
import base64
import secrets
import pytest


# =============================================================================
# AES-256 ENCRYPTION
# =============================================================================

class TestAES256Provider:
    """Tests for AES-256-GCM encryption at rest."""

    def test_encrypt_decrypt_roundtrip(self, encryption_provider):
        plaintext = b"Confidential attorney-client data"
        ciphertext = encryption_provider.encrypt(plaintext)
        assert ciphertext != plaintext
        decrypted = encryption_provider.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_different_ciphertexts_per_call(self, encryption_provider):
        """Each encryption should produce unique ciphertext (random nonce)."""
        plaintext = b"Same data"
        c1 = encryption_provider.encrypt(plaintext)
        c2 = encryption_provider.encrypt(plaintext)
        assert c1 != c2  # Different nonces

    def test_json_roundtrip(self, encryption_provider):
        data = {"user": "alice@firm.com", "risk_score": 87, "events": [1, 2, 3]}
        encrypted = encryption_provider.encrypt_json(data)
        assert isinstance(encrypted, str)
        decrypted = encryption_provider.decrypt_json(encrypted)
        assert decrypted == data

    def test_wrong_key_fails(self):
        from aionos.security.encryption import AES256Provider
        key1 = secrets.token_bytes(32)
        key2 = secrets.token_bytes(32)
        provider1 = AES256Provider(key=key1)
        provider2 = AES256Provider(key=key2)

        ciphertext = provider1.encrypt(b"secret")
        with pytest.raises(Exception):
            provider2.decrypt(ciphertext)

    def test_passphrase_derivation(self):
        from aionos.security.encryption import AES256Provider
        provider = AES256Provider(passphrase="my-secure-passphrase-2026")
        assert provider.is_enabled()
        ct = provider.encrypt(b"test")
        pt = provider.decrypt(ct)
        assert pt == b"test"

    def test_invalid_key_size_rejected(self):
        from aionos.security.encryption import AES256Provider
        with pytest.raises(ValueError, match="32 bytes"):
            AES256Provider(key=b"too_short")

    def test_empty_data(self, encryption_provider):
        ct = encryption_provider.encrypt(b"")
        pt = encryption_provider.decrypt(ct)
        assert pt == b""

    def test_large_data(self, encryption_provider):
        """Encrypt 1MB of data."""
        data = secrets.token_bytes(1024 * 1024)
        ct = encryption_provider.encrypt(data)
        pt = encryption_provider.decrypt(ct)
        assert pt == data


class TestNoOpProvider:
    """Tests for the NoOp (plaintext) encryption provider."""

    def test_passthrough(self, noop_encryption):
        data = b"plaintext data"
        assert noop_encryption.encrypt(data) == data
        assert noop_encryption.decrypt(data) == data

    def test_not_enabled(self, noop_encryption):
        assert noop_encryption.is_enabled() is False

    def test_json_passthrough(self, noop_encryption):
        data = {"key": "value"}
        encrypted = noop_encryption.encrypt_json(data)
        decrypted = noop_encryption.decrypt_json(encrypted)
        assert decrypted == data


class TestKeyGeneration:
    """Tests for key generation utility."""

    def test_generate_key_format(self):
        from aionos.security.encryption import generate_key
        key = generate_key()
        raw = base64.b64decode(key)
        assert len(raw) == 32

    def test_generate_key_unique(self):
        from aionos.security.encryption import generate_key
        k1 = generate_key()
        k2 = generate_key()
        assert k1 != k2


class TestEncryptionFactory:
    """Tests for get_encryption_provider() factory."""

    def test_no_env_returns_noop(self, monkeypatch):
        monkeypatch.delenv("AION_ENCRYPTION_KEY", raising=False)
        monkeypatch.delenv("AION_ENCRYPTION_PASSPHRASE", raising=False)
        monkeypatch.delenv("AION_KEY_FILE", raising=False)

        import aionos.security.encryption as mod
        mod._global_provider = None
        provider = mod.get_encryption_provider()
        assert provider.is_enabled() is False

    def test_env_key_returns_aes(self, monkeypatch):
        key = base64.b64encode(secrets.token_bytes(32)).decode()
        monkeypatch.setenv("AION_ENCRYPTION_KEY", key)

        import aionos.security.encryption as mod
        mod._global_provider = None
        provider = mod.get_encryption_provider()
        assert provider.is_enabled() is True

    def test_env_passphrase_returns_aes(self, monkeypatch):
        monkeypatch.delenv("AION_ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("AION_ENCRYPTION_PASSPHRASE", "test-pass-2026")

        import aionos.security.encryption as mod
        mod._global_provider = None
        provider = mod.get_encryption_provider()
        assert provider.is_enabled() is True


# =============================================================================
# IdP INTEGRATION
# =============================================================================

class TestIdPIntegration:
    """Tests for identity provider integration."""

    def test_not_configured_by_default(self):
        from aionos.security.idp import IdPIntegration, IdPConfig, IdPProvider
        config = IdPConfig(provider=IdPProvider.NONE)
        idp = IdPIntegration(config)
        assert idp.is_configured() is False

    def test_role_mapping_admin(self):
        from aionos.security.idp import IdPIntegration, IdPConfig, IdPProvider, TokenClaims
        config = IdPConfig(
            provider=IdPProvider.OKTA,
            admin_groups={"AION-Admins"},
            analyst_groups={"AION-Analysts"},
        )
        idp = IdPIntegration.__new__(IdPIntegration)
        idp._config = config
        idp._validator = None

        claims = TokenClaims(subject="alice", groups=["AION-Admins"])
        assert idp.map_role(claims) == "admin"

    def test_role_mapping_analyst(self):
        from aionos.security.idp import IdPIntegration, IdPConfig, IdPProvider, TokenClaims
        config = IdPConfig(
            admin_groups={"AION-Admins"},
            analyst_groups={"AION-Analysts"},
        )
        idp = IdPIntegration.__new__(IdPIntegration)
        idp._config = config
        idp._validator = None

        claims = TokenClaims(subject="bob", groups=["AION-Analysts"])
        assert idp.map_role(claims) == "analyst"

    def test_role_mapping_no_group_defaults_viewer(self):
        from aionos.security.idp import IdPIntegration, IdPConfig, TokenClaims
        config = IdPConfig(
            admin_groups={"AION-Admins"},
            analyst_groups={"AION-Analysts"},
            viewer_groups={"AION-Viewers"},
        )
        idp = IdPIntegration.__new__(IdPIntegration)
        idp._config = config
        idp._validator = None

        claims = TokenClaims(subject="charlie", groups=["Some-Other-Group"])
        assert idp.map_role(claims) == "viewer"

    def test_user_context_shape(self):
        from aionos.security.idp import IdPIntegration, IdPConfig, TokenClaims
        config = IdPConfig(admin_groups={"AION-Admins"})
        idp = IdPIntegration.__new__(IdPIntegration)
        idp._config = config
        idp._validator = None

        claims = TokenClaims(
            subject="alice", email="alice@firm.com", name="Alice",
            groups=["AION-Admins"], issuer="https://okta.example.com",
        )
        ctx = idp.get_user_context(claims)
        assert ctx["user_id"] == "alice"
        assert ctx["email"] == "alice@firm.com"
        assert ctx["role"] == "admin"
        assert ctx["auth_method"] == "idp"


class TestJWTValidatorStdlib:
    """Tests for stdlib JWT validation (no PyJWT dependency required)."""

    def _make_unsigned_jwt(self, payload: dict) -> str:
        """Create a JWT-like token for testing (no signature)."""
        import json, base64
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).rstrip(b"=").decode()
        body = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).rstrip(b"=").decode()
        return f"{header}.{body}.nosig"

    def test_expired_token_rejected(self):
        from aionos.security.idp import JWTValidator, IdPConfig
        config = IdPConfig(issuer="", audience="")
        validator = JWTValidator(config)
        token = self._make_unsigned_jwt({"sub": "alice", "exp": time.time() - 3600})
        with pytest.raises(ValueError, match="expired"):
            validator._validate_stdlib(token)

    def test_valid_token_parsed(self):
        from aionos.security.idp import JWTValidator, IdPConfig
        config = IdPConfig(issuer="", audience="")
        validator = JWTValidator(config)
        token = self._make_unsigned_jwt({
            "sub": "alice",
            "email": "alice@firm.com",
            "exp": time.time() + 3600,
            "iat": time.time(),
        })
        claims = validator._validate_stdlib(token)
        assert claims.subject == "alice"
        assert claims.email == "alice@firm.com"

    def test_issuer_mismatch_rejected(self):
        from aionos.security.idp import JWTValidator, IdPConfig
        config = IdPConfig(issuer="https://expected.okta.com")
        validator = JWTValidator(config)
        token = self._make_unsigned_jwt({
            "sub": "alice", "iss": "https://wrong.okta.com",
            "exp": time.time() + 3600,
        })
        with pytest.raises(ValueError, match="Issuer"):
            validator._validate_stdlib(token)
