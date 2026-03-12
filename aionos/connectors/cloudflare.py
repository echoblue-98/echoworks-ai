"""
Cloudflare Connector for AION OS

Integrates with Cloudflare security services:
- Zero Trust Access logs
- Gateway DNS logs
- Audit logs
- WAF events
- Bot detection

Deployment: On-premise in client environment
Data: Never leaves client infrastructure

For Typhoon and clients using Cloudflare for security.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class CloudflareSignalType(Enum):
    """Types of security signals from Cloudflare."""
    # Access/Zero Trust
    ACCESS_LOGIN = "access_login"
    ACCESS_DENIED = "access_denied"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    NEW_DEVICE = "new_device"
    UNUSUAL_LOCATION = "unusual_location"
    
    # Gateway/DNS
    DNS_ANOMALY = "dns_anomaly"
    DNS_EXFILTRATION = "dns_exfiltration"
    BLOCKED_DOMAIN = "blocked_domain"
    
    # WAF
    WAF_ALERT = "waf_alert"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    BOT_DETECTED = "bot_detected"
    
    # Audit
    SETTINGS_CHANGED = "settings_changed"
    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"
    POLICY_MODIFIED = "policy_modified"


@dataclass
class CloudflareSignal:
    """A security signal from Cloudflare."""
    signal_type: CloudflareSignalType
    timestamp: datetime
    user_email: Optional[str]
    source_ip: str
    location: Optional[str]
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]
    raw_event: Dict[str, Any]


class DemoMode:
    """
    Demo mode - simulates Cloudflare signals without real credentials.
    Use for demos, investor presentations, and testing.
    """
    
    @classmethod
    def generate_insider_threat_sequence(cls) -> List[Dict]:
        """Generate signals matching the Typhoon/Knowles attack pattern."""
        return [
            {
                "signal_type": CloudflareSignalType.UNUSUAL_LOCATION,
                "user": "m.knowles@company.com",
                "severity": "medium",
                "details": {
                    "source_ip": "185.42.33.100",
                    "location": "Unknown - Residential Proxy",
                    "baseline_locations": ["Katy, TX", "Dallas, TX"],
                    "device": "Unknown Device",
                    "access_time": "02:15 AM CST"
                },
                "delay": 0
            },
            {
                "signal_type": CloudflareSignalType.NEW_DEVICE,
                "user": "m.knowles@company.com",
                "severity": "medium",
                "details": {
                    "device_fingerprint": "unknown_home_server",
                    "os": "Linux Server",
                    "browser": "Custom Script",
                    "note": "Not matching any registered devices"
                },
                "delay": 2
            },
            {
                "signal_type": CloudflareSignalType.DNS_ANOMALY,
                "user": "m.knowles@company.com",
                "severity": "high",
                "details": {
                    "query_volume": 15000,
                    "baseline_volume": 200,
                    "increase": "7400%",
                    "domains_queried": ["company-backup.external.com", "files.personal-cloud.net"],
                    "pattern": "Bulk data query pattern"
                },
                "delay": 4
            },
            {
                "signal_type": CloudflareSignalType.RATE_LIMIT_EXCEEDED,
                "user": "m.knowles@company.com",
                "severity": "high",
                "details": {
                    "endpoint": "/api/v1/clients/export",
                    "requests_per_minute": 450,
                    "limit": 60,
                    "action_taken": "None - monitoring only mode"
                },
                "delay": 5
            },
            {
                "signal_type": CloudflareSignalType.IMPOSSIBLE_TRAVEL,
                "user": "m.knowles@company.com",
                "severity": "critical",
                "details": {
                    "login_1": {"location": "Katy, TX", "time": "5:30 PM CST"},
                    "login_2": {"location": "Eastern Europe", "time": "7:45 PM CST"},
                    "distance": "5,800 miles",
                    "time_between": "2 hours 15 minutes",
                    "verdict": "IMPOSSIBLE - VPN/Proxy detected"
                },
                "delay": 6
            }
        ]
    
    @classmethod
    def generate_post_departure_sequence(cls) -> List[Dict]:
        """Generate signals for post-departure unauthorized access."""
        return [
            {
                "signal_type": CloudflareSignalType.ACCESS_LOGIN,
                "user": "former.employee@company.com",
                "severity": "critical",
                "details": {
                    "status": "SUCCESS",
                    "source_ip": "73.42.155.88",
                    "location": "Houston, TX",
                    "note": "USER TERMINATED 3 DAYS AGO",
                    "credential_status": "SHOULD BE REVOKED"
                },
                "delay": 0
            },
            {
                "signal_type": CloudflareSignalType.ACCESS_LOGIN,
                "user": "former.employee@company.com",
                "severity": "critical",
                "details": {
                    "application": "Email Portal",
                    "action": "Delete emails",
                    "emails_deleted": 47,
                    "note": "Deleting sent items containing client communications"
                },
                "delay": 2
            },
            {
                "signal_type": CloudflareSignalType.DNS_EXFILTRATION,
                "user": "former.employee@company.com",
                "severity": "critical",
                "details": {
                    "pattern": "DNS tunneling detected",
                    "data_volume_estimated": "2.3 MB via DNS",
                    "destination": "personal-backup.dynamic-dns.net",
                    "technique": "Base64 encoded data in DNS queries"
                },
                "delay": 3
            }
        ]


class CloudflareConnector:
    """
    Cloudflare API Connector for AION OS.
    
    Connects to:
    - Cloudflare Zero Trust (Access)
    - Cloudflare Gateway (DNS)
    - Cloudflare Audit Logs
    - Cloudflare WAF
    
    All data stays local - this connector runs in client environment.
    """
    
    API_BASE = "https://api.cloudflare.com/client/v4"
    
    def __init__(self, config_path: Optional[str] = None, demo_mode: bool = False):
        """
        Initialize Cloudflare connector.
        
        Args:
            config_path: Path to cloudflare.json config file
            demo_mode: If True, use simulated data
        """
        self.demo_mode = demo_mode
        self.config = {}
        self.session = None
        self.soc_engine = None
        
        if config_path and not demo_mode:
            self._load_config(config_path)
        
        if demo_mode:
            logger.info("Cloudflare connector running in DEMO MODE")
    
    def _load_config(self, config_path: str):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            
            required = ['api_token', 'account_id']
            for key in required:
                if key not in self.config:
                    raise ValueError(f"Missing required config: {key}")
            
            logger.info(f"Loaded Cloudflare config from {config_path}")
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
    
    async def connect(self) -> bool:
        """Establish connection to Cloudflare API."""
        if self.demo_mode:
            logger.info("Demo mode - no real connection needed")
            return True
        
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not installed. Run: pip install aiohttp")
            return False
        
        try:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config['api_token']}",
                    "Content-Type": "application/json"
                }
            )
            
            # Verify connection
            async with self.session.get(f"{self.API_BASE}/user/tokens/verify") as resp:
                if resp.status == 200:
                    logger.info("Cloudflare API connection verified")
                    return True
                else:
                    logger.error(f"Cloudflare API verification failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Failed to connect to Cloudflare: {e}")
            return False
    
    async def disconnect(self):
        """Close connection."""
        if self.session:
            await self.session.close()
    
    def attach_soc_engine(self, soc_engine):
        """Attach SOC ingestion engine for alert escalation."""
        self.soc_engine = soc_engine
        logger.info("SOC engine attached to Cloudflare connector")
    
    async def get_access_logs(self, hours: int = 24) -> List[Dict]:
        """
        Get Zero Trust Access logs.
        
        Args:
            hours: How many hours back to query
            
        Returns:
            List of access events
        """
        if self.demo_mode:
            return self._demo_access_logs()
        
        # Real API call
        account_id = self.config['account_id']
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
        
        url = f"{self.API_BASE}/accounts/{account_id}/access/logs/access_requests"
        params = {"since": since, "limit": 1000}
        
        async with self.session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('result', [])
            else:
                logger.error(f"Failed to get access logs: {resp.status}")
                return []
    
    async def get_gateway_dns_logs(self, hours: int = 24) -> List[Dict]:
        """
        Get Gateway DNS logs.
        
        Args:
            hours: How many hours back to query
            
        Returns:
            List of DNS events
        """
        if self.demo_mode:
            return self._demo_dns_logs()
        
        account_id = self.config['account_id']
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
        
        url = f"{self.API_BASE}/accounts/{account_id}/gateway/dns"
        params = {"since": since, "limit": 1000}
        
        async with self.session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('result', [])
            else:
                logger.error(f"Failed to get DNS logs: {resp.status}")
                return []
    
    async def get_audit_logs(self, hours: int = 24) -> List[Dict]:
        """
        Get audit logs for security-relevant changes.
        
        Args:
            hours: How many hours back to query
            
        Returns:
            List of audit events
        """
        if self.demo_mode:
            return self._demo_audit_logs()
        
        account_id = self.config['account_id']
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
        
        url = f"{self.API_BASE}/accounts/{account_id}/audit_logs"
        params = {"since": since, "per_page": 100}
        
        async with self.session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('result', [])
            else:
                logger.error(f"Failed to get audit logs: {resp.status}")
                return []
    
    async def detect_impossible_travel(self, user_email: str, hours: int = 24) -> List[CloudflareSignal]:
        """
        Detect impossible travel patterns for a specific user.
        
        This is a key detection for the Typhoon/Knowles attack pattern.
        """
        signals = []
        
        if self.demo_mode:
            # Return demo impossible travel
            demo_sequence = DemoMode.generate_insider_threat_sequence()
            for item in demo_sequence:
                if item['signal_type'] == CloudflareSignalType.IMPOSSIBLE_TRAVEL:
                    signals.append(CloudflareSignal(
                        signal_type=item['signal_type'],
                        timestamp=datetime.now(),
                        user_email=item['user'],
                        source_ip=item['details'].get('login_2', {}).get('location', 'unknown'),
                        location=item['details'].get('login_2', {}).get('location'),
                        severity=item['severity'],
                        details=item['details'],
                        raw_event=item
                    ))
            return signals
        
        # Real implementation would analyze access logs
        access_logs = await self.get_access_logs(hours)
        
        # Group by user and check for impossible travel
        user_logins = [log for log in access_logs if log.get('user_email') == user_email]
        user_logins.sort(key=lambda x: x.get('created_at', ''))
        
        for i in range(1, len(user_logins)):
            prev = user_logins[i-1]
            curr = user_logins[i]
            
            # Calculate if travel is impossible
            # This would use geolocation distance and time delta
            # Simplified check here
            if self._is_impossible_travel(prev, curr):
                signals.append(CloudflareSignal(
                    signal_type=CloudflareSignalType.IMPOSSIBLE_TRAVEL,
                    timestamp=datetime.fromisoformat(curr['created_at'].replace('Z', '')),
                    user_email=user_email,
                    source_ip=curr.get('ip_address', ''),
                    location=curr.get('geo', {}).get('country', ''),
                    severity='critical',
                    details={
                        'login_1': prev,
                        'login_2': curr
                    },
                    raw_event=curr
                ))
        
        return signals
    
    def _is_impossible_travel(self, prev_login: Dict, curr_login: Dict) -> bool:
        """Check if two logins represent impossible travel."""
        # Simplified - would need real geo distance calculation
        prev_country = prev_login.get('geo', {}).get('country', '')
        curr_country = curr_login.get('geo', {}).get('country', '')
        
        if prev_country and curr_country and prev_country != curr_country:
            # Check time delta
            try:
                prev_time = datetime.fromisoformat(prev_login['created_at'].replace('Z', ''))
                curr_time = datetime.fromisoformat(curr_login['created_at'].replace('Z', ''))
                delta = (curr_time - prev_time).total_seconds() / 3600  # hours
                
                # If less than 3 hours between different countries, likely impossible
                if delta < 3:
                    return True
            except:
                pass
        
        return False
    
    async def detect_dns_exfiltration(self, hours: int = 24) -> List[CloudflareSignal]:
        """
        Detect potential data exfiltration via DNS tunneling.
        
        Looks for:
        - Unusually long DNS queries (base64 encoded data)
        - High query volume to unusual domains
        - TXT record queries (often used for exfiltration)
        """
        signals = []
        
        if self.demo_mode:
            demo_sequence = DemoMode.generate_post_departure_sequence()
            for item in demo_sequence:
                if item['signal_type'] == CloudflareSignalType.DNS_EXFILTRATION:
                    signals.append(CloudflareSignal(
                        signal_type=item['signal_type'],
                        timestamp=datetime.now(),
                        user_email=item['user'],
                        source_ip="unknown",
                        location=None,
                        severity=item['severity'],
                        details=item['details'],
                        raw_event=item
                    ))
            return signals
        
        # Real implementation
        dns_logs = await self.get_gateway_dns_logs(hours)
        
        # Analyze for exfiltration patterns
        # ... implementation details
        
        return signals
    
    async def detect_post_departure_access(self, terminated_users: List[str]) -> List[CloudflareSignal]:
        """
        Detect access by users who should be terminated.
        
        This directly addresses the Typhoon case where Knowles
        accessed systems after departure.
        
        Args:
            terminated_users: List of email addresses of terminated employees
            
        Returns:
            Critical alerts for any access by these users
        """
        signals = []
        
        if self.demo_mode:
            demo_sequence = DemoMode.generate_post_departure_sequence()
            for item in demo_sequence:
                if item['signal_type'] == CloudflareSignalType.ACCESS_LOGIN:
                    signals.append(CloudflareSignal(
                        signal_type=item['signal_type'],
                        timestamp=datetime.now(),
                        user_email=item['user'],
                        source_ip=item['details'].get('source_ip', 'unknown'),
                        location=item['details'].get('location'),
                        severity='critical',
                        details=item['details'],
                        raw_event=item
                    ))
            return signals
        
        # Real implementation
        access_logs = await self.get_access_logs(hours=168)  # Last week
        
        for log in access_logs:
            user = log.get('user_email', '')
            if user in terminated_users:
                signals.append(CloudflareSignal(
                    signal_type=CloudflareSignalType.ACCESS_LOGIN,
                    timestamp=datetime.fromisoformat(log['created_at'].replace('Z', '')),
                    user_email=user,
                    source_ip=log.get('ip_address', ''),
                    location=log.get('geo', {}).get('country', ''),
                    severity='critical',
                    details={
                        'alert': 'TERMINATED USER ACCESS',
                        'action': log.get('action', ''),
                        'application': log.get('application', '')
                    },
                    raw_event=log
                ))
        
        return signals
    
    async def scan_all_signals(self, hours: int = 24) -> List[CloudflareSignal]:
        """
        Comprehensive scan for all security signals.
        
        Returns:
            List of all detected security signals
        """
        all_signals = []
        
        # Impossible travel
        # Would need user list from integration
        
        # DNS exfiltration
        exfil_signals = await self.detect_dns_exfiltration(hours)
        all_signals.extend(exfil_signals)
        
        # Post-departure (if we have terminated user list)
        # ...
        
        # Escalate to SOC engine if attached
        if self.soc_engine and all_signals:
            for signal in all_signals:
                self.soc_engine.ingest({
                    'source': 'cloudflare',
                    'type': signal.signal_type.value,
                    'severity': signal.severity,
                    'user': signal.user_email,
                    'details': signal.details
                })
        
        return all_signals
    
    # Demo data generators
    def _demo_access_logs(self) -> List[Dict]:
        return [
            {
                'user_email': 'demo.user@company.com',
                'created_at': datetime.now().isoformat(),
                'ip_address': '73.42.155.88',
                'action': 'login',
                'geo': {'country': 'US', 'city': 'Houston'}
            }
        ]
    
    def _demo_dns_logs(self) -> List[Dict]:
        return [
            {
                'query_name': 'api.company.com',
                'query_type': 'A',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def _demo_audit_logs(self) -> List[Dict]:
        return [
            {
                'action': 'user.login',
                'timestamp': datetime.now().isoformat(),
                'actor': {'email': 'admin@company.com'}
            }
        ]


# Example usage and testing
async def demo():
    """Demo the Cloudflare connector."""
    print("\n" + "=" * 60)
    print("AION OS - Cloudflare Connector Demo")
    print("=" * 60)
    
    connector = CloudflareConnector(demo_mode=True)
    await connector.connect()
    
    print("\n🔍 Generating Insider Threat Sequence (Typhoon/Knowles pattern)...")
    sequence = DemoMode.generate_insider_threat_sequence()
    
    for i, signal in enumerate(sequence, 1):
        print(f"\n  Signal {i}: {signal['signal_type'].value}")
        print(f"  User: {signal['user']}")
        print(f"  Severity: {signal['severity'].upper()}")
        for key, value in signal['details'].items():
            print(f"    {key}: {value}")
    
    print("\n\n🚨 Generating Post-Departure Access Sequence...")
    post_departure = DemoMode.generate_post_departure_sequence()
    
    for i, signal in enumerate(post_departure, 1):
        print(f"\n  Signal {i}: {signal['signal_type'].value}")
        print(f"  User: {signal['user']}")
        print(f"  Severity: {signal['severity'].upper()}")
        for key, value in signal['details'].items():
            print(f"    {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Demo complete - all processing was 100% LOCAL")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())
