"""
AION OS - SOC (Security Operations Center) Ingestion Module

Receives and processes security alerts from SIEM systems (Splunk, Sentinel, etc.)
Correlates alerts with departure risk patterns for real-time detection.

Key alert types:
- VPN access anomalies (geographic, timing, frequency)
- Database query patterns (bulk exports, unusual tables)
- File access anomalies (mass downloads, cloud sync)
- Credential events (failed logins, password changes)
"""

import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import re


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    VPN_ANOMALY = "vpn_anomaly"
    DATABASE_ACCESS = "database_access"
    FILE_EXFILTRATION = "file_exfiltration"
    CREDENTIAL_EVENT = "credential_event"
    AFTER_HOURS_ACCESS = "after_hours_access"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    BULK_DOWNLOAD = "bulk_download"
    EMAIL_FORWARDING = "email_forwarding"
    CLOUD_SYNC = "cloud_sync"
    PRINT_ANOMALY = "print_anomaly"


@dataclass
class SOCAlert:
    """Normalized security alert from SIEM"""
    id: str
    timestamp: str
    alert_type: str
    severity: str
    user_id: str
    user_email: Optional[str]
    source_ip: Optional[str]
    source_location: Optional[str]
    destination: Optional[str]
    action: str
    details: Dict[str, Any]
    raw_event: Optional[Dict] = None
    correlation_id: Optional[str] = None
    departure_risk_score: float = 0.0
    pattern_matches: List[str] = field(default_factory=list)
    agent_analysis: Optional[Dict] = None  # Security Attacker analysis when triggered


class SOCIngestionEngine:
    """
    Ingests security alerts and correlates with departure risk patterns.
    
    This is what would have caught Dan's VPN database theft:
    - Alert: VPN login from unusual location
    - Alert: Database query bulk export
    - Alert: After-hours access pattern
    - Correlation: High departure risk score
    """
    
    def __init__(self):
        self.alerts: List[SOCAlert] = []
        self.user_risk_scores: Dict[str, float] = {}
        self.alert_file = Path(__file__).parent.parent / "logs" / "soc_alerts.jsonl"
        self.alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Risk weights for different alert types
        self.risk_weights = {
            AlertType.VPN_ANOMALY.value: 25,
            AlertType.DATABASE_ACCESS.value: 30,
            AlertType.FILE_EXFILTRATION.value: 35,
            AlertType.CREDENTIAL_EVENT.value: 15,
            AlertType.AFTER_HOURS_ACCESS.value: 20,
            AlertType.GEOGRAPHIC_ANOMALY.value: 25,
            AlertType.BULK_DOWNLOAD.value: 30,
            AlertType.EMAIL_FORWARDING.value: 25,
            AlertType.CLOUD_SYNC.value: 20,
            AlertType.PRINT_ANOMALY.value: 15,
        }
        
        # High-risk patterns from Typhoon case + common departure scenarios
        self.high_risk_patterns = [
            # Pattern 1: Exactly what happened to Dan
            {
                "name": "vpn_database_theft",
                "description": "VPN access followed by database bulk export (Typhoon pattern)",
                "sequence": [AlertType.VPN_ANOMALY.value, AlertType.DATABASE_ACCESS.value],
                "window_hours": 24,
                "risk_multiplier": 3.0
            },
            # Pattern 2: Classic pre-departure data grab
            {
                "name": "pre_departure_exfil",
                "description": "After-hours access + bulk downloads",
                "sequence": [AlertType.AFTER_HOURS_ACCESS.value, AlertType.BULK_DOWNLOAD.value],
                "window_hours": 48,
                "risk_multiplier": 2.5
            },
            # Pattern 3: Setting up external data channel
            {
                "name": "email_cloud_combo",
                "description": "Email forwarding + cloud sync (external data channel)",
                "sequence": [AlertType.EMAIL_FORWARDING.value, AlertType.CLOUD_SYNC.value],
                "window_hours": 72,
                "risk_multiplier": 2.0
            },
            # Pattern 4: Credential abuse from new location
            {
                "name": "geographic_vpn_abuse",
                "description": "VPN from new location after credential event",
                "sequence": [AlertType.CREDENTIAL_EVENT.value, AlertType.GEOGRAPHIC_ANOMALY.value],
                "window_hours": 12,
                "risk_multiplier": 2.5
            },
            # Pattern 5: Print + download = physical exfil prep
            {
                "name": "physical_exfil_prep",
                "description": "Print job + bulk download (preparing physical copies)",
                "sequence": [AlertType.BULK_DOWNLOAD.value, AlertType.PRINT_ANOMALY.value],
                "window_hours": 24,
                "risk_multiplier": 2.0
            }
        ]
    
    def ingest_alert(self, alert_data: Dict[str, Any], source: str = "generic", auto_escalate: bool = True) -> SOCAlert:
        """
        Ingest and normalize an alert from SIEM.
        
        Supports: Splunk, Microsoft Sentinel, generic JSON
        
        Args:
            alert_data: Raw alert from SIEM
            source: Source type (splunk, sentinel, generic)
            auto_escalate: If True, triggers Security Attacker agent on pattern match
        """
        # Normalize based on source
        if source == "splunk":
            normalized = self._normalize_splunk(alert_data)
        elif source == "sentinel":
            normalized = self._normalize_sentinel(alert_data)
        else:
            normalized = self._normalize_generic(alert_data)
        
        # Calculate departure risk
        normalized.departure_risk_score = self._calculate_risk_score(normalized)
        
        # Check pattern matches
        normalized.pattern_matches = self._check_pattern_matches(normalized)
        
        # Update user risk score
        self._update_user_risk(normalized)
        
        # Store alert
        self.alerts.append(normalized)
        self._persist_alert(normalized)
        
        # AUTO-ESCALATE: Trigger Security Attacker agent on high-risk patterns
        if auto_escalate and normalized.pattern_matches and self.user_risk_scores.get(normalized.user_id, 0) > 50:
            normalized.agent_analysis = self.trigger_security_attacker(normalized.user_id)
        
        return normalized
    
    def _normalize_generic(self, data: Dict) -> SOCAlert:
        """Normalize generic JSON alert"""
        return SOCAlert(
            id=data.get("id", f"alert_{datetime.utcnow().timestamp()}"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            alert_type=data.get("alert_type", data.get("type", "unknown")),
            severity=data.get("severity", "medium"),
            user_id=data.get("user_id", data.get("user", "unknown")),
            user_email=data.get("user_email", data.get("email")),
            source_ip=data.get("source_ip", data.get("src_ip")),
            source_location=data.get("source_location", data.get("location")),
            destination=data.get("destination", data.get("dest")),
            action=data.get("action", "unknown"),
            details=data.get("details", {}),
            raw_event=data
        )
    
    def _normalize_splunk(self, data: Dict) -> SOCAlert:
        """Normalize Splunk alert format"""
        result = data.get("result", data)
        return SOCAlert(
            id=result.get("_cd", f"splunk_{datetime.utcnow().timestamp()}"),
            timestamp=result.get("_time", datetime.utcnow().isoformat()),
            alert_type=self._classify_splunk_event(result),
            severity=result.get("severity", "medium"),
            user_id=result.get("user", result.get("src_user", "unknown")),
            user_email=result.get("user_email"),
            source_ip=result.get("src_ip", result.get("src")),
            source_location=result.get("src_location"),
            destination=result.get("dest", result.get("dest_ip")),
            action=result.get("action", result.get("signature", "unknown")),
            details={
                "app": result.get("app"),
                "bytes": result.get("bytes_out"),
                "duration": result.get("duration"),
            },
            raw_event=data
        )
    
    def _normalize_sentinel(self, data: Dict) -> SOCAlert:
        """Normalize Microsoft Sentinel alert format"""
        return SOCAlert(
            id=data.get("SystemAlertId", f"sentinel_{datetime.utcnow().timestamp()}"),
            timestamp=data.get("TimeGenerated", datetime.utcnow().isoformat()),
            alert_type=self._classify_sentinel_event(data),
            severity=data.get("Severity", "medium").lower(),
            user_id=data.get("AccountName", data.get("UserPrincipalName", "unknown")),
            user_email=data.get("UserPrincipalName"),
            source_ip=data.get("SourceIP", data.get("IPAddress")),
            source_location=data.get("Location"),
            destination=data.get("DestinationIP"),
            action=data.get("Activity", data.get("OperationName", "unknown")),
            details={
                "provider": data.get("ProviderName"),
                "resource": data.get("Resource"),
                "category": data.get("Category"),
            },
            raw_event=data
        )
    
    def _classify_splunk_event(self, event: Dict) -> str:
        """Classify Splunk event into alert type"""
        action = str(event.get("action", "")).lower()
        signature = str(event.get("signature", "")).lower()
        app = str(event.get("app", "")).lower()
        
        if "vpn" in app or "vpn" in action:
            return AlertType.VPN_ANOMALY.value
        elif "database" in app or "sql" in action:
            return AlertType.DATABASE_ACCESS.value
        elif "download" in action or "export" in action:
            return AlertType.BULK_DOWNLOAD.value
        elif "forward" in action and "email" in app:
            return AlertType.EMAIL_FORWARDING.value
        elif "cloud" in app or "sync" in action:
            return AlertType.CLOUD_SYNC.value
        elif "auth" in app or "login" in action:
            return AlertType.CREDENTIAL_EVENT.value
        else:
            return "unknown"
    
    def _classify_sentinel_event(self, event: Dict) -> str:
        """Classify Sentinel event into alert type"""
        operation = str(event.get("OperationName", "")).lower()
        category = str(event.get("Category", "")).lower()
        
        if "signin" in operation and "unusual" in str(event.get("Activity", "")).lower():
            return AlertType.GEOGRAPHIC_ANOMALY.value
        elif "vpn" in operation or "vpn" in category:
            return AlertType.VPN_ANOMALY.value
        elif "database" in category or "sql" in operation:
            return AlertType.DATABASE_ACCESS.value
        elif "download" in operation or "filedownload" in operation:
            return AlertType.BULK_DOWNLOAD.value
        elif "mailforward" in operation or "inbox" in operation:
            return AlertType.EMAIL_FORWARDING.value
        elif "sharepoint" in category or "onedrive" in category:
            return AlertType.CLOUD_SYNC.value
        else:
            return "unknown"
    
    def _calculate_risk_score(self, alert: SOCAlert) -> float:
        """Calculate departure risk score for alert"""
        base_score = self.risk_weights.get(alert.alert_type, 10)
        
        # Severity multiplier
        severity_mult = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0
        }
        mult = severity_mult.get(alert.severity, 1.0)
        
        # Time-based multiplier (after hours = higher risk)
        try:
            alert_time = datetime.fromisoformat(alert.timestamp.replace("Z", "+00:00"))
            hour = alert_time.hour
            if hour < 6 or hour > 20:  # After hours
                mult *= 1.5
            if alert_time.weekday() >= 5:  # Weekend
                mult *= 1.3
        except:
            pass
        
        return min(base_score * mult, 100)
    
    def _check_pattern_matches(self, alert: SOCAlert) -> List[str]:
        """Check if alert matches known departure patterns"""
        matches = []
        user_alerts = [a for a in self.alerts if a.user_id == alert.user_id]
        
        for pattern in self.high_risk_patterns:
            window = timedelta(hours=pattern["window_hours"])
            sequence = pattern["sequence"]
            
            # Check if this alert could complete a pattern
            if alert.alert_type in sequence:
                # Look for preceding alerts in sequence
                for prev_alert in user_alerts:
                    try:
                        prev_time = datetime.fromisoformat(prev_alert.timestamp.replace("Z", "+00:00"))
                        alert_time = datetime.fromisoformat(alert.timestamp.replace("Z", "+00:00"))
                        
                        if alert_time - prev_time <= window:
                            if prev_alert.alert_type in sequence:
                                # Found a matching sequence
                                matches.append(pattern["name"])
                                # Apply risk multiplier
                                alert.departure_risk_score *= pattern["risk_multiplier"]
                                break
                    except:
                        continue
        
        return list(set(matches))
    
    def _update_user_risk(self, alert: SOCAlert):
        """Update cumulative risk score for user"""
        current = self.user_risk_scores.get(alert.user_id, 0)
        # Decay old score, add new
        new_score = (current * 0.8) + alert.departure_risk_score
        self.user_risk_scores[alert.user_id] = min(new_score, 100)
    
    def _persist_alert(self, alert: SOCAlert):
        """Persist alert to log file"""
        with open(self.alert_file, "a") as f:
            f.write(json.dumps(asdict(alert)) + "\n")
    
    def get_status(self) -> Dict[str, Any]:
        """Get SOC ingestion status"""
        return {
            "status": "operational",
            "total_alerts": len(self.alerts),
            "high_risk_users": [
                {"user_id": uid, "risk_score": score}
                for uid, score in self.user_risk_scores.items()
                if score > 50
            ],
            "recent_alerts": [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "severity": a.severity,
                    "user_id": a.user_id,
                    "risk_score": a.departure_risk_score,
                    "pattern_matches": a.pattern_matches
                }
                for a in self.alerts[-10:]
            ],
            "pattern_detections": sum(
                1 for a in self.alerts if a.pattern_matches
            )
        }
    
    def get_user_risk(self, user_id: str) -> Dict[str, Any]:
        """Get risk profile for specific user"""
        user_alerts = [a for a in self.alerts if a.user_id == user_id]
        
        return {
            "user_id": user_id,
            "cumulative_risk_score": self.user_risk_scores.get(user_id, 0),
            "alert_count": len(user_alerts),
            "alert_types": list(set(a.alert_type for a in user_alerts)),
            "pattern_matches": list(set(
                m for a in user_alerts for m in a.pattern_matches
            )),
            "recent_alerts": [
                {
                    "timestamp": a.timestamp,
                    "type": a.alert_type,
                    "severity": a.severity,
                    "risk_score": a.departure_risk_score
                }
                for a in user_alerts[-5:]
            ],
            "recommendation": self._get_recommendation(user_id, user_alerts)
        }
    
    def _get_recommendation(self, user_id: str, alerts: List[SOCAlert]) -> str:
        """Generate recommendation based on user risk profile"""
        risk = self.user_risk_scores.get(user_id, 0)
        
        if risk > 75:
            return "CRITICAL: Immediate audit required. Revoke VPN access, audit database queries, review file access logs."
        elif risk > 50:
            return "HIGH: Schedule audit within 24 hours. Monitor all database and file access closely."
        elif risk > 25:
            return "MEDIUM: Add to watchlist. Review access patterns weekly."
        else:
            return "LOW: Normal monitoring. No immediate action required."
    
    def trigger_security_attacker(self, user_id: str, use_local: bool = True) -> Dict[str, Any]:
        """
        Trigger Security Attacker agent for deep adversarial analysis.
        
        Called when SOC detects high-risk pattern - feeds real-time alerts
        into the adversarial framework.
        
        Args:
            user_id: User to analyze
            use_local: If True (default), uses 100% local analysis. If False, uses Claude API.
        """
        from aionos.core.local_security_attacker import get_local_attacker
        
        # Get user's alert history
        user_alerts = [a for a in self.alerts if a.user_id == user_id]
        risk_score = self.user_risk_scores.get(user_id, 0)
        pattern_matches = list(set(m for a in user_alerts for m in a.pattern_matches))
        
        # Build context for agent
        alert_summary = []
        for a in user_alerts[-10:]:  # Last 10 alerts
            alert_summary.append({
                "type": a.alert_type,
                "severity": a.severity,
                "action": a.action,
                "timestamp": a.timestamp,
                "source_location": a.source_location
            })
        
        # DEFAULT: Use 100% local analysis (the AION way)
        if use_local:
            attacker = get_local_attacker()
            assessment = attacker.analyze(
                user_id=user_id,
                risk_score=risk_score,
                pattern_matches=pattern_matches,
                alert_summary=alert_summary
            )
            
            return {
                "agent": "Security Attacker (LOCAL)",
                "mode": "100% LOCAL - Zero LLM",
                "triggered_by": pattern_matches,
                "user_id": user_id,
                "risk_score": risk_score,
                "threat_type": assessment.threat_type,
                "severity": assessment.severity,
                "confidence": f"{assessment.confidence * 100:.0f}%",
                "attack_objective": assessment.attack_objective,
                "immediate_actions": assessment.immediate_actions,
                "forensic_preservation": assessment.forensic_preservation,
                "notifications": assessment.notifications,
                "prevention_recommendations": assessment.prevention_recommendations
            }
        
        # OPTIONAL: Use Claude API for enhanced analysis
        else:
            from aionos.core.adversarial_engine import AdversarialEngine, IntensityLevel, AgentPerspective
            
            query = f"""
DEFENSIVE SECURITY ASSESSMENT - SIEM ALERT TRIAGE

Security consultant helping a law firm's IT team respond to suspicious activity.

ALERT SUMMARY:
- User ID: {user_id}
- Risk Score: {risk_score}/100
- Pattern Flags: {pattern_matches}

Recent SIEM Alerts:
{json.dumps(alert_summary, indent=2)}

Provide: 1) Threat assessment 2) Immediate actions 3) Forensic preservation 4) Notifications 5) Prevention recommendations
"""
            engine = AdversarialEngine(intensity=IntensityLevel.LEVEL_5_MAXIMUM)
            
            security_agent = None
            for agent in engine.agents:
                if agent.perspective == AgentPerspective.SECURITY_ATTACKER:
                    security_agent = agent
                    break
            
            if security_agent and engine.use_real_api:
                result = engine._run_chained_attack(
                    agent=security_agent,
                    query=query,
                    context={"use_case_type": "soc_realtime"},
                    attack_history="",
                    stage=1,
                    use_case_type="soc_realtime"
                )
                return {
                    "agent": "Security Attacker (CLAUDE)",
                    "mode": "Claude API",
                    "triggered_by": pattern_matches,
                    "user_id": user_id,
                    "risk_score": risk_score,
                    "analysis": result.get("findings", result.get("response", "")),
                    "severity": "CRITICAL" if risk_score > 75 else "HIGH"
                }
            else:
                # Fall back to local if API not available
                return self.trigger_security_attacker(user_id, use_local=True)


# Singleton instance
_soc_engine: Optional[SOCIngestionEngine] = None


def get_soc_engine() -> SOCIngestionEngine:
    """Get or create SOC engine singleton"""
    global _soc_engine
    if _soc_engine is None:
        _soc_engine = SOCIngestionEngine()
    return _soc_engine


def ingest_alert(alert_data: Dict, source: str = "generic") -> SOCAlert:
    """Ingest a security alert"""
    return get_soc_engine().ingest_alert(alert_data, source)


def get_soc_status() -> Dict[str, Any]:
    """Get SOC status"""
    return get_soc_engine().get_status()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC signature for webhook authentication"""
    if not secret:
        return True  # No secret configured, allow all
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)
