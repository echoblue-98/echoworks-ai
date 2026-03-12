"""
AION OS - Shared pytest fixtures and configuration.

Provides reusable test infrastructure: engines, stores, events, etc.
"""

import os
import time
import uuid
import shutil
import pytest
from pathlib import Path
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Ensure tests run without requiring real API keys / encryption keys
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure no stale singletons or env vars leak between tests."""
    # Reset encryption singleton so each test starts fresh
    import aionos.core.persistence as pers
    pers._encryption_provider = None

    # Reset IdP singleton
    import aionos.security.idp as idp_mod
    idp_mod._global_idp = None

    # Reset encryption singleton
    import aionos.security.encryption as enc_mod
    enc_mod._global_provider = None


# ---------------------------------------------------------------------------
# Temporary data directory (cleaned after each test)
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory for persistence tests."""
    data_dir = tmp_path / "aion_data"
    data_dir.mkdir()
    (data_dir / "events").mkdir()
    (data_dir / "reports").mkdir()
    return data_dir


# ---------------------------------------------------------------------------
# Core engine fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temporal_engine():
    """Create a TemporalCorrelationEngine with test knowledge base."""
    from aionos.core.temporal_engine import TemporalCorrelationEngine
    knowledge_path = Path("aionos/knowledge/test_events.json")
    return TemporalCorrelationEngine(knowledge_path)


@pytest.fixture
def baseline_engine():
    """Create a BaselineEngine for deviation testing."""
    from aionos.core.baseline_engine import BaselineEngine
    return BaselineEngine()


@pytest.fixture
def intent_classifier():
    """Create an IntentClassifier."""
    from aionos.core.intent_classifier import IntentClassifier
    return IntentClassifier()


@pytest.fixture
def ethics_layer():
    """Create an EthicsLayer."""
    from aionos.safety.ethics_layer import EthicsLayer
    return EthicsLayer()


@pytest.fixture
def improvement_engine():
    """Create an ImprovementEngine in mock mode."""
    from aionos.improvement import ImprovementEngine
    engine = ImprovementEngine(llm_provider="mock")
    engine.initialize()
    return engine


# ---------------------------------------------------------------------------
# Persistence fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def memory_store():
    """Create an in-memory EventStore."""
    from aionos.core.persistence import InMemoryStore
    return InMemoryStore()


@pytest.fixture
def json_store(tmp_data_dir):
    """Create a JsonFileStore backed by tmp directory."""
    from aionos.core.persistence import JsonFileStore
    store = JsonFileStore(data_dir=str(tmp_data_dir), auto_save_interval=9999)
    yield store
    store.close()


@pytest.fixture
def report_store(tmp_data_dir):
    """Create a ReportStore backed by tmp directory."""
    from aionos.core.persistence import ReportStore
    return ReportStore(data_dir=str(tmp_data_dir))


# ---------------------------------------------------------------------------
# Security fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def encryption_provider():
    """Create an AES256Provider with a test key."""
    from aionos.security.encryption import AES256Provider
    import secrets
    key = secrets.token_bytes(32)
    return AES256Provider(key=key)


@pytest.fixture
def noop_encryption():
    """Create a NoOpEncryptionProvider (plaintext)."""
    from aionos.security.encryption import NoOpEncryptionProvider
    return NoOpEncryptionProvider()


# ---------------------------------------------------------------------------
# Event factories
# ---------------------------------------------------------------------------

@pytest.fixture
def make_security_event():
    """Factory fixture: create SecurityEvent instances."""
    from aionos.core.temporal_engine import SecurityEvent, EventType

    def _make(
        user_id: str = "test@lawfirm.com",
        event_type: EventType = EventType.VPN_ACCESS,
        days_ago: int = 0,
        details: dict = None,
    ) -> SecurityEvent:
        return SecurityEvent(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.utcnow() - timedelta(days=days_ago),
            source_system="test_harness",
            details=details or {},
        )

    return _make


@pytest.fixture
def sample_events(make_security_event):
    """Pre-built sequence of events simulating a departing attorney pattern."""
    from aionos.core.temporal_engine import EventType

    return [
        make_security_event(event_type=EventType.VPN_ACCESS, days_ago=5),
        make_security_event(event_type=EventType.DATABASE_QUERY, days_ago=3,
                            details={"query": "SELECT * FROM clients", "rows": 25000}),
        make_security_event(event_type=EventType.BULK_OPERATION, days_ago=2,
                            details={"operation": "copy", "files": 8000}),
        make_security_event(event_type=EventType.CLOUD_SYNC, days_ago=1,
                            details={"destination": "personal_dropbox", "files": 5000}),
    ]
