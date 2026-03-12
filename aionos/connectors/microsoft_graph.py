"""
Microsoft Graph API Connector for AION OS

Integrates with:
- Azure Active Directory (user status, roles, terminations)
- Office 365 (email rules, forwarding, sharing)
- SharePoint/OneDrive (document access, downloads)
- Sign-in logs (VPN, geographic anomalies)

Deployment: On-premise in client environment
Data: Never leaves client infrastructure
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Microsoft libraries - install with: pip install msal aiohttp
try:
    import msal
    import aiohttp
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False

logger = logging.getLogger(__name__)


class DemoMode:
    """
    Demo mode - simulates Microsoft Graph signals without real credentials.
    Use for demos, investor presentations, and testing.
    """
    
    DEMO_USERS = [
        {
            'id': 'demo-001',
            'email': 'sarah.johnson@demolaw.com',
            'display_name': 'Sarah Johnson',
            'job_title': 'Senior Partner',
            'department': 'Corporate M&A'
        },
        {
            'id': 'demo-002', 
            'email': 'michael.chen@demolaw.com',
            'display_name': 'Michael Chen',
            'job_title': 'Partner',
            'department': 'Litigation'
        },
        {
            'id': 'demo-003',
            'email': 'former.employee@demolaw.com',
            'display_name': 'Former Employee',
            'job_title': 'Associate',
            'department': 'IT'
        }
    ]
    
    @classmethod
    def generate_vpn_breach_sequence(cls) -> List[Dict]:
        """Generate the Typhoon attack sequence"""
        return [
            {
                'signal_type': SignalType.VPN_ANOMALY,
                'user': cls.DEMO_USERS[2],
                'severity': 'high',
                'details': {
                    'location': 'Eastern Europe VPN',
                    'ip_address': '185.42.33.100',
                    'time': '02:34 AM',
                    'baseline_locations': ['New York, NY', 'Home Office']
                },
                'delay': 0
            },
            {
                'signal_type': SignalType.AFTER_HOURS_ACCESS,
                'user': cls.DEMO_USERS[2],
                'severity': 'medium',
                'details': {
                    'access_time': '02:34 AM',
                    'typical_hours': '9 AM - 6 PM',
                    'systems_accessed': ['VPN Gateway', 'Internal Network']
                },
                'delay': 2
            },
            {
                'signal_type': SignalType.BULK_DOWNLOAD,
                'user': cls.DEMO_USERS[2],
                'severity': 'critical',
                'details': {
                    'download_count': 15000,
                    'data_type': 'Client Database Records',
                    'tables': ['clients', 'billing', 'campaigns', 'contacts'],
                    'estimated_value': '$2.3M'
                },
                'delay': 4
            },
            {
                'signal_type': SignalType.GEO_ANOMALY,
                'user': cls.DEMO_USERS[2],
                'severity': 'critical',
                'details': {
                    'new_location': 'Unknown - Eastern Europe',
                    'impossible_travel': True,
                    'last_known_location': 'New York, NY',
                    'time_between_logins': '2 hours'
                },
                'delay': 5
            }
        ]
    
    @classmethod
    def generate_departure_sequence(cls) -> List[Dict]:
        """Generate attorney departure exfiltration sequence"""
        return [
            {
                'signal_type': SignalType.EMAIL_FORWARD_CREATED,
                'user': cls.DEMO_USERS[0],
                'severity': 'critical',
                'details': {
                    'rule_name': 'Auto Forward',
                    'forward_to': 'sarah.personal@gmail.com',
                    'is_external': True,
                    'created': 'Today, 3:42 PM'
                },
                'delay': 0
            },
            {
                'signal_type': SignalType.BULK_DOWNLOAD,
                'user': cls.DEMO_USERS[0],
                'severity': 'high',
                'details': {
                    'download_count': 234,
                    'baseline_average': 45,
                    'increase_percentage': '520%',
                    'file_types': ['Client Contacts', 'Deal Memos', 'Pricing']
                },
                'delay': 3
            },
            {
                'signal_type': SignalType.SHARING_EXTERNAL,
                'user': cls.DEMO_USERS[0],
                'severity': 'high',
                'details': {
                    'sharing_links_created': 47,
                    'external_recipients': 3,
                    'sensitive_docs': True
                },
                'delay': 5
            },
            {
                'signal_type': SignalType.MAILBOX_RULE_CREATED,
                'user': cls.DEMO_USERS[0],
                'severity': 'medium',
                'details': {
                    'rule_name': 'Move to RSS Feeds',
                    'action': 'Hide incoming emails matching "HR" or "Exit"',
                    'suspicious': True
                },
                'delay': 7
            },
            {
                'signal_type': SignalType.AFTER_HOURS_ACCESS,
                'user': cls.DEMO_USERS[0],
                'severity': 'medium',
                'details': {
                    'after_hours_percentage': 68,
                    'recent_pattern': 'Last 7 days',
                    'systems': ['SharePoint', 'iManage', 'Email']
                },
                'delay': 8
            }
        ]


class SignalType(Enum):
    """Types of signals AION monitors"""
    USER_TERMINATED = "user_terminated"
    USER_DISABLED = "user_disabled"
    ROLE_CHANGED = "role_changed"
    EMAIL_FORWARD_CREATED = "email_forward_created"
    MAILBOX_RULE_CREATED = "mailbox_rule_created"
    BULK_DOWNLOAD = "bulk_download"
    AFTER_HOURS_ACCESS = "after_hours_access"
    GEO_ANOMALY = "geo_anomaly"
    SHARING_EXTERNAL = "sharing_external"
    FAILED_LOGIN_SPIKE = "failed_login_spike"
    NEW_DEVICE = "new_device"
    VPN_ANOMALY = "vpn_anomaly"


@dataclass
class GraphSignal:
    """A signal detected from Microsoft Graph"""
    signal_type: SignalType
    user_id: str
    user_email: str
    user_display_name: str
    severity: str  # critical, high, medium, low
    timestamp: datetime
    details: Dict[str, Any]
    raw_event: Optional[Dict] = None

    def to_soc_alert(self) -> Dict:
        """Convert to SOC ingestion format"""
        return {
            'alert_type': self.signal_type.value,
            'user_id': self.user_email,
            'severity': self.severity,
            'action': self._build_action_string(),
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'source': 'microsoft_graph'
        }

    def _build_action_string(self) -> str:
        """Human-readable action description"""
        descriptions = {
            SignalType.USER_TERMINATED: f"User {self.user_display_name} marked as terminated",
            SignalType.USER_DISABLED: f"User account {self.user_display_name} disabled",
            SignalType.EMAIL_FORWARD_CREATED: f"Email forwarding rule created for {self.user_display_name}",
            SignalType.MAILBOX_RULE_CREATED: f"New mailbox rule created by {self.user_display_name}",
            SignalType.BULK_DOWNLOAD: f"Bulk file download detected for {self.user_display_name}",
            SignalType.AFTER_HOURS_ACCESS: f"After-hours access by {self.user_display_name}",
            SignalType.GEO_ANOMALY: f"Geographic anomaly detected for {self.user_display_name}",
            SignalType.SHARING_EXTERNAL: f"External sharing by {self.user_display_name}",
            SignalType.VPN_ANOMALY: f"VPN anomaly detected for {self.user_display_name}",
        }
        return descriptions.get(self.signal_type, f"Signal: {self.signal_type.value}")


class MicrosoftGraphConnector:
    """
    Microsoft Graph API connector for AION OS
    
    Monitors Azure AD, O365, SharePoint for departure risk signals.
    Runs on-premise. Zero data leaves client environment.
    
    Required Azure AD App Registration:
    - Application (client) ID
    - Directory (tenant) ID  
    - Client secret or certificate
    
    Required API Permissions (Application):
    - User.Read.All
    - AuditLog.Read.All
    - MailboxSettings.Read
    - Sites.Read.All
    - Directory.Read.All
    """

    GRAPH_URL = "https://graph.microsoft.com/v1.0"
    GRAPH_BETA_URL = "https://graph.microsoft.com/beta"

    def __init__(
        self,
        tenant_id: str = None,
        client_id: str = None,
        client_secret: str = None,
        config_path: str = None
    ):
        """
        Initialize the connector.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: App registration client ID
            client_secret: App registration secret
            config_path: Path to config file (alternative to params)
        """
        if not GRAPH_AVAILABLE:
            raise ImportError(
                "Microsoft Graph dependencies not installed. "
                "Run: pip install msal aiohttp"
            )

        # Load config
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            self.tenant_id = config.get('tenant_id')
            self.client_id = config.get('client_id')
            self.client_secret = config.get('client_secret')
        else:
            self.tenant_id = tenant_id or os.getenv('AZURE_TENANT_ID')
            self.client_id = client_id or os.getenv('AZURE_CLIENT_ID')
            self.client_secret = client_secret or os.getenv('AZURE_CLIENT_SECRET')

        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError(
                "Missing Azure credentials. Provide tenant_id, client_id, and client_secret "
                "via parameters, config file, or environment variables."
            )

        # Initialize MSAL client
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )

        self._token = None
        self._token_expiry = None

        # Monitoring state
        self.watched_users: Dict[str, Dict] = {}  # user_id -> user info + risk factors
        self.baseline_data: Dict[str, Dict] = {}  # user_id -> behavioral baseline

        # SOC integration
        self.soc_engine = None

        logger.info(f"Microsoft Graph connector initialized for tenant {self.tenant_id[:8]}...")

    async def connect(self) -> bool:
        """Establish connection and verify credentials"""
        try:
            await self._get_token()
            # Test connection
            async with aiohttp.ClientSession() as session:
                headers = await self._get_headers()
                async with session.get(
                    f"{self.GRAPH_URL}/organization",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        org_name = data['value'][0].get('displayName', 'Unknown')
                        logger.info(f"Connected to: {org_name}")
                        return True
                    else:
                        logger.error(f"Connection failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def _get_token(self) -> str:
        """Get or refresh access token"""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        result = self.app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )

        if "access_token" in result:
            self._token = result["access_token"]
            self._token_expiry = datetime.now() + timedelta(minutes=55)
            return self._token
        else:
            raise Exception(f"Token acquisition failed: {result.get('error_description')}")

    async def _get_headers(self) -> Dict:
        """Get authorization headers"""
        token = await self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    # =========================================================================
    # USER MONITORING
    # =========================================================================

    async def watch_user(self, user_email: str) -> Dict:
        """
        Add a user to the watch list for departure risk monitoring.
        Establishes behavioral baseline.
        """
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()

            # Get user details
            async with session.get(
                f"{self.GRAPH_URL}/users/{user_email}",
                headers=headers
            ) as response:
                if response.status != 200:
                    return {"error": f"User not found: {user_email}"}
                user_data = await response.json()

            user_id = user_data['id']

            # Store user info
            self.watched_users[user_id] = {
                'email': user_email,
                'display_name': user_data.get('displayName'),
                'job_title': user_data.get('jobTitle'),
                'department': user_data.get('department'),
                'added_at': datetime.now().isoformat(),
                'risk_score': 0
            }

            # Build baseline
            await self._build_baseline(user_id, session, headers)

            logger.info(f"Now watching: {user_email}")
            return self.watched_users[user_id]

    async def _build_baseline(self, user_id: str, session, headers) -> None:
        """Build behavioral baseline for a user"""
        baseline = {
            'avg_emails_per_day': 0,
            'avg_files_accessed_per_day': 0,
            'typical_login_hours': [],
            'typical_locations': [],
            'known_devices': [],
            'mailbox_rules_count': 0
        }

        # Get recent sign-in activity for baseline
        try:
            async with session.get(
                f"{self.GRAPH_BETA_URL}/auditLogs/signIns?$filter=userId eq '{user_id}'&$top=100",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    sign_ins = data.get('value', [])

                    locations = set()
                    devices = set()
                    hours = []

                    for sign_in in sign_ins:
                        if sign_in.get('location', {}).get('city'):
                            locations.add(sign_in['location']['city'])
                        if sign_in.get('deviceDetail', {}).get('deviceId'):
                            devices.add(sign_in['deviceDetail']['deviceId'])
                        if sign_in.get('createdDateTime'):
                            try:
                                dt = datetime.fromisoformat(sign_in['createdDateTime'].replace('Z', '+00:00'))
                                hours.append(dt.hour)
                            except:
                                pass

                    baseline['typical_locations'] = list(locations)
                    baseline['known_devices'] = list(devices)
                    baseline['typical_login_hours'] = list(set(hours))

        except Exception as e:
            logger.warning(f"Could not build sign-in baseline: {e}")

        # Get mailbox rules count
        try:
            user_email = self.watched_users[user_id]['email']
            async with session.get(
                f"{self.GRAPH_URL}/users/{user_email}/mailFolders/inbox/messageRules",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    baseline['mailbox_rules_count'] = len(data.get('value', []))
        except Exception as e:
            logger.warning(f"Could not get mailbox rules: {e}")

        self.baseline_data[user_id] = baseline

    # =========================================================================
    # SIGNAL DETECTION
    # =========================================================================

    async def scan_all_signals(self) -> List[GraphSignal]:
        """Run all signal detection scans"""
        signals = []

        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()

            # Run all detectors
            signals.extend(await self._detect_email_forwards(session, headers))
            signals.extend(await self._detect_mailbox_rules(session, headers))
            signals.extend(await self._detect_geo_anomalies(session, headers))
            signals.extend(await self._detect_after_hours(session, headers))
            signals.extend(await self._detect_bulk_downloads(session, headers))
            signals.extend(await self._detect_external_sharing(session, headers))

        # Feed signals to SOC
        if self.soc_engine and signals:
            for signal in signals:
                self.soc_engine.ingest_alert(signal.to_soc_alert(), auto_escalate=True)

        return signals

    async def _detect_email_forwards(self, session, headers) -> List[GraphSignal]:
        """Detect new email forwarding rules"""
        signals = []

        for user_id, user_info in self.watched_users.items():
            try:
                async with session.get(
                    f"{self.GRAPH_URL}/users/{user_info['email']}/mailFolders/inbox/messageRules",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    rules = data.get('value', [])

                    baseline_count = self.baseline_data.get(user_id, {}).get('mailbox_rules_count', 0)

                    for rule in rules:
                        # Check for forwarding rules
                        actions = rule.get('actions', {})
                        forward_to = actions.get('forwardTo', [])
                        redirect_to = actions.get('redirectTo', [])

                        all_forwards = forward_to + redirect_to

                        for recipient in all_forwards:
                            email = recipient.get('emailAddress', {}).get('address', '')

                            # External forwarding is HIGH risk
                            if email and not email.endswith(user_info['email'].split('@')[1]):
                                signals.append(GraphSignal(
                                    signal_type=SignalType.EMAIL_FORWARD_CREATED,
                                    user_id=user_id,
                                    user_email=user_info['email'],
                                    user_display_name=user_info['display_name'],
                                    severity='critical' if 'gmail' in email or 'yahoo' in email else 'high',
                                    timestamp=datetime.now(),
                                    details={
                                        'rule_name': rule.get('displayName'),
                                        'forward_to': email,
                                        'is_external': True
                                    },
                                    raw_event=rule
                                ))

            except Exception as e:
                logger.warning(f"Email forward detection failed for {user_id}: {e}")

        return signals

    async def _detect_mailbox_rules(self, session, headers) -> List[GraphSignal]:
        """Detect suspicious mailbox rules (delete, move to hide)"""
        signals = []

        for user_id, user_info in self.watched_users.items():
            try:
                async with session.get(
                    f"{self.GRAPH_URL}/users/{user_info['email']}/mailFolders/inbox/messageRules",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    rules = data.get('value', [])

                    for rule in rules:
                        actions = rule.get('actions', {})

                        # Suspicious: delete permanently
                        if actions.get('permanentDelete'):
                            signals.append(GraphSignal(
                                signal_type=SignalType.MAILBOX_RULE_CREATED,
                                user_id=user_id,
                                user_email=user_info['email'],
                                user_display_name=user_info['display_name'],
                                severity='high',
                                timestamp=datetime.now(),
                                details={
                                    'rule_name': rule.get('displayName'),
                                    'action': 'permanent_delete',
                                    'suspicious': True
                                },
                                raw_event=rule
                            ))

                        # Suspicious: move to obscure folder
                        if actions.get('moveToFolder') and 'RSS' in str(actions.get('moveToFolder', '')):
                            signals.append(GraphSignal(
                                signal_type=SignalType.MAILBOX_RULE_CREATED,
                                user_id=user_id,
                                user_email=user_info['email'],
                                user_display_name=user_info['display_name'],
                                severity='medium',
                                timestamp=datetime.now(),
                                details={
                                    'rule_name': rule.get('displayName'),
                                    'action': 'move_to_hidden_folder',
                                    'suspicious': True
                                },
                                raw_event=rule
                            ))

            except Exception as e:
                logger.warning(f"Mailbox rule detection failed for {user_id}: {e}")

        return signals

    async def _detect_geo_anomalies(self, session, headers) -> List[GraphSignal]:
        """Detect logins from unusual locations"""
        signals = []

        for user_id, user_info in self.watched_users.items():
            try:
                # Get recent sign-ins
                async with session.get(
                    f"{self.GRAPH_BETA_URL}/auditLogs/signIns?$filter=userId eq '{user_id}'&$top=20&$orderby=createdDateTime desc",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    sign_ins = data.get('value', [])

                    baseline_locations = set(self.baseline_data.get(user_id, {}).get('typical_locations', []))

                    for sign_in in sign_ins:
                        location = sign_in.get('location', {})
                        city = location.get('city', '')
                        country = location.get('countryOrRegion', '')

                        if city and city not in baseline_locations:
                            # New location detected
                            signals.append(GraphSignal(
                                signal_type=SignalType.GEO_ANOMALY,
                                user_id=user_id,
                                user_email=user_info['email'],
                                user_display_name=user_info['display_name'],
                                severity='high' if country not in ['US', 'United States'] else 'medium',
                                timestamp=datetime.now(),
                                details={
                                    'new_location': f"{city}, {country}",
                                    'ip_address': sign_in.get('ipAddress'),
                                    'baseline_locations': list(baseline_locations),
                                    'app_used': sign_in.get('appDisplayName')
                                },
                                raw_event=sign_in
                            ))

            except Exception as e:
                logger.warning(f"Geo anomaly detection failed for {user_id}: {e}")

        return signals

    async def _detect_after_hours(self, session, headers) -> List[GraphSignal]:
        """Detect after-hours access patterns"""
        signals = []

        # Define business hours (customize per client)
        business_start = 7
        business_end = 20

        for user_id, user_info in self.watched_users.items():
            try:
                async with session.get(
                    f"{self.GRAPH_BETA_URL}/auditLogs/signIns?$filter=userId eq '{user_id}'&$top=50&$orderby=createdDateTime desc",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    sign_ins = data.get('value', [])

                    after_hours_count = 0
                    for sign_in in sign_ins:
                        try:
                            dt = datetime.fromisoformat(sign_in['createdDateTime'].replace('Z', '+00:00'))
                            if dt.hour < business_start or dt.hour > business_end:
                                after_hours_count += 1
                        except:
                            pass

                    # Alert if >30% of recent activity is after hours
                    if sign_ins and (after_hours_count / len(sign_ins)) > 0.3:
                        signals.append(GraphSignal(
                            signal_type=SignalType.AFTER_HOURS_ACCESS,
                            user_id=user_id,
                            user_email=user_info['email'],
                            user_display_name=user_info['display_name'],
                            severity='medium',
                            timestamp=datetime.now(),
                            details={
                                'after_hours_percentage': round((after_hours_count / len(sign_ins)) * 100),
                                'after_hours_count': after_hours_count,
                                'total_sign_ins': len(sign_ins)
                            }
                        ))

            except Exception as e:
                logger.warning(f"After hours detection failed for {user_id}: {e}")

        return signals

    async def _detect_bulk_downloads(self, session, headers) -> List[GraphSignal]:
        """Detect bulk file downloads from SharePoint/OneDrive"""
        signals = []

        for user_id, user_info in self.watched_users.items():
            try:
                # Query audit logs for file downloads
                async with session.get(
                    f"{self.GRAPH_BETA_URL}/auditLogs/directoryAudits?$filter=initiatedBy/user/id eq '{user_id}'",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    audits = data.get('value', [])

                    # Count file-related activities
                    file_downloads = [a for a in audits if 'download' in a.get('activityDisplayName', '').lower()]

                    if len(file_downloads) > 50:  # Threshold
                        signals.append(GraphSignal(
                            signal_type=SignalType.BULK_DOWNLOAD,
                            user_id=user_id,
                            user_email=user_info['email'],
                            user_display_name=user_info['display_name'],
                            severity='critical' if len(file_downloads) > 100 else 'high',
                            timestamp=datetime.now(),
                            details={
                                'download_count': len(file_downloads),
                                'threshold': 50
                            }
                        ))

            except Exception as e:
                logger.warning(f"Bulk download detection failed for {user_id}: {e}")

        return signals

    async def _detect_external_sharing(self, session, headers) -> List[GraphSignal]:
        """Detect external file sharing"""
        signals = []

        for user_id, user_info in self.watched_users.items():
            try:
                # Get user's OneDrive
                async with session.get(
                    f"{self.GRAPH_URL}/users/{user_info['email']}/drive/sharedWithMe",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        continue

                    # Check for sharing activities in audit logs
                    async with session.get(
                        f"{self.GRAPH_BETA_URL}/auditLogs/directoryAudits?$filter=initiatedBy/user/id eq '{user_id}' and activityDisplayName eq 'Add sharing link'",
                        headers=headers
                    ) as audit_response:
                        if audit_response.status == 200:
                            data = await audit_response.json()
                            shares = data.get('value', [])

                            if len(shares) > 10:  # Many sharing links created
                                signals.append(GraphSignal(
                                    signal_type=SignalType.SHARING_EXTERNAL,
                                    user_id=user_id,
                                    user_email=user_info['email'],
                                    user_display_name=user_info['display_name'],
                                    severity='high',
                                    timestamp=datetime.now(),
                                    details={
                                        'sharing_links_created': len(shares)
                                    }
                                ))

            except Exception as e:
                logger.warning(f"External sharing detection failed for {user_id}: {e}")

        return signals

    # =========================================================================
    # CONTINUOUS MONITORING
    # =========================================================================

    async def start_monitoring(self, interval_seconds: int = 300):
        """
        Start continuous monitoring loop.
        
        Args:
            interval_seconds: Scan interval (default 5 minutes)
        """
        logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")

        while True:
            try:
                signals = await self.scan_all_signals()

                if signals:
                    logger.info(f"Detected {len(signals)} signals")
                    for signal in signals:
                        logger.warning(f"[{signal.severity.upper()}] {signal.signal_type.value}: {signal.user_email}")

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    def attach_soc_engine(self, soc_engine):
        """Attach SOC ingestion engine for automatic alert processing"""
        self.soc_engine = soc_engine
        logger.info("SOC engine attached - signals will auto-escalate")

    # =========================================================================
    # MANUAL INVESTIGATIONS
    # =========================================================================

    async def investigate_user(self, user_email: str) -> Dict:
        """
        Full investigation of a user's recent activity.
        Returns comprehensive risk assessment.
        """
        async with aiohttp.ClientSession() as session:
            headers = await self._get_headers()

            # Get user info
            async with session.get(
                f"{self.GRAPH_URL}/users/{user_email}",
                headers=headers
            ) as response:
                if response.status != 200:
                    return {"error": "User not found"}
                user_data = await response.json()

            user_id = user_data['id']

            investigation = {
                'user': {
                    'email': user_email,
                    'display_name': user_data.get('displayName'),
                    'job_title': user_data.get('jobTitle'),
                    'department': user_data.get('department')
                },
                'risk_score': 0,
                'findings': [],
                'signals': [],
                'recommendations': []
            }

            # Add to watch list temporarily for investigation
            self.watched_users[user_id] = {
                'email': user_email,
                'display_name': user_data.get('displayName'),
                'job_title': user_data.get('jobTitle'),
                'department': user_data.get('department'),
                'added_at': datetime.now().isoformat(),
                'risk_score': 0
            }

            await self._build_baseline(user_id, session, headers)

            # Run all detectors
            signals = await self.scan_all_signals()

            # Filter to this user only
            user_signals = [s for s in signals if s.user_id == user_id]

            # Calculate risk score
            severity_scores = {'critical': 30, 'high': 20, 'medium': 10, 'low': 5}
            for signal in user_signals:
                investigation['risk_score'] += severity_scores.get(signal.severity, 5)
                investigation['findings'].append({
                    'type': signal.signal_type.value,
                    'severity': signal.severity,
                    'details': signal.details
                })

            investigation['risk_score'] = min(100, investigation['risk_score'])

            # Add recommendations based on findings
            if investigation['risk_score'] >= 70:
                investigation['recommendations'].append("IMMEDIATE: Disable external email forwarding")
                investigation['recommendations'].append("IMMEDIATE: Revoke cloud sync permissions")
                investigation['recommendations'].append("Review all mailbox rules created in past 30 days")

            if investigation['risk_score'] >= 50:
                investigation['recommendations'].append("Conduct exit interview with IT present")
                investigation['recommendations'].append("Preserve all email and document access logs")

            # Cleanup
            del self.watched_users[user_id]

            return investigation


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Microsoft Graph Connector for AION OS")
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--watch", type=str, help="Add user to watch list")
    parser.add_argument("--investigate", type=str, help="Full investigation of user")
    parser.add_argument("--scan", action="store_true", help="Run signal scan")

    args = parser.parse_args()

    async def main():
        connector = MicrosoftGraphConnector()

        if args.test:
            connected = await connector.connect()
            print(f"Connection: {'SUCCESS' if connected else 'FAILED'}")

        elif args.watch:
            await connector.connect()
            result = await connector.watch_user(args.watch)
            print(f"Watching: {result}")

        elif args.investigate:
            await connector.connect()
            result = await connector.investigate_user(args.investigate)
            print(json.dumps(result, indent=2, default=str))

        elif args.scan:
            await connector.connect()
            signals = await connector.scan_all_signals()
            for signal in signals:
                print(f"[{signal.severity}] {signal.signal_type.value}: {signal.user_email}")

    asyncio.run(main())
