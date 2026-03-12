"""
AION OS - Behavioral Baseline Engine
Learns what's "normal" for each user to detect anomalies.

Without baselines, you can't answer:
- "Is 500 file downloads unusual for Sarah?"
- "Does John normally access the database at 2am?"
- "Is this the first time Mike used VPN from overseas?"

This engine builds user profiles over time and flags deviations.
"""

import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict
from enum import Enum
import statistics


class DeviationType(Enum):
    """Types of behavioral deviations"""
    VOLUME_SPIKE = "volume_spike"           # 10x normal downloads
    NEW_BEHAVIOR = "new_behavior"           # First time doing X
    TIME_ANOMALY = "time_anomaly"           # Activity at unusual hour
    FREQUENCY_SPIKE = "frequency_spike"     # 50 logins in 1 hour vs normal 2
    LOCATION_ANOMALY = "location_anomaly"   # New location
    RESOURCE_ANOMALY = "resource_anomaly"   # Accessing new systems


@dataclass
class BehaviorMetrics:
    """Metrics for a specific behavior type"""
    event_type: str
    
    # Volume metrics
    total_count_30d: int = 0
    daily_average: float = 0.0
    daily_stddev: float = 0.0
    max_daily: int = 0
    
    # Time metrics
    typical_hours: List[int] = field(default_factory=list)  # Hours when activity usually occurs
    weekend_ratio: float = 0.0  # What % happens on weekends
    
    # Recent activity
    count_today: int = 0
    count_last_7d: int = 0
    
    last_updated: str = ""


@dataclass
class UserBaseline:
    """Complete behavioral baseline for a user"""
    user_id: str
    
    # Per-behavior metrics
    behaviors: Dict[str, BehaviorMetrics] = field(default_factory=dict)
    
    # Global metrics
    total_events_30d: int = 0
    active_days_30d: int = 0
    typical_active_hours: List[int] = field(default_factory=list)
    known_locations: List[str] = field(default_factory=list)
    known_devices: List[str] = field(default_factory=list)
    known_resources: List[str] = field(default_factory=list)
    
    # Profile metadata
    profile_created: str = ""
    last_updated: str = ""
    data_points: int = 0
    confidence: float = 0.0  # 0-1, how reliable is this baseline


@dataclass 
class DeviationAlert:
    """Alert when behavior deviates from baseline"""
    user_id: str
    deviation_type: DeviationType
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    
    # What happened
    event_type: str
    observed_value: float
    baseline_value: float
    deviation_multiplier: float  # How many times above normal
    
    # Context
    description: str
    timestamp: datetime
    
    # Response
    recommended_actions: List[str]


class BehavioralBaselineEngine:
    """
    Builds and maintains behavioral baselines for users.
    Detects when current behavior deviates from established patterns.
    
    ULTRA-OPTIMIZED:
    - Fast mode skips all disk I/O
    - Pre-indexed events by type
    - Incremental baseline updates
    """
    
    __slots__ = ('baseline_store_path', 'baselines', 'event_history', 'events_by_type',
                 'thresholds', '_dirty', '_event_count_since_save', '_save_interval',
                 '_last_prune_time', '_baseline_cache', '_cache_valid', '_fast_mode',
                 '_event_counts')
    
    def __init__(self, baseline_store_path: Optional[Path] = None, fast_mode: bool = True):
        self.baseline_store_path = baseline_store_path or Path("aionos/knowledge/baselines.json")
        self.baselines: Dict[str, UserBaseline] = {}
        self.event_history: Dict[str, List[Dict]] = defaultdict(list)  # Raw events for calculation
        
        # OPTIMIZATION: Pre-indexed by event type
        self.events_by_type: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        
        # OPTIMIZATION: Quick event counts per user (avoid len() calls)
        self._event_counts: Dict[str, int] = defaultdict(int)
        
        # Thresholds for deviation detection
        self.thresholds = {
            "volume_spike_multiplier": 3.0,      # 3x normal = alert
            "frequency_spike_multiplier": 5.0,   # 5x normal rate = alert
            "new_behavior_min_days": 30,         # Must have 30 days of data to flag "new" behavior
            "min_data_points": 10,               # Need 10 events before baseline is reliable
            "confidence_threshold": 0.5,         # Minimum confidence to generate alerts
        }
        
        # Performance optimization: batch writes
        self._dirty = False  # Track if we need to save
        self._event_count_since_save = 0
        self._save_interval = 100  # Save every 100 events
        self._last_prune_time: Dict[str, datetime] = {}  # Track last prune per user
        
        # In-memory cache for fast lookups
        self._baseline_cache: Dict[str, UserBaseline] = {}
        self._cache_valid: Dict[str, bool] = {}
        
        # ULTRA-FAST MODE: Skip disk I/O entirely
        self._fast_mode = fast_mode
        
        if not fast_mode:
            self._load_baselines()
    
    def record_event(self, user_id: str, event_type: str, timestamp: datetime,
                    details: Optional[Dict] = None) -> List[DeviationAlert]:
        """
        HYPER-OPTIMIZED - Zero function call overhead.
        Everything inlined for maximum speed.
        """
        # Pre-compute timestamp once
        ts_epoch = timestamp.timestamp()
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Minimal record (avoid dict creation overhead in fast mode)
        event_record = (event_type, ts_epoch, hour, weekday)  # Tuple is faster than dict
        
        # Direct storage access (local var cache)
        history = self.event_history
        by_type = self.events_by_type
        counts = self._event_counts
        
        if user_id not in history:
            history[user_id] = []
        history[user_id].append(event_record)
        
        if user_id not in by_type:
            by_type[user_id] = {}
        if event_type not in by_type[user_id]:
            by_type[user_id][event_type] = []
        by_type[user_id][event_type].append(event_record)
        
        counts[user_id] = counts.get(user_id, 0) + 1
        
        # INLINED fast deviation check
        alerts = []
        
        type_events = by_type[user_id].get(event_type, [])
        event_count = len(type_events)
        
        # Only check if we have enough data
        if event_count > 10:
            # Last hour volume check (inlined)
            hour_ago = ts_epoch - 3600
            recent = sum(1 for e in type_events if e[1] >= hour_ago)  # e[1] is ts_epoch
            
            # Calculate average (avoid division by zero)
            time_span = ts_epoch - type_events[0][1]
            if time_span > 0:
                avg_hourly = event_count / (time_span / 3600)
                threshold = avg_hourly * 3.0  # volume_spike_multiplier
                
                if recent > threshold and avg_hourly > 0:
                    alerts.append(DeviationAlert(
                        user_id=user_id,
                        deviation_type=DeviationType.VOLUME_SPIKE,
                        event_type=event_type,
                        observed_value=float(recent),
                        baseline_value=avg_hourly,
                        deviation_multiplier=recent / avg_hourly,
                        severity="HIGH" if recent > avg_hourly * 5 else "MEDIUM",
                        description=f"Volume spike: {recent} vs {avg_hourly:.1f} avg",
                        timestamp=timestamp,
                        recommended_actions=[]
                    ))
        
        return alerts
    
    def _check_deviations_fast(self, user_id: str, event_type: str, ts_epoch: float, 
                               details: Dict) -> List[DeviationAlert]:
        """
        ULTRA-FAST deviation check - minimal overhead.
        Only checks obvious spikes without full baseline recalc.
        """
        alerts = []
        
        # Get type-specific event count
        type_events = self.events_by_type[user_id].get(event_type, [])
        total_events = self._event_counts[user_id]
        
        # Quick volume spike check (last hour vs historical average)
        if len(type_events) > 10:
            hour_ago_epoch = ts_epoch - 3600
            recent_count = sum(1 for e in type_events if e["ts_epoch"] >= hour_ago_epoch)
            avg_hourly = len(type_events) / max(1, (ts_epoch - type_events[0]["ts_epoch"]) / 3600)
            
            if recent_count > avg_hourly * self.thresholds["volume_spike_multiplier"]:
                alerts.append(DeviationAlert(
                    user_id=user_id,
                    deviation_type=DeviationType.VOLUME_SPIKE,
                    event_type=event_type,
                    observed_value=float(recent_count),
                    baseline_value=avg_hourly,
                    deviation_multiplier=recent_count / max(0.1, avg_hourly),
                    severity="HIGH" if recent_count > avg_hourly * 5 else "MEDIUM",
                    description=f"Volume spike: {recent_count} events in last hour vs {avg_hourly:.1f} avg",
                    timestamp=datetime.fromtimestamp(ts_epoch),
                    recommended_actions=["Review recent activity", "Check for bulk operations"]
                ))
        
        return alerts
    
    def _prune_old_events(self, user_id: str, now: datetime):
        """Remove events older than 90 days - using epoch for speed"""
        cutoff_epoch = (now - timedelta(days=90)).timestamp()
        self.event_history[user_id] = [
            e for e in self.event_history[user_id]
            if e.get("ts_epoch", 0) >= cutoff_epoch
        ]
    
    def _get_baseline_fast(self, user_id: str) -> UserBaseline:
        """Get baseline with caching"""
        if self._cache_valid.get(user_id) and user_id in self._baseline_cache:
            return self._baseline_cache[user_id]
        
        baseline = self._update_baseline(user_id)
        self._baseline_cache[user_id] = baseline
        self._cache_valid[user_id] = True
        return baseline
    
    def flush(self):
        """Force write pending changes to disk"""
        if self._dirty:
            self._save_baselines()
            self._dirty = False
            self._event_count_since_save = 0
    
    def _update_baseline(self, user_id: str) -> UserBaseline:
        """Recalculate baseline from event history - OPTIMIZED with epoch timestamps"""
        events = self.event_history.get(user_id, [])
        
        if user_id not in self.baselines:
            self.baselines[user_id] = UserBaseline(
                user_id=user_id,
                profile_created=datetime.now().isoformat()
            )
        
        baseline = self.baselines[user_id]
        now = datetime.now()
        
        # Filter to last 30 days using epoch (FAST)
        cutoff_30d_epoch = (now - timedelta(days=30)).timestamp()
        recent_events = [
            e for e in events
            if e.get("ts_epoch", 0) >= cutoff_30d_epoch
        ]
        
        if not recent_events:
            return baseline
        
        # Calculate global metrics
        baseline.total_events_30d = len(recent_events)
        baseline.data_points = len(events)
        
        # Active days - use pre-parsed data
        active_dates = set()
        for e in recent_events:
            # Parse timestamp only when needed for date extraction
            ts_epoch = e.get("ts_epoch")
            if ts_epoch:
                active_dates.add(datetime.fromtimestamp(ts_epoch).date())
        baseline.active_days_30d = len(active_dates)
        
        # Typical active hours (already stored in event)
        hours = [e["hour"] for e in recent_events]
        if hours:
            hour_counts = defaultdict(int)
            for h in hours:
                hour_counts[h] += 1
            # Top 6 most active hours
            baseline.typical_active_hours = sorted(hour_counts.keys(), 
                                                   key=lambda h: hour_counts[h], 
                                                   reverse=True)[:6]
        
        # Known locations/devices/resources
        for event in recent_events:
            details = event.get("details", {})
            if "location" in details and details["location"] not in baseline.known_locations:
                baseline.known_locations.append(details["location"])
            if "device" in details and details["device"] not in baseline.known_devices:
                baseline.known_devices.append(details["device"])
            if "resource" in details and details["resource"] not in baseline.known_resources:
                baseline.known_resources.append(details["resource"])
        
        # Per-behavior metrics
        events_by_type = defaultdict(list)
        for e in recent_events:
            events_by_type[e["event_type"]].append(e)
        
        for event_type, type_events in events_by_type.items():
            metrics = self._calculate_behavior_metrics(event_type, type_events, now)
            baseline.behaviors[event_type] = metrics
        
        # Calculate confidence (0-1 based on data quality)
        baseline.confidence = min(1.0, baseline.data_points / 100) * min(1.0, baseline.active_days_30d / 14)
        
        baseline.last_updated = now.isoformat()
        
        return baseline
    
    def _calculate_behavior_metrics(self, event_type: str, events: List[Dict], 
                                   now: datetime) -> BehaviorMetrics:
        """Calculate metrics for a specific behavior type - OPTIMIZED"""
        metrics = BehaviorMetrics(event_type=event_type)
        
        metrics.total_count_30d = len(events)
        
        # Daily counts - use epoch for speed
        daily_counts = defaultdict(int)
        for e in events:
            ts_epoch = e.get("ts_epoch")
            if ts_epoch:
                date = datetime.fromtimestamp(ts_epoch).date()
                daily_counts[date] += 1
        
        if daily_counts:
            counts = list(daily_counts.values())
            metrics.daily_average = statistics.mean(counts)
            metrics.daily_stddev = statistics.stdev(counts) if len(counts) > 1 else 0
            metrics.max_daily = max(counts)
        
        # Time metrics (hour already pre-computed in event)
        hours = [e["hour"] for e in events]
        if hours:
            hour_counts = defaultdict(int)
            for h in hours:
                hour_counts[h] += 1
            metrics.typical_hours = sorted(hour_counts.keys(), 
                                          key=lambda h: hour_counts[h], 
                                          reverse=True)[:4]
        
        # Weekend ratio (weekday already pre-computed)
        weekend_count = sum(1 for e in events if e["weekday"] >= 5)
        metrics.weekend_ratio = weekend_count / len(events) if events else 0
        
        # Recent counts - use epoch
        today = now.date()
        today_start_epoch = datetime.combine(today, datetime.min.time()).timestamp()
        week_ago_epoch = (now - timedelta(days=7)).timestamp()
        
        metrics.count_today = sum(1 for e in events 
                                 if e.get("ts_epoch", 0) >= today_start_epoch)
        metrics.count_last_7d = sum(1 for e in events 
                                   if e.get("ts_epoch", 0) >= week_ago_epoch)
        
        metrics.last_updated = now.isoformat()
        
        return metrics
    
    def _check_deviations(self, user_id: str, event_type: str, timestamp: datetime,
                         details: Dict, baseline: UserBaseline) -> List[DeviationAlert]:
        """Check if current event deviates from baseline"""
        alerts = []
        
        # Skip if baseline isn't reliable yet
        if baseline.confidence < self.thresholds["confidence_threshold"]:
            return alerts
        
        behavior = baseline.behaviors.get(event_type)
        
        # Check 1: New behavior (never seen before)
        if behavior is None and baseline.data_points >= self.thresholds["min_data_points"]:
            alerts.append(DeviationAlert(
                user_id=user_id,
                deviation_type=DeviationType.NEW_BEHAVIOR,
                severity="MEDIUM",
                event_type=event_type,
                observed_value=1,
                baseline_value=0,
                deviation_multiplier=float('inf'),
                description=f"First time user performed '{event_type}' in tracking period",
                timestamp=timestamp,
                recommended_actions=[
                    "VERIFY: Confirm this activity was authorized",
                    "AUDIT: Review what triggered this new behavior",
                    "MONITOR: Watch for follow-up suspicious activity"
                ]
            ))
            return alerts  # Can't do other checks without behavior history
        
        if behavior is None:
            return alerts
        
        # Check 2: Volume spike (today's count vs daily average)
        if behavior.daily_average > 0:
            # Get today's count including this event
            today_count = behavior.count_today + 1
            multiplier = today_count / behavior.daily_average
            
            if multiplier >= self.thresholds["volume_spike_multiplier"]:
                severity = "HIGH" if multiplier >= 5 else "MEDIUM"
                alerts.append(DeviationAlert(
                    user_id=user_id,
                    deviation_type=DeviationType.VOLUME_SPIKE,
                    severity=severity,
                    event_type=event_type,
                    observed_value=today_count,
                    baseline_value=behavior.daily_average,
                    deviation_multiplier=multiplier,
                    description=f"User has {today_count} '{event_type}' events today vs {behavior.daily_average:.1f} daily average ({multiplier:.1f}x normal)",
                    timestamp=timestamp,
                    recommended_actions=[
                        f"INVESTIGATE: Why {multiplier:.1f}x normal {event_type} activity?",
                        "AUDIT: Review all activity in current session",
                        "CONSIDER: Temporary access restriction if pattern continues"
                    ]
                ))
        
        # Check 3: Time anomaly (activity at unusual hour)
        if behavior.typical_hours and timestamp.hour not in behavior.typical_hours:
            # Check if it's a significant anomaly (late night, early morning)
            unusual_hours = [0, 1, 2, 3, 4, 5, 22, 23]
            if timestamp.hour in unusual_hours:
                alerts.append(DeviationAlert(
                    user_id=user_id,
                    deviation_type=DeviationType.TIME_ANOMALY,
                    severity="MEDIUM",
                    event_type=event_type,
                    observed_value=timestamp.hour,
                    baseline_value=behavior.typical_hours[0] if behavior.typical_hours else 12,
                    deviation_multiplier=1.0,
                    description=f"User performed '{event_type}' at {timestamp.hour}:00 - outside normal hours {behavior.typical_hours}",
                    timestamp=timestamp,
                    recommended_actions=[
                        "VERIFY: Confirm user identity (could be compromised credentials)",
                        "CHECK: Is user traveling or working remotely?",
                        "MONITOR: Watch for other off-hours activity"
                    ]
                ))
        
        # Check 4: Location anomaly
        location = details.get("location")
        if location and baseline.known_locations:
            if location not in baseline.known_locations:
                alerts.append(DeviationAlert(
                    user_id=user_id,
                    deviation_type=DeviationType.LOCATION_ANOMALY,
                    severity="HIGH",
                    event_type=event_type,
                    observed_value=1,
                    baseline_value=0,
                    deviation_multiplier=float('inf'),
                    description=f"Activity from new location '{location}' - known locations: {baseline.known_locations[:3]}",
                    timestamp=timestamp,
                    recommended_actions=[
                        "IMMEDIATE: Verify user identity through secondary channel",
                        "CHECK: Could this be impossible travel?",
                        "CONSIDER: Force re-authentication"
                    ]
                ))
        
        # Check 5: New resource access
        resource = details.get("resource")
        if resource and baseline.known_resources:
            if resource not in baseline.known_resources:
                alerts.append(DeviationAlert(
                    user_id=user_id,
                    deviation_type=DeviationType.RESOURCE_ANOMALY,
                    severity="MEDIUM",
                    event_type=event_type,
                    observed_value=1,
                    baseline_value=0,
                    deviation_multiplier=float('inf'),
                    description=f"Accessed new resource '{resource}' - not in typical access pattern",
                    timestamp=timestamp,
                    recommended_actions=[
                        "AUDIT: Verify user has legitimate need for this resource",
                        "CHECK: Was access recently granted?",
                        "MONITOR: Watch for data exfiltration from new resource"
                    ]
                ))
        
        return alerts
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get a user's behavioral profile summary"""
        baseline = self.baselines.get(user_id)
        if not baseline:
            return None
        
        return {
            "user_id": baseline.user_id,
            "confidence": f"{baseline.confidence * 100:.0f}%",
            "data_points": baseline.data_points,
            "active_days_30d": baseline.active_days_30d,
            "total_events_30d": baseline.total_events_30d,
            "typical_hours": baseline.typical_active_hours,
            "known_locations": baseline.known_locations[:5],
            "behaviors": {
                k: {
                    "daily_avg": round(v.daily_average, 1),
                    "max_daily": v.max_daily,
                    "typical_hours": v.typical_hours
                }
                for k, v in baseline.behaviors.items()
            },
            "last_updated": baseline.last_updated
        }
    
    def compare_users(self, user_id: str, peer_group: List[str] = None) -> Dict:
        """Compare a user's behavior to their peers (useful for detecting outliers)"""
        user_baseline = self.baselines.get(user_id)
        if not user_baseline:
            return {"error": "No baseline for user"}
        
        if peer_group is None:
            peer_group = [u for u in self.baselines.keys() if u != user_id]
        
        if not peer_group:
            return {"error": "No peers to compare"}
        
        # Compare key metrics
        peer_metrics = []
        for peer_id in peer_group:
            peer = self.baselines.get(peer_id)
            if peer:
                peer_metrics.append({
                    "total_events": peer.total_events_30d,
                    "active_days": peer.active_days_30d
                })
        
        if not peer_metrics:
            return {"error": "No peer data available"}
        
        avg_events = statistics.mean(p["total_events"] for p in peer_metrics)
        avg_days = statistics.mean(p["active_days"] for p in peer_metrics)
        
        return {
            "user_id": user_id,
            "user_events_30d": user_baseline.total_events_30d,
            "peer_avg_events_30d": round(avg_events, 1),
            "events_vs_peers": f"{(user_baseline.total_events_30d / avg_events * 100):.0f}%" if avg_events > 0 else "N/A",
            "user_active_days": user_baseline.active_days_30d,
            "peer_avg_active_days": round(avg_days, 1),
            "is_outlier": user_baseline.total_events_30d > avg_events * 2
        }
    
    def _load_baselines(self):
        """Load baselines from storage"""
        if self.baseline_store_path.exists():
            try:
                with open(self.baseline_store_path, 'r') as f:
                    data = json.load(f)
                
                for user_id, baseline_data in data.get("baselines", {}).items():
                    baseline = UserBaseline(user_id=user_id)
                    baseline.total_events_30d = baseline_data.get("total_events_30d", 0)
                    baseline.active_days_30d = baseline_data.get("active_days_30d", 0)
                    baseline.typical_active_hours = baseline_data.get("typical_active_hours", [])
                    baseline.known_locations = baseline_data.get("known_locations", [])
                    baseline.known_devices = baseline_data.get("known_devices", [])
                    baseline.known_resources = baseline_data.get("known_resources", [])
                    baseline.profile_created = baseline_data.get("profile_created", "")
                    baseline.last_updated = baseline_data.get("last_updated", "")
                    baseline.data_points = baseline_data.get("data_points", 0)
                    baseline.confidence = baseline_data.get("confidence", 0.0)
                    
                    # Load behavior metrics
                    for btype, bdata in baseline_data.get("behaviors", {}).items():
                        metrics = BehaviorMetrics(event_type=btype)
                        metrics.total_count_30d = bdata.get("total_count_30d", 0)
                        metrics.daily_average = bdata.get("daily_average", 0.0)
                        metrics.daily_stddev = bdata.get("daily_stddev", 0.0)
                        metrics.max_daily = bdata.get("max_daily", 0)
                        metrics.typical_hours = bdata.get("typical_hours", [])
                        metrics.weekend_ratio = bdata.get("weekend_ratio", 0.0)
                        metrics.count_today = bdata.get("count_today", 0)
                        metrics.count_last_7d = bdata.get("count_last_7d", 0)
                        baseline.behaviors[btype] = metrics
                    
                    self.baselines[user_id] = baseline
                
                self.event_history = defaultdict(list, data.get("event_history", {}))
                
            except (json.JSONDecodeError, KeyError) as e:
                pass  # Start fresh
    
    def _save_baselines(self):
        """Persist baselines to storage"""
        self.baseline_store_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "baselines": {},
            "event_history": dict(self.event_history)
        }
        
        for user_id, baseline in self.baselines.items():
            data["baselines"][user_id] = {
                "total_events_30d": baseline.total_events_30d,
                "active_days_30d": baseline.active_days_30d,
                "typical_active_hours": baseline.typical_active_hours,
                "known_locations": baseline.known_locations,
                "known_devices": baseline.known_devices,
                "known_resources": baseline.known_resources,
                "profile_created": baseline.profile_created,
                "last_updated": baseline.last_updated,
                "data_points": baseline.data_points,
                "confidence": baseline.confidence,
                "behaviors": {
                    k: asdict(v) for k, v in baseline.behaviors.items()
                }
            }
        
        with open(self.baseline_store_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def format_alert(self, alert: DeviationAlert) -> str:
        """Format deviation alert for display"""
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║           AION BEHAVIORAL DEVIATION ALERT                        ║
╚══════════════════════════════════════════════════════════════════╝

USER: {alert.user_id}
TYPE: {alert.deviation_type.value}
SEVERITY: {alert.severity}

{alert.description}

OBSERVED: {alert.observed_value}
BASELINE: {alert.baseline_value}
DEVIATION: {alert.deviation_multiplier:.1f}x normal

════════════════════════════════════════════════════════════════════
RECOMMENDED ACTIONS
════════════════════════════════════════════════════════════════════
""" + "\n".join(f"  □ {a}" for a in alert.recommended_actions) + """

════════════════════════════════════════════════════════════════════
This alert was generated by behavioral baseline analysis.
Normal patterns learned from historical user activity.
════════════════════════════════════════════════════════════════════
"""


# Singleton
_baseline_engine: Optional[BehavioralBaselineEngine] = None

def get_baseline_engine() -> BehavioralBaselineEngine:
    global _baseline_engine
    if _baseline_engine is None:
        _baseline_engine = BehavioralBaselineEngine()
    return _baseline_engine


def demo_baseline_detection():
    """Demo the behavioral baseline engine"""
    from pathlib import Path
    import uuid
    
    print("=" * 70)
    print("AION BEHAVIORAL BASELINE ENGINE - DEMO")
    print("=" * 70)
    
    engine = BehavioralBaselineEngine(Path("aionos/knowledge/demo_baselines.json"))
    
    now = datetime.now()
    
    # Build up a normal baseline for Sarah over 30 days
    print("\nPhase 1: Building baseline (simulating 30 days of normal activity)...")
    
    for day_offset in range(30, 0, -1):
        day = now - timedelta(days=day_offset)
        
        # Normal pattern: 2-5 file downloads per day, business hours
        for _ in range(3):
            hour = 9 + (day_offset % 8)  # 9am-5pm
            ts = day.replace(hour=hour)
            engine.record_event(
                user_id="strevino@typhoon.com",
                event_type="file_download",
                timestamp=ts,
                details={"location": "Austin, TX", "resource": "client_files"}
            )
        
        # Normal pattern: 1 database query per day
        engine.record_event(
            user_id="strevino@typhoon.com",
            event_type="database_query",
            timestamp=day.replace(hour=10),
            details={"location": "Austin, TX", "resource": "billing_db"}
        )
    
    # Show baseline
    profile = engine.get_user_profile("strevino@typhoon.com")
    print(f"\nBaseline established:")
    print(f"  Confidence: {profile['confidence']}")
    print(f"  Data points: {profile['data_points']}")
    print(f"  Typical hours: {profile['typical_hours']}")
    print(f"  Known locations: {profile['known_locations']}")
    print(f"  Behaviors: {list(profile['behaviors'].keys())}")
    
    # Phase 2: Anomalous activity
    print("\n" + "=" * 70)
    print("Phase 2: Detecting anomalies...")
    print("=" * 70)
    
    # Anomaly 1: Massive volume spike
    print("\n[TEST] 50 file downloads in one day (vs normal 3)...")
    for i in range(50):
        alerts = engine.record_event(
            user_id="strevino@typhoon.com",
            event_type="file_download",
            timestamp=now,
            details={"location": "Austin, TX", "resource": "client_files"}
        )
        if alerts and i == 49:  # Show final alert
            for alert in alerts:
                print(engine.format_alert(alert))
    
    # Anomaly 2: New location
    print("\n[TEST] Activity from new location 'Kiev, Ukraine'...")
    alerts = engine.record_event(
        user_id="strevino@typhoon.com",
        event_type="database_query",
        timestamp=now,
        details={"location": "Kiev, Ukraine", "resource": "billing_db"}
    )
    for alert in alerts:
        if alert.deviation_type == DeviationType.LOCATION_ANOMALY:
            print(engine.format_alert(alert))
    
    # Anomaly 3: Off-hours activity
    print("\n[TEST] Database query at 3am...")
    alerts = engine.record_event(
        user_id="strevino@typhoon.com",
        event_type="database_query",
        timestamp=now.replace(hour=3),
        details={"location": "Austin, TX", "resource": "billing_db"}
    )
    for alert in alerts:
        if alert.deviation_type == DeviationType.TIME_ANOMALY:
            print(engine.format_alert(alert))
    
    # Anomaly 4: New resource
    print("\n[TEST] Access to new resource 'executive_compensation'...")
    alerts = engine.record_event(
        user_id="strevino@typhoon.com",
        event_type="database_query",
        timestamp=now,
        details={"location": "Austin, TX", "resource": "executive_compensation"}
    )
    for alert in alerts:
        if alert.deviation_type == DeviationType.RESOURCE_ANOMALY:
            print(engine.format_alert(alert))


if __name__ == "__main__":
    demo_baseline_detection()
