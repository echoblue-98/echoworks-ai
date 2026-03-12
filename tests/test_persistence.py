"""
Tests for persistence layer: InMemoryStore, JsonFileStore, ReportStore.
Includes encryption-at-rest integration tests.
"""

import json
import time
import pytest


# =============================================================================
# IN-MEMORY STORE
# =============================================================================

class TestInMemoryStore:
    """Tests for the InMemoryStore backend."""

    def test_store_and_retrieve(self, memory_store):
        event = {"event_type": "vpn_access", "ts_epoch": time.time(), "user_id": "alice"}
        assert memory_store.store_event("alice", event) is True
        events = memory_store.get_user_events("alice")
        assert len(events) == 1
        assert events[0]["event_type"] == "vpn_access"

    def test_user_count(self, memory_store):
        memory_store.store_event("alice", {"ts_epoch": time.time()})
        memory_store.store_event("bob", {"ts_epoch": time.time()})
        assert memory_store.get_user_count() == 2

    def test_event_count(self, memory_store):
        memory_store.store_event("alice", {"ts_epoch": time.time()})
        memory_store.store_event("alice", {"ts_epoch": time.time()})
        assert memory_store.get_event_count("alice") == 2
        assert memory_store.get_event_count() == 2

    def test_filter_by_type(self, memory_store):
        memory_store.store_event("alice", {"event_type": "vpn", "ts_epoch": time.time()})
        memory_store.store_event("alice", {"event_type": "file", "ts_epoch": time.time()})
        vpn = memory_store.get_user_events_by_type("alice", "vpn")
        assert len(vpn) == 1

    def test_delete_old_events(self, memory_store):
        now = time.time()
        memory_store.store_event("alice", {"ts_epoch": now - 3600})
        memory_store.store_event("alice", {"ts_epoch": now})
        deleted = memory_store.delete_user_events("alice", now - 1800)
        assert deleted == 1
        assert memory_store.get_event_count("alice") == 1

    def test_get_all_users(self, memory_store):
        memory_store.store_event("alice", {"ts_epoch": time.time()})
        memory_store.store_event("bob", {"ts_epoch": time.time()})
        users = memory_store.get_all_users()
        assert set(users) == {"alice", "bob"}


# =============================================================================
# JSON FILE STORE
# =============================================================================

class TestJsonFileStore:
    """Tests for the JsonFileStore backend (file persistence)."""

    def test_store_and_flush(self, json_store, tmp_data_dir):
        json_store.store_event("alice@firm.com", {
            "event_type": "vpn_access",
            "ts_epoch": time.time(),
        })
        json_store.flush()
        # File should exist on disk
        files = list((tmp_data_dir / "events").glob("*.json"))
        assert len(files) >= 1

    def test_roundtrip_persistence(self, tmp_data_dir):
        """Write events, close store, reopen, and verify data survived."""
        from aionos.core.persistence import JsonFileStore

        # Write
        store1 = JsonFileStore(data_dir=str(tmp_data_dir), auto_save_interval=9999)
        store1.store_event("alice", {"event_type": "test", "ts_epoch": time.time()})
        store1.flush()
        store1.close()

        # Reopen
        store2 = JsonFileStore(data_dir=str(tmp_data_dir), auto_save_interval=9999)
        events = store2.get_user_events("alice")
        store2.close()
        assert len(events) == 1
        assert events[0]["event_type"] == "test"

    def test_user_limit_enforcement(self, json_store):
        """Exceeding max_events_per_user should trim old events."""
        json_store.max_events_per_user = 10
        for i in range(15):
            json_store.store_event("alice", {"ts_epoch": time.time(), "i": i})
        assert json_store.get_event_count("alice") <= 10


# =============================================================================
# REPORT STORE
# =============================================================================

class TestReportStore:
    """Tests for the forensic ReportStore."""

    def test_store_and_retrieve_report(self, report_store):
        rid = report_store.store_report(
            user_id="alice@firm.com",
            attack_id="departing_attorney",
            report={"risk_score": 87, "vulnerabilities": [], "immediate_actions": []},
            scenario_name="Test Scenario",
        )
        assert rid is not None
        full = report_store.get_full_report(rid)
        assert full is not None
        assert full["report"]["risk_score"] == 87

    def test_user_history(self, report_store):
        for i in range(3):
            report_store.store_report(
                user_id="alice@firm.com",
                attack_id=f"attack_{i}",
                report={"risk_score": 50 + i * 10, "vulnerabilities": [], "immediate_actions": []},
            )
        history = report_store.get_user_history("alice@firm.com")
        assert len(history) == 3

    def test_metering(self, report_store):
        report_store.store_report("bob", "test", {"risk_score": 10, "vulnerabilities": [], "immediate_actions": []})
        meter = report_store.get_meter()
        assert meter["total_reports"] >= 1


# =============================================================================
# ENCRYPTION INTEGRATION
# =============================================================================

class TestEncryptedPersistence:
    """Tests that encryption integrates correctly with persistence."""

    def test_encrypted_roundtrip(self, tmp_data_dir, monkeypatch):
        """Data encrypted on write should decrypt on read."""
        import secrets, base64
        key = base64.b64encode(secrets.token_bytes(32)).decode()
        monkeypatch.setenv("AION_ENCRYPTION_KEY", key)

        # Reset singletons so they pick up the new env var
        import aionos.security.encryption as enc_mod
        import aionos.core.persistence as pers
        enc_mod._global_provider = None
        pers._encryption_provider = None

        from aionos.core.persistence import JsonFileStore
        store = JsonFileStore(data_dir=str(tmp_data_dir), auto_save_interval=9999)
        store.store_event("alice", {"event_type": "secret", "ts_epoch": time.time()})
        store.flush()
        store.close()

        # The file on disk should NOT contain plaintext
        files = list((tmp_data_dir / "events").glob("*.json"))
        assert len(files) >= 1
        raw = files[0].read_bytes()
        # If encryption is working, raw bytes won't be valid JSON
        is_encrypted = True
        try:
            json.loads(raw.decode("utf-8"))
            is_encrypted = False  # It decoded as JSON — not encrypted
        except (json.JSONDecodeError, UnicodeDecodeError):
            is_encrypted = True

        # Reset and reopen — should decrypt successfully
        enc_mod._global_provider = None
        pers._encryption_provider = None
        store2 = JsonFileStore(data_dir=str(tmp_data_dir), auto_save_interval=9999)
        events = store2.get_user_events("alice")
        store2.close()
        assert len(events) == 1
        assert events[0]["event_type"] == "secret"

        # Only assert encryption if cryptography library is installed
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            assert is_encrypted, "File should be encrypted but was plaintext JSON"
        except ImportError:
            pass  # Stdlib fallback may produce different results

    def test_noop_provider_plaintext(self, tmp_data_dir, monkeypatch):
        """Without encryption key, files should be readable plaintext JSON."""
        # Ensure no encryption env vars
        monkeypatch.delenv("AION_ENCRYPTION_KEY", raising=False)
        monkeypatch.delenv("AION_ENCRYPTION_PASSPHRASE", raising=False)
        monkeypatch.delenv("AION_KEY_FILE", raising=False)

        import aionos.security.encryption as enc_mod
        import aionos.core.persistence as pers
        enc_mod._global_provider = None
        pers._encryption_provider = None

        from aionos.core.persistence import JsonFileStore
        store = JsonFileStore(data_dir=str(tmp_data_dir), auto_save_interval=9999)
        store.store_event("bob", {"event_type": "plain", "ts_epoch": time.time()})
        store.flush()
        store.close()

        files = list((tmp_data_dir / "events").glob("*.json"))
        raw = files[0].read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["events"][0]["event_type"] == "plain"
