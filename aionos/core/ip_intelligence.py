"""
AION OS — IP Intelligence Engine
100% OFFLINE. Zero API calls. Zero cloud dependencies.

Takes an IP address and produces:
- Geolocation (from local DB)
- ISP/network classification
- Proxy/VPN/Tor detection
- Threat scoring with reasons
- Correlation against firm activity logs
- Professional incident report

This engine runs with WiFi OFF. That's the point.
"""

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from aionos.core.ip_threat_db import (
    LocalIPThreatDB, IPRecord, ProxyType, ThreatCategory,
    ISPType, CIDREntry
)

logger = logging.getLogger("aionos.ip_intelligence")


# =============================================================================
# CORRELATION DATA STRUCTURES
# =============================================================================

class AccessType(Enum):
    """Types of system access to correlate against"""
    VPN_LOGIN = "vpn_login"
    EMAIL_LOGIN = "email_login"
    FILE_SERVER = "file_server"
    DATABASE_QUERY = "database_query"
    CLOUD_STORAGE = "cloud_storage"
    ADMIN_PANEL = "admin_panel"
    EXTERNAL_TRANSFER = "external_transfer"
    PRINT_JOB = "print_job"
    USB_MOUNT = "usb_mount"


@dataclass
class AccessEvent:
    """A single access event from firm logs"""
    timestamp: str
    ip_address: str
    user: str = ""
    access_type: AccessType = AccessType.VPN_LOGIN
    resource: str = ""
    bytes_transferred: int = 0
    success: bool = True
    details: str = ""


@dataclass
class CorrelationResult:
    """Result of correlating an IP against firm activity"""
    ip: str
    matching_events: List[AccessEvent] = field(default_factory=list)
    unique_users: List[str] = field(default_factory=list)
    access_types: List[str] = field(default_factory=list)
    total_bytes: int = 0
    first_seen_internal: str = ""
    last_seen_internal: str = ""
    event_count: int = 0
    risk_multiplier: float = 1.0
    correlation_notes: List[str] = field(default_factory=list)


@dataclass 
class IPIntelReport:
    """Complete IP intelligence report"""
    # Target
    target_ip: str
    analysis_timestamp: str
    analysis_duration_ms: float
    
    # Intelligence
    ip_record: Optional[IPRecord] = None
    
    # Correlation
    correlation: Optional[CorrelationResult] = None
    
    # Assessment
    overall_risk_score: int = 0
    risk_level: str = "UNKNOWN"
    executive_summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    iocs: List[str] = field(default_factory=list)  # Indicators of compromise
    
    # Metadata
    engine_version: str = "1.0.0"
    offline_mode: bool = True


# =============================================================================
# IP INTELLIGENCE ENGINE
# =============================================================================

class IPIntelligenceEngine:
    """
    Offline IP threat intelligence and correlation engine.
    
    Pipeline:
    1. IP Lookup       → Local threat DB (CIDR, ISP, proxy detection)
    2. Correlation     → Match IP against firm access logs
    3. Risk Scoring    → Combine threat intel + correlation findings
    4. Report          → Generate executive-ready threat report
    
    ZERO network calls. ZERO API dependencies. Runs on airplane mode.
    """

    def __init__(self, threat_db: Optional[LocalIPThreatDB] = None):
        self.threat_db = threat_db or LocalIPThreatDB()
        self._access_logs: List[AccessEvent] = []
        self.version = "1.0.0"

    def ingest_access_logs(self, events: List[AccessEvent]):
        """Ingest firm access logs for correlation."""
        self._access_logs.extend(events)
        logger.info(f"Ingested {len(events)} access events (total: {len(self._access_logs)})")

    def ingest_manual_ip(self, ip: str, data: Dict[str, Any]):
        """
        Ingest manually gathered IP intelligence (e.g., from IP2Location screenshot).
        This is how field-collected OSINT gets into the system.
        """
        record = IPRecord(
            ip=ip,
            country=data.get("country", "Unknown"),
            country_code=data.get("country_code", "US"),
            region=data.get("region", "Unknown"),
            city=data.get("city", "Unknown"),
            zip_code=data.get("zip_code", ""),
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
            isp=data.get("isp", "Unknown"),
            isp_type=ISPType(data.get("isp_type", "unknown")),
            asn=data.get("asn", ""),
            domain=data.get("domain", ""),
            net_speed=data.get("net_speed", ""),
            is_proxy=data.get("is_proxy", False),
            proxy_type=ProxyType(data.get("proxy_type", "none")),
            is_anonymous=data.get("is_anonymous", False),
            threat_score=data.get("fraud_score", 0),
            last_seen=data.get("last_seen", ""),
            confidence=1.0,  # Manual entry = high confidence
            raw_data=data,
        )
        
        # Run threat scoring on top of manual data
        self.threat_db.add_manual_entry(record)
        logger.info(f"Ingested manual IP intel for {ip}")

    def analyze(self, ip: str) -> IPIntelReport:
        """
        Full analysis pipeline for a target IP.
        100% offline. Returns complete intelligence report.
        """
        start_time = time.perf_counter()
        
        # Step 1: IP Lookup
        ip_record = self.threat_db.lookup(ip)
        
        # Step 2: Correlate against firm logs
        correlation = self._correlate_ip(ip)
        
        # Step 3: Combined risk scoring
        overall_score, risk_level = self._calculate_risk(ip_record, correlation)
        
        # Step 4: Generate assessment
        summary = self._generate_summary(ip_record, correlation, overall_score)
        recommendations = self._generate_recommendations(ip_record, correlation, overall_score)
        iocs = self._extract_iocs(ip_record, correlation)
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        report = IPIntelReport(
            target_ip=ip,
            analysis_timestamp=datetime.now().isoformat(),
            analysis_duration_ms=round(elapsed_ms, 3),
            ip_record=ip_record,
            correlation=correlation,
            overall_risk_score=overall_score,
            risk_level=risk_level,
            executive_summary=summary,
            recommendations=recommendations,
            iocs=iocs,
            engine_version=self.version,
            offline_mode=True,
        )
        
        logger.info(f"IP analysis complete: {ip} → {risk_level} ({overall_score}/100) in {elapsed_ms:.1f}ms")
        return report

    def _correlate_ip(self, ip: str) -> CorrelationResult:
        """Correlate an IP against ingested access logs."""
        result = CorrelationResult(ip=ip)
        
        matching = [e for e in self._access_logs if e.ip_address == ip]
        
        if not matching:
            result.correlation_notes.append("No matching events found in firm access logs")
            return result
        
        result.matching_events = matching
        result.event_count = len(matching)
        result.unique_users = list(set(e.user for e in matching if e.user))
        result.access_types = list(set(e.access_type.value for e in matching))
        result.total_bytes = sum(e.bytes_transferred for e in matching)
        
        timestamps = sorted(e.timestamp for e in matching if e.timestamp)
        if timestamps:
            result.first_seen_internal = timestamps[0]
            result.last_seen_internal = timestamps[-1]
        
        # Risk multipliers based on correlation
        if len(result.unique_users) > 1:
            result.risk_multiplier = 1.5
            result.correlation_notes.append(
                f"ALERT: IP used by {len(result.unique_users)} different users — possible shared proxy"
            )
        
        if AccessType.EXTERNAL_TRANSFER.value in result.access_types:
            result.risk_multiplier *= 1.3
            result.correlation_notes.append("Data exfiltration activity detected from this IP")
        
        if AccessType.ADMIN_PANEL.value in result.access_types:
            result.risk_multiplier *= 1.2
            result.correlation_notes.append("Administrative access from this IP")
        
        if result.total_bytes > 100_000_000:  # 100MB+
            result.risk_multiplier *= 1.2
            result.correlation_notes.append(
                f"High volume transfer: {result.total_bytes / 1_000_000:.1f}MB total"
            )
        
        return result

    def _calculate_risk(self, ip_record: IPRecord, correlation: CorrelationResult) -> Tuple[int, str]:
        """Combined risk score from threat intel + correlation."""
        base_score = ip_record.threat_score
        
        # Apply correlation multiplier
        adjusted = int(base_score * correlation.risk_multiplier)
        
        # Add points for internal activity
        if correlation.event_count > 0:
            adjusted += min(correlation.event_count * 2, 20)  # Up to +20 for activity
        
        if correlation.total_bytes > 50_000_000:
            adjusted += 10
        
        # Cap at 100
        final_score = min(adjusted, 100)
        
        # Classify
        if final_score >= 80:
            level = "CRITICAL"
        elif final_score >= 60:
            level = "HIGH"
        elif final_score >= 40:
            level = "MEDIUM"
        elif final_score >= 20:
            level = "LOW"
        else:
            level = "INFORMATIONAL"
        
        return final_score, level

    def _generate_summary(self, ip_record: IPRecord, correlation: CorrelationResult, score: int) -> str:
        """Generate executive summary text."""
        parts = []
        
        parts.append(
            f"Analysis of IP {ip_record.ip} — {ip_record.isp} "
            f"({ip_record.city}, {ip_record.region}, {ip_record.country_code})."
        )
        
        if ip_record.is_proxy:
            proxy_desc = ip_record.proxy_type.value.replace("_", " ").title()
            parts.append(
                f"This IP is flagged as an ANONYMOUS PROXY ({proxy_desc}). "
                f"Traffic routed through this address is being deliberately obfuscated."
            )
        
        if ip_record.isp_type == ISPType.RESIDENTIAL and ip_record.is_proxy:
            parts.append(
                "The IP belongs to a residential ISP but operates as a proxy, "
                "indicating a potentially compromised device being used as a relay. "
                "This is a common tactic in advanced persistent threats."
            )
        
        if correlation.event_count > 0:
            parts.append(
                f"This IP was found in {correlation.event_count} internal access events "
                f"involving {len(correlation.unique_users)} user(s). "
                f"Activity types: {', '.join(correlation.access_types)}."
            )
        
        if correlation.total_bytes > 0:
            mb = correlation.total_bytes / 1_000_000
            parts.append(f"Total data transferred: {mb:.1f} MB.")
        
        parts.append(f"Overall risk assessment: {score}/100.")
        
        return " ".join(parts)

    def _generate_recommendations(self, ip_record: IPRecord, correlation: CorrelationResult, score: int) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if score >= 60:
            recs.append("IMMEDIATE: Block this IP at the firewall/VPN gateway")
            recs.append("IMMEDIATE: Review all user sessions originating from this IP in the last 30 days")
        
        if ip_record.is_proxy:
            recs.append(
                "Investigate proxy usage — determine if any authorized users "
                "have legitimate reasons to route traffic through anonymous proxies"
            )
        
        if ip_record.isp_type == ISPType.RESIDENTIAL and ip_record.is_proxy:
            recs.append(
                "This residential proxy pattern suggests a compromised device relay. "
                "Consider reporting to ISP (Charter/Spectrum) abuse department"
            )
            recs.append(
                "Preserve all logs referencing this IP for potential legal proceedings. "
                "A subpoena to the ISP can identify the subscriber"
            )
        
        if correlation.event_count > 0:
            if len(correlation.unique_users) > 1:
                recs.append(
                    f"Multiple users ({', '.join(correlation.unique_users)}) accessed systems "
                    f"from this IP — investigate for credential sharing or compromise"
                )
            recs.append("Conduct forensic review of all files accessed during these sessions")
        
        if correlation.total_bytes > 50_000_000:
            recs.append(
                f"Large data transfer ({correlation.total_bytes / 1_000_000:.1f} MB) detected. "
                f"Verify against authorized data movement requests"
            )
        
        if score >= 40:
            recs.append("Add this IP to the permanent watchlist for ongoing monitoring")
        
        # Always recommend
        recs.append("Document findings for inclusion in incident response report")
        
        if ip_record.isp and "Charter" in ip_record.isp:
            recs.append(
                "For subscriber identification: Legal team can issue subpoena to "
                "Charter Communications Inc (Spectrum) — AS11427. "
                "Include IP address, timestamps, and suspected activity in the request"
            )
        
        return recs

    def _extract_iocs(self, ip_record: IPRecord, correlation: CorrelationResult) -> List[str]:
        """Extract Indicators of Compromise."""
        iocs = [f"IP: {ip_record.ip}"]
        
        if ip_record.asn:
            iocs.append(f"ASN: {ip_record.asn}")
        if ip_record.domain:
            iocs.append(f"Domain: {ip_record.domain}")
        if ip_record.is_proxy:
            iocs.append(f"Proxy Type: {ip_record.proxy_type.value}")
        
        for event in correlation.matching_events:
            if event.user:
                iocs.append(f"Associated User: {event.user}")
            if event.resource:
                iocs.append(f"Accessed Resource: {event.resource}")
        
        return list(set(iocs))  # Deduplicate
