"""
AION OS — Detection Result Cache
=================================

LRU + TTL cache for detection pipeline results.
Eliminates redundant LLM calls and pattern re-computation.

Performance target:
  - Cache HIT:  < 50μs  (instant for demos)
  - Cache MISS: falls through to full pipeline

Architecture:
  ┌────────────┐     HIT (< 50μs)     ┌──────────────┐
  │  Inbound   │ ───────────────────▶  │  Cached      │
  │  Event     │                       │  Result      │
  └─────┬──────┘                       └──────────────┘
        │ MISS
        ▼
  ┌────────────────┐
  │  Full Pipeline │  (pattern engines → LLM if needed)
  │  + cache write │
  └────────────────┘

Cache keys are content-hashed (SHA-256 of normalized input).
No PII stored in cache keys — only event-type fingerprints.
"""

import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class CacheEntry:
    """Single cached detection result."""
    key: str
    result: Dict[str, Any]
    created_at: float          # epoch
    expires_at: float          # epoch
    hit_count: int = 0
    source: str = "pipeline"   # pipeline | precompute | daemon


class DetectionCache:
    """
    Thread-safe LRU + TTL cache for detection results.

    Parameters:
        max_entries: Maximum items before LRU eviction (default 2048)
        ttl_seconds: Time-to-live per entry (default 1 hour)
    """

    def __init__(self, max_entries: int = 2048, ttl_seconds: int = 3600):
        self._max = max_entries
        self._ttl = ttl_seconds
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired": 0,
            "writes": 0,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result. Returns None on miss or expiry."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            now = time.time()
            if now > entry.expires_at:
                # Expired — remove silently
                del self._store[key]
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                return None

            # Hit — move to end (most-recently-used)
            self._store.move_to_end(key)
            entry.hit_count += 1
            self._stats["hits"] += 1
            return entry.result

    def put(self, key: str, result: Dict[str, Any], source: str = "pipeline") -> None:
        """Store a detection result."""
        now = time.time()
        with self._lock:
            if key in self._store:
                # Update existing
                self._store[key].result = result
                self._store[key].expires_at = now + self._ttl
                self._store[key].source = source
                self._store.move_to_end(key)
            else:
                # Evict LRU if at capacity
                while len(self._store) >= self._max:
                    self._store.popitem(last=False)
                    self._stats["evictions"] += 1

                self._store[key] = CacheEntry(
                    key=key,
                    result=result,
                    created_at=now,
                    expires_at=now + self._ttl,
                    source=source,
                )
            self._stats["writes"] += 1

    def invalidate(self, key: str) -> bool:
        """Remove a specific entry. Returns True if it existed."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> int:
        """Flush all entries. Returns count removed."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def stats(self) -> Dict[str, Any]:
        """Return cache performance metrics."""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            return {
                **self._stats,
                "size": len(self._store),
                "max_entries": self._max,
                "ttl_seconds": self._ttl,
                "hit_rate": (self._stats["hits"] / total) if total > 0 else 0.0,
            }

    # ------------------------------------------------------------------
    # Key generation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def make_key(event_types: List[str], user_id: str = "",
                 context_hash: str = "") -> str:
        """
        Build a deterministic, PII-free cache key.

        Uses SHA-256 of sorted event-type fingerprint.
        user_id is hashed (never stored raw).
        """
        fingerprint = {
            "types": sorted(event_types),
            "user": hashlib.sha256(user_id.encode()).hexdigest()[:16] if user_id else "",
            "ctx": context_hash,
        }
        raw = json.dumps(fingerprint, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def make_analysis_key(content: str, intensity: int = 3,
                          analysis_type: str = "general") -> str:
        """
        Build cache key for LLM analysis requests.

        Normalizes whitespace so trivial reformats still hit cache.
        """
        normalized = " ".join(content.lower().split())
        fingerprint = {
            "content": hashlib.sha256(normalized.encode()).hexdigest(),
            "intensity": intensity,
            "type": analysis_type,
        }
        raw = json.dumps(fingerprint, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()
