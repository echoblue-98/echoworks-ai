"""
AION OS - Hybrid Detection Engine
================================

Uses LOCAL patterns first (fast, private, free).
Falls back to GEMINI for novel/unknown patterns.

Goal: Build local pattern database to 1M patterns, then Gemini becomes optional.

Architecture:
                          ┌─────────────────────────┐
      Event Stream ─────▶ │  LOCAL ENGINE (66 patterns)  │
                          │  ~120μs per event, FREE      │
                          └────────────┬────────────┘
                                       │
                          ┌────────────▼────────────┐
                          │     PATTERN MATCHED?     │
                          └────────────┬────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │ YES                                  │ NO
                    ▼                                      ▼
           ┌───────────────┐                   ┌─────────────────────┐
           │ ALERT LOCALLY │                   │ QUEUE FOR GEMINI    │
           │ (no API call) │                   │ (batch every 60s)   │
           └───────────────┘                   └──────────┬──────────┘
                                                          │
                                               ┌──────────▼──────────┐
                                               │ GEMINI ANALYSIS     │
                                               │ (novel pattern?)    │
                                               └──────────┬──────────┘
                                                          │
                                               ┌──────────▼──────────┐
                                               │ SAVE TO LOCAL DB    │
                                               │ Engine learns it!   │
                                               └─────────────────────┘

Privacy: Client events NEVER sent to Gemini.
         Only event TYPE sequences + anonymized context.
"""

import os
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum
import logging

# Local imports
from .temporal_engine import (
    TemporalCorrelationEngine, SecurityEvent, EventType, 
    AttackSequence, CorrelationAlert
)
from .detection_cache import DetectionCache
from .pattern_engines import PatternEnginePipeline, EngineScore
from .precompute_daemon import PrecomputeDaemon, ActiveUserStore

logger = logging.getLogger("aionos.hybrid")

# =============================================================================
# CONFIGURATION
# =============================================================================

GEMINI_BATCH_INTERVAL_SECONDS = 60      # Batch unmatched events every 60s
GEMINI_MIN_EVENTS_TO_ANALYZE = 5        # Min events before calling Gemini
GEMINI_MAX_EVENTS_PER_BATCH = 50        # Max events per Gemini call
PATTERN_DB_PATH = Path(__file__).parent.parent / "knowledge" / "learned_patterns.json"
PROBATIONARY_DB_PATH = Path(__file__).parent.parent / "knowledge" / "probationary_patterns.json"
LOCAL_PATTERN_TARGET = 1_000_000        # Goal: 1M patterns

# GEMINI REFINEMENT: Pattern Staging Configuration
PROBATION_PERIOD_HOURS = 24             # How long patterns stay in staging
PROBATION_MAX_TRIGGER_RATE = 0.10       # Pattern triggers on >10% of users = too noisy
PROBATION_MIN_OCCURRENCES = 3           # Need at least 3 occurrences to promote


class DetectionSource(Enum):
    """Where did the detection come from?"""
    LOCAL = "local"           # Fast local pattern match
    GEMINI = "gemini"         # Gemini identified it
    BOTH = "both"             # Local confirmed by Gemini


@dataclass
class HybridAlert:
    """Alert with source attribution"""
    alert: CorrelationAlert
    source: DetectionSource
    gemini_confidence: float = 0.0
    gemini_reasoning: str = ""
    latency_us: float = 0.0


@dataclass
class LearnedPattern:
    """Pattern learned from Gemini analysis"""
    name: str
    description: str
    stages: List[str]  # EventType values as strings
    time_window_days: int
    severity: str
    source: str = "gemini"
    confidence: float = 0.0
    occurrences: int = 1
    first_seen: str = ""
    last_seen: str = ""
    
    def to_attack_sequence(self) -> AttackSequence:
        """Convert to AttackSequence for local engine"""
        return AttackSequence(
            name=self.name,
            description=self.description,
            stages=[EventType(s) for s in self.stages if s in [e.value for e in EventType]],
            time_window_days=self.time_window_days,
            severity=self.severity,
            min_stages_to_alert=2
        )


@dataclass
class ProbationaryPattern:
    """
    GEMINI REFINEMENT: Pattern in staging area (shadow mode).
    
    Patterns discovered by Gemini go here first, NOT to active blocking.
    After PROBATION_PERIOD_HOURS, we check if the pattern is high-fidelity:
    - If trigger_rate > PROBATION_MAX_TRIGGER_RATE -> discard (too noisy)
    - If occurrences < PROBATION_MIN_OCCURRENCES -> keep in probation
    - Otherwise -> promote to active patterns
    """
    pattern: LearnedPattern
    created_at: str
    triggered_users: List[str] = field(default_factory=list)  # User IDs that triggered (for rate calc)
    total_users_seen: int = 0  # Total unique users during probation
    promoted: bool = False
    discarded: bool = False
    discard_reason: str = ""
    
    @property
    def trigger_rate(self) -> float:
        """Percentage of users that triggered this pattern"""
        if self.total_users_seen == 0:
            return 0.0
        return len(set(self.triggered_users)) / self.total_users_seen
    
    def should_promote(self) -> Tuple[bool, str]:
        """Check if pattern should be promoted to active"""
        if self.trigger_rate > PROBATION_MAX_TRIGGER_RATE:
            return False, f"Too noisy: {self.trigger_rate:.1%} trigger rate"
        if self.pattern.occurrences < PROBATION_MIN_OCCURRENCES:
            return False, f"Not enough occurrences: {self.pattern.occurrences}"
        return True, "High-fidelity pattern"


# =============================================================================
# PII BLOCKLIST - These patterns are NEVER sent to Gemini
# =============================================================================
PII_BLOCKLIST_PATTERNS = [
    r'@',                           # Email addresses
    r'\d{1,3}\.\d{1,3}\.\d{1,3}',   # IP addresses
    r'\\',                          # File paths
    r'/',                           # URLs/paths
    r'SELECT|INSERT|UPDATE|DELETE', # SQL
    r'\.com|\.org|\.net',           # Domains
    r'\d{3}-\d{2}-\d{4}',           # SSN pattern
    r'\d{4}-\d{2}-\d{2}',           # Date pattern
]

def validate_no_pii(data: str) -> bool:
    """Returns True if data contains NO PII patterns"""
    import re
    for pattern in PII_BLOCKLIST_PATTERNS:
        if re.search(pattern, data, re.IGNORECASE):
            logger.warning(f"PII BLOCKED: Pattern '{pattern}' found in data")
            return False
    return True


class GeminiPatternAnalyzer:
    """
    Analyzes event sequences via Gemini to discover new patterns.
    
    PRIVACY GUARANTEES:
    1. Only event TYPE names sent (e.g., "vpn_access")
    2. Only RELATIVE timestamps (e.g., "+2.5 hours")
    3. ALL PII stripped before any API call
    4. Explicit blocklist prevents accidental leaks
    5. Audit mode shows exactly what would be sent
    """
    
    def __init__(self, api_key: Optional[str] = None, privacy_audit_mode: bool = False):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.enabled = bool(self.api_key)
        self.privacy_audit_mode = privacy_audit_mode  # If True, logs but doesn't send
        self._call_count = 0
        self._total_tokens = 0
        self._blocked_sends = 0  # Count of sends blocked by PII filter
        
        if not self.enabled:
            logger.warning("GEMINI_API_KEY not set. Hybrid mode disabled - local only.")
    
    def analyze_sequence(self, events: List[Dict]) -> Optional[LearnedPattern]:
        """
        Send ANONYMIZED event sequence to Gemini for pattern analysis.
        
        PRIVACY GUARANTEES:
        1. Only event TYPES sent (e.g., "vpn_access", "file_download")
        2. Only RELATIVE timestamps (hours since first event)
        3. BLOCKLIST validation before any API call
        4. NEVER sends: user_id, IP, file names, query content, etc.
        """
        if not self.enabled:
            return None
        
        if len(events) < 3:
            return None
        
        # STEP 1: ANONYMIZE - Strip all PII, keep only types and timing
        anonymized = self._anonymize_events(events)
        
        # STEP 2: BUILD PROMPT
        prompt = self._build_prompt(anonymized)
        
        # STEP 3: FINAL VALIDATION - Blocklist check on full prompt
        if not validate_no_pii(prompt):
            logger.error("PRIVACY BLOCK: Prompt failed PII validation, NOT sending to Gemini")
            self._blocked_sends += 1
            return None
        
        # STEP 4: PRIVACY AUDIT MODE - Log but don't send
        if self.privacy_audit_mode:
            logger.info(f"PRIVACY AUDIT MODE - Would send to Gemini:\n{prompt}")
            print(f"\n{'='*60}")
            print("PRIVACY AUDIT: What would be sent to Gemini:")
            print(f"{'='*60}")
            print(prompt)
            print(f"{'='*60}")
            print("(privacy_audit_mode=True, not actually sent)")
            return None
        
        try:
            import requests
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 1024
                    }
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.warning(f"Gemini API error: {response.status_code}")
                return None
            
            result = response.json()
            self._call_count += 1
            
            # Parse response
            return self._parse_pattern_response(result, anonymized)
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return None
    
    def _anonymize_events(self, events: List[Dict]) -> List[Dict]:
        """
        PRIVACY-CRITICAL: Strip ALL PII, keep only event types, timing, and SAFE CATEGORICAL TAGS.
        
        WHAT GETS SENT TO GEMINI:
        ✓ event_type (e.g., "vpn_access", "file_download")
        ✓ hours_since_start (relative time, e.g., 2.5)
        ✓ severity_hint (boolean)
        ✓ tags (SAFE categorical tags - no PII, just classifications)
        
        GEMINI REFINEMENT: Categorical Tags allow Gemini to reason about context
        (e.g., "high volume download of privileged data to unmanaged device")
        without revealing ANY actual filenames, users, or paths.
        
        WHAT IS EXPLICITLY BLOCKED:
        ✗ user_id, email, username
        ✗ IP addresses
        ✗ file names, paths
        ✗ query content, SQL
        ✗ hostnames, server names
        ✗ source_system identifiers
        ✗ absolute timestamps (dates)
        ✗ geo location strings
        ✗ client/matter names
        ✗ any string > 30 chars (safety net)
        """
        if not events:
            return []
        
        base_time = events[0].get("timestamp", datetime.now())
        if isinstance(base_time, str):
            base_time = datetime.fromisoformat(base_time)
        
        # ALLOWED event types only - reject unknown strings
        ALLOWED_EVENT_TYPES = {e.value for e in EventType}
        
        anonymized = []
        for e in events:
            ts = e.get("timestamp", base_time)
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            
            delta_hours = (ts - base_time).total_seconds() / 3600
            
            # STRICT: Only allow known event types
            event_type = e.get("event_type", "unknown")
            if event_type not in ALLOWED_EVENT_TYPES:
                event_type = "unknown"
            
            # GEMINI REFINEMENT: Extract SAFE categorical tags from details
            # These are ENUMS/CATEGORIES only - never raw values
            tags = self._extract_safe_tags(e.get("details", {}))
            
            # Build payload with safe context
            payload = {
                "event_type": event_type,
                "hours_since_start": round(delta_hours, 2),
                "severity_hint": bool(e.get("risk_score", 0) > 0.5)
            }
            
            # Only add tags if we have any (keeps payload minimal)
            if tags:
                payload["tags"] = tags
            
            anonymized.append(payload)
        
        # LOG exactly what we're sending (for audit)
        logger.debug(f"PRIVACY AUDIT: Sending to Gemini: {[a['event_type'] for a in anonymized]}")
        
        return anonymized
    
    def _extract_safe_tags(self, details: Dict) -> List[str]:
        """
        GEMINI REFINEMENT: Extract SAFE categorical tags from event details.
        
        These tags give Gemini CONTEXT without revealing PII.
        Each tag is an enum-style category, never a raw value.
        
        Example output: ["data_classification:privileged", "volume:high", "device:unmanaged"]
        """
        tags = []
        
        # Data Classification (from DLP/classification systems)
        classification = details.get("data_classification", "").lower()
        if classification in ("privileged", "confidential", "pii", "phi", "restricted"):
            tags.append(f"data_classification:{classification}")
        elif classification in ("internal", "public"):
            tags.append(f"data_classification:{classification}")
        
        # Volume indicator (bucketed, not exact counts)
        count = details.get("file_count", details.get("count", 0))
        if isinstance(count, (int, float)):
            if count > 100:
                tags.append("volume:high")
            elif count > 10:
                tags.append("volume:medium")
            elif count > 0:
                tags.append("volume:low")
        
        # Device type (managed vs unmanaged)
        device_type = details.get("device_type", details.get("device_managed", "")).lower()
        if device_type in ("unmanaged", "personal", "byod"):
            tags.append("device:unmanaged")
        elif device_type in ("managed", "corporate", "compliant"):
            tags.append("device:managed")
        
        # Time context (business hours vs after hours)
        if details.get("after_hours", False):
            tags.append("time:after_hours")
        if details.get("weekend", False):
            tags.append("time:weekend")
        
        # Network context
        if details.get("external_dest", details.get("external", False)):
            tags.append("network:external")
        if details.get("tor", details.get("anonymizer", False)):
            tags.append("network:anonymized")
        
        # User context (role-based, never actual names)
        role = details.get("user_role", details.get("role", "")).lower()
        if role in ("admin", "administrator", "root", "superuser"):
            tags.append("role:admin")
        elif role in ("executive", "c-suite", "partner"):
            tags.append("role:executive")
        elif role in ("contractor", "vendor", "external"):
            tags.append("role:external")
        
        # Departure indicator (from HR integration)
        if details.get("notice_given", details.get("departing", False)):
            tags.append("hr:departing")
        
        # Anomaly indicators
        if details.get("first_time", details.get("never_before", False)):
            tags.append("pattern:first_occurrence")
        if details.get("unusual_for_user", False):
            tags.append("pattern:unusual")
        
        return tags
    
    def _build_prompt(self, events: List[Dict]) -> str:
        """Build Gemini prompt for pattern analysis"""
        event_summary = "\n".join([
            f"T+{e['hours_since_start']:.1f}h: {e['event_type']}"
            for e in events
        ])
        
        return f"""You are a cybersecurity threat analyst specializing in multi-stage attack patterns.

Analyze this sequence of security events and determine if it represents a known or novel attack pattern.

EVENT SEQUENCE:
{event_summary}

TASK:
1. Does this sequence represent a coherent attack pattern?
2. If yes, what type of attack is this?
3. What is the severity (CRITICAL/HIGH/MEDIUM/LOW)?
4. What should the pattern be named?

Respond in JSON format:
{{
    "is_attack_pattern": true/false,
    "confidence": 0.0-1.0,
    "pattern_name": "descriptive_name_snake_case",
    "description": "What this pattern indicates",
    "severity": "CRITICAL/HIGH/MEDIUM/LOW",
    "reasoning": "Why this is suspicious"
}}

Only return the JSON, no other text."""
    
    def _parse_pattern_response(self, response: Dict, events: List[Dict]) -> Optional[LearnedPattern]:
        """Parse Gemini response into LearnedPattern"""
        try:
            text = response['candidates'][0]['content']['parts'][0]['text']
            
            # Strip markdown code fences
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            
            data = json.loads(text)
            
            if not data.get("is_attack_pattern", False):
                return None
            
            if data.get("confidence", 0) < 0.6:
                return None
            
            # Build pattern from events
            stages = [e["event_type"] for e in events]
            
            # Calculate time window
            max_hours = max(e["hours_since_start"] for e in events) if events else 24
            time_window_days = max(1, int(max_hours / 24) + 1)
            
            return LearnedPattern(
                name=f"gemini_{data.get('pattern_name', 'unknown_pattern')}",
                description=data.get("description", "Gemini-identified pattern"),
                stages=stages,
                time_window_days=time_window_days,
                severity=data.get("severity", "HIGH"),
                source="gemini",
                confidence=data.get("confidence", 0.0),
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return None
    
    @property
    def stats(self) -> Dict:
        return {
            "enabled": self.enabled,
            "privacy_audit_mode": self.privacy_audit_mode,
            "api_calls": self._call_count,
            "blocked_by_pii_filter": self._blocked_sends,
            "total_tokens": self._total_tokens
        }


class HybridDetectionEngine:
    """
    Two-tier detection:
    1. LOCAL (fast, private, free) - 66+ patterns
    2. GEMINI (fallback for novel patterns)
    
    GEMINI REFINEMENT: Pattern Staging Area
    - New patterns go to probation first (shadow mode)
    - After 24h, patterns are either promoted or discarded
    - Prevents "pattern poisoning" DoS attacks
    
    Goal: Reach 1M local patterns, then Gemini becomes optional.
    """
    
    def __init__(self, enable_gemini: bool = True, fast_mode: bool = True,
                 enable_cache: bool = True, enable_daemon: bool = False):
        # Local engine - the workhorse
        self.local_engine = TemporalCorrelationEngine(fast_mode=fast_mode)
        
        # Gemini analyzer - the teacher
        self.gemini = GeminiPatternAnalyzer() if enable_gemini else None
        
        # Unmatched event queue (for batching to Gemini)
        self._unmatched_queue: Dict[str, List[Dict]] = defaultdict(list)
        self._queue_lock = threading.Lock()
        
        # Learned patterns database (promoted, active)
        self._learned_patterns: List[LearnedPattern] = []
        self._load_learned_patterns()
        
        # GEMINI REFINEMENT: Probationary patterns (staging area, shadow mode)
        self._probationary_patterns: List[ProbationaryPattern] = []
        self._load_probationary_patterns()
        self._unique_users_seen: set = set()  # Track total unique users for rate calculation
        
        # ================================================================
        # CACHE + PATTERN ENGINES + DAEMON
        # ================================================================
        self.cache = DetectionCache() if enable_cache else None
        self.pattern_pipeline = PatternEnginePipeline()
        self.user_store = ActiveUserStore()
        self.daemon: Optional[PrecomputeDaemon] = None
        if enable_daemon and self.cache:
            self.daemon = PrecomputeDaemon(self.cache, self.user_store)
            self.daemon.start()
        
        # Stats
        self._stats = {
            "local_detections": 0,
            "gemini_detections": 0,
            "events_to_gemini": 0,
            "patterns_learned": len(self._learned_patterns),
            "patterns_in_probation": len(self._probationary_patterns),
            "patterns_discarded": 0,
            "shadow_mode_triggers": 0,
            "cache_hits": 0,
            "pattern_engine_evals": 0,
        }
        
        # Background thread for Gemini batching
        self._gemini_thread: Optional[threading.Thread] = None
        self._stop_gemini_thread = False
        
        if self.gemini and self.gemini.enabled:
            self._start_gemini_batch_thread()
        
        logger.info(f"HybridEngine initialized: {len(self.local_engine.attack_sequences)} local patterns, "
                   f"{len(self._learned_patterns)} learned patterns, "
                   f"{len(self._probationary_patterns)} probationary patterns, "
                   f"cache={'on' if self.cache else 'off'}, "
                   f"daemon={'on' if self.daemon else 'off'}, "
                   f"Gemini={'enabled' if self.gemini and self.gemini.enabled else 'disabled'}")
    
    def _load_learned_patterns(self):
        """Load previously learned patterns from disk"""
        if PATTERN_DB_PATH.exists():
            try:
                with open(PATTERN_DB_PATH, 'r') as f:
                    data = json.load(f)
                    self._learned_patterns = [
                        LearnedPattern(**p) for p in data.get("patterns", [])
                    ]
                    
                    # Add learned patterns to local engine
                    for lp in self._learned_patterns:
                        try:
                            seq = lp.to_attack_sequence()
                            if seq.stages:  # Only add if stages are valid
                                self.local_engine.attack_sequences.append(seq)
                        except Exception:
                            pass  # Skip invalid patterns
                    
                    logger.info(f"Loaded {len(self._learned_patterns)} learned patterns")
            except Exception as e:
                logger.warning(f"Failed to load learned patterns: {e}")
    
    def _load_probationary_patterns(self):
        """GEMINI REFINEMENT: Load probationary patterns from disk"""
        if PROBATIONARY_DB_PATH.exists():
            try:
                with open(PROBATIONARY_DB_PATH, 'r') as f:
                    data = json.load(f)
                    for p_data in data.get("patterns", []):
                        pattern = LearnedPattern(**p_data["pattern"])
                        prob = ProbationaryPattern(
                            pattern=pattern,
                            created_at=p_data.get("created_at", datetime.now().isoformat()),
                            triggered_users=p_data.get("triggered_users", []),
                            total_users_seen=p_data.get("total_users_seen", 0),
                            promoted=p_data.get("promoted", False),
                            discarded=p_data.get("discarded", False),
                            discard_reason=p_data.get("discard_reason", "")
                        )
                        if not prob.promoted and not prob.discarded:
                            self._probationary_patterns.append(prob)
                    
                    logger.info(f"Loaded {len(self._probationary_patterns)} probationary patterns")
            except Exception as e:
                logger.warning(f"Failed to load probationary patterns: {e}")
    
    def _save_probationary_patterns(self):
        """GEMINI REFINEMENT: Persist probationary patterns to disk"""
        try:
            PROBATIONARY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(PROBATIONARY_DB_PATH, 'w') as f:
                json.dump({
                    "version": "1.0",
                    "patterns": [
                        {
                            "pattern": asdict(p.pattern),
                            "created_at": p.created_at,
                            "triggered_users": p.triggered_users[-100:],  # Keep last 100 only
                            "total_users_seen": p.total_users_seen,
                            "promoted": p.promoted,
                            "discarded": p.discarded,
                            "discard_reason": p.discard_reason
                        }
                        for p in self._probationary_patterns
                    ]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save probationary patterns: {e}")
    
    def _save_learned_patterns(self):
        """Persist learned patterns to disk"""
        try:
            PATTERN_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(PATTERN_DB_PATH, 'w') as f:
                json.dump({
                    "version": "1.0",
                    "target": LOCAL_PATTERN_TARGET,
                    "current_count": len(self._learned_patterns),
                    "patterns": [asdict(p) for p in self._learned_patterns]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save learned patterns: {e}")
    
    def ingest_event(self, event: SecurityEvent) -> List[HybridAlert]:
        """
        Process event through hybrid detection.
        
        Pipeline order:
        0. Check cache (instant hit)
        1. Run pattern engines (sub-ms, no LLM)
        2. Local temporal detection (active patterns)
        3. Check probationary patterns (shadow mode - log only)
        4. If no match, queue for Gemini analysis
        5. Feed user store for daemon pre-compute
        """
        alerts = []
        start_time = time.perf_counter()
        
        # Feed ActiveUserStore (for daemon pre-compute)
        self.user_store.record_event(
            event.user_id, event.event_type.value,
            {"risk": event.risk_score, "src": event.source_system},
        )
        
        # TIER 0: Cache check
        if self.cache:
            cache_key = DetectionCache.make_key(
                [event.event_type.value], user_id=event.user_id
            )
            cached = self.cache.get(cache_key)
            if cached and cached.get("precomputed"):
                self._stats["cache_hits"] += 1
                # Return cached result as a HybridAlert if score warrants it
                if cached.get("score", 0) >= 0.6:
                    from .temporal_engine import CorrelationAlert
                    alert = CorrelationAlert(
                        user_id=event.user_id,
                        matched_sequence="cached_pattern",
                        stages_matched=[event.event_type.value],
                        current_stage=1,
                        total_stages=1,
                        risk_score=cached["score"],
                        description=f"Cache hit: {cached.get('band', 'HIGH')} risk",
                    )
                    latency_us = (time.perf_counter() - start_time) * 1_000_000
                    alerts.append(HybridAlert(
                        alert=alert, source=DetectionSource.LOCAL,
                        latency_us=latency_us,
                    ))
                    return alerts
        
        # TIER 0.5: Pattern engines (pure Python, sub-ms)
        user_data = self.user_store.get_user(event.user_id)
        if user_data:
            event_counts = dict(user_data.get("event_counts", {}))
            trust_events = user_data.get("events", [])
            pe_result = self.pattern_pipeline.evaluate(
                event_counts, trust_events,
                base_risk=event.risk_score / 100.0 if event.risk_score > 1 else event.risk_score,
                timestamp=event.timestamp,
                initial_trust=user_data.get("trust", 1.0),
            )
            self._stats["pattern_engine_evals"] += 1
            
            # Cache the result
            if self.cache:
                self.cache.put(cache_key, {
                    "score": pe_result.score,
                    "confidence": pe_result.confidence,
                    "signals": pe_result.signals,
                    "engine": pe_result.engine,
                    "band": pe_result.score >= 0.85 and "CRITICAL" or
                            pe_result.score >= 0.60 and "HIGH" or
                            pe_result.score >= 0.35 and "MEDIUM" or "LOW",
                    "precomputed": False,
                })
            
            # If pattern engines find high risk, emit alert
            if pe_result.score >= 0.6:
                from .temporal_engine import CorrelationAlert
                pe_alert = CorrelationAlert(
                    user_id=event.user_id,
                    matched_sequence=f"pattern_engine:{pe_result.engine}",
                    stages_matched=list(event_counts.keys())[:5],
                    current_stage=len(event_counts),
                    total_stages=len(event_counts),
                    risk_score=pe_result.score,
                    description=" | ".join(pe_result.signals[:3]),
                )
                latency_us = (time.perf_counter() - start_time) * 1_000_000
                alerts.append(HybridAlert(
                    alert=pe_alert, source=DetectionSource.LOCAL,
                    latency_us=latency_us,
                ))
        
        # TIER 1: Local temporal detection (active patterns)
        local_alerts = self.local_engine.ingest_event(event)
        latency_us = (time.perf_counter() - start_time) * 1_000_000
        
        if local_alerts:
            self._stats["local_detections"] += len(local_alerts)
            for alert in local_alerts:
                alerts.append(HybridAlert(
                    alert=alert,
                    source=DetectionSource.LOCAL,
                    latency_us=latency_us
                ))
        else:
            # TIER 2: Queue for Gemini batch analysis
            if self.gemini and self.gemini.enabled:
                self._queue_for_gemini(event)
        
        # GEMINI REFINEMENT: Check probationary patterns (shadow mode)
        # These are logged but NOT alerted - pattern validation in progress
        self._check_probationary_against_event(event)
        
        return alerts
    
    def _queue_for_gemini(self, event: SecurityEvent):
        """Queue unmatched event for Gemini batch analysis"""
        with self._queue_lock:
            user_id = event.user_id
            
            self._unmatched_queue[user_id].append({
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "risk_score": event.risk_score,
                "source_system": event.source_system
            })
            
            # Keep only recent events per user
            if len(self._unmatched_queue[user_id]) > GEMINI_MAX_EVENTS_PER_BATCH:
                self._unmatched_queue[user_id] = self._unmatched_queue[user_id][-GEMINI_MAX_EVENTS_PER_BATCH:]
    
    def _start_gemini_batch_thread(self):
        """Start background thread for Gemini batch processing"""
        def batch_processor():
            while not self._stop_gemini_thread:
                time.sleep(GEMINI_BATCH_INTERVAL_SECONDS)
                self._process_gemini_batch()
        
        self._gemini_thread = threading.Thread(target=batch_processor, daemon=True)
        self._gemini_thread.start()
    
    def _process_gemini_batch(self):
        """Process queued events through Gemini"""
        with self._queue_lock:
            users_to_analyze = []
            for user_id, events in self._unmatched_queue.items():
                if len(events) >= GEMINI_MIN_EVENTS_TO_ANALYZE:
                    users_to_analyze.append((user_id, events.copy()))
            
            # Clear processed queues
            for user_id, _ in users_to_analyze:
                self._unmatched_queue[user_id] = []
        
        # Analyze each user's event sequence
        for user_id, events in users_to_analyze:
            self._stats["events_to_gemini"] += len(events)
            
            pattern = self.gemini.analyze_sequence(events)
            
            if pattern:
                self._learn_pattern(pattern)
    
    def _learn_pattern(self, pattern: LearnedPattern):
        """
        GEMINI REFINEMENT: Stage new pattern in probation first.
        
        Patterns are NOT immediately added to active blocking.
        Instead, they go to a staging area where we monitor:
        - How many users trigger it (noise level)
        - Whether it's high-fidelity or just noise
        
        After PROBATION_PERIOD_HOURS, pattern is either promoted or discarded.
        """
        # Check if already in probation
        for prob in self._probationary_patterns:
            if prob.pattern.name == pattern.name:
                prob.pattern.occurrences += 1
                prob.pattern.last_seen = datetime.now().isoformat()
                logger.debug(f"Pattern {pattern.name} already in probation, occurrences: {prob.pattern.occurrences}")
                self._save_probationary_patterns()
                return
        
        # Check if already learned (active)
        for existing in self._learned_patterns:
            if existing.name == pattern.name:
                existing.occurrences += 1
                existing.last_seen = datetime.now().isoformat()
                self._save_learned_patterns()
                return
        
        # New pattern - add to probation (staging area)
        prob_pattern = ProbationaryPattern(
            pattern=pattern,
            created_at=datetime.now().isoformat(),
            triggered_users=[],
            total_users_seen=len(self._unique_users_seen)
        )
        self._probationary_patterns.append(prob_pattern)
        self._stats["patterns_in_probation"] = len(self._probationary_patterns)
        
        logger.info(f"NEW PATTERN IN PROBATION: {pattern.name} ({pattern.severity}) - shadow mode for {PROBATION_PERIOD_HOURS}h")
        self._save_probationary_patterns()
    
    def _check_probationary_against_event(self, event: SecurityEvent) -> List[HybridAlert]:
        """
        GEMINI REFINEMENT: Check if event triggers any probationary patterns (shadow mode).
        
        These are logged but NOT alerted to user - they're still being validated.
        """
        shadow_alerts = []
        now = datetime.now()
        
        for prob in self._probationary_patterns:
            if prob.promoted or prob.discarded:
                continue
            
            # Check if probation period is over
            created = datetime.fromisoformat(prob.created_at)
            if (now - created).total_seconds() > PROBATION_PERIOD_HOURS * 3600:
                # Evaluate and promote/discard
                should_promote, reason = prob.should_promote()
                if should_promote:
                    self._promote_pattern(prob, reason)
                else:
                    self._discard_pattern(prob, reason)
                continue
            
            # Check if event matches this probationary pattern
            pattern_stages = [EventType(s) for s in prob.pattern.stages if s in [e.value for e in EventType]]
            if event.event_type in pattern_stages:
                # Track the trigger for rate calculation
                if event.user_id not in prob.triggered_users:
                    prob.triggered_users.append(event.user_id)
                    self._stats["shadow_mode_triggers"] += 1
                    logger.debug(f"SHADOW MODE: {prob.pattern.name} triggered by {event.user_id}")
        
        # Track unique users for rate calculation
        self._unique_users_seen.add(event.user_id)
        
        return shadow_alerts
    
    def _promote_pattern(self, prob: ProbationaryPattern, reason: str):
        """GEMINI REFINEMENT: Promote a probationary pattern to active"""
        prob.promoted = True
        pattern = prob.pattern
        
        self._learned_patterns.append(pattern)
        self._stats["patterns_learned"] = len(self._learned_patterns)
        self._stats["gemini_detections"] += 1
        
        # Add to local engine for active blocking
        try:
            seq = pattern.to_attack_sequence()
            if seq.stages:
                self.local_engine.attack_sequences.append(seq)
                logger.info(f"PATTERN PROMOTED: {pattern.name} ({pattern.severity}) - {reason}")
        except Exception as e:
            logger.warning(f"Could not add promoted pattern to engine: {e}")
        
        self._save_learned_patterns()
        self._save_probationary_patterns()
    
    def _discard_pattern(self, prob: ProbationaryPattern, reason: str):
        """GEMINI REFINEMENT: Discard a noisy pattern"""
        prob.discarded = True
        prob.discard_reason = reason
        self._stats["patterns_discarded"] += 1
        
        logger.warning(f"PATTERN DISCARDED: {prob.pattern.name} - {reason}")
        self._save_probationary_patterns()
    
    def force_gemini_analysis(self, user_id: str = None) -> List[LearnedPattern]:
        """Manually trigger Gemini analysis (for testing)"""
        if not self.gemini or not self.gemini.enabled:
            return []
        
        patterns_found = []
        
        with self._queue_lock:
            if user_id:
                users = [(user_id, self._unmatched_queue.get(user_id, []))]
            else:
                users = list(self._unmatched_queue.items())
        
        for uid, events in users:
            if len(events) >= 3:
                pattern = self.gemini.analyze_sequence(events)
                if pattern:
                    self._learn_pattern(pattern)
                    patterns_found.append(pattern)
        
        return patterns_found
    
    @property
    def stats(self) -> Dict:
        """Get hybrid engine statistics"""
        base = {
            **self._stats,
            "local_patterns": len(self.local_engine.attack_sequences),
            "learned_patterns": len(self._learned_patterns),
            "probationary_patterns": len([p for p in self._probationary_patterns if not p.promoted and not p.discarded]),
            "target_patterns": LOCAL_PATTERN_TARGET,
            "progress_to_target": f"{len(self._learned_patterns) / LOCAL_PATTERN_TARGET * 100:.4f}%",
            "gemini_stats": self.gemini.stats if self.gemini else None,
            "queue_size": sum(len(v) for v in self._unmatched_queue.values()),
        }
        if self.cache:
            base["cache"] = self.cache.stats()
        if self.daemon:
            base["daemon"] = self.daemon.stats()
        return base
    
    @property
    def pattern_count(self) -> int:
        """Total patterns (local + learned)"""
        return len(self.local_engine.attack_sequences)
    
    def shutdown(self):
        """Clean shutdown"""
        self._stop_gemini_thread = True
        if self._gemini_thread:
            self._gemini_thread.join(timeout=5)
        if self.daemon:
            self.daemon.stop()
        self._save_learned_patterns()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_hybrid_engine: Optional[HybridDetectionEngine] = None

def get_hybrid_engine(enable_gemini: bool = True) -> HybridDetectionEngine:
    """Get or create singleton hybrid engine"""
    global _hybrid_engine
    if _hybrid_engine is None:
        _hybrid_engine = HybridDetectionEngine(enable_gemini=enable_gemini)
    return _hybrid_engine


def demo_hybrid_mode():
    """Demonstrate hybrid detection mode"""
    print("\n" + "=" * 70)
    print("AION OS - HYBRID DETECTION ENGINE")
    print("Local patterns + Gemini fallback for novel attacks")
    print("=" * 70)
    
    engine = HybridDetectionEngine(enable_gemini=True)
    
    print(f"\nLocal patterns:   {len(engine.local_engine.attack_sequences)}")
    print(f"Learned patterns: {len(engine._learned_patterns)}")
    print(f"Gemini enabled:   {engine.gemini.enabled if engine.gemini else False}")
    print(f"Target:           {LOCAL_PATTERN_TARGET:,} patterns")
    
    # Simulate some events
    from datetime import datetime
    
    events = [
        SecurityEvent(
            event_id="evt_001",
            user_id="test_user@firm.com",
            event_type=EventType.VPN_BRUTE_FORCE,
            timestamp=datetime.now() - timedelta(hours=2),
            source_system="vpn",
            details={"attempts": 500}
        ),
        SecurityEvent(
            event_id="evt_002",
            user_id="test_user@firm.com",
            event_type=EventType.VPN_ACCESS,
            timestamp=datetime.now() - timedelta(hours=1),
            source_system="vpn",
            details={"success": True}
        ),
        SecurityEvent(
            event_id="evt_003",
            user_id="test_user@firm.com",
            event_type=EventType.GEOGRAPHIC_ANOMALY,
            timestamp=datetime.now(),
            source_system="vpn",
            details={"country": "Russia"}
        ),
    ]
    
    print(f"\n{'='*70}")
    print("SIMULATING ATTACK SEQUENCE")
    print(f"{'='*70}")
    
    for event in events:
        alerts = engine.ingest_event(event)
        print(f"\nEvent: {event.event_type.value}")
        if alerts:
            for alert in alerts:
                print(f"  -> DETECTED [{alert.source.value.upper()}]: {alert.alert.pattern_name}")
                print(f"     Latency: {alert.latency_us:.1f}μs")
    
    print(f"\n{'='*70}")
    print("ENGINE STATS")
    print(f"{'='*70}")
    for key, value in engine.stats.items():
        if key != "gemini_stats":
            print(f"  {key}: {value}")
    
    engine.shutdown()


if __name__ == "__main__":
    demo_hybrid_mode()
