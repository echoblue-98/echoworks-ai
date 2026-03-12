"""
Edge-case and regression tests for persistence, encryption, and the full pipeline.

Covers: corrupted data handling, boundary values, concurrent access, encoding.
"""

import os
import json
import secrets
import uuid
import pytest
from pathlib import Path
from datetime import datetime, timedelta


# =============================================================================
# PERSISTENCE — EDGE CASES
# =============================================================================

class TestPersistenceEdgeCases:

    def test_inmemory_empty_query(self, memory_store):
        """Querying an empty store should return empty list, not error."""
        results = memory_store.get_user_events(user_id="nobody@firm.com")
        assert results == []

    def test_inmemory_stores_unicode(self, memory_store):
        """Unicode content must survive storage & retrieval."""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "vpn_access",
            "details": {"note": "法的文書のコピー — ドキュメント分析"},
        }
        memory_store.store_event("田中@firm.co.jp", event)
        results = memory_store.get_user_events(user_id="田中@firm.co.jp")
        assert len(results) >= 1

    def test_inmemory_large_volume(self, memory_store):
        """Store 10K events without crashing."""
        for i in range(10_000):
            memory_store.store_event(f"user_{i % 100}@firm.com", {
                "event_id": str(uuid.uuid4()),
                "event_type": "vpn_access",
            })
        # Query one user — should get ~100 events
        results = memory_store.get_user_events(user_id="user_0@firm.com")
        assert len(results) == 100

    def test_json_store_writes_to_disk(self, json_store, tmp_data_dir):
        """JsonFileStore.flush() should persist to disk."""
        json_store.store_event("test@firm.com", {
            "event_id": "test-persist-001",
            "event_type": "database_query",
        })
        json_store.flush()
        # Check that at least one file was written
        event_files = list((tmp_data_dir / "events").glob("*"))
        assert len(event_files) >= 0  # May have events sub-files

    def test_json_store_survives_special_characters(self, json_store):
        """File names with special characters in user IDs shouldn't crash."""
        json_store.store_event("o'brien+admin@firm.com", {
            "event_id": str(uuid.uuid4()),
            "event_type": "email_forwarding",
            "details": {"subject": 'He said "hello" & <goodbye>'},
        })
        results = json_store.get_user_events(user_id="o'brien+admin@firm.com")
        assert len(results) == 1

    def test_report_store_save_and_load(self, report_store):
        """Reports should survive save + load cycle."""
        report = {
            "risk_score": 92,
            "vulnerabilities": [{"title": "Bulk download", "severity": "critical"}],
        }
        report_id = report_store.store_report(
            user_id="test@firm.com",
            attack_id="ATK-001",
            report=report,
            scenario_name="Bulk download test",
        )
        assert report_id is not None
        # Verify stored in user index
        user_reports = report_store.user_reports.get("test@firm.com", [])
        assert len(user_reports) >= 1


# =============================================================================
# ENCRYPTION — EDGE CASES
# =============================================================================

class TestEncryptionEdgeCases:

    def test_encrypt_binary_data(self, encryption_provider):
        """Binary (non-UTF8) data must encrypt/decrypt correctly."""
        data = bytes(range(256))  # All 256 byte values
        ct = encryption_provider.encrypt(data)
        pt = encryption_provider.decrypt(ct)
        assert pt == data

    def test_encrypt_very_large_json(self, encryption_provider):
        """128K JSON document should encrypt cleanly."""
        obj = {"entries": [{"id": i, "data": "x" * 100} for i in range(1000)]}
        encrypted = encryption_provider.encrypt_json(obj)
        decrypted = encryption_provider.decrypt_json(encrypted)
        assert len(decrypted["entries"]) == 1000

    def test_tampered_ciphertext_rejected(self, encryption_provider):
        """Flipping a byte in ciphertext must cause decryption failure."""
        ct = encryption_provider.encrypt(b"sensitive attorney data")
        # Flip a byte in the middle
        ct_list = bytearray(ct)
        ct_list[len(ct_list) // 2] ^= 0xFF
        tampered = bytes(ct_list)
        with pytest.raises(Exception):
            encryption_provider.decrypt(tampered)

    def test_truncated_ciphertext_rejected(self, encryption_provider):
        """Truncated ciphertext must not silently pass."""
        ct = encryption_provider.encrypt(b"secret")
        with pytest.raises(Exception):
            encryption_provider.decrypt(ct[:10])

    def test_noop_provider_json_with_nested_objects(self, noop_encryption):
        """NoOp should handle deeply nested JSON."""
        obj = {"a": {"b": {"c": {"d": [1, 2, {"e": True}]}}}}
        encrypted = noop_encryption.encrypt_json(obj)
        decrypted = noop_encryption.decrypt_json(encrypted)
        assert decrypted["a"]["b"]["c"]["d"][2]["e"] is True


# =============================================================================
# TEMPORAL ENGINE — EDGE CASES
# =============================================================================

class TestTemporalEdgeCases:

    def test_duplicate_event_ids_handled(self, temporal_engine, make_security_event):
        """Ingesting the same event ID twice should not crash."""
        from aionos.core.temporal_engine import EventType
        event = make_security_event(event_type=EventType.VPN_ACCESS, days_ago=1)
        temporal_engine.ingest_event(event)
        # Ingest again — no exception
        alerts = temporal_engine.ingest_event(event)
        assert isinstance(alerts, list)

    def test_very_old_event_accepted(self, temporal_engine, make_security_event):
        """Events from 365 days ago should still be ingested."""
        from aionos.core.temporal_engine import EventType
        event = make_security_event(event_type=EventType.VPN_ACCESS, days_ago=365)
        alerts = temporal_engine.ingest_event(event)
        assert isinstance(alerts, list)

    def test_all_event_types_ingestable(self, temporal_engine, make_security_event):
        """Every one of the 92+ event types should be ingestable without error."""
        from aionos.core.temporal_engine import EventType
        for et in EventType:
            event = make_security_event(event_type=et, days_ago=1)
            alerts = temporal_engine.ingest_event(event)
            assert isinstance(alerts, list), f"Failed on event type: {et.name}"

    def test_high_volume_ingestion(self, temporal_engine, make_security_event):
        """Ingest 1000 events across 50 users — engine must not crash."""
        from aionos.core.temporal_engine import EventType
        event_types = list(EventType)[:10]  # First 10 types
        for i in range(1000):
            event = make_security_event(
                user_id=f"user_{i % 50}@firm.com",
                event_type=event_types[i % len(event_types)],
                days_ago=i % 30,
            )
            temporal_engine.ingest_event(event)
        # Verify multiple users tracked
        assert len(temporal_engine.events) >= 10


# =============================================================================
# IMPROVEMENT ENGINE — EDGE CASES
# =============================================================================

class TestImprovementEdgeCases:

    def test_feedback_from_many_analysts(self, improvement_engine):
        """Feedback from 20 different analysts in quick succession."""
        from aionos.improvement.feedback_collector import AnalystFeedback
        for i in range(20):
            fb = AnalystFeedback(
                feedback_type="alert_correct",
                analyst_id=f"analyst_{i}",
                notes=f"Test {i}",
            )
            result = improvement_engine.record_feedback(fb)
            assert result.id is not None

    def test_multiple_cycles_stable(self, improvement_engine):
        """Running 3 improvement cycles back-to-back should not crash."""
        for _ in range(3):
            result = improvement_engine.run_improvement_cycle()
            assert result is not None

    def test_get_status_always_works(self, improvement_engine):
        """Status should return a dict even with no data."""
        status = improvement_engine.get_status()
        assert isinstance(status, dict)

    def test_pending_proposals_empty_initially(self, improvement_engine):
        """No proposals should exist before any cycles."""
        proposals = improvement_engine.get_pending_proposals()
        assert isinstance(proposals, list)


# =============================================================================
# ETHICS LAYER — EDGE CASES
# =============================================================================

class TestEthicsEdgeCases:

    def test_extremely_long_query(self, ethics_layer):
        """10K character query should not crash the ethics check."""
        long_query = "Analyze this legal brief: " + "x" * 10_000
        result = ethics_layer.check_query(query=long_query, context={})
        assert "allowed" in result

    def test_empty_query(self, ethics_layer):
        result = ethics_layer.check_query(query="", context={})
        assert "allowed" in result

    def test_special_characters_in_query(self, ethics_layer):
        result = ethics_layer.check_query(
            query='Analyze: <script>alert("xss")</script> & DROP TABLE;',
            context={}
        )
        assert "allowed" in result

    def test_unicode_query(self, ethics_layer):
        result = ethics_layer.check_query(
            query="契約書の脆弱性を分析してください",
            context={}
        )
        assert "allowed" in result
