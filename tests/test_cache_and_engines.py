"""
Tests for cache layer, pattern engines, and daemon.
"""

import time
import pytest
from datetime import datetime, timedelta


# =============================================================================
# DETECTION CACHE
# =============================================================================

class TestDetectionCache:

    def test_put_and_get(self):
        from aionos.core.detection_cache import DetectionCache
        cache = DetectionCache(max_entries=10, ttl_seconds=60)
        cache.put("k1", {"score": 0.8})
        assert cache.get("k1") == {"score": 0.8}

    def test_miss_returns_none(self):
        from aionos.core.detection_cache import DetectionCache
        cache = DetectionCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        from aionos.core.detection_cache import DetectionCache
        cache = DetectionCache(ttl_seconds=0)  # Immediate expiry
        cache.put("k1", {"v": 1})
        time.sleep(0.01)
        assert cache.get("k1") is None

    def test_lru_eviction(self):
        from aionos.core.detection_cache import DetectionCache
        cache = DetectionCache(max_entries=2, ttl_seconds=60)
        cache.put("k1", {"v": 1})
        cache.put("k2", {"v": 2})
        cache.put("k3", {"v": 3})  # Should evict k1
        assert cache.get("k1") is None
        assert cache.get("k2") == {"v": 2}
        assert cache.get("k3") == {"v": 3}

    def test_lru_access_refreshes(self):
        from aionos.core.detection_cache import DetectionCache
        cache = DetectionCache(max_entries=2, ttl_seconds=60)
        cache.put("k1", {"v": 1})
        cache.put("k2", {"v": 2})
        cache.get("k1")  # Refresh k1
        cache.put("k3", {"v": 3})  # Should evict k2 (LRU)
        assert cache.get("k1") == {"v": 1}
        assert cache.get("k2") is None

    def test_invalidate(self):
        from aionos.core.detection_cache import DetectionCache
        cache = DetectionCache()
        cache.put("k1", {"v": 1})
        assert cache.invalidate("k1") is True
        assert cache.get("k1") is None
        assert cache.invalidate("k1") is False

    def test_clear(self):
        from aionos.core.detection_cache import DetectionCache
        cache = DetectionCache()
        cache.put("k1", {"v": 1})
        cache.put("k2", {"v": 2})
        assert cache.clear() == 2
        assert cache.get("k1") is None

    def test_stats_hit_rate(self):
        from aionos.core.detection_cache import DetectionCache
        cache = DetectionCache()
        cache.put("k1", {"v": 1})
        cache.get("k1")  # hit
        cache.get("k2")  # miss
        s = cache.stats()
        assert s["hits"] == 1
        assert s["misses"] == 1
        assert s["hit_rate"] == 0.5

    def test_make_key_deterministic(self):
        from aionos.core.detection_cache import DetectionCache
        k1 = DetectionCache.make_key(["vpn_access", "file_download"], user_id="alice")
        k2 = DetectionCache.make_key(["file_download", "vpn_access"], user_id="alice")
        assert k1 == k2  # Sorted, so order-independent

    def test_make_key_user_hashed(self):
        from aionos.core.detection_cache import DetectionCache
        k = DetectionCache.make_key(["vpn"], user_id="alice@firm.com")
        assert "alice" not in k
        assert "@" not in k

    def test_make_analysis_key_whitespace_normalization(self):
        from aionos.core.detection_cache import DetectionCache
        k1 = DetectionCache.make_analysis_key("hello  world")
        k2 = DetectionCache.make_analysis_key("Hello World")
        assert k1 == k2


# =============================================================================
# PATTERN ENGINES
# =============================================================================

class TestProximityEngine:

    def test_empty_events_returns_zero(self):
        from aionos.core.pattern_engines import ProximityEngine
        eng = ProximityEngine()
        result = eng.score({})
        assert result.score == 0.0

    def test_exfil_cluster_match(self):
        from aionos.core.pattern_engines import ProximityEngine
        eng = ProximityEngine()
        events = {"file_download": 50, "bulk_operation": 30, "cloud_sync": 20}
        result = eng.score(events)
        assert result.score > 0.5
        assert "data_exfiltration" in result.signals[0] or "pre_departure" in result.signals[0]

    def test_credential_theft_cluster(self):
        from aionos.core.pattern_engines import ProximityEngine
        eng = ProximityEngine()
        events = {"vpn_brute_force": 10, "impossible_travel": 5, "credential_access": 8}
        result = eng.score(events)
        assert result.score > 0.5
        assert "credential_theft" in result.signals[0]

    def test_latency_sub_millisecond(self):
        from aionos.core.pattern_engines import ProximityEngine
        eng = ProximityEngine()
        events = {"file_download": 10, "vpn_access": 5}
        result = eng.score(events)
        assert result.latency_us < 1000  # < 1ms


class TestTrustEngine:

    def test_clean_user_stays_trusted(self):
        from aionos.core.pattern_engines import TrustEngine
        eng = TrustEngine()
        result = eng.score([])
        assert result.score == 0.0  # Risk = 1 - trust(1.0) = 0.0

    def test_suspicious_events_decay_trust(self):
        from aionos.core.pattern_engines import TrustEngine
        eng = TrustEngine()
        events = [
            {"type": "after_hours_access"},
            {"type": "bulk_operation"},
            {"type": "security_disable"},
        ]
        result = eng.score(events)
        assert result.score > 0.5  # High risk after 3 decay events

    def test_recovery_after_clean_hours(self):
        from aionos.core.pattern_engines import TrustEngine
        eng = TrustEngine()
        events = [{"type": "security_disable"}]  # -0.40
        r1 = eng.score(events, hours_since_last_event=0)
        r2 = eng.score(events, hours_since_last_event=10)
        assert r2.score < r1.score  # Recovery should reduce risk


class TestPhaseEngine:

    def test_business_hours_no_amplification(self):
        from aionos.core.pattern_engines import PhaseEngine
        eng = PhaseEngine()
        ts = datetime(2026, 3, 16, 14, 0)  # 2PM Monday (weekday)
        result = eng.score(0.5, ts)
        assert result.score == 0.5  # No amp

    def test_graveyard_amplification(self):
        from aionos.core.pattern_engines import PhaseEngine
        eng = PhaseEngine()
        ts = datetime(2026, 3, 15, 2, 0)  # 2AM
        result = eng.score(0.5, ts)
        assert result.score > 0.5  # Amplified

    def test_weekend_amplification(self):
        from aionos.core.pattern_engines import PhaseEngine
        eng = PhaseEngine()
        ts = datetime(2026, 3, 14, 14, 0)  # Saturday 2PM
        result = eng.score(0.5, ts)
        assert result.score > 0.5


class TestVibeSynergy:

    def test_agreement_bonus(self):
        from aionos.core.pattern_engines import VibeSynergy, EngineScore
        syn = VibeSynergy()
        scores = [
            EngineScore("proximity", 0.7, 0.9, []),
            EngineScore("trust", 0.8, 0.9, []),
            EngineScore("phase", 0.75, 0.9, []),
        ]
        result = syn.fuse(scores)
        assert result.score > 0.7  # Base + agreement bonus

    def test_disagreement_damping(self):
        from aionos.core.pattern_engines import VibeSynergy, EngineScore
        syn = VibeSynergy()
        scores = [
            EngineScore("proximity", 0.9, 0.9, []),
            EngineScore("trust", 0.1, 0.9, []),
        ]
        result = syn.fuse(scores)
        # Should be damped due to high disagreement
        assert result.score < 0.9

    def test_empty_scores(self):
        from aionos.core.pattern_engines import VibeSynergy
        syn = VibeSynergy()
        result = syn.fuse([])
        assert result.score == 0.0


class TestPatternEnginePipeline:

    def test_full_evaluation(self):
        from aionos.core.pattern_engines import PatternEnginePipeline
        pipe = PatternEnginePipeline()
        result = pipe.evaluate(
            {"file_download": 50, "bulk_operation": 30},
            [{"type": "file_download"}, {"type": "bulk_operation"}],
        )
        assert 0 <= result.score <= 1.0
        assert result.engine == "synergy"

    def test_quick_evaluation(self):
        from aionos.core.pattern_engines import PatternEnginePipeline
        pipe = PatternEnginePipeline()
        result = pipe.evaluate_quick({"vpn_brute_force": 10})
        assert 0 <= result.score <= 1.0

    def test_pipeline_latency_sub_ms(self):
        from aionos.core.pattern_engines import PatternEnginePipeline
        pipe = PatternEnginePipeline()
        t0 = time.perf_counter()
        pipe.evaluate({"file_download": 10}, [{"type": "file_download"}])
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 5  # Well under 5ms


# =============================================================================
# ACTIVE USER STORE
# =============================================================================

class TestActiveUserStore:

    def test_record_and_retrieve(self):
        from aionos.core.precompute_daemon import ActiveUserStore
        store = ActiveUserStore()
        store.record_event("alice", "vpn_access")
        user = store.get_user("alice")
        assert user is not None
        assert user["event_counts"]["vpn_access"] == 1

    def test_multiple_events_accumulate(self):
        from aionos.core.precompute_daemon import ActiveUserStore
        store = ActiveUserStore()
        store.record_event("alice", "vpn_access")
        store.record_event("alice", "vpn_access")
        store.record_event("alice", "file_download")
        user = store.get_user("alice")
        assert user["event_counts"]["vpn_access"] == 2
        assert user["event_counts"]["file_download"] == 1

    def test_get_active_users(self):
        from aionos.core.precompute_daemon import ActiveUserStore
        store = ActiveUserStore(window_seconds=3600)
        store.record_event("alice", "vpn_access")
        store.record_event("bob", "file_download")
        active = store.get_active_users()
        assert len(active) == 2

    def test_prune_stale(self):
        from aionos.core.precompute_daemon import ActiveUserStore
        store = ActiveUserStore(window_seconds=0)  # Immediate expiry
        store.record_event("alice", "vpn_access")
        time.sleep(0.01)
        pruned = store.prune()
        assert pruned == 1
        assert store.size == 0


# =============================================================================
# PRECOMPUTE DAEMON
# =============================================================================

class TestPrecomputeDaemon:

    def test_daemon_starts_and_stops(self):
        from aionos.core.detection_cache import DetectionCache
        from aionos.core.precompute_daemon import PrecomputeDaemon, ActiveUserStore
        cache = DetectionCache()
        store = ActiveUserStore()
        daemon = PrecomputeDaemon(cache, store, interval_seconds=1)
        daemon.start()
        assert daemon.running
        daemon.stop()
        assert not daemon.running

    def test_daemon_warms_cache(self):
        from aionos.core.detection_cache import DetectionCache
        from aionos.core.precompute_daemon import PrecomputeDaemon, ActiveUserStore
        cache = DetectionCache()
        store = ActiveUserStore()
        # Inject a user with enough signal to cache
        for _ in range(20):
            store.record_event("attacker@firm.com", "file_download")
            store.record_event("attacker@firm.com", "bulk_operation")
        daemon = PrecomputeDaemon(cache, store, interval_seconds=1)
        daemon.start()
        time.sleep(2)  # Let one cycle run
        daemon.stop()
        assert cache.stats()["writes"] > 0

    def test_daemon_stats(self):
        from aionos.core.detection_cache import DetectionCache
        from aionos.core.precompute_daemon import PrecomputeDaemon, ActiveUserStore
        cache = DetectionCache()
        store = ActiveUserStore()
        daemon = PrecomputeDaemon(cache, store, interval_seconds=60)
        s = daemon.stats()
        assert "cycles" in s
        assert "active_users" in s


# =============================================================================
# HYBRID ENGINE INTEGRATION
# =============================================================================

class TestHybridWithCache:

    def test_hybrid_initializes_with_cache(self):
        from aionos.core.hybrid_engine import HybridDetectionEngine
        engine = HybridDetectionEngine(enable_gemini=False, enable_cache=True)
        assert engine.cache is not None
        assert engine.pattern_pipeline is not None
        engine.shutdown()

    def test_hybrid_cache_disabled(self):
        from aionos.core.hybrid_engine import HybridDetectionEngine
        engine = HybridDetectionEngine(enable_gemini=False, enable_cache=False)
        assert engine.cache is None
        engine.shutdown()

    def test_ingest_feeds_user_store(self):
        from aionos.core.hybrid_engine import HybridDetectionEngine
        from aionos.core.temporal_engine import SecurityEvent, EventType
        engine = HybridDetectionEngine(enable_gemini=False, enable_cache=True)
        event = SecurityEvent(
            event_id="e1", user_id="alice@firm.com",
            event_type=EventType.VPN_ACCESS,
            timestamp=datetime.utcnow(), source_system="test",
        )
        engine.ingest_event(event)
        user = engine.user_store.get_user("alice@firm.com")
        assert user is not None
        assert user["event_counts"]["vpn_access"] == 1
        engine.shutdown()

    def test_stats_include_cache(self):
        from aionos.core.hybrid_engine import HybridDetectionEngine
        engine = HybridDetectionEngine(enable_gemini=False, enable_cache=True)
        s = engine.stats
        assert "cache" in s
        assert "hit_rate" in s["cache"]
        engine.shutdown()

    def test_pattern_engine_eval_counted(self):
        from aionos.core.hybrid_engine import HybridDetectionEngine
        from aionos.core.temporal_engine import SecurityEvent, EventType
        engine = HybridDetectionEngine(enable_gemini=False, enable_cache=True)
        event = SecurityEvent(
            event_id="e1", user_id="bob@firm.com",
            event_type=EventType.FILE_DOWNLOAD,
            timestamp=datetime.utcnow(), source_system="test",
        )
        engine.ingest_event(event)
        assert engine.stats["pattern_engine_evals"] >= 1
        engine.shutdown()
