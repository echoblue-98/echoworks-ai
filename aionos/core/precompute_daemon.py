"""
AION OS — Background Pre-compute Daemon
=========================================

Keeps the cache warm by periodically re-evaluating active users
through the pattern engines. When Dan demos, results are INSTANT
because the daemon already computed them.

Architecture:
  ┌──────────────────────┐
  │  PrecomputeDaemon    │
  │  (background thread) │
  └──────┬───────────────┘
         │ every N seconds
         ▼
  ┌──────────────────────┐     ┌──────────────────┐
  │  Active User Store   │────▶│  PatternPipeline │
  │  (recent events)     │     │  (4 engines)     │
  └──────────────────────┘     └────────┬─────────┘
                                        │
                               ┌────────▼─────────┐
                               │ DetectionCache    │
                               │ (warm results)    │
                               └──────────────────┘

Daemon is opt-in. Disabled by default in tests.
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from .detection_cache import DetectionCache
from .pattern_engines import PatternEnginePipeline, EngineScore

logger = logging.getLogger("aionos.daemon")


class ActiveUserStore:
    """
    Tracks recently active users and their event counts.

    Thread-safe. The daemon reads this; the ingestion pipeline writes it.
    """

    def __init__(self, window_seconds: int = 3600):
        self._window = window_seconds
        self._lock = threading.Lock()
        # user_id → {"event_counts": {type: count}, "events": [...], "last_seen": epoch}
        self._users: Dict[str, Dict[str, Any]] = {}

    def record_event(self, user_id: str, event_type: str,
                     event_data: Optional[Dict] = None) -> None:
        """Record a new event for a user."""
        now = time.time()
        with self._lock:
            if user_id not in self._users:
                self._users[user_id] = {
                    "event_counts": defaultdict(int),
                    "events": [],
                    "last_seen": now,
                    "trust": 1.0,
                }
            entry = self._users[user_id]
            entry["event_counts"][event_type] += 1
            entry["events"].append({"type": event_type, **(event_data or {})})
            # Keep bounded
            if len(entry["events"]) > 200:
                entry["events"] = entry["events"][-200:]
            entry["last_seen"] = now

    def get_active_users(self) -> Dict[str, Dict[str, Any]]:
        """Return snapshot of users active within the window."""
        cutoff = time.time() - self._window
        with self._lock:
            return {
                uid: dict(data)
                for uid, data in self._users.items()
                if data["last_seen"] >= cutoff
            }

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._users.get(user_id)
            return dict(data) if data else None

    def prune(self) -> int:
        """Remove stale users. Returns count removed."""
        cutoff = time.time() - self._window
        with self._lock:
            stale = [uid for uid, d in self._users.items() if d["last_seen"] < cutoff]
            for uid in stale:
                del self._users[uid]
            return len(stale)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._users)


class PrecomputeDaemon:
    """
    Background daemon that keeps pattern engine results cache-warm.

    Parameters:
        cache: DetectionCache instance to write warm results into
        user_store: ActiveUserStore tracking recent events
        interval_seconds: How often to re-evaluate (default 30s)
    """

    def __init__(
        self,
        cache: DetectionCache,
        user_store: ActiveUserStore,
        interval_seconds: int = 30,
    ):
        self.cache = cache
        self.user_store = user_store
        self.interval = interval_seconds
        self.pipeline = PatternEnginePipeline()

        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._stats = {
            "cycles": 0,
            "users_evaluated": 0,
            "cache_writes": 0,
            "errors": 0,
        }

    def start(self) -> None:
        """Start the background daemon thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="aion-precompute"
        )
        self._thread.start()
        logger.info(f"PrecomputeDaemon started (interval={self.interval}s)")

    def stop(self) -> None:
        """Stop the daemon gracefully."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.interval + 5)
        logger.info("PrecomputeDaemon stopped")

    def _run_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._evaluate_cycle()
            except Exception as e:
                self._stats["errors"] += 1
                logger.error(f"Daemon cycle error: {e}")
            self._stop.wait(self.interval)

    def _evaluate_cycle(self) -> None:
        """Run one evaluation cycle over all active users."""
        active = self.user_store.get_active_users()
        self._stats["cycles"] += 1

        for user_id, data in active.items():
            event_counts = dict(data.get("event_counts", {}))
            trust_events = data.get("events", [])
            trust_level = data.get("trust", 1.0)

            # Build cache key
            key = DetectionCache.make_key(
                list(event_counts.keys()), user_id=user_id
            )

            # Quick evaluation (proximity + phase only for daemon)
            result = self.pipeline.evaluate_quick(event_counts)

            # Only cache if there's meaningful signal
            if result.score > 0.1:
                self.cache.put(key, {
                    "score": result.score,
                    "confidence": result.confidence,
                    "signals": result.signals,
                    "engine": result.engine,
                    "band": result.score >= 0.85 and "CRITICAL" or
                            result.score >= 0.60 and "HIGH" or
                            result.score >= 0.35 and "MEDIUM" or "LOW",
                    "precomputed": True,
                    "daemon_cycle": self._stats["cycles"],
                }, source="daemon")
                self._stats["cache_writes"] += 1

            self._stats["users_evaluated"] += 1

        # Prune stale users periodically
        if self._stats["cycles"] % 10 == 0:
            pruned = self.user_store.prune()
            if pruned:
                logger.info(f"Daemon pruned {pruned} stale users")

    def stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "active_users": self.user_store.size,
            "cache_stats": self.cache.stats(),
            "running": self._thread.is_alive() if self._thread else False,
        }

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
