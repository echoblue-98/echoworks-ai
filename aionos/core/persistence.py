"""
AION OS - Persistence Layer
GEMINI RECOMMENDATION: Abstract storage to support Redis/SQL for multi-week tracking.

This module provides a storage abstraction that allows the TemporalCorrelationEngine
to persist state across restarts - critical for detecting "Typhoon" style attacks
that unfold over weeks.

Usage:
    # In-memory (default, for development)
    store = InMemoryStore()
    
    # JSON file (survives restarts, no dependencies)
    store = JsonFileStore(data_dir='./aion_data')
    
    # Redis (recommended for production)
    store = RedisStore(host='localhost', port=6379, db=0)
    
    # PostgreSQL (for compliance/audit requirements)
    store = PostgresStore(connection_string='...')
"""

import json
import logging
import time
import hashlib
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("aionos.persistence")

# Lazy encryption provider (loaded on first use)
_encryption_provider = None

def _get_encryption():
    """Get encryption provider (lazy import to avoid circular deps)."""
    global _encryption_provider
    if _encryption_provider is None:
        try:
            from aionos.security.encryption import get_encryption_provider
            _encryption_provider = get_encryption_provider()
        except ImportError:
            logger.debug("Encryption module not available — data stored in plaintext")
            _encryption_provider = "disabled"
    if _encryption_provider == "disabled":
        return None
    return _encryption_provider


def _encrypt_and_write(path: Path, data: str):
    """Write data to file, encrypting if provider is available and enabled."""
    enc = _get_encryption()
    if enc and enc.is_enabled():
        encrypted = enc.encrypt(data.encode("utf-8"))
        path.write_bytes(encrypted)
    else:
        path.write_text(data, encoding="utf-8")


def _read_and_decrypt(path: Path) -> str:
    """Read data from file, decrypting if needed. Backwards-compatible with plaintext."""
    enc = _get_encryption()
    if enc and enc.is_enabled():
        raw = path.read_bytes()
        try:
            return enc.decrypt(raw).decode("utf-8")
        except Exception:
            # Fallback: file was written before encryption was enabled
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError(f"Cannot decrypt {path} — wrong key or corrupted")
    return path.read_text(encoding="utf-8")


class EventStore(ABC):
    """
    Abstract base class for event storage backends.
    
    All implementations must support:
    - Store/retrieve events by user
    - TTL-based expiration
    - Atomic operations for consistency
    """
    
    @abstractmethod
    def store_event(self, user_id: str, event_data: Dict[str, Any]) -> bool:
        """Store a single event for a user. Returns True on success."""
        pass
    
    @abstractmethod
    def get_user_events(self, user_id: str, since_epoch: Optional[float] = None) -> List[Dict]:
        """Get all events for a user, optionally filtered by time."""
        pass
    
    @abstractmethod
    def get_user_events_by_type(self, user_id: str, event_type: str, since_epoch: Optional[float] = None) -> List[Dict]:
        """Get events of a specific type for a user."""
        pass
    
    @abstractmethod
    def delete_user_events(self, user_id: str, before_epoch: float) -> int:
        """Delete events older than timestamp. Returns count deleted."""
        pass
    
    @abstractmethod
    def get_all_users(self) -> List[str]:
        """Get list of all tracked user IDs."""
        pass
    
    @abstractmethod
    def get_user_count(self) -> int:
        """Get total number of tracked users."""
        pass
    
    @abstractmethod
    def get_event_count(self, user_id: Optional[str] = None) -> int:
        """Get event count, optionally for a specific user."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Ensure all pending writes are persisted."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass


class InMemoryStore(EventStore):
    """
    In-memory event storage for development and testing.
    
    WARNING: All data is lost on restart. Use RedisStore or PostgresStore
    for production deployments tracking multi-week attack patterns.
    """
    
    def __init__(self, max_events_per_user: int = 10000, max_users: int = 50000):
        self.events: Dict[str, List[Dict]] = {}
        self.events_by_type: Dict[str, Dict[str, List[Dict]]] = {}
        self.max_events_per_user = max_events_per_user
        self.max_users = max_users
        logger.info("InMemoryStore initialized (data will not persist across restarts)")
    
    def store_event(self, user_id: str, event_data: Dict[str, Any]) -> bool:
        if user_id not in self.events:
            if len(self.events) >= self.max_users:
                logger.warning(f"Max users ({self.max_users}) reached, rejecting new user")
                return False
            self.events[user_id] = []
            self.events_by_type[user_id] = {}
        
        # Enforce per-user limit
        if len(self.events[user_id]) >= self.max_events_per_user:
            # Evict oldest 20%
            keep = int(self.max_events_per_user * 0.8)
            self.events[user_id] = self.events[user_id][-keep:]
        
        self.events[user_id].append(event_data)
        
        # Index by type
        event_type = event_data.get('event_type', 'unknown')
        if event_type not in self.events_by_type[user_id]:
            self.events_by_type[user_id][event_type] = []
        self.events_by_type[user_id][event_type].append(event_data)
        
        return True
    
    def get_user_events(self, user_id: str, since_epoch: Optional[float] = None) -> List[Dict]:
        events = self.events.get(user_id, [])
        if since_epoch:
            events = [e for e in events if e.get('ts_epoch', 0) >= since_epoch]
        return events
    
    def get_user_events_by_type(self, user_id: str, event_type: str, since_epoch: Optional[float] = None) -> List[Dict]:
        type_events = self.events_by_type.get(user_id, {}).get(event_type, [])
        if since_epoch:
            type_events = [e for e in type_events if e.get('ts_epoch', 0) >= since_epoch]
        return type_events
    
    def delete_user_events(self, user_id: str, before_epoch: float) -> int:
        if user_id not in self.events:
            return 0
        original = len(self.events[user_id])
        self.events[user_id] = [e for e in self.events[user_id] if e.get('ts_epoch', 0) >= before_epoch]
        deleted = original - len(self.events[user_id])
        
        # Also clean type index
        if user_id in self.events_by_type:
            for event_type in self.events_by_type[user_id]:
                self.events_by_type[user_id][event_type] = [
                    e for e in self.events_by_type[user_id][event_type]
                    if e.get('ts_epoch', 0) >= before_epoch
                ]
        
        return deleted
    
    def get_all_users(self) -> List[str]:
        return list(self.events.keys())
    
    def get_user_count(self) -> int:
        return len(self.events)
    
    def get_event_count(self, user_id: Optional[str] = None) -> int:
        if user_id:
            return len(self.events.get(user_id, []))
        return sum(len(events) for events in self.events.values())
    
    def flush(self) -> None:
        pass  # No-op for in-memory
    
    def close(self) -> None:
        self.events.clear()
        self.events_by_type.clear()


class JsonFileStore(EventStore):
    """
    JSON file-backed event storage that survives restarts.
    
    No external dependencies. Data stored as one JSON file per user.
    Auto-saves on a configurable interval, with write-ahead flushing.
    
    Good for:
    - Development with persistence
    - Single-server deployments
    - Windows environments without Redis
    
    Directory structure:
        data_dir/
        ├── events/
        │   ├── user1@firm.com.json
        │   └── user2@firm.com.json
        └── reports/
            ├── report_<hash>.json
            └── report_<hash>.json
    """
    
    def __init__(self, data_dir: str = './aion_data', max_events_per_user: int = 10000, 
                 auto_save_interval: int = 30):
        self.data_dir = Path(data_dir)
        self.events_dir = self.data_dir / 'events'
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_events_per_user = max_events_per_user
        self.auto_save_interval = auto_save_interval
        
        # In-memory cache (loaded from disk on init)
        self.events: Dict[str, List[Dict]] = {}
        self.events_by_type: Dict[str, Dict[str, List[Dict]]] = {}
        self._dirty_users: set = set()  # Users with unsaved changes
        
        # Load existing data
        self._load_all()
        
        # Auto-save thread
        self._save_lock = threading.Lock()
        self._running = True
        self._save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self._save_thread.start()
        
        logger.info(f"JsonFileStore initialized: {self.data_dir} ({self.get_user_count()} users, {self.get_event_count()} events loaded)")
    
    def _user_file(self, user_id: str) -> Path:
        """Get file path for a user (sanitize email to filename)"""
        safe_name = user_id.replace('@', '_at_').replace('.', '_')
        return self.events_dir / f"{safe_name}.json"
    
    def _load_all(self):
        """Load all user events from disk (decrypting if encryption is enabled)"""
        for f in self.events_dir.glob('*.json'):
            try:
                text = _read_and_decrypt(f)
                data = json.loads(text)
                user_id = data.get('user_id', f.stem)
                events = data.get('events', [])
                self.events[user_id] = events
                
                # Rebuild type index
                self.events_by_type[user_id] = {}
                for evt in events:
                    etype = evt.get('event_type', 'unknown')
                    if etype not in self.events_by_type[user_id]:
                        self.events_by_type[user_id][etype] = []
                    self.events_by_type[user_id][etype].append(evt)
            except Exception as e:
                logger.warning(f"Failed to load {f}: {e}")
    
    def _save_user(self, user_id: str):
        """Save a single user's events to disk (encrypted if provider is enabled)"""
        try:
            data = {
                'user_id': user_id,
                'events': self.events.get(user_id, []),
                'updated_at': time.time()
            }
            _encrypt_and_write(
                self._user_file(user_id),
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.error(f"Failed to save user {user_id}: {e}")
    
    def _auto_save_loop(self):
        """Background thread that periodically saves dirty users"""
        while self._running:
            time.sleep(self.auto_save_interval)
            self.flush()
    
    def store_event(self, user_id: str, event_data: Dict[str, Any]) -> bool:
        if user_id not in self.events:
            self.events[user_id] = []
            self.events_by_type[user_id] = {}
        
        # Enforce per-user limit
        if len(self.events[user_id]) >= self.max_events_per_user:
            keep = int(self.max_events_per_user * 0.8)
            self.events[user_id] = self.events[user_id][-keep:]
        
        self.events[user_id].append(event_data)
        
        # Type index
        event_type = event_data.get('event_type', 'unknown')
        if event_type not in self.events_by_type[user_id]:
            self.events_by_type[user_id][event_type] = []
        self.events_by_type[user_id][event_type].append(event_data)
        
        self._dirty_users.add(user_id)
        return True
    
    def get_user_events(self, user_id: str, since_epoch: Optional[float] = None) -> List[Dict]:
        events = self.events.get(user_id, [])
        if since_epoch:
            events = [e for e in events if e.get('ts_epoch', 0) >= since_epoch]
        return events
    
    def get_user_events_by_type(self, user_id: str, event_type: str, since_epoch: Optional[float] = None) -> List[Dict]:
        type_events = self.events_by_type.get(user_id, {}).get(event_type, [])
        if since_epoch:
            type_events = [e for e in type_events if e.get('ts_epoch', 0) >= since_epoch]
        return type_events
    
    def delete_user_events(self, user_id: str, before_epoch: float) -> int:
        if user_id not in self.events:
            return 0
        original = len(self.events[user_id])
        self.events[user_id] = [e for e in self.events[user_id] if e.get('ts_epoch', 0) >= before_epoch]
        deleted = original - len(self.events[user_id])
        
        if user_id in self.events_by_type:
            for etype in self.events_by_type[user_id]:
                self.events_by_type[user_id][etype] = [
                    e for e in self.events_by_type[user_id][etype]
                    if e.get('ts_epoch', 0) >= before_epoch
                ]
        
        if deleted > 0:
            self._dirty_users.add(user_id)
        return deleted
    
    def get_all_users(self) -> List[str]:
        return list(self.events.keys())
    
    def get_user_count(self) -> int:
        return len(self.events)
    
    def get_event_count(self, user_id: Optional[str] = None) -> int:
        if user_id:
            return len(self.events.get(user_id, []))
        return sum(len(events) for events in self.events.values())
    
    def flush(self) -> None:
        """Save all dirty users to disk"""
        with self._save_lock:
            dirty = self._dirty_users.copy()
            self._dirty_users.clear()
        
        for user_id in dirty:
            self._save_user(user_id)
        
        if dirty:
            logger.debug(f"JsonFileStore flushed {len(dirty)} users to disk")
    
    def close(self) -> None:
        self._running = False
        self.flush()  # Final save
        self.events.clear()
        self.events_by_type.clear()
        logger.info("JsonFileStore closed")


# =============================================================================
# FORENSIC REPORT STORE — Persists LLM-generated reports for case history
# =============================================================================

class ReportStore:
    """
    Stores forensic reports with user-level history for case-level LLM memory.
    
    Each report is stored with:
    - user_id: who was investigated
    - attack_id: what scenario triggered it
    - timestamp: when it was generated
    - report: the full ForensicReport data
    - summary: a compact text summary for injecting into future LLM prompts
    
    Supports both in-memory and JSON file persistence.
    """
    
    def __init__(self, data_dir: str = './aion_data'):
        self.data_dir = Path(data_dir)
        self.reports_dir = self.data_dir / 'reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Index: user_id -> list of report metadata
        self.user_reports: Dict[str, List[Dict]] = {}
        
        # Metering: total reports generated
        self.meter_file = self.data_dir / 'meter.json'
        self.meter: Dict[str, Any] = self._load_meter()
        
        # Load existing reports
        self._load_index()
        
        logger.info(f"ReportStore initialized: {len(self._all_report_ids())} reports, "
                     f"meter: {self.meter.get('total_reports', 0)} total")
    
    def _load_meter(self) -> Dict[str, Any]:
        """Load or create the metering file (decrypting if needed)"""
        if self.meter_file.exists():
            try:
                text = _read_and_decrypt(self.meter_file)
                return json.loads(text)
            except:
                pass
        return {
            'total_reports': 0,
            'reports_by_month': {},
            'reports_by_user': {},
            'created_at': datetime.now().isoformat()
        }
    
    def _save_meter(self):
        """Persist meter to disk (encrypted if provider is enabled)"""
        _encrypt_and_write(self.meter_file, json.dumps(self.meter, indent=2, default=str))
    
    def _load_index(self):
        """Load report index from disk (decrypting if needed)"""
        index_file = self.reports_dir / '_index.json'
        if index_file.exists():
            try:
                text = _read_and_decrypt(index_file)
                self.user_reports = json.loads(text)
            except:
                self.user_reports = {}
    
    def _save_index(self):
        """Save report index (encrypted if provider is enabled)"""
        index_file = self.reports_dir / '_index.json'
        _encrypt_and_write(index_file, json.dumps(self.user_reports, indent=2, default=str))
    
    def _all_report_ids(self) -> List[str]:
        """Get all report IDs"""
        ids = []
        for user_reports in self.user_reports.values():
            for r in user_reports:
                ids.append(r.get('report_id', ''))
        return ids
    
    def store_report(self, user_id: str, attack_id: str, report: Dict[str, Any], 
                     scenario_name: str = '') -> str:
        """
        Store a forensic report and update metering.
        
        Returns:
            report_id for future reference
        """
        report_id = hashlib.sha256(
            f"{user_id}:{attack_id}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        timestamp = datetime.now().isoformat()
        month_key = datetime.now().strftime('%Y-%m')
        
        # Build compact summary for LLM context injection
        vuln_summaries = []
        for v in report.get('vulnerabilities', [])[:5]:
            vuln_summaries.append(f"  - [{v.get('severity', 'UNKNOWN')}] {v.get('title', 'Unknown')}")
        
        summary = (
            f"Report {report_id} ({timestamp}): {scenario_name or attack_id}\n"
            f"  Risk Score: {report.get('risk_score', 0)}/100\n"
            f"  Vulnerabilities found:\n" + '\n'.join(vuln_summaries) + "\n"
            f"  Actions: {', '.join(report.get('immediate_actions', [])[:3])}"
        )
        
        # Store full report
        report_data = {
            'report_id': report_id,
            'user_id': user_id,
            'attack_id': attack_id,
            'scenario_name': scenario_name,
            'timestamp': timestamp,
            'report': report,
            'summary': summary
        }
        
        report_file = self.reports_dir / f"{report_id}.json"
        _encrypt_and_write(report_file, json.dumps(report_data, indent=2, default=str))
        
        # Update user index
        if user_id not in self.user_reports:
            self.user_reports[user_id] = []
        self.user_reports[user_id].append({
            'report_id': report_id,
            'attack_id': attack_id,
            'scenario_name': scenario_name,
            'timestamp': timestamp,
            'risk_score': report.get('risk_score', 0),
            'summary': summary
        })
        self._save_index()
        
        # Update meter
        self.meter['total_reports'] = self.meter.get('total_reports', 0) + 1
        self.meter['reports_by_month'][month_key] = self.meter.get('reports_by_month', {}).get(month_key, 0) + 1
        self.meter['reports_by_user'][user_id] = self.meter.get('reports_by_user', {}).get(user_id, 0) + 1
        self.meter['last_report_at'] = timestamp
        self._save_meter()
        
        logger.info(f"Report stored: {report_id} for {user_id} (total: {self.meter['total_reports']})")
        return report_id
    
    def get_user_history(self, user_id: str, max_reports: int = 10) -> List[Dict]:
        """Get recent report metadata for a user (for LLM context injection)"""
        reports = self.user_reports.get(user_id, [])
        return reports[-max_reports:]  # Most recent
    
    def get_user_summaries(self, user_id: str, max_reports: int = 5) -> str:
        """
        Get compact text summaries of prior reports for a user.
        Designed to be injected directly into LLM prompts for case-level memory.
        """
        reports = self.get_user_history(user_id, max_reports)
        if not reports:
            return ""
        
        lines = [f"PRIOR INVESTIGATION HISTORY ({len(reports)} reports):"]
        for r in reports:
            lines.append(r.get('summary', f"  Report {r.get('report_id', '?')} - {r.get('timestamp', '?')}"))
        return '\n'.join(lines)
    
    def get_full_report(self, report_id: str) -> Optional[Dict]:
        """Load a full report from disk (decrypting if needed)"""
        report_file = self.reports_dir / f"{report_id}.json"
        if report_file.exists():
            text = _read_and_decrypt(report_file)
            return json.loads(text)
        return None
    
    def get_meter(self) -> Dict[str, Any]:
        """Get current metering data"""
        return self.meter.copy()


class RedisStore(EventStore):
    """
    Redis-backed event storage for production deployments.
    
    Features:
    - Automatic TTL expiration (no manual purging needed)
    - Persistence across restarts (RDB/AOF)
    - Horizontal scaling via Redis Cluster
    - Sub-millisecond latency
    
    Requirements:
    - pip install redis
    - Redis server running
    
    Schema:
    - events:{user_id} -> Sorted set (score=timestamp, value=event JSON)
    - events:{user_id}:{event_type} -> Sorted set for type-indexed queries
    """
    
    def __init__(
        self, 
        host: str = 'localhost', 
        port: int = 6379, 
        db: int = 0,
        password: Optional[str] = None,
        ttl_days: int = 30,
        key_prefix: str = 'aion:'
    ):
        self.ttl_seconds = ttl_days * 86400
        self.key_prefix = key_prefix
        
        try:
            import redis
            self.redis = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                password=password,
                decode_responses=True
            )
            self.redis.ping()
            logger.info(f"RedisStore connected to {host}:{port}/{db}")
        except ImportError:
            logger.error("redis package not installed. Run: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def _user_key(self, user_id: str) -> str:
        return f"{self.key_prefix}events:{user_id}"
    
    def _type_key(self, user_id: str, event_type: str) -> str:
        return f"{self.key_prefix}events:{user_id}:{event_type}"
    
    def store_event(self, user_id: str, event_data: Dict[str, Any]) -> bool:
        try:
            ts_epoch = event_data.get('ts_epoch', time.time())
            event_json = json.dumps(event_data)
            event_type = event_data.get('event_type', 'unknown')
            
            pipe = self.redis.pipeline()
            
            # Add to user's event set
            user_key = self._user_key(user_id)
            pipe.zadd(user_key, {event_json: ts_epoch})
            pipe.expire(user_key, self.ttl_seconds)
            
            # Add to type-indexed set
            type_key = self._type_key(user_id, event_type)
            pipe.zadd(type_key, {event_json: ts_epoch})
            pipe.expire(type_key, self.ttl_seconds)
            
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis store_event failed: {e}")
            return False
    
    def get_user_events(self, user_id: str, since_epoch: Optional[float] = None) -> List[Dict]:
        try:
            user_key = self._user_key(user_id)
            min_score = since_epoch if since_epoch else '-inf'
            events_json = self.redis.zrangebyscore(user_key, min_score, '+inf')
            return [json.loads(e) for e in events_json]
        except Exception as e:
            logger.error(f"Redis get_user_events failed: {e}")
            return []
    
    def get_user_events_by_type(self, user_id: str, event_type: str, since_epoch: Optional[float] = None) -> List[Dict]:
        try:
            type_key = self._type_key(user_id, event_type)
            min_score = since_epoch if since_epoch else '-inf'
            events_json = self.redis.zrangebyscore(type_key, min_score, '+inf')
            return [json.loads(e) for e in events_json]
        except Exception as e:
            logger.error(f"Redis get_user_events_by_type failed: {e}")
            return []
    
    def delete_user_events(self, user_id: str, before_epoch: float) -> int:
        try:
            user_key = self._user_key(user_id)
            deleted = self.redis.zremrangebyscore(user_key, '-inf', before_epoch)
            
            # Also clean type-indexed keys (scan for pattern)
            pattern = f"{self.key_prefix}events:{user_id}:*"
            for key in self.redis.scan_iter(match=pattern):
                self.redis.zremrangebyscore(key, '-inf', before_epoch)
            
            return deleted
        except Exception as e:
            logger.error(f"Redis delete_user_events failed: {e}")
            return 0
    
    def get_all_users(self) -> List[str]:
        try:
            pattern = f"{self.key_prefix}events:*"
            users = set()
            for key in self.redis.scan_iter(match=pattern):
                # Extract user_id from key
                parts = key.replace(self.key_prefix, '').split(':')
                if len(parts) >= 2:
                    users.add(parts[1])
            return list(users)
        except Exception as e:
            logger.error(f"Redis get_all_users failed: {e}")
            return []
    
    def get_user_count(self) -> int:
        return len(self.get_all_users())
    
    def get_event_count(self, user_id: Optional[str] = None) -> int:
        try:
            if user_id:
                return self.redis.zcard(self._user_key(user_id))
            # Sum across all users
            total = 0
            for user in self.get_all_users():
                total += self.redis.zcard(self._user_key(user))
            return total
        except Exception as e:
            logger.error(f"Redis get_event_count failed: {e}")
            return 0
    
    def flush(self) -> None:
        # Redis handles persistence automatically
        pass
    
    def close(self) -> None:
        self.redis.close()


class PostgresStore(EventStore):
    """
    PostgreSQL-backed event storage for compliance/audit requirements.
    
    Features:
    - Full ACID compliance
    - Complex queries for investigations
    - Long-term retention policies
    - Native JSON support
    
    Requirements:
    - pip install psycopg2-binary
    - PostgreSQL server with schema created
    
    Schema (run once):
    ```sql
    CREATE TABLE security_events (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(256) NOT NULL,
        event_type VARCHAR(64) NOT NULL,
        event_data JSONB NOT NULL,
        ts_epoch DOUBLE PRECISION NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_time (user_id, ts_epoch),
        INDEX idx_user_type (user_id, event_type)
    );
    ```
    """
    
    def __init__(self, connection_string: str, ttl_days: int = 30):
        self.connection_string = connection_string
        self.ttl_days = ttl_days
        
        try:
            import psycopg2
            self.conn = psycopg2.connect(connection_string)
            logger.info("PostgresStore connected")
        except ImportError:
            logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
            raise
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def store_event(self, user_id: str, event_data: Dict[str, Any]) -> bool:
        try:
            import psycopg2.extras
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO security_events (user_id, event_type, event_data, ts_epoch)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        event_data.get('event_type', 'unknown'),
                        json.dumps(event_data),
                        event_data.get('ts_epoch', time.time())
                    )
                )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL store_event failed: {e}")
            self.conn.rollback()
            return False
    
    def get_user_events(self, user_id: str, since_epoch: Optional[float] = None) -> List[Dict]:
        try:
            with self.conn.cursor() as cur:
                if since_epoch:
                    cur.execute(
                        "SELECT event_data FROM security_events WHERE user_id = %s AND ts_epoch >= %s ORDER BY ts_epoch",
                        (user_id, since_epoch)
                    )
                else:
                    cur.execute(
                        "SELECT event_data FROM security_events WHERE user_id = %s ORDER BY ts_epoch",
                        (user_id,)
                    )
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"PostgreSQL get_user_events failed: {e}")
            return []
    
    def get_user_events_by_type(self, user_id: str, event_type: str, since_epoch: Optional[float] = None) -> List[Dict]:
        try:
            with self.conn.cursor() as cur:
                if since_epoch:
                    cur.execute(
                        "SELECT event_data FROM security_events WHERE user_id = %s AND event_type = %s AND ts_epoch >= %s ORDER BY ts_epoch",
                        (user_id, event_type, since_epoch)
                    )
                else:
                    cur.execute(
                        "SELECT event_data FROM security_events WHERE user_id = %s AND event_type = %s ORDER BY ts_epoch",
                        (user_id, event_type)
                    )
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"PostgreSQL get_user_events_by_type failed: {e}")
            return []
    
    def delete_user_events(self, user_id: str, before_epoch: float) -> int:
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM security_events WHERE user_id = %s AND ts_epoch < %s",
                    (user_id, before_epoch)
                )
                deleted = cur.rowcount
            self.conn.commit()
            return deleted
        except Exception as e:
            logger.error(f"PostgreSQL delete_user_events failed: {e}")
            self.conn.rollback()
            return 0
    
    def get_all_users(self) -> List[str]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT DISTINCT user_id FROM security_events")
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"PostgreSQL get_all_users failed: {e}")
            return []
    
    def get_user_count(self) -> int:
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(DISTINCT user_id) FROM security_events")
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"PostgreSQL get_user_count failed: {e}")
            return 0
    
    def get_event_count(self, user_id: Optional[str] = None) -> int:
        try:
            with self.conn.cursor() as cur:
                if user_id:
                    cur.execute("SELECT COUNT(*) FROM security_events WHERE user_id = %s", (user_id,))
                else:
                    cur.execute("SELECT COUNT(*) FROM security_events")
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"PostgreSQL get_event_count failed: {e}")
            return 0
    
    def flush(self) -> None:
        self.conn.commit()
    
    def close(self) -> None:
        self.conn.close()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_store(backend: str = 'auto', **kwargs) -> EventStore:
    """
    Factory function to create the appropriate event store.
    
    Args:
        backend: 'auto', 'memory', 'json', 'redis', or 'postgres'
        **kwargs: Backend-specific configuration
    
    Returns:
        Configured EventStore instance
    
    Examples:
        # Auto-detect (Redis > JSON > Memory)
        store = create_store('auto')
        
        # JSON file persistence (no dependencies)
        store = create_store('json', data_dir='./aion_data')
        
        # Production with Redis
        store = create_store('redis', host='redis.prod.internal', password='secret')
    """
    if backend == 'auto':
        # Try Redis first, fall back to JSON file store
        try:
            import redis as redis_lib
            r = redis_lib.Redis(**{k: v for k, v in kwargs.items() if k in ('host', 'port', 'db', 'password')})
            r.ping()
            logger.info("Auto-detected Redis — using RedisStore")
            return RedisStore(**kwargs)
        except:
            logger.info("Redis unavailable — using JsonFileStore (data persists across restarts)")
            return JsonFileStore(**{k: v for k, v in kwargs.items() if k in ('data_dir', 'max_events_per_user', 'auto_save_interval')})
    elif backend == 'memory':
        return InMemoryStore(**kwargs)
    elif backend == 'json':
        return JsonFileStore(**kwargs)
    elif backend == 'redis':
        return RedisStore(**kwargs)
    elif backend == 'postgres':
        return PostgresStore(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'auto', 'memory', 'json', 'redis', or 'postgres'")


# =============================================================================
# DEMO / TEST
# =============================================================================

if __name__ == "__main__":
    print("=== AION OS Persistence Layer ===")
    print()
    
    # Test in-memory store
    store = create_store('memory')
    
    # Store some test events
    test_events = [
        {"user_id": "alice@firm.com", "event_type": "vpn_access", "ts_epoch": time.time() - 3600},
        {"user_id": "alice@firm.com", "event_type": "file_download", "ts_epoch": time.time() - 1800},
        {"user_id": "alice@firm.com", "event_type": "database_query", "ts_epoch": time.time()},
        {"user_id": "bob@firm.com", "event_type": "vpn_access", "ts_epoch": time.time()},
    ]
    
    for event in test_events:
        store.store_event(event["user_id"], event)
    
    print(f"Stored {len(test_events)} events")
    print(f"Users: {store.get_user_count()}")
    print(f"Total events: {store.get_event_count()}")
    print(f"Alice's events: {store.get_event_count('alice@firm.com')}")
    print()
    
    # Test retrieval
    alice_events = store.get_user_events("alice@firm.com")
    print(f"Retrieved {len(alice_events)} events for Alice:")
    for e in alice_events:
        print(f"  - {e['event_type']}")
    print()
    
    # Test type-filtered retrieval
    vpn_events = store.get_user_events_by_type("alice@firm.com", "vpn_access")
    print(f"Alice's VPN events: {len(vpn_events)}")
    print()
    
    print("✓ Persistence layer ready for production")
    print()
    print("To enable Redis persistence:")
    print("  1. pip install redis")
    print("  2. store = create_store('redis', host='localhost')")
    print()
    print("To enable PostgreSQL persistence:")
    print("  1. pip install psycopg2-binary")
    print("  2. Run the SQL schema (see docstring)")
    print("  3. store = create_store('postgres', connection_string='...')")
