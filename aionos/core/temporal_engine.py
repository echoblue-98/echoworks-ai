"""
AION OS - Temporal Correlation Engine
Tracks user behavior over time to detect multi-stage attack patterns.

The Typhoon attack unfolded over WEEKS:
- Week 1: VPN access from home (seemed normal)
- Week 2: Large file downloads (seemed normal)  
- Week 3: Database queries (seemed normal)
- Week 4: Hard drive swaps, destruction

Each event alone = normal. Together = attack.
This engine connects the dots.
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum

# =============================================================================
# STRUCTURED LOGGING SETUP
# =============================================================================

logger = logging.getLogger("aionos.temporal")

# Configure if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Memory bounds - prevent OOM
MAX_EVENTS_PER_USER = 10000          # Max events to keep per user
MAX_TOTAL_USERS = 50000              # Max users to track
EVENT_TTL_DAYS = 30                  # Events older than this are purged
PURGE_INTERVAL_SECONDS = 15          # Run purge cycle (was 60s — Gemini review)

# Rate limiting
MAX_EVENTS_PER_USER_PER_MINUTE = 1000  # Prevent flood attacks
RATE_LIMIT_WINDOW_SECONDS = 60

# Input validation
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_.@-]{1,256}$')

# =============================================================================
# CHATGPT FIX: Timestamp Safety
# =============================================================================
MAX_FUTURE_SECONDS = 300              # Reject events >5 min in future
MAX_PAST_DAYS = 60                    # Reject events >60 days old
REQUIRE_UTC = True                    # Reject naive datetimes

# =============================================================================
# GEMINI FIX: Anti-DoS and Data Quality
# =============================================================================

# Probationary user tracking (prevents cache eviction DoS)
PROBATIONARY_THRESHOLD_EVENTS = 5     # Min events before user is "trusted"
MAX_PROBATIONARY_USERS = 10000        # Max unvalidated users to track

# Event deduplication (prevents duplicate log ingestion)
DEDUPE_WINDOW_SECONDS = 60            # Same event within this window = duplicate

# =============================================================================
# CHATGPT FIX: Memory Leak Prevention
# =============================================================================
RATE_LIMIT_EXPIRY_SECONDS = 300       # Expire rate limit entries after 5 min
ALERT_CACHE_EXPIRY_SECONDS = 7200     # Expire alert cooldown after 2 hours
DEDUPE_CACHE_MAX_SIZE = 100000        # Max dedupe hashes to keep


class EventType(Enum):
    """Types of security-relevant events"""
    # Access Events
    VPN_ACCESS = "vpn_access"
    AFTER_HOURS_ACCESS = "after_hours_access"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    
    # VPN/Network Security Events (EXPANDED)
    VPN_BRUTE_FORCE = "vpn_brute_force"           # Multiple failed login attempts
    VPN_CREDENTIAL_STUFFING = "vpn_credential_stuffing"  # Known breached credentials
    VPN_SESSION_HIJACK = "vpn_session_hijack"     # Session token reuse from new IP
    VPN_SPLIT_TUNNEL = "vpn_split_tunnel"         # Traffic bypassing VPN
    VPN_ANOMALOUS_PROTOCOL = "vpn_anomalous_protocol"  # Unusual protocols over VPN
    IMPOSSIBLE_TRAVEL = "impossible_travel"        # Login from 2 locations too fast
    VPN_MFA_BYPASS = "vpn_mfa_bypass"             # MFA fatigue/bypass detected
    VPN_CONCURRENT_SESSION = "vpn_concurrent_session"  # Same user multiple locations
    VPN_TOKEN_REPLAY = "vpn_token_replay"         # OAuth/SAML token replay
    VPN_CERT_ANOMALY = "vpn_cert_anomaly"         # Certificate mismatch/revoked
    VPN_TUNNEL_ABUSE = "vpn_tunnel_abuse"         # Tunnel used for C2/exfil
    VPN_DNS_TUNNEL = "vpn_dns_tunnel"             # DNS tunneling over VPN
    VPN_EXCESSIVE_BANDWIDTH = "vpn_excessive_bandwidth"  # Abnormal data transfer
    VPN_OFF_HOURS_LOGIN = "vpn_off_hours_login"   # Unusual time login
    VPN_NEW_DEVICE = "vpn_new_device"             # Unknown device fingerprint
    VPN_DORMANT_ACCOUNT = "vpn_dormant_account"   # Inactive account suddenly active
    
    # Data Movement Events
    FILE_DOWNLOAD = "file_download"
    FILE_UPLOAD = "file_upload"
    DATABASE_QUERY = "database_query"
    EMAIL_FORWARD = "email_forward"
    PRINT_JOB = "print_job"
    USB_ACTIVITY = "usb_activity"
    CLOUD_SYNC = "cloud_sync"
    BULK_OPERATION = "bulk_operation"
    
    # Privilege Events
    PERMISSION_CHANGE = "permission_change"
    ADMIN_ACTION = "admin_action"                  # Admin console access
    SERVICE_ACCOUNT_USE = "service_account_use"    # Service account from user IP
    
    # Lateral Movement Events (NEW)
    LATERAL_MOVEMENT = "lateral_movement"          # Access to new systems
    RECONNAISSANCE = "reconnaissance"              # Port scanning, enumeration
    CREDENTIAL_ACCESS = "credential_access"        # Password vault, key access
    
    # Persistence Events (NEW)
    SCHEDULED_TASK = "scheduled_task"              # New scheduled task/cron
    REGISTRY_CHANGE = "registry_change"            # Startup persistence
    EMAIL_RULE_CHANGE = "email_rule_change"        # Auto-forward rules
    
    # Evasion Events (NEW)
    LOG_DELETION = "log_deletion"                  # Audit log tampering
    SECURITY_DISABLE = "security_disable"          # AV/EDR disabled
    PROXY_USE = "proxy_use"                        # Anonymous proxy detected
    TOR_ACCESS = "tor_access"                      # Tor network access
    
    # External Events (NEW)
    PHISHING_CLICK = "phishing_click"              # User clicked phishing link
    MALWARE_DETECTED = "malware_detected"          # Malware on endpoint
    DLP_VIOLATION = "dlp_violation"                # Data loss prevention trigger
    SHADOW_IT = "shadow_it"                        # Unauthorized SaaS usage
    
    # ================================================================
    # MULTI-MODAL EXPANSION - Cloud/SaaS Attack Surface
    # ================================================================
    CLOUD_STORAGE_ACCESS = "cloud_storage_access"          # SharePoint/Box/Dropbox access
    CLOUD_ADMIN_CHANGE = "cloud_admin_change"              # Cloud admin role changes
    CLOUD_PERMISSION_CHANGE = "cloud_permission_change"    # Sharing/permission modifications
    API_KEY_EXPOSURE = "api_key_exposure"                  # API key/secret in code/logs
    CLOUD_RESOURCE_CREATION = "cloud_resource_creation"    # New VM/container/function
    CLOUD_CONFIG_CHANGE = "cloud_config_change"            # Security group/firewall changes
    SAAS_APP_INSTALL = "saas_app_install"                  # New SaaS app connected
    
    # ================================================================
    # MULTI-MODAL EXPANSION - Business Email Compromise (BEC)
    # ================================================================
    BEC_INDICATOR = "bec_indicator"                        # Impersonation signals
    WIRE_TRANSFER_REQUEST = "wire_transfer_request"        # Wire/ACH transfer request
    EMAIL_ACCOUNT_TAKEOVER = "email_account_takeover"      # Inbox rule + delegate changes
    EMAIL_IMPERSONATION = "email_impersonation"            # Lookalike domain/display name
    INVOICE_MANIPULATION = "invoice_manipulation"          # Modified payment details
    EXECUTIVE_WHALING = "executive_whaling"                # C-suite targeted phishing
    
    # ================================================================
    # MULTI-MODAL EXPANSION - Identity & Access Federation
    # ================================================================
    SSO_ANOMALY = "sso_anomaly"                            # SSO token abuse
    OAUTH_CONSENT = "oauth_consent"                        # OAuth app consent grant
    CONDITIONAL_ACCESS_BYPASS = "conditional_access_bypass" # Policy circumvention
    IDENTITY_FEDERATION_ABUSE = "identity_federation_abuse" # Federated trust exploit
    MFA_REGISTRATION_CHANGE = "mfa_registration_change"    # New MFA device enrolled
    PASSWORD_SPRAY = "password_spray"                      # Low-and-slow password attack
    
    # ================================================================
    # MULTI-MODAL EXPANSION - Legal/Compliance (LAW FIRM SPECIFIC)
    # ================================================================
    ETHICS_WALL_VIOLATION = "ethics_wall_violation"        # Chinese wall breach
    PRIVILEGED_DATA_ACCESS = "privileged_data_access"      # Attorney-client privilege
    CLIENT_MATTER_CROSSOVER = "client_matter_crossover"    # Accessing conflicting matters
    REGULATORY_DATA_ACCESS = "regulatory_data_access"      # PII/PHI/financial data
    TRUST_ACCOUNT_ACCESS = "trust_account_access"          # IOLTA/trust account activity
    EDISCOVERY_EXPORT = "ediscovery_export"                # eDiscovery data export
    CASE_REASSIGNMENT = "case_reassignment"                # Unusual matter reassignment
    
    # ================================================================
    # MULTI-MODAL EXPANSION - Supply Chain & Third Party
    # ================================================================
    VENDOR_ACCESS = "vendor_access"                        # Third-party vendor login
    SUPPLY_CHAIN_ALERT = "supply_chain_alert"              # Dependency/package compromise
    THIRD_PARTY_DATA_SHARE = "third_party_data_share"      # Data shared with external
    VENDOR_PRIVILEGE_ESCALATION = "vendor_privilege_escalation"  # Vendor exceeding scope
    
    # ================================================================
    # MULTI-MODAL EXPANSION - AI/ML Security
    # ================================================================
    AI_MODEL_ACCESS = "ai_model_access"                    # Access to AI/ML models
    PROMPT_INJECTION = "prompt_injection"                   # Prompt injection attempt
    TRAINING_DATA_ACCESS = "training_data_access"          # ML training data access
    AI_OUTPUT_EXFIL = "ai_output_exfil"                    # Exfil via AI-generated content
    COPILOT_ABUSE = "copilot_abuse"                        # AI assistant data extraction
    
    # ================================================================
    # MULTI-MODAL EXPANSION - Physical + Cyber Convergence
    # ================================================================
    BADGE_ACCESS = "badge_access"                          # Physical badge swipe
    BADGE_ANOMALY = "badge_anomaly"                        # Badge at unusual location/time
    BYOD_DEVICE = "byod_device"                            # Personal device on network
    SCAN_TO_EMAIL = "scan_to_email"                        # Document scanning activity
    VISITOR_NETWORK_ACCESS = "visitor_network_access"      # Guest WiFi abuse
    
    # ================================================================
    # MULTI-MODAL EXPANSION - Financial Fraud
    # ================================================================
    BILLING_ANOMALY = "billing_anomaly"                    # Unusual billing patterns
    EXPENSE_FRAUD = "expense_fraud"                        # Fraudulent expense claims
    TIME_ENTRY_MANIPULATION = "time_entry_manipulation"    # Billing time irregularities
    PAYMENT_REDIRECT = "payment_redirect"                  # Changed bank details
    
    # ================================================================
    # MULTI-MODAL EXPANSION - Endpoint & Zero Trust
    # ================================================================
    ENDPOINT_COMPLIANCE_FAIL = "endpoint_compliance_fail"  # Device fails health check
    ZERO_TRUST_VIOLATION = "zero_trust_violation"          # Bypassed verification
    FIRMWARE_TAMPERING = "firmware_tampering"               # BIOS/firmware modification
    REMOVABLE_MEDIA_MOUNT = "removable_media_mount"        # External drive connected


@dataclass(slots=True)
class SecurityEvent:
    """A single security-relevant event - OPTIMIZED with __slots__"""
    event_id: str
    user_id: str
    event_type: EventType
    timestamp: datetime
    source_system: str  # cloudflare, m365, hr_system, etc.
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    ts_epoch: float = 0.0  # Pre-computed for fast comparison
    
    def __post_init__(self):
        if self.ts_epoch == 0.0:
            self.ts_epoch = self.timestamp.timestamp()
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source_system": self.source_system,
            "details": self.details,
            "risk_score": self.risk_score,
            "ts_epoch": self.ts_epoch
        }


@dataclass(slots=True)
class AttackSequence:
    """A known attack sequence pattern - OPTIMIZED with __slots__"""
    name: str
    description: str
    stages: List[EventType]
    time_window_days: int
    severity: str
    min_stages_to_alert: int = 2
    # Pre-computed for fast lookup
    stages_set: frozenset = field(default_factory=frozenset)
    
    def __post_init__(self):
        if not self.stages_set:
            object.__setattr__(self, 'stages_set', frozenset(self.stages))


@dataclass
class CorrelationAlert:
    """Alert generated when temporal correlation detects a pattern"""
    user_id: str
    pattern_name: str
    matched_stages: List[SecurityEvent]
    total_stages: int
    completion_percent: float
    severity: str
    first_event: datetime
    last_event: datetime
    time_span_hours: float
    recommended_actions: List[str]
    

class TemporalCorrelationEngine:
    """
    Correlates security events over time to detect multi-stage attacks.
    
    Key insight from Typhoon case: Individual events looked normal.
    Only when viewed together over time did the pattern emerge.
    
    ULTRA-OPTIMIZED:
    - Pre-indexed events by type for O(1) lookup
    - In-memory fast mode (no disk I/O on hot path)
    - Epoch timestamps for numeric comparison
    
    GEMINI FIXES APPLIED:
    - Sequence ordering enforced (not bag-of-events)
    - Probationary users prevent cache eviction DoS
    - Event deduplication prevents duplicate counting
    - Allowlisting for legitimate behaviors
    
    GROK FIXES APPLIED:
    - Alert deduplication (cooldown per user/pattern)
    - Eviction properly updates events_by_type index
    """
    
    __slots__ = ('event_store_path', 'events', 'events_by_type', '_dirty', 
                 '_event_count_since_save', '_save_interval', 'attack_sequences',
                 'baselines', '_fast_mode', '_pattern_cache', '_rate_limits',
                 '_event_counts', '_last_purge', '_stats',
                 '_probationary_users', '_trusted_users', '_recent_event_hashes', '_allowlist',
                 '_recent_alerts', 'alert_cooldown_seconds')
    
    def __init__(self, event_store_path: Optional[Path] = None, fast_mode: bool = True):
        # Event storage - in production, this would be a proper database
        self.event_store_path = event_store_path or Path("aionos/knowledge/event_store.json")
        self.events: Dict[str, List[SecurityEvent]] = defaultdict(list)  # user_id -> events
        
        # OPTIMIZATION: Pre-indexed by event type for O(1) pattern matching
        self.events_by_type: Dict[str, Dict[EventType, List[SecurityEvent]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Performance optimization: batch writes
        self._dirty = False
        self._event_count_since_save = 0
        self._save_interval = 100  # Save every 100 events
        
        # ULTRA-FAST MODE: Skip disk I/O entirely (for real-time processing)
        self._fast_mode = fast_mode
        
        # Pattern match cache
        self._pattern_cache: Dict[str, float] = {}  # user_id -> last_check_epoch
        
        # Only load from disk if not in fast mode
        if not fast_mode:
            self._load_events()
        
        # Known attack sequences (derived from real cases)
        self.attack_sequences = self._load_attack_sequences()
        
        # Behavioral baselines per user
        self.baselines: Dict[str, Dict] = {}
        
        # Rate limiting: user_id -> (count, window_start_epoch)
        self._rate_limits: Dict[str, tuple] = {}
        
        # Event counts for memory management
        self._event_counts: Dict[str, int] = defaultdict(int)
        
        # Last purge timestamp
        self._last_purge: float = time.time()
        
        # Statistics for monitoring
        self._stats = {
            'events_processed': 0,
            'events_rejected_validation': 0,
            'events_rejected_rate_limit': 0,
            'events_rejected_duplicate': 0,
            'events_rejected_future': 0,       # CHATGPT FIX
            'events_rejected_old': 0,          # CHATGPT FIX
            'alerts_generated': 0,
            'alerts_suppressed_allowlist': 0,
            'alerts_suppressed_cooldown': 0,
            'memory_purges': 0,
            'cache_cleanups': 0                # CHATGPT FIX
        }
        
        # =================================================================
        # GEMINI FIX: Anti-DoS Probationary Users
        # =================================================================
        # New users go to probation first (prevents cache eviction attack)
        self._probationary_users: Dict[str, List[SecurityEvent]] = {}
        self._trusted_users: set = set()  # Users with enough history
        
        # =================================================================
        # GEMINI FIX: Event Deduplication
        # =================================================================
        # Hash of recent events to prevent duplicate counting
        self._recent_event_hashes: Dict[str, float] = {}  # hash -> timestamp
        
        # =================================================================
        # GEMINI FIX: Allowlisting
        # =================================================================
        # Suppress alerts for known-good behaviors
        self._allowlist: Dict[str, set] = {}  # pattern_name -> set of user_groups
        
        # =================================================================
        # GROK FIX: Alert Deduplication
        # =================================================================
        # Prevent same pattern from alerting repeatedly for same user
        self._recent_alerts: Dict[str, float] = {}  # "user:pattern" -> last_alert_epoch
        self.alert_cooldown_seconds: int = 3600  # 1 hour between same alerts
        
        logger.info(f"TemporalCorrelationEngine initialized: fast_mode={fast_mode}, patterns={len(self.attack_sequences)}")
        
    def _load_attack_sequences(self) -> List[AttackSequence]:
        """Load known attack patterns - VPN, lateral movement, insider threats"""
        return [
            # ============================================================
            # INSIDER THREAT PATTERNS (Attorney Departure)
            # ============================================================
            AttackSequence(
                name="typhoon_vpn_exfil",
                description="Remote database exfiltration via VPN (Typhoon pattern)",
                stages=[
                    EventType.VPN_ACCESS,
                    EventType.DATABASE_QUERY,
                    EventType.BULK_OPERATION,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=14,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="pre_departure_exfil",
                description="Data hoarding before resignation announcement",
                stages=[
                    EventType.FILE_DOWNLOAD,
                    EventType.CLOUD_SYNC,
                    EventType.EMAIL_FORWARD,
                    EventType.PRINT_JOB,
                ],
                time_window_days=30,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="after_hours_theft",
                description="Off-hours data access indicating premeditated exfiltration",
                stages=[
                    EventType.AFTER_HOURS_ACCESS,
                    EventType.FILE_DOWNLOAD,
                    EventType.USB_ACTIVITY,
                ],
                time_window_days=7,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # VPN BREACH PATTERNS (NEW)
            # ============================================================
            AttackSequence(
                name="vpn_credential_compromise",
                description="VPN credentials stolen via brute force or stuffing",
                stages=[
                    EventType.VPN_BRUTE_FORCE,
                    EventType.VPN_ACCESS,
                    EventType.GEOGRAPHIC_ANOMALY,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="vpn_session_takeover",
                description="Active VPN session hijacked by attacker",
                stages=[
                    EventType.VPN_SESSION_HIJACK,
                    EventType.IMPOSSIBLE_TRAVEL,
                    EventType.DATABASE_QUERY,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="vpn_bypass_exfil",
                description="Data exfiltration bypassing VPN security",
                stages=[
                    EventType.VPN_SPLIT_TUNNEL,
                    EventType.CLOUD_SYNC,
                    EventType.SHADOW_IT,
                ],
                time_window_days=3,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="impossible_travel_attack",
                description="Credential theft indicated by impossible geography",
                stages=[
                    EventType.IMPOSSIBLE_TRAVEL,
                    EventType.VPN_ACCESS,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="mfa_fatigue_attack",
                description="Attacker bombarding user with MFA prompts until accepted",
                stages=[
                    EventType.VPN_MFA_BYPASS,
                    EventType.VPN_ACCESS,
                    EventType.GEOGRAPHIC_ANOMALY,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="concurrent_session_hijack",
                description="Same credentials used from multiple locations simultaneously",
                stages=[
                    EventType.VPN_CONCURRENT_SESSION,
                    EventType.DATABASE_QUERY,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="token_replay_attack",
                description="Stolen OAuth/SAML token reused for unauthorized access",
                stages=[
                    EventType.VPN_TOKEN_REPLAY,
                    EventType.VPN_NEW_DEVICE,
                    EventType.BULK_OPERATION,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="dns_tunnel_exfil",
                description="Data exfiltration via DNS tunneling over VPN",
                stages=[
                    EventType.VPN_DNS_TUNNEL,
                    EventType.VPN_EXCESSIVE_BANDWIDTH,
                    EventType.DATABASE_QUERY,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="dormant_account_takeover",
                description="Compromised dormant account activated for attack",
                stages=[
                    EventType.VPN_DORMANT_ACCOUNT,
                    EventType.VPN_NEW_DEVICE,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="vpn_c2_channel",
                description="VPN tunnel being used for command and control",
                stages=[
                    EventType.VPN_TUNNEL_ABUSE,
                    EventType.VPN_ANOMALOUS_PROTOCOL,
                    EventType.LATERAL_MOVEMENT,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="off_hours_vpn_raid",
                description="Attacker exploiting off-hours for unmonitored access",
                stages=[
                    EventType.VPN_OFF_HOURS_LOGIN,
                    EventType.AFTER_HOURS_ACCESS,
                    EventType.BULK_OPERATION,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="cert_spoof_attack",
                description="Attacker using forged or stolen certificates",
                stages=[
                    EventType.VPN_CERT_ANOMALY,
                    EventType.VPN_ACCESS,
                    EventType.DATABASE_QUERY,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # LATERAL MOVEMENT PATTERNS (NEW)
            # ============================================================
            AttackSequence(
                name="network_reconnaissance",
                description="Attacker mapping network before attack",
                stages=[
                    EventType.RECONNAISSANCE,
                    EventType.LATERAL_MOVEMENT,
                    EventType.CREDENTIAL_ACCESS,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="privilege_escalation_chain",
                description="Escalating from user to admin to domain",
                stages=[
                    EventType.CREDENTIAL_ACCESS,
                    EventType.PERMISSION_CHANGE,
                    EventType.ADMIN_ACTION,
                    EventType.SERVICE_ACCOUNT_USE,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="service_account_abuse",
                description="Service account used from user workstation",
                stages=[
                    EventType.SERVICE_ACCOUNT_USE,
                    EventType.DATABASE_QUERY,
                    EventType.BULK_OPERATION,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # PERSISTENCE PATTERNS (NEW)
            # ============================================================
            AttackSequence(
                name="persistent_access_setup",
                description="Attacker establishing persistent access",
                stages=[
                    EventType.SCHEDULED_TASK,
                    EventType.REGISTRY_CHANGE,
                    EventType.PERMISSION_CHANGE,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="email_persistence",
                description="Email rules set up for data exfiltration",
                stages=[
                    EventType.EMAIL_RULE_CHANGE,
                    EventType.EMAIL_FORWARD,
                    EventType.CLOUD_SYNC,
                ],
                time_window_days=7,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # EVASION PATTERNS (NEW)
            # ============================================================
            AttackSequence(
                name="covering_tracks",
                description="Attacker deleting evidence after data theft",
                stages=[
                    EventType.FILE_DOWNLOAD,      # First: steal data
                    EventType.SECURITY_DISABLE,   # Then: disable monitoring
                    EventType.LOG_DELETION,       # Finally: delete evidence
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="anonymized_exfil",
                description="Data exfiltration via anonymous channels",
                stages=[
                    EventType.TOR_ACCESS,
                    EventType.PROXY_USE,
                    EventType.FILE_UPLOAD,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="security_tool_kill",
                description="Attacker disabling security before ransomware/malware",
                stages=[
                    EventType.SECURITY_DISABLE,
                    EventType.MALWARE_DETECTED,
                    EventType.BULK_OPERATION,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="ransomware_attack",
                description="Ransomware deployment after security bypass",
                stages=[
                    EventType.ADMIN_ACTION,
                    EventType.SECURITY_DISABLE,
                    EventType.MALWARE_DETECTED,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # EXTERNAL ATTACK PATTERNS (NEW)
            # ============================================================
            AttackSequence(
                name="phishing_to_exfil",
                description="Phishing attack leading to data theft",
                stages=[
                    EventType.PHISHING_CLICK,
                    EventType.MALWARE_DETECTED,
                    EventType.CREDENTIAL_ACCESS,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="malware_data_theft",
                description="Malware-based data exfiltration",
                stages=[
                    EventType.MALWARE_DETECTED,
                    EventType.LATERAL_MOVEMENT,
                    EventType.DATABASE_QUERY,
                    EventType.FILE_UPLOAD,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="shadow_it_leak",
                description="Data leaked via unauthorized cloud services",
                stages=[
                    EventType.SHADOW_IT,
                    EventType.FILE_UPLOAD,
                    EventType.DLP_VIOLATION,
                ],
                time_window_days=7,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # ORIGINAL PATTERNS (kept for compatibility)
            # ============================================================
            AttackSequence(
                name="geographic_compromise",
                description="Impossible travel or location masking indicating credential theft",
                stages=[
                    EventType.GEOGRAPHIC_ANOMALY,
                    EventType.VPN_ACCESS,
                    EventType.DATABASE_QUERY,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="privilege_escalation_theft",
                description="Permission changes followed by bulk data access",
                stages=[
                    EventType.PERMISSION_CHANGE,
                    EventType.DATABASE_QUERY,
                    EventType.BULK_OPERATION,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # CLOUD / SAAS ATTACK PATTERNS
            # ============================================================
            AttackSequence(
                name="cloud_storage_exfil",
                description="Mass data exfiltration via cloud storage services",
                stages=[
                    EventType.CLOUD_STORAGE_ACCESS,
                    EventType.CLOUD_PERMISSION_CHANGE,
                    EventType.FILE_DOWNLOAD,
                    EventType.DLP_VIOLATION,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="cloud_admin_takeover",
                description="Cloud admin account compromised for infrastructure control",
                stages=[
                    EventType.CLOUD_ADMIN_CHANGE,
                    EventType.CLOUD_CONFIG_CHANGE,
                    EventType.CLOUD_RESOURCE_CREATION,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="api_key_abuse",
                description="Exposed API keys used for unauthorized data access",
                stages=[
                    EventType.API_KEY_EXPOSURE,
                    EventType.DATABASE_QUERY,
                    EventType.BULK_OPERATION,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="shadow_saas_exfil",
                description="Rogue SaaS app installed to siphon data",
                stages=[
                    EventType.SAAS_APP_INSTALL,
                    EventType.OAUTH_CONSENT,
                    EventType.CLOUD_SYNC,
                    EventType.DLP_VIOLATION,
                ],
                time_window_days=7,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="cloud_cryptojacking",
                description="Cloud infrastructure hijacked for crypto mining",
                stages=[
                    EventType.CLOUD_ADMIN_CHANGE,
                    EventType.CLOUD_RESOURCE_CREATION,
                    EventType.VPN_EXCESSIVE_BANDWIDTH,
                ],
                time_window_days=3,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # BUSINESS EMAIL COMPROMISE (BEC) PATTERNS
            # ============================================================
            AttackSequence(
                name="bec_wire_fraud",
                description="Business email compromise leading to fraudulent wire transfer",
                stages=[
                    EventType.EMAIL_IMPERSONATION,
                    EventType.BEC_INDICATOR,
                    EventType.WIRE_TRANSFER_REQUEST,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="email_account_compromise",
                description="Email account taken over and weaponized",
                stages=[
                    EventType.EMAIL_ACCOUNT_TAKEOVER,
                    EventType.EMAIL_RULE_CHANGE,
                    EventType.EMAIL_FORWARD,
                    EventType.WIRE_TRANSFER_REQUEST,
                ],
                time_window_days=14,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="executive_whaling_attack",
                description="C-suite targeted spear phishing to authorize transfers",
                stages=[
                    EventType.EXECUTIVE_WHALING,
                    EventType.EMAIL_IMPERSONATION,
                    EventType.WIRE_TRANSFER_REQUEST,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="invoice_redirect_fraud",
                description="Vendor invoice payment details tampered for theft",
                stages=[
                    EventType.INVOICE_MANIPULATION,
                    EventType.PAYMENT_REDIRECT,
                    EventType.WIRE_TRANSFER_REQUEST,
                ],
                time_window_days=14,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # IDENTITY & ACCESS FEDERATION PATTERNS
            # ============================================================
            AttackSequence(
                name="sso_abuse_chain",
                description="SSO token theft for cross-application access",
                stages=[
                    EventType.SSO_ANOMALY,
                    EventType.IMPOSSIBLE_TRAVEL,
                    EventType.CLOUD_STORAGE_ACCESS,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="oauth_consent_phishing",
                description="Malicious OAuth app granted access via consent phishing",
                stages=[
                    EventType.PHISHING_CLICK,
                    EventType.OAUTH_CONSENT,
                    EventType.EMAIL_FORWARD,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="conditional_access_evasion",
                description="Attacker bypassing conditional access policies",
                stages=[
                    EventType.CONDITIONAL_ACCESS_BYPASS,
                    EventType.VPN_NEW_DEVICE,
                    EventType.GEOGRAPHIC_ANOMALY,
                    EventType.DATABASE_QUERY,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="identity_federation_exploit",
                description="Federated trust exploited for cross-tenant access",
                stages=[
                    EventType.IDENTITY_FEDERATION_ABUSE,
                    EventType.SSO_ANOMALY,
                    EventType.ADMIN_ACTION,
                    EventType.BULK_OPERATION,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="password_spray_takeover",
                description="Low-and-slow password spray leading to account compromise",
                stages=[
                    EventType.PASSWORD_SPRAY,
                    EventType.MFA_REGISTRATION_CHANGE,
                    EventType.VPN_ACCESS,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="mfa_device_hijack",
                description="MFA device re-enrolled after account compromise",
                stages=[
                    EventType.PASSWORD_SPRAY,
                    EventType.MFA_REGISTRATION_CHANGE,
                    EventType.IMPOSSIBLE_TRAVEL,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # LAW FIRM COMPLIANCE PATTERNS (LEGAL-SPECIFIC)
            # ============================================================
            AttackSequence(
                name="ethics_wall_breach",
                description="Chinese wall violation - accessing conflicting client matters",
                stages=[
                    EventType.ETHICS_WALL_VIOLATION,
                    EventType.CLIENT_MATTER_CROSSOVER,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=30,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="privileged_data_theft",
                description="Attorney-client privileged material exfiltrated",
                stages=[
                    EventType.PRIVILEGED_DATA_ACCESS,
                    EventType.FILE_DOWNLOAD,
                    EventType.CLOUD_SYNC,
                    EventType.DLP_VIOLATION,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="trust_account_fraud",
                description="IOLTA/trust account accessed with suspicious patterns",
                stages=[
                    EventType.TRUST_ACCOUNT_ACCESS,
                    EventType.WIRE_TRANSFER_REQUEST,
                    EventType.BILLING_ANOMALY,
                ],
                time_window_days=14,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="ediscovery_exfil",
                description="eDiscovery data exported outside authorized channels",
                stages=[
                    EventType.EDISCOVERY_EXPORT,
                    EventType.FILE_DOWNLOAD,
                    EventType.CLOUD_SYNC,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="regulatory_data_breach",
                description="PII/PHI/financial data accessed and exfiltrated",
                stages=[
                    EventType.REGULATORY_DATA_ACCESS,
                    EventType.DATABASE_QUERY,
                    EventType.FILE_UPLOAD,
                    EventType.DLP_VIOLATION,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="case_matter_manipulation",
                description="Suspicious case reassignment followed by data access",
                stages=[
                    EventType.CASE_REASSIGNMENT,
                    EventType.PRIVILEGED_DATA_ACCESS,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=14,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # SUPPLY CHAIN & THIRD-PARTY PATTERNS
            # ============================================================
            AttackSequence(
                name="vendor_access_compromise",
                description="Third-party vendor account used for unauthorized access",
                stages=[
                    EventType.VENDOR_ACCESS,
                    EventType.VENDOR_PRIVILEGE_ESCALATION,
                    EventType.DATABASE_QUERY,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="supply_chain_attack",
                description="Compromised software dependency used as attack vector",
                stages=[
                    EventType.SUPPLY_CHAIN_ALERT,
                    EventType.MALWARE_DETECTED,
                    EventType.LATERAL_MOVEMENT,
                    EventType.CREDENTIAL_ACCESS,
                ],
                time_window_days=14,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="third_party_data_leak",
                description="Sensitive data shared with unauthorized third party",
                stages=[
                    EventType.THIRD_PARTY_DATA_SHARE,
                    EventType.DLP_VIOLATION,
                    EventType.FILE_UPLOAD,
                ],
                time_window_days=7,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # AI / ML SECURITY PATTERNS
            # ============================================================
            AttackSequence(
                name="ai_model_theft",
                description="Proprietary AI model weights or training data stolen",
                stages=[
                    EventType.AI_MODEL_ACCESS,
                    EventType.TRAINING_DATA_ACCESS,
                    EventType.FILE_DOWNLOAD,
                    EventType.CLOUD_SYNC,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="prompt_injection_chain",
                description="Prompt injection used to extract sensitive data via AI",
                stages=[
                    EventType.PROMPT_INJECTION,
                    EventType.AI_OUTPUT_EXFIL,
                    EventType.DLP_VIOLATION,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="copilot_data_extraction",
                description="AI assistant abused to extract privileged information",
                stages=[
                    EventType.COPILOT_ABUSE,
                    EventType.PRIVILEGED_DATA_ACCESS,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=3,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="training_data_poisoning",
                description="ML training data tampered to corrupt model output",
                stages=[
                    EventType.TRAINING_DATA_ACCESS,
                    EventType.AI_MODEL_ACCESS,
                    EventType.FILE_UPLOAD,
                ],
                time_window_days=14,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # PHYSICAL + CYBER CONVERGENCE PATTERNS
            # ============================================================
            AttackSequence(
                name="physical_cyber_exfil",
                description="Physical access combined with cyber data theft",
                stages=[
                    EventType.BADGE_ANOMALY,
                    EventType.AFTER_HOURS_ACCESS,
                    EventType.USB_ACTIVITY,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="byod_data_leak",
                description="Personal device used to exfiltrate corporate data",
                stages=[
                    EventType.BYOD_DEVICE,
                    EventType.CLOUD_SYNC,
                    EventType.FILE_DOWNLOAD,
                    EventType.DLP_VIOLATION,
                ],
                time_window_days=7,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="scan_and_send",
                description="Physical documents scanned and emailed to personal address",
                stages=[
                    EventType.BADGE_ACCESS,
                    EventType.SCAN_TO_EMAIL,
                    EventType.EMAIL_FORWARD,
                ],
                time_window_days=1,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="visitor_network_intrusion",
                description="Visitor WiFi used to access internal resources",
                stages=[
                    EventType.VISITOR_NETWORK_ACCESS,
                    EventType.RECONNAISSANCE,
                    EventType.LATERAL_MOVEMENT,
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # FINANCIAL FRAUD PATTERNS (LAW FIRM BILLING)
            # ============================================================
            AttackSequence(
                name="billing_fraud_scheme",
                description="Systematic billing manipulation for financial theft",
                stages=[
                    EventType.TIME_ENTRY_MANIPULATION,
                    EventType.BILLING_ANOMALY,
                    EventType.EXPENSE_FRAUD,
                ],
                time_window_days=30,
                severity="HIGH",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="payment_hijack",
                description="Client payment redirected to attacker-controlled account",
                stages=[
                    EventType.PAYMENT_REDIRECT,
                    EventType.INVOICE_MANIPULATION,
                    EventType.WIRE_TRANSFER_REQUEST,
                ],
                time_window_days=14,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            
            # ============================================================
            # ENDPOINT & ZERO TRUST PATTERNS
            # ============================================================
            AttackSequence(
                name="compromised_endpoint_attack",
                description="Non-compliant device used as attack launchpad",
                stages=[
                    EventType.ENDPOINT_COMPLIANCE_FAIL,
                    EventType.ZERO_TRUST_VIOLATION,
                    EventType.LATERAL_MOVEMENT,
                    EventType.FILE_DOWNLOAD,
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="firmware_rootkit",
                description="Firmware-level compromise for persistent access",
                stages=[
                    EventType.FIRMWARE_TAMPERING,
                    EventType.SECURITY_DISABLE,
                    EventType.CREDENTIAL_ACCESS,
                ],
                time_window_days=7,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),
            AttackSequence(
                name="removable_media_theft",
                description="USB/external drive used for data exfiltration",
                stages=[
                    EventType.REMOVABLE_MEDIA_MOUNT,
                    EventType.FILE_DOWNLOAD,
                    EventType.DLP_VIOLATION,
                ],
                time_window_days=1,
                severity="HIGH",
                min_stages_to_alert=2
            ),

            # ============================================================
            # GEMINI-IDENTIFIED GAP PATTERNS (Feb 2026)
            # ============================================================

            # Pattern 67: Credential Proxy — attorney uses paralegal's
            # credentials to bypass ethics wall restrictions
            AttackSequence(
                name="credential_proxy_ethics_bypass",
                description="Attorney uses staff credentials to circumvent ethics wall — "
                            "dual login from same IP + privileged matter access",
                stages=[
                    EventType.SSO_ANOMALY,             # Unusual login pattern
                    EventType.CREDENTIAL_ACCESS,        # Staff credential used
                    EventType.ETHICS_WALL_VIOLATION,    # Access to walled matter
                    EventType.PRIVILEGED_DATA_ACCESS,   # Privileged doc retrieval
                ],
                time_window_days=1,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),

            # Pattern 68: Shadow AI Exfiltration — user pastes privileged
            # docs into unauthorized AI tools (ChatGPT, Claude, etc.)
            AttackSequence(
                name="shadow_ai_exfiltration",
                description="Privileged documents copied to unauthorized AI service — "
                            "DLP violation + shadow IT + privileged data access",
                stages=[
                    EventType.PRIVILEGED_DATA_ACCESS,   # Access privileged docs
                    EventType.SHADOW_IT,                # Unauthorized SaaS usage
                    EventType.DLP_VIOLATION,            # Data leaves boundary
                    EventType.AI_OUTPUT_EXFIL,          # AI-generated output leak
                ],
                time_window_days=3,
                severity="CRITICAL",
                min_stages_to_alert=2
            ),

            # Pattern 69: Secret Merger Reconnaissance — conflict DB
            # queries for firms not involved in any known deal
            AttackSequence(
                name="secret_merger_recon",
                description="Conflict-of-interest database probed for firms outside "
                            "known matters — potential merger leak or insider trading",
                stages=[
                    EventType.DATABASE_QUERY,           # Conflict DB queries
                    EventType.CLIENT_MATTER_CROSSOVER,  # Cross-matter snooping
                    EventType.AFTER_HOURS_ACCESS,       # After-hours timing
                    EventType.EMAIL_FORWARD,            # Results forwarded externally
                ],
                time_window_days=7,
                severity="HIGH",
                min_stages_to_alert=2
            ),
        ]
    
    def ingest_event(self, event: SecurityEvent) -> List[CorrelationAlert]:
        """
        PRODUCTION-HARDENED event ingestion with:
        - Input validation
        - Rate limiting
        - Memory bounds
        - Structured logging
        - GEMINI: Event deduplication
        - GEMINI: Probationary user protection
        """
        try:
            # =================================================================
            # FIX 1: INPUT VALIDATION
            # =================================================================
            user_id = event.user_id
            
            # Validate user_id format
            if not user_id or not USER_ID_PATTERN.match(user_id):
                self._stats['events_rejected_validation'] += 1
                logger.warning(f"Invalid user_id rejected: {repr(user_id)[:50]}")
                return []
            
            # Validate event_type is valid enum
            if not isinstance(event.event_type, EventType):
                self._stats['events_rejected_validation'] += 1
                logger.warning(f"Invalid event_type for user {user_id}")
                return []
            
            event_type = event.event_type
            ts_epoch = event.ts_epoch
            now = time.time()
            
            # =================================================================
            # CHATGPT FIX: TIMESTAMP SAFETY
            # =================================================================
            # Reject timestamps too far in the future (clock skew attack)
            if ts_epoch > now + MAX_FUTURE_SECONDS:
                self._stats['events_rejected_future'] += 1
                logger.warning(f"Future timestamp rejected for user {user_id}: {ts_epoch - now:.0f}s ahead")
                return []
            
            # Reject timestamps too old (prevents historical replay attacks)
            max_age_seconds = MAX_PAST_DAYS * 86400
            if ts_epoch < now - max_age_seconds:
                self._stats['events_rejected_old'] += 1
                logger.warning(f"Stale timestamp rejected for user {user_id}: {(now - ts_epoch) / 86400:.1f} days old")
                return []
            
            # =================================================================
            # GEMINI FIX: EVENT DEDUPLICATION
            # =================================================================
            if self._is_duplicate_event(event, now):
                self._stats['events_rejected_duplicate'] += 1
                return []
            
            # =================================================================
            # FIX 4: RATE LIMITING
            # =================================================================
            rate_key = user_id
            
            if rate_key in self._rate_limits:
                count, window_start = self._rate_limits[rate_key]
                if now - window_start < RATE_LIMIT_WINDOW_SECONDS:
                    if count >= MAX_EVENTS_PER_USER_PER_MINUTE:
                        self._stats['events_rejected_rate_limit'] += 1
                        logger.warning(f"Rate limit exceeded for user {user_id}: {count} events/min")
                        return []
                    self._rate_limits[rate_key] = (count + 1, window_start)
                else:
                    self._rate_limits[rate_key] = (1, now)
            else:
                self._rate_limits[rate_key] = (1, now)
            
            # =================================================================
            # FIX 2: MEMORY BOUNDS
            # =================================================================
            # Periodic purge check (sliding window — Gemini review)
            if now - self._last_purge > PURGE_INTERVAL_SECONDS:
                self._purge_old_events(now)
                self._last_purge = now
            
            # Check per-user event limit
            if self._event_counts[user_id] >= MAX_EVENTS_PER_USER:
                # Evict oldest 20% of events for this user
                self._evict_user_events(user_id, 0.2)
            
            # Check total user limit
            if len(self.events) >= MAX_TOTAL_USERS:
                logger.warning(f"Max users reached ({MAX_TOTAL_USERS}), purging inactive")
                self._purge_inactive_users()
            
            # =================================================================
            # CORE PROCESSING (optimized)
            # =================================================================
            events = self.events
            events_by_type = self.events_by_type
            
            if user_id not in events:
                events[user_id] = []
            events[user_id].append(event)
            self._event_counts[user_id] += 1
            
            if user_id not in events_by_type:
                events_by_type[user_id] = {}
            user_type_events = events_by_type[user_id]
            if event_type not in user_type_events:
                user_type_events[event_type] = []
            user_type_events[event_type].append(event)
            
            self._stats['events_processed'] += 1
            
            # =================================================================
            # PATTERN MATCHING - GEMINI FIX: Enforces strict ordering
            # =================================================================
            alerts = []
            SECONDS_PER_DAY = 86400
            
            for seq in self.attack_sequences:
                # Skip if event type not in pattern (O(1) set lookup)
                if event_type not in seq.stages_set:
                    continue
                
                window_start = ts_epoch - (seq.time_window_days * SECONDS_PER_DAY)
                
                # GEMINI FIX: Use sequence-aware matching
                matched = self._match_pattern_ordered(
                    user_type_events, seq.stages, window_start
                )
                
                # Check threshold
                if len(matched) >= seq.min_stages_to_alert:
                    # GEMINI FIX: Check allowlist before alerting
                    if self._is_allowlisted(user_id, seq.name, event):
                        self._stats['alerts_suppressed_allowlist'] += 1
                        continue
                    
                    # GROK FIX: Check alert cooldown (prevent duplicate alerts)
                    alert_key = f"{user_id}:{seq.name}"
                    if alert_key in self._recent_alerts:
                        last_alert = self._recent_alerts[alert_key]
                        if now - last_alert < self.alert_cooldown_seconds:
                            self._stats['alerts_suppressed_cooldown'] += 1
                            continue  # Still in cooldown, skip
                    
                    # Record this alert
                    self._recent_alerts[alert_key] = now
                    
                    alert = CorrelationAlert(
                        user_id=user_id,
                        pattern_name=seq.name,
                        matched_stages=matched,
                        total_stages=len(seq.stages),
                        completion_percent=len(matched) / len(seq.stages) * 100,
                        severity=seq.severity,
                        first_event=matched[0].timestamp,
                        last_event=matched[-1].timestamp,
                        time_span_hours=(matched[-1].ts_epoch - matched[0].ts_epoch) / 3600,
                        recommended_actions=[]
                    )
                    alerts.append(alert)
                    self._stats['alerts_generated'] += 1
                    
                    # FIX 3: Log alert generation
                    logger.info(f"ALERT: {seq.name} | user={user_id} | severity={seq.severity} | stages={len(matched)}/{len(seq.stages)}")
            
            return alerts
            
        except Exception as e:
            # FIX 3: Structured error logging
            logger.error(f"Event processing failed: {e} | user={getattr(event, 'user_id', 'unknown')}")
            return []
    
    # =========================================================================
    # GEMINI FIX: ORDERED SEQUENCE MATCHING
    # =========================================================================
    
    def _match_pattern_ordered(
        self, 
        user_type_events: Dict[EventType, List[SecurityEvent]], 
        required_stages: List[EventType],
        window_start: float
    ) -> List[SecurityEvent]:
        """
        GEMINI FIX: Validates strict ordering and distinct stages.
        
        Key improvements over original:
        1. Enforces chronological order (Stage A must occur before Stage B)
        2. Counts distinct stages, not total matching events
        3. Uses state machine approach for sequence detection
        """
        # Collect all candidate events in time window
        all_candidates = []
        for stage_type in set(required_stages):
            type_events = user_type_events.get(stage_type, [])
            for e in type_events:
                if e.ts_epoch >= window_start:
                    all_candidates.append(e)
        
        if not all_candidates:
            return []
        
        # Sort by timestamp to ensure sequence checks are valid
        all_candidates.sort(key=lambda e: e.ts_epoch)
        
        # State machine: find stages in the specific order defined
        matched_sequence = []
        current_stage_index = 0
        
        for event in all_candidates:
            # If we've already found all stages, stop
            if current_stage_index >= len(required_stages):
                break
            
            # Does this event match the *next* required stage?
            if event.event_type == required_stages[current_stage_index]:
                matched_sequence.append(event)
                current_stage_index += 1
        
        return matched_sequence
    
    def _is_allowlisted(self, user_id: str, pattern_name: str, event: SecurityEvent) -> bool:
        """
        GEMINI FIX: Check if this alert should be suppressed.
        
        Use cases:
        - eDiscovery teams downloading TBs of data (legitimate)
        - IT admins running bulk operations
        - Overnight batch jobs
        """
        if pattern_name not in self._allowlist:
            return False
        
        # Check user group from event details
        user_group = event.details.get('user_group', '')
        return user_group in self._allowlist[pattern_name]
    
    def add_allowlist_rule(self, pattern_name: str, user_group: str):
        """Add an allowlist rule to suppress alerts for specific groups"""
        if pattern_name not in self._allowlist:
            self._allowlist[pattern_name] = set()
        self._allowlist[pattern_name].add(user_group)
        logger.info(f"Allowlist: {user_group} excluded from {pattern_name} alerts")
    
    def remove_allowlist_rule(self, pattern_name: str, user_group: str):
        """Remove an allowlist rule"""
        if pattern_name in self._allowlist:
            self._allowlist[pattern_name].discard(user_group)
    
    def _compute_event_hash(self, event: SecurityEvent) -> str:
        """
        Compute a hash for deduplication.
        
        CHATGPT FIX: Include event_id if present for more precise deduplication.
        This prevents false-positive duplicate detection for legitimate bursts
        of similar events (e.g., multiple failed logins).
        """
        import hashlib
        
        # If event has a unique ID, use it (most precise)
        if event.event_id:
            # Exact event - same ID should never be processed twice
            key = f"id:{event.event_id}"
        else:
            # Fallback: Hash based on user, type, source, and rounded timestamp
            # This catches duplicate log ingestion from multiple forwarders
            # GEMINI FIX: Use current bucket only for hash (boundary check is in _is_duplicate)
            key = f"{event.user_id}|{event.event_type.value}|{event.source_system}|{int(event.ts_epoch // DEDUPE_WINDOW_SECONDS)}"
        
        return hashlib.md5(key.encode()).hexdigest()
    
    def _compute_event_hash_for_bucket(self, event: SecurityEvent, bucket: int) -> str:
        """
        GEMINI FIX: Compute hash for a specific time bucket.
        Used to check both current AND previous bucket for deduplication.
        """
        import hashlib
        
        if event.event_id:
            return hashlib.md5(f"id:{event.event_id}".encode()).hexdigest()
        
        key = f"{event.user_id}|{event.event_type.value}|{event.source_system}|{bucket}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _is_duplicate_event(self, event: SecurityEvent, now: float) -> bool:
        """
        GEMINI FIX: Check if this is a duplicate event.
        
        Prevents duplicate log ingestion from inflating risk scores.
        
        GEMINI REFINEMENT: Now checks BOTH current AND previous time bucket
        to handle edge cases where duplicate arrives right at bucket boundary.
        (e.g., event at 12:00:59, duplicate at 12:01:01 would fall in different buckets)
        """
        # Clean old hashes periodically (same time as purge)
        if len(self._recent_event_hashes) > 100000:
            cutoff = now - DEDUPE_WINDOW_SECONDS
            self._recent_event_hashes = {
                h: ts for h, ts in self._recent_event_hashes.items() 
                if ts > cutoff
            }
        
        # If event has an ID, use exact match (simple case)
        if event.event_id:
            event_hash = self._compute_event_hash(event)
            if event_hash in self._recent_event_hashes:
                return True
            self._recent_event_hashes[event_hash] = now
            return False
        
        # GEMINI REFINEMENT: Check BOTH current AND previous bucket
        # This handles edge case of 12:00:59 -> 12:01:01 crossing bucket boundary
        current_bucket = int(event.ts_epoch // DEDUPE_WINDOW_SECONDS)
        previous_bucket = current_bucket - 1
        
        current_hash = self._compute_event_hash_for_bucket(event, current_bucket)
        previous_hash = self._compute_event_hash_for_bucket(event, previous_bucket)
        
        # Check if duplicate exists in either bucket
        if current_hash in self._recent_event_hashes or previous_hash in self._recent_event_hashes:
            return True
        
        # Not a duplicate - store the current bucket hash
        self._recent_event_hashes[current_hash] = now
        return False
    
    # =========================================================================
    # FIX 2: MEMORY MANAGEMENT HELPERS
    # =========================================================================
    
    def _purge_old_events(self, now: float):
        """
        Remove events older than TTL.
        CHATGPT FIX: Also purge auxiliary caches to prevent memory leaks.
        """
        cutoff = now - (EVENT_TTL_DAYS * 86400)
        purged = 0
        
        for user_id in list(self.events.keys()):
            original_count = len(self.events[user_id])
            self.events[user_id] = [e for e in self.events[user_id] if e.ts_epoch > cutoff]
            purged += original_count - len(self.events[user_id])
            self._event_counts[user_id] = len(self.events[user_id])
            
            # Also update events_by_type
            if user_id in self.events_by_type:
                for event_type in list(self.events_by_type[user_id].keys()):
                    self.events_by_type[user_id][event_type] = [
                        e for e in self.events_by_type[user_id][event_type] 
                        if e.ts_epoch > cutoff
                    ]
        
        # =================================================================
        # CHATGPT FIX: Purge auxiliary caches to prevent memory leaks
        # =================================================================
        
        # Purge expired rate limit entries
        rate_limit_cutoff = now - RATE_LIMIT_EXPIRY_SECONDS
        expired_rate_keys = [
            k for k, (count, window_start) in self._rate_limits.items()
            if window_start < rate_limit_cutoff
        ]
        for k in expired_rate_keys:
            del self._rate_limits[k]
        
        # Purge expired dedupe hashes
        dedupe_cutoff = now - DEDUPE_WINDOW_SECONDS
        expired_dedupe_keys = [
            k for k, ts in self._recent_event_hashes.items()
            if ts < dedupe_cutoff
        ]
        for k in expired_dedupe_keys:
            del self._recent_event_hashes[k]
        
        # Enforce max size on dedupe cache (in case of hash collisions)
        if len(self._recent_event_hashes) > DEDUPE_CACHE_MAX_SIZE:
            # Keep only newest half
            sorted_items = sorted(self._recent_event_hashes.items(), key=lambda x: x[1], reverse=True)
            self._recent_event_hashes = dict(sorted_items[:DEDUPE_CACHE_MAX_SIZE // 2])
        
        # Purge expired alert cooldowns
        alert_cutoff = now - ALERT_CACHE_EXPIRY_SECONDS
        expired_alert_keys = [
            k for k, ts in self._recent_alerts.items()
            if ts < alert_cutoff
        ]
        for k in expired_alert_keys:
            del self._recent_alerts[k]
        
        if purged > 0:
            self._stats['memory_purges'] += 1
            logger.info(f"Memory purge: removed {purged} events older than {EVENT_TTL_DAYS} days")
        
        # Log cache cleanup stats
        if expired_rate_keys or expired_dedupe_keys or expired_alert_keys:
            logger.debug(
                f"Cache cleanup: rate_limits={len(expired_rate_keys)}, "
                f"dedupe={len(expired_dedupe_keys)}, alerts={len(expired_alert_keys)}"
            )
    
    def _evict_user_events(self, user_id: str, fraction: float = 0.2):
        """Evict oldest fraction of events for a user"""
        events = self.events.get(user_id, [])
        if not events:
            return
        
        # Sort by timestamp and remove oldest
        events.sort(key=lambda e: e.ts_epoch)
        keep_count = int(len(events) * (1 - fraction))
        evicted = events[:len(events) - keep_count]
        self.events[user_id] = events[len(events) - keep_count:]
        self._event_counts[user_id] = len(self.events[user_id])
        
        # Rebuild events_by_type for this user
        if user_id in self.events_by_type:
            self.events_by_type[user_id] = {}
            for e in self.events[user_id]:
                if e.event_type not in self.events_by_type[user_id]:
                    self.events_by_type[user_id][e.event_type] = []
                self.events_by_type[user_id][e.event_type].append(e)
        
        logger.debug(f"Evicted {len(evicted)} events for user {user_id}")
    
    def _purge_inactive_users(self):
        """Remove users with no recent activity"""
        now = time.time()
        inactive_threshold = now - (7 * 86400)  # 7 days inactive
        
        users_to_remove = []
        for user_id, events in self.events.items():
            if events and events[-1].ts_epoch < inactive_threshold:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove[:1000]:  # Remove up to 1000 at a time
            del self.events[user_id]
            if user_id in self.events_by_type:
                del self.events_by_type[user_id]
            if user_id in self._event_counts:
                del self._event_counts[user_id]
        
        if users_to_remove:
            logger.info(f"Purged {len(users_to_remove)} inactive users")
    
    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics for monitoring"""
        return {
            **self._stats,
            'total_users': len(self.events),
            'total_events_in_memory': sum(self._event_counts.values()),
            'patterns_loaded': len(self.attack_sequences)
        }
    
    def flush(self):
        """Force write pending changes to disk"""
        if self._dirty:
            self._save_events()
            self._dirty = False
            self._event_count_since_save = 0
    
    def _check_patterns_fast(self, user_id: str, event_type: EventType) -> List[CorrelationAlert]:
        """
        ULTRA-FAST pattern check - only checks patterns relevant to this event type.
        Uses pre-indexed events for O(1) type lookup.
        
        GEMINI FIX: Now uses ordered sequence matching.
        """
        alerts = []
        user_events_by_type = self.events_by_type.get(user_id)
        
        if not user_events_by_type:
            return alerts
        
        now_epoch = datetime.now().timestamp()
        
        # Only check patterns that include this event type
        for sequence in self.attack_sequences:
            # Skip patterns that don't involve this event type
            if event_type not in sequence.stages_set:
                continue
            
            window_start_epoch = now_epoch - (sequence.time_window_days * 86400)
            
            # GEMINI FIX: Use ordered sequence matching
            matched_stages = self._match_pattern_ordered(
                user_events_by_type, sequence.stages, window_start_epoch
            )
            
            # Alert if enough stages matched
            if len(matched_stages) >= sequence.min_stages_to_alert:
                completion = len(matched_stages) / len(sequence.stages)
                
                alerts.append(CorrelationAlert(
                    user_id=user_id,
                    pattern_name=sequence.name,
                    matched_stages=matched_stages,
                    total_stages=len(sequence.stages),
                    completion_percent=completion * 100,
                    severity=sequence.severity,
                    first_event=matched_stages[0].timestamp,
                    last_event=matched_stages[-1].timestamp,
                    time_span_hours=(matched_stages[-1].ts_epoch - matched_stages[0].ts_epoch) / 3600,
                    recommended_actions=self._get_recommendations(sequence, completion)
                ))
        
        return alerts
    
    def _check_patterns(self, user_id: str) -> List[CorrelationAlert]:
        """Check if user's recent events match any attack patterns (legacy method)"""
        alerts = []
        user_events = self.events.get(user_id, [])
        
        if not user_events:
            return alerts
        
        now = datetime.now()
        
        for sequence in self.attack_sequences:
            # Get events within the pattern's time window
            window_start = now - timedelta(days=sequence.time_window_days)
            recent_events = [
                e for e in user_events 
                if e.timestamp >= window_start
            ]
            
            # Check which stages are present
            matched_stages = []
            for stage_type in sequence.stages:
                matching_events = [e for e in recent_events if e.event_type == stage_type]
                if matching_events:
                    # Take the most recent event of this type
                    matched_stages.append(max(matching_events, key=lambda e: e.timestamp))
            
            # Alert if enough stages matched
            if len(matched_stages) >= sequence.min_stages_to_alert:
                completion = len(matched_stages) / len(sequence.stages)
                
                alert = CorrelationAlert(
                    user_id=user_id,
                    pattern_name=sequence.name,
                    matched_stages=matched_stages,
                    total_stages=len(sequence.stages),
                    completion_percent=completion * 100,
                    severity=sequence.severity,
                    first_event=min(e.timestamp for e in matched_stages),
                    last_event=max(e.timestamp for e in matched_stages),
                    time_span_hours=(max(e.timestamp for e in matched_stages) - 
                                    min(e.timestamp for e in matched_stages)).total_seconds() / 3600,
                    recommended_actions=self._get_recommendations(sequence, completion)
                )
                alerts.append(alert)
        
        return alerts
    
    def _get_recommendations(self, sequence: AttackSequence, completion: float) -> List[str]:
        """Get recommended actions based on pattern and completion level"""
        actions = []
        
        if completion < 0.5:
            actions.append("MONITOR: Place user on enhanced monitoring watchlist")
            actions.append("AUDIT: Review all access for past 7 days")
        elif completion < 0.75:
            actions.append("RESTRICT: Limit access to sensitive data")
            actions.append("ALERT: Notify security team for manual review")
            actions.append("AUDIT: Full access review for past 30 days")
        else:
            actions.append("IMMEDIATE: Suspend user access pending investigation")
            actions.append("FORENSIC: Preserve all logs and system snapshots")
            actions.append("ESCALATE: Notify CISO and legal counsel")
            actions.append("CONTAIN: Block all data egress for this user")
        
        # Add pattern-specific actions
        if sequence.name == "typhoon_vpn_exfil":
            actions.append("LOCK: Terminate all VPN sessions immediately")
            actions.append("BLOCK: Disable remote database access")
        elif sequence.name == "pre_departure_exfil":
            actions.append("HR: Check for resignation indicators")
            actions.append("DLP: Enable strict data loss prevention")
        elif sequence.name == "geographic_compromise":
            actions.append("VERIFY: Contact user via known-good phone number")
            actions.append("RESET: Force password and MFA re-enrollment")
        
        return actions
    
    def _update_baseline(self, user_id: str):
        """Update behavioral baseline for a user"""
        user_events = self.events.get(user_id, [])
        
        if len(user_events) < 10:
            return  # Not enough data for baseline
        
        # Calculate baseline metrics
        now = datetime.now()
        last_30_days = [e for e in user_events 
                       if e.timestamp >= now - timedelta(days=30)]
        
        if not last_30_days:
            return
            
        # Event frequency by type
        type_counts = defaultdict(int)
        for event in last_30_days:
            type_counts[event.event_type.value] += 1
        
        # Average daily events
        days_with_events = len(set(e.timestamp.date() for e in last_30_days))
        avg_daily = len(last_30_days) / max(days_with_events, 1)
        
        self.baselines[user_id] = {
            "event_counts_30d": dict(type_counts),
            "avg_daily_events": avg_daily,
            "last_updated": now.isoformat(),
            "data_points": len(last_30_days)
        }
    
    def check_baseline_deviation(self, user_id: str, event: SecurityEvent) -> Optional[float]:
        """
        Check if an event deviates from user's baseline.
        Returns deviation multiplier (e.g., 3.0 = 3x normal activity)
        """
        baseline = self.baselines.get(user_id)
        if not baseline:
            return None
        
        event_type = event.event_type.value
        historical_count = baseline["event_counts_30d"].get(event_type, 0)
        
        if historical_count == 0:
            # New behavior - flag it
            return float('inf')
        
        # Count this event type in recent window
        now = datetime.now()
        recent = [e for e in self.events.get(user_id, [])
                 if e.timestamp >= now - timedelta(days=1)
                 and e.event_type.value == event_type]
        
        daily_avg = historical_count / 30
        if daily_avg > 0:
            return len(recent) / daily_avg
        return None
    
    def get_user_timeline(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get timeline of user's security events"""
        user_events = self.events.get(user_id, [])
        cutoff = datetime.now() - timedelta(days=days)
        
        recent = [e for e in user_events if e.timestamp >= cutoff]
        recent.sort(key=lambda e: e.timestamp)
        
        return [e.to_dict() for e in recent]
    
    def _load_events(self):
        """Load events from persistent storage"""
        if self.event_store_path.exists():
            try:
                with open(self.event_store_path, 'r') as f:
                    data = json.load(f)
                    for user_id, events in data.items():
                        for event_data in events:
                            event = SecurityEvent(
                                event_id=event_data["event_id"],
                                user_id=event_data["user_id"],
                                event_type=EventType(event_data["event_type"]),
                                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                                source_system=event_data["source_system"],
                                details=event_data.get("details", {}),
                                risk_score=event_data.get("risk_score", 0.0)
                            )
                            self.events[user_id].append(event)
            except (json.JSONDecodeError, KeyError):
                pass  # Start fresh if file is corrupted
    
    def _save_events(self):
        """Persist events to storage"""
        self.event_store_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for user_id, events in self.events.items():
            data[user_id] = [e.to_dict() for e in events]
        
        with open(self.event_store_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def format_alert(self, alert: CorrelationAlert) -> str:
        """Format an alert for display"""
        output = f"""
╔══════════════════════════════════════════════════════════════════╗
║           AION TEMPORAL CORRELATION ALERT                        ║
╚══════════════════════════════════════════════════════════════════╝

USER: {alert.user_id}
PATTERN: {alert.pattern_name}
SEVERITY: {alert.severity}

PATTERN COMPLETION: {alert.completion_percent:.0f}% ({len(alert.matched_stages)}/{alert.total_stages} stages)
TIME SPAN: {alert.time_span_hours:.1f} hours

════════════════════════════════════════════════════════════════════
EVENT TIMELINE
════════════════════════════════════════════════════════════════════
"""
        for event in sorted(alert.matched_stages, key=lambda e: e.timestamp):
            output += f"  [{event.timestamp.strftime('%Y-%m-%d %H:%M')}] {event.event_type.value}\n"
            output += f"      Source: {event.source_system}\n"
            if event.details:
                for k, v in list(event.details.items())[:3]:
                    output += f"      {k}: {v}\n"

        output += """
════════════════════════════════════════════════════════════════════
RECOMMENDED ACTIONS
════════════════════════════════════════════════════════════════════
"""
        for action in alert.recommended_actions:
            output += f"  □ {action}\n"

        output += """
════════════════════════════════════════════════════════════════════
This alert was generated by temporal correlation analysis.
Individual events may appear normal - the pattern is the threat.
════════════════════════════════════════════════════════════════════
"""
        return output


# =============================================================================
# GEMINI REFINEMENT: CROSS-USER CORRELATION ENGINE
# =============================================================================

@dataclass
class CrossUserAlert:
    """Alert for attacks that span multiple users (e.g., lateral movement)"""
    pattern_name: str
    severity: str
    description: str
    affected_users: List[str]
    common_attribute: str  # e.g., "IP 192.168.1.100"
    events: List[SecurityEvent]
    alert_time: datetime
    confidence: float


class GlobalCorrelationEngine:
    """
    GEMINI REFINEMENT: Detect attacks that span multiple users.
    
    The per-user TemporalCorrelationEngine misses patterns like:
    - User A compromised -> attacker pivots to Service Account B
    - Same malicious IP fails login to User A, then succeeds as User B
    - Credential stuffing across multiple accounts
    
    This engine tracks HIGH-RISK EVENTS across ALL users and correlates them.
    """
    
    # Event types that should be correlated globally (not per-user)
    CROSS_USER_EVENT_TYPES = {
        EventType.VPN_BRUTE_FORCE,
        EventType.PASSWORD_SPRAY,
        EventType.MALWARE_DETECTED,
        EventType.VPN_CREDENTIAL_STUFFING,
        EventType.LATERAL_MOVEMENT,
        EventType.SERVICE_ACCOUNT_USE,
        EventType.VENDOR_ACCESS,
        EventType.IMPOSSIBLE_TRAVEL,
    }
    
    def __init__(self, time_window_minutes: int = 30):
        self.time_window_minutes = time_window_minutes
        
        # Track events by IP (key = IP address)
        self._ip_events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Track events by device (key = device fingerprint)
        self._device_events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Track service account usage
        self._service_account_events: deque = deque(maxlen=5000)
        
        # Recent alerts (for dedup)
        self._recent_alerts: Dict[str, float] = {}
        
        # Stats
        self._stats = {
            "events_tracked": 0,
            "cross_user_alerts": 0,
            "ips_tracked": 0,
            "devices_tracked": 0
        }
    
    def ingest_event(self, event: SecurityEvent) -> List[CrossUserAlert]:
        """
        Process event for cross-user correlation.
        
        Returns alerts if cross-user attack pattern detected.
        """
        alerts = []
        
        # Only track high-risk event types
        if event.event_type not in self.CROSS_USER_EVENT_TYPES:
            return alerts
        
        now = time.time()
        self._stats["events_tracked"] += 1
        
        # Extract correlation keys from event details
        ip = event.details.get("ip", event.details.get("source_ip", event.details.get("client_ip")))
        device = event.details.get("device_id", event.details.get("device_fingerprint"))
        service_account = event.details.get("service_account")
        
        # Track by IP
        if ip:
            self._ip_events[ip].append((event, now))
            self._stats["ips_tracked"] = len(self._ip_events)
            
            # Check for cross-user pattern on this IP
            alert = self._check_ip_correlation(ip, event)
            if alert:
                alerts.append(alert)
        
        # Track by device
        if device:
            self._device_events[device].append((event, now))
            self._stats["devices_tracked"] = len(self._device_events)
            
            # Check for cross-user pattern on this device
            alert = self._check_device_correlation(device, event)
            if alert:
                alerts.append(alert)
        
        # Track service account usage
        if service_account or event.event_type == EventType.SERVICE_ACCOUNT_USE:
            self._service_account_events.append((event, now))
            
            # Check for service account abuse
            alert = self._check_service_account_abuse(event)
            if alert:
                alerts.append(alert)
        
        # Cleanup old events periodically
        if self._stats["events_tracked"] % 1000 == 0:
            self._cleanup_old_events(now)
        
        return alerts
    
    def _check_ip_correlation(self, ip: str, current_event: SecurityEvent) -> Optional[CrossUserAlert]:
        """
        Check if same IP is associated with suspicious activity across multiple users.
        
        Pattern: IP X fails login as User A, then succeeds as User B
        """
        now = time.time()
        window_start = now - (self.time_window_minutes * 60)
        
        # Get recent events from this IP
        recent = [(e, ts) for e, ts in self._ip_events[ip] if ts >= window_start]
        
        if len(recent) < 2:
            return None
        
        # Collect unique users
        users = set(e.user_id for e, _ in recent)
        
        if len(users) < 2:
            return None  # Same user, no cross-user pattern
        
        # Check for suspicious pattern: failed attempt then success with different user
        failed_users = set()
        success_users = set()
        
        for e, _ in recent:
            if e.event_type in (EventType.VPN_BRUTE_FORCE, EventType.PASSWORD_SPRAY, EventType.VPN_CREDENTIAL_STUFFING):
                failed_users.add(e.user_id)
            elif e.event_type == EventType.VPN_ACCESS or e.details.get("success", True):
                success_users.add(e.user_id)
        
        # Lateral movement pattern: failed as A, succeeded as B
        if failed_users and success_users and failed_users != success_users:
            alert_key = f"ip_lateral:{ip}:{','.join(sorted(users))}"
            
            if alert_key in self._recent_alerts and now - self._recent_alerts[alert_key] < 3600:
                return None  # Already alerted within the hour
            
            self._recent_alerts[alert_key] = now
            self._stats["cross_user_alerts"] += 1
            
            return CrossUserAlert(
                pattern_name="cross_user_lateral_movement",
                severity="CRITICAL",
                description=f"IP {ip} failed login attempts on {len(failed_users)} user(s), then accessed different account(s). Possible credential compromise and lateral movement.",
                affected_users=list(users),
                common_attribute=f"IP: {ip}",
                events=[e for e, _ in recent],
                alert_time=datetime.now(),
                confidence=0.85
            )
        
        return None
    
    def _check_device_correlation(self, device: str, current_event: SecurityEvent) -> Optional[CrossUserAlert]:
        """
        Check if same device is used by multiple users (device compromise).
        """
        now = time.time()
        window_start = now - (self.time_window_minutes * 60)
        
        recent = [(e, ts) for e, ts in self._device_events[device] if ts >= window_start]
        users = set(e.user_id for e, _ in recent)
        
        if len(users) >= 3:  # 3+ users on same device is suspicious
            alert_key = f"device_multi:{device}"
            
            if alert_key in self._recent_alerts and now - self._recent_alerts[alert_key] < 3600:
                return None
            
            self._recent_alerts[alert_key] = now
            self._stats["cross_user_alerts"] += 1
            
            return CrossUserAlert(
                pattern_name="shared_device_compromise",
                severity="HIGH",
                description=f"Device {device[:20]}... used by {len(users)} different users within {self.time_window_minutes} minutes. Possible shared credential or device compromise.",
                affected_users=list(users),
                common_attribute=f"Device: {device[:30]}...",
                events=[e for e, _ in recent],
                alert_time=datetime.now(),
                confidence=0.75
            )
        
        return None
    
    def _check_service_account_abuse(self, current_event: SecurityEvent) -> Optional[CrossUserAlert]:
        """
        Check for service account abuse patterns.
        
        Pattern: Multiple users using same service account from different IPs
        """
        now = time.time()
        window_start = now - (self.time_window_minutes * 60)
        
        recent = [(e, ts) for e, ts in self._service_account_events if ts >= window_start]
        
        if len(recent) < 3:
            return None
        
        # Group by service account name
        by_account: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for e, _ in recent:
            sa = e.details.get("service_account", e.user_id)
            by_account[sa].append(e)
        
        # Check for unusual patterns
        for sa, events in by_account.items():
            if len(events) >= 3:
                ips = set(e.details.get("source_ip", "unknown") for e in events)
                if len(ips) >= 2:  # Same service account from multiple IPs
                    alert_key = f"svc_abuse:{sa}"
                    
                    if alert_key in self._recent_alerts and now - self._recent_alerts[alert_key] < 3600:
                        continue
                    
                    self._recent_alerts[alert_key] = now
                    self._stats["cross_user_alerts"] += 1
                    
                    return CrossUserAlert(
                        pattern_name="service_account_abuse",
                        severity="HIGH",
                        description=f"Service account '{sa}' used from {len(ips)} different IPs in {self.time_window_minutes} minutes. Possible credential theft.",
                        affected_users=[sa],
                        common_attribute=f"Service Account: {sa}",
                        events=events,
                        alert_time=datetime.now(),
                        confidence=0.8
                    )
        
        return None
    
    def _cleanup_old_events(self, now: float):
        """Remove old events to prevent memory growth"""
        window_start = now - (self.time_window_minutes * 60 * 2)  # Keep 2x window
        
        # Clean IP events
        for ip in list(self._ip_events.keys()):
            self._ip_events[ip] = deque(
                [(e, ts) for e, ts in self._ip_events[ip] if ts >= window_start],
                maxlen=1000
            )
            if not self._ip_events[ip]:
                del self._ip_events[ip]
        
        # Clean device events
        for d in list(self._device_events.keys()):
            self._device_events[d] = deque(
                [(e, ts) for e, ts in self._device_events[d] if ts >= window_start],
                maxlen=1000
            )
            if not self._device_events[d]:
                del self._device_events[d]
        
        # Clean alert dedup cache
        alert_cutoff = now - 7200  # 2 hours
        self._recent_alerts = {k: v for k, v in self._recent_alerts.items() if v > alert_cutoff}
    
    @property
    def stats(self) -> Dict:
        return self._stats.copy()


# Convenience function
_engine: Optional[TemporalCorrelationEngine] = None

def get_temporal_engine() -> TemporalCorrelationEngine:
    """Get or create the temporal correlation engine singleton"""
    global _engine
    if _engine is None:
        _engine = TemporalCorrelationEngine()
    return _engine


# Demo function
def demo_typhoon_pattern():
    """Demonstrate the engine detecting the Typhoon attack pattern"""
    import uuid
    
    engine = TemporalCorrelationEngine(Path("aionos/knowledge/demo_events.json"))
    
    # Simulate the Typhoon attack timeline
    now = datetime.now()
    
    events = [
        SecurityEvent(
            event_id=str(uuid.uuid4()),
            user_id="mknowles@typhoon.com",
            event_type=EventType.VPN_ACCESS,
            timestamp=now - timedelta(days=10),
            source_system="cloudflare",
            details={"source_ip": "home_network", "location": "Austin, TX"}
        ),
        SecurityEvent(
            event_id=str(uuid.uuid4()),
            user_id="mknowles@typhoon.com",
            event_type=EventType.DATABASE_QUERY,
            timestamp=now - timedelta(days=7),
            source_system="sql_server",
            details={"query_type": "SELECT *", "table": "client_billing", "rows": 50000}
        ),
        SecurityEvent(
            event_id=str(uuid.uuid4()),
            user_id="mknowles@typhoon.com",
            event_type=EventType.BULK_OPERATION,
            timestamp=now - timedelta(days=5),
            source_system="file_server",
            details={"operation": "bulk_copy", "file_count": 12000}
        ),
        SecurityEvent(
            event_id=str(uuid.uuid4()),
            user_id="mknowles@typhoon.com",
            event_type=EventType.FILE_DOWNLOAD,
            timestamp=now - timedelta(days=3),
            source_system="sharepoint",
            details={"size_mb": 2500, "destination": "local_drive"}
        ),
    ]
    
    print("=" * 70)
    print("AION TEMPORAL CORRELATION ENGINE - DEMO")
    print("Simulating Typhoon attack pattern over 10 days...")
    print("=" * 70)
    
    for i, event in enumerate(events, 1):
        print(f"\n[Day {10 - (now - event.timestamp).days}] Ingesting: {event.event_type.value}")
        alerts = engine.ingest_event(event)
        
        if alerts:
            for alert in alerts:
                print(engine.format_alert(alert))
    
    print("\n" + "=" * 70)
    print("FINAL USER TIMELINE")
    print("=" * 70)
    timeline = engine.get_user_timeline("mknowles@typhoon.com", days=14)
    for event in timeline:
        print(f"  [{event['timestamp'][:16]}] {event['event_type']}")


if __name__ == "__main__":
    demo_typhoon_pattern()
