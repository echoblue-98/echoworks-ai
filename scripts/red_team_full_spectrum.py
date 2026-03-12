"""
RED TEAM vs AION OS - FULL MULTI-MODAL ATTACK SIMULATION
==========================================================

EXPANDED COVERAGE:
- VPN Breaches                  - Lateral Movement
- Credential Theft              - Persistence Mechanisms
- Evasion Techniques            - External Attacks (Phishing, Malware)
- Cloud/SaaS Attacks            - Business Email Compromise (BEC)
- Identity & SSO Abuse          - Law Firm Compliance Violations
- Supply Chain Attacks          - AI/ML Security
- Physical + Cyber Convergence  - Financial Fraud
- Endpoint & Zero Trust
"""

import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

import warnings
warnings.filterwarnings("ignore")

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from aionos.core.temporal_engine import (
    TemporalCorrelationEngine, SecurityEvent, EventType
)
from aionos.core.baseline_engine import BehavioralBaselineEngine
from aionos.core.reasoning_engine import LLMReasoningEngine, LLMProvider


@dataclass
class AttackScenario:
    name: str
    category: str  # VPN, LATERAL, PERSISTENCE, EVASION, EXTERNAL, INSIDER
    description: str
    difficulty: str
    events: List[Dict]
    real_world_example: str


class ExpandedRedTeamSimulator:
    """Simulates 20+ attack scenarios across all categories"""
    
    def __init__(self):
        print("\n" + "=" * 70)
        print("INITIALIZING AION OS - FULL SPECTRUM DEFENSE")
        print("=" * 70)
        
        start = time.perf_counter()
        self.temporal = TemporalCorrelationEngine(fast_mode=True)
        self.baseline = BehavioralBaselineEngine(fast_mode=True)
        init_time = (time.perf_counter() - start) * 1000
        
        # Count patterns
        pattern_count = len(self.temporal.attack_sequences)
        event_types = len(EventType)
        
        print(f"  Initialized in {init_time:.2f}ms")
        print(f"  Attack patterns loaded: {pattern_count}")
        print(f"  Event types supported: {event_types}")
        print("=" * 70)
        
        self.scenarios = self._load_all_scenarios()
        self.results = []
    
    def _load_all_scenarios(self) -> List[AttackScenario]:
        """Load comprehensive attack scenarios"""
        
        return [
            # ============================================================
            # VPN BREACH ATTACKS
            # ============================================================
            AttackScenario(
                name="VPN Brute Force",
                category="VPN",
                description="Automated password guessing attack on VPN gateway",
                difficulty="EASY",
                events=[
                    {"type": EventType.VPN_BRUTE_FORCE, "details": {"attempts": 5000, "duration_min": 30}},
                    {"type": EventType.VPN_ACCESS, "delay_hours": 0.5, "details": {"success_after_failures": True}},
                    {"type": EventType.GEOGRAPHIC_ANOMALY, "delay_hours": 0.6, "details": {"location": "Russia"}},
                ],
                real_world_example="2023 Cisco VPN breach - Yanluowang ransomware"
            ),
            AttackScenario(
                name="Credential Stuffing Attack",
                category="VPN",
                description="Using leaked credentials from other breaches",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.VPN_CREDENTIAL_STUFFING, "details": {"source": "darkweb_dump"}},
                    {"type": EventType.VPN_ACCESS, "delay_hours": 0.1, "details": {"credential_age": "leaked_2023"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.5, "details": {"query": "SELECT * FROM clients"}},
                ],
                real_world_example="2024 23andMe breach - credential stuffing"
            ),
            AttackScenario(
                name="VPN Session Hijacking",
                category="VPN",
                description="Stealing active VPN session token",
                difficulty="HARD",
                events=[
                    {"type": EventType.VPN_SESSION_HIJACK, "details": {"method": "token_theft"}},
                    {"type": EventType.IMPOSSIBLE_TRAVEL, "delay_hours": 0.05, "details": {"from": "NYC", "to": "Beijing", "minutes": 3}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.1, "details": {"sensitive": True}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.2, "details": {"file_count": 500}},
                ],
                real_world_example="Lapsus$ session token attacks on Okta/Microsoft"
            ),
            AttackScenario(
                name="Split Tunnel Data Leak",
                category="VPN",
                description="Exfiltrating data through non-VPN connection",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.VPN_ACCESS, "details": {"connected": True}},
                    {"type": EventType.VPN_SPLIT_TUNNEL, "delay_hours": 0.1, "details": {"detected": True}},
                    {"type": EventType.SHADOW_IT, "delay_hours": 0.2, "details": {"service": "personal_dropbox"}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 0.3, "details": {"destination": "unmonitored"}},
                ],
                real_world_example="Remote work VPN bypass incidents"
            ),
            
            # ============================================================
            # ADVANCED VPN ATTACKS (PUSHED TO THE LIMIT)
            # ============================================================
            AttackScenario(
                name="MFA Fatigue Attack",
                category="VPN",
                description="Bombarding user with MFA prompts until they accept",
                difficulty="HARD",
                events=[
                    {"type": EventType.VPN_MFA_BYPASS, "details": {"mfa_attempts": 50, "method": "push_spam"}},
                    {"type": EventType.VPN_ACCESS, "delay_hours": 0.1, "details": {"approved_at": "2am"}},
                    {"type": EventType.GEOGRAPHIC_ANOMALY, "delay_hours": 0.2, "details": {"country": "North Korea"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.5, "details": {"sensitive_files": 200}},
                ],
                real_world_example="2022 Uber breach - Lapsus$ MFA fatigue attack"
            ),
            AttackScenario(
                name="Concurrent Session Hijack",
                category="VPN",
                description="Same credentials active in two locations simultaneously",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.VPN_CONCURRENT_SESSION, "details": {"locations": ["NYC", "Moscow"]}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.05, "details": {"query": "client_billing"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.1, "details": {"parallel_download": True}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 0.2, "details": {"records": 50000}},
                ],
                real_world_example="APT29 dual-session credential abuse"
            ),
            AttackScenario(
                name="OAuth Token Replay",
                category="VPN",
                description="Stolen SAML/OAuth token replayed from new device",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.VPN_TOKEN_REPLAY, "details": {"token_age_hours": 48}},
                    {"type": EventType.VPN_NEW_DEVICE, "delay_hours": 0.01, "details": {"fingerprint": "unknown"}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 0.5, "details": {"action": "export_all"}},
                    {"type": EventType.FILE_UPLOAD, "delay_hours": 1, "details": {"to": "external_storage"}},
                ],
                real_world_example="Golden SAML attacks - SolarWinds style"
            ),
            AttackScenario(
                name="DNS Tunnel Exfiltration",
                category="VPN",
                description="Covert data exfiltration via DNS queries over VPN",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.VPN_DNS_TUNNEL, "details": {"dns_queries_per_min": 1000}},
                    {"type": EventType.VPN_EXCESSIVE_BANDWIDTH, "delay_hours": 0.5, "details": {"gb_transferred": 50}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 1, "details": {"exfil_target": True}},
                ],
                real_world_example="DNScat2/Iodine covert channel attacks"
            ),
            AttackScenario(
                name="Dormant Account Takeover",
                category="VPN",
                description="Compromised dormant account suddenly activated",
                difficulty="HARD",
                events=[
                    {"type": EventType.VPN_DORMANT_ACCOUNT, "details": {"inactive_days": 180}},
                    {"type": EventType.VPN_NEW_DEVICE, "delay_hours": 0.01, "details": {"os": "Kali Linux"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.5, "details": {"years_of_data": True}},
                    {"type": EventType.USB_ACTIVITY, "delay_hours": 1, "details": {"device": "unknown_usb"}},
                ],
                real_world_example="Terminated employee credential abuse"
            ),
            AttackScenario(
                name="VPN C2 Channel",
                category="VPN",
                description="VPN tunnel hijacked for command & control traffic",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.VPN_TUNNEL_ABUSE, "details": {"c2_beacons_detected": True}},
                    {"type": EventType.VPN_ANOMALOUS_PROTOCOL, "delay_hours": 0.1, "details": {"protocol": "custom_binary"}},
                    {"type": EventType.LATERAL_MOVEMENT, "delay_hours": 0.5, "details": {"systems_touched": 15}},
                    {"type": EventType.MALWARE_DETECTED, "delay_hours": 1, "details": {"type": "cobalt_strike"}},
                ],
                real_world_example="APT41 VPN tunnel abuse for lateral movement"
            ),
            AttackScenario(
                name="Off-Hours VPN Raid",
                category="VPN",
                description="Attacker strikes during minimal monitoring hours",
                difficulty="HARD",
                events=[
                    {"type": EventType.VPN_OFF_HOURS_LOGIN, "details": {"time": "03:47 AM", "holiday": True}},
                    {"type": EventType.AFTER_HOURS_ACCESS, "delay_hours": 0.1, "details": {"first_in_6_months": True}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 0.5, "details": {"select_all_matters": True}},
                    {"type": EventType.FILE_UPLOAD, "delay_hours": 1, "details": {"to": "mega.nz"}},
                ],
                real_world_example="Holiday ransomware attacks (Kaseya July 4th)"
            ),
            AttackScenario(
                name="Certificate Spoofing",
                category="VPN",
                description="Attacker using forged/stolen VPN certificates",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.VPN_CERT_ANOMALY, "details": {"cert_status": "revoked_but_used"}},
                    {"type": EventType.VPN_ACCESS, "delay_hours": 0.01, "details": {"bypassed_cert_check": True}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.5, "details": {"query": "all_client_data"}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 1, "details": {"to": "attacker_controlled"}},
                ],
                real_world_example="Fortinet VPN certificate bypass CVE-2022-40684"
            ),
            
            # ============================================================
            # LATERAL MOVEMENT ATTACKS
            # ============================================================
            AttackScenario(
                name="Network Reconnaissance",
                category="LATERAL",
                description="Attacker mapping internal network after initial access",
                difficulty="HARD",
                events=[
                    {"type": EventType.VPN_ACCESS, "details": {"initial_compromise": True}},
                    {"type": EventType.RECONNAISSANCE, "delay_hours": 1, "details": {"ports_scanned": 1000}},
                    {"type": EventType.LATERAL_MOVEMENT, "delay_hours": 2, "details": {"systems": 5}},
                    {"type": EventType.CREDENTIAL_ACCESS, "delay_hours": 3, "details": {"vault": "password_manager"}},
                ],
                real_world_example="SolarWinds attack lateral movement phase"
            ),
            AttackScenario(
                name="Domain Admin Escalation",
                category="LATERAL",
                description="Escalating from user to domain administrator",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.CREDENTIAL_ACCESS, "details": {"target": "local_admin"}},
                    {"type": EventType.LATERAL_MOVEMENT, "delay_hours": 1, "details": {"target": "domain_controller"}},
                    {"type": EventType.PERMISSION_CHANGE, "delay_hours": 2, "details": {"new_role": "domain_admin"}},
                    {"type": EventType.ADMIN_ACTION, "delay_hours": 2.5, "details": {"action": "create_backdoor_account"}},
                    {"type": EventType.SERVICE_ACCOUNT_USE, "delay_hours": 3, "details": {"account": "backup_svc"}},
                ],
                real_world_example="Kaseya VSA ransomware attack"
            ),
            AttackScenario(
                name="Service Account Abuse",
                category="LATERAL",
                description="Hijacking service account for unrestricted access",
                difficulty="HARD",
                events=[
                    {"type": EventType.SERVICE_ACCOUNT_USE, "details": {"from": "user_workstation"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.1, "details": {"scope": "all_databases"}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 0.5, "details": {"records": 100000}},
                ],
                real_world_example="Capital One breach via misconfigured WAF"
            ),
            
            # ============================================================
            # PERSISTENCE ATTACKS
            # ============================================================
            AttackScenario(
                name="Scheduled Task Backdoor",
                category="PERSISTENCE",
                description="Creating persistent access via scheduled tasks",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.ADMIN_ACTION, "details": {"action": "access_task_scheduler"}},
                    {"type": EventType.SCHEDULED_TASK, "delay_hours": 0.1, "details": {"task": "system_update.exe"}},
                    {"type": EventType.REGISTRY_CHANGE, "delay_hours": 0.2, "details": {"key": "Run"}},
                ],
                real_world_example="APT29 persistence techniques"
            ),
            AttackScenario(
                name="Email Auto-Forward Attack",
                category="PERSISTENCE",
                description="Setting up email forwarding for ongoing exfiltration",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.EMAIL_RULE_CHANGE, "details": {"rule": "forward_all"}},
                    {"type": EventType.EMAIL_FORWARD, "delay_hours": 24, "details": {"to": "attacker@gmail.com"}},
                    {"type": EventType.EMAIL_FORWARD, "delay_hours": 48, "details": {"emails": 500}},
                ],
                real_world_example="BEC attacks via email rule manipulation"
            ),
            
            # ============================================================
            # EVASION ATTACKS
            # ============================================================
            AttackScenario(
                name="Evidence Destruction",
                category="EVASION",
                description="Attacker covering tracks after data theft",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.FILE_DOWNLOAD, "details": {"file_count": 1000}},
                    {"type": EventType.SECURITY_DISABLE, "delay_hours": 0.1, "details": {"disabled": "audit_logging"}},
                    {"type": EventType.LOG_DELETION, "delay_hours": 0.2, "details": {"logs": "security_events"}},
                ],
                real_world_example="NotPetya wiper malware"
            ),
            AttackScenario(
                name="Tor Exfiltration",
                category="EVASION",
                description="Exfiltrating data through Tor network",
                difficulty="HARD",
                events=[
                    {"type": EventType.TOR_ACCESS, "details": {"connection": "established"}},
                    {"type": EventType.PROXY_USE, "delay_hours": 0.1, "details": {"type": "onion_routing"}},
                    {"type": EventType.FILE_UPLOAD, "delay_hours": 0.5, "details": {"destination": "unknown", "size_mb": 500}},
                ],
                real_world_example="Ransomware C2 communication patterns"
            ),
            AttackScenario(
                name="Security Tool Disable",
                category="EVASION",
                description="Disabling EDR/AV before attack",
                difficulty="HARD",
                events=[
                    {"type": EventType.ADMIN_ACTION, "details": {"action": "access_security_console"}},
                    {"type": EventType.SECURITY_DISABLE, "delay_hours": 0.1, "details": {"tool": "EDR"}},
                    {"type": EventType.MALWARE_DETECTED, "delay_hours": 0.5, "details": {"type": "ransomware"}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 1, "details": {"operation": "encrypt_files"}},
                ],
                real_world_example="BlackCat ransomware EDR killer"
            ),
            
            # ============================================================
            # EXTERNAL ATTACKS
            # ============================================================
            AttackScenario(
                name="Phishing to Data Theft",
                category="EXTERNAL",
                description="Spearphishing leading to credential theft and exfil",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.PHISHING_CLICK, "details": {"email": "invoice_update.pdf"}},
                    {"type": EventType.MALWARE_DETECTED, "delay_hours": 0.01, "details": {"type": "infostealer"}},
                    {"type": EventType.CREDENTIAL_ACCESS, "delay_hours": 0.1, "details": {"captured": "browser_passwords"}},
                    {"type": EventType.VPN_ACCESS, "delay_hours": 1, "details": {"using": "stolen_creds"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 2, "details": {"file_count": 200}},
                ],
                real_world_example="2023 MGM/Caesars social engineering attack"
            ),
            AttackScenario(
                name="Malware Lateral Spread",
                category="EXTERNAL",
                description="Malware spreading through network",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.MALWARE_DETECTED, "details": {"patient_zero": True}},
                    {"type": EventType.LATERAL_MOVEMENT, "delay_hours": 0.5, "details": {"via": "smb_exploit"}},
                    {"type": EventType.LATERAL_MOVEMENT, "delay_hours": 1, "details": {"systems_infected": 10}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 2, "details": {"exfil_target": True}},
                    {"type": EventType.FILE_UPLOAD, "delay_hours": 3, "details": {"to": "c2_server"}},
                ],
                real_world_example="WannaCry/EternalBlue spread pattern"
            ),
            AttackScenario(
                name="Shadow IT Data Leak",
                category="EXTERNAL",
                description="Sensitive data uploaded to unauthorized cloud",
                difficulty="EASY",
                events=[
                    {"type": EventType.SHADOW_IT, "details": {"service": "personal_google_drive"}},
                    {"type": EventType.FILE_UPLOAD, "delay_hours": 0.1, "details": {"files": "client_contracts"}},
                    {"type": EventType.DLP_VIOLATION, "delay_hours": 0.2, "details": {"policy": "PII_detected"}},
                ],
                real_world_example="Employee cloud storage misuse"
            ),
            
            # ============================================================
            # INSIDER THREAT PATTERNS
            # ============================================================
            AttackScenario(
                name="Departing Attorney Classic",
                category="INSIDER",
                description="Partner taking client data before departure",
                difficulty="HARD",
                events=[
                    {"type": EventType.EMAIL_FORWARD, "details": {"to": "personal_email", "type": "client_contacts"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 24, "details": {"file_count": 100, "type": "client_matters"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 48, "details": {"query": "billing_history"}},
                    {"type": EventType.PRINT_JOB, "delay_hours": 72, "details": {"pages": 500}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 96, "details": {"to": "personal_dropbox"}},
                ],
                real_world_example="Typhoon case - $2M+ client theft"
            ),
            AttackScenario(
                name="After Hours Mass Download",
                category="INSIDER",
                description="Employee downloading everything at 3 AM",
                difficulty="EASY",
                events=[
                    {"type": EventType.AFTER_HOURS_ACCESS, "details": {"time": "03:00"}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 0.1, "details": {"select_all": True}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.2, "details": {"file_count": 5000}},
                    {"type": EventType.USB_ACTIVITY, "delay_hours": 0.3, "details": {"action": "copy_to_usb"}},
                ],
                real_world_example="Disgruntled employee theft pattern"
            ),
            AttackScenario(
                name="Privilege Abuse",
                category="INSIDER",
                description="Admin abusing elevated access for personal gain",
                difficulty="HARD",
                events=[
                    {"type": EventType.ADMIN_ACTION, "details": {"action": "query_all_users"}},
                    {"type": EventType.PERMISSION_CHANGE, "delay_hours": 0.5, "details": {"granted_self": "billing_access"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 1, "details": {"table": "compensation"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 2, "details": {"file": "salary_data.xlsx"}},
                ],
                real_world_example="Insider trading via HR data access"
            ),
            
            # ============================================================
            # CLOUD / SAAS ATTACKS 
            # ============================================================
            AttackScenario(
                name="Cloud Storage Mass Exfil",
                category="CLOUD",
                description="SharePoint/Box mass download with permission changes",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.CLOUD_STORAGE_ACCESS, "details": {"service": "SharePoint"}},
                    {"type": EventType.CLOUD_PERMISSION_CHANGE, "delay_hours": 0.1, "details": {"sharing": "external_link"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.5, "details": {"file_count": 2000}},
                    {"type": EventType.DLP_VIOLATION, "delay_hours": 0.6, "details": {"policy": "confidential_data"}},
                ],
                real_world_example="2024 Microsoft 365 tenant breaches"
            ),
            AttackScenario(
                name="Cloud Admin Account Takeover",
                category="CLOUD",
                description="Cloud admin compromised, infrastructure hijacked",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.CLOUD_ADMIN_CHANGE, "details": {"action": "new_global_admin"}},
                    {"type": EventType.CLOUD_CONFIG_CHANGE, "delay_hours": 0.1, "details": {"firewall": "disabled"}},
                    {"type": EventType.CLOUD_RESOURCE_CREATION, "delay_hours": 0.5, "details": {"resource": "10_large_VMs"}},
                ],
                real_world_example="Capital One AWS breach via SSRF"
            ),
            AttackScenario(
                name="API Key Data Breach",
                category="CLOUD",
                description="Exposed API key used to dump database",
                difficulty="EASY",
                events=[
                    {"type": EventType.API_KEY_EXPOSURE, "details": {"source": "github_commit"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.5, "details": {"query": "SELECT * FROM clients"}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 1, "details": {"records_exported": 500000}},
                ],
                real_world_example="Twitch 125GB source code leak via exposed keys"
            ),
            AttackScenario(
                name="Rogue SaaS App",
                category="CLOUD",
                description="Malicious SaaS app granted org-wide consent",
                difficulty="HARD",
                events=[
                    {"type": EventType.SAAS_APP_INSTALL, "details": {"app": "productivity_helper_v2"}},
                    {"type": EventType.OAUTH_CONSENT, "delay_hours": 0.01, "details": {"scope": "Mail.Read, Files.ReadWrite.All"}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 1, "details": {"data_synced_gb": 15}},
                    {"type": EventType.DLP_VIOLATION, "delay_hours": 1.5, "details": {"policy": "bulk_external_share"}},
                ],
                real_world_example="Storm-0558 Microsoft cloud breach 2023"
            ),
            
            # ============================================================
            # BUSINESS EMAIL COMPROMISE (BEC)
            # ============================================================
            AttackScenario(
                name="CEO Wire Fraud",
                category="BEC",
                description="Impersonating CEO to authorize fraudulent wire transfer",
                difficulty="HARD",
                events=[
                    {"type": EventType.EMAIL_IMPERSONATION, "details": {"spoofed": "ceo@firm.com", "to": "cfo@firm.com"}},
                    {"type": EventType.BEC_INDICATOR, "delay_hours": 0.1, "details": {"urgency": "immediate_transfer_needed"}},
                    {"type": EventType.WIRE_TRANSFER_REQUEST, "delay_hours": 0.5, "details": {"amount": 2500000, "to": "offshore_account"}},
                ],
                real_world_example="Ubiquiti $46.7M BEC fraud 2015"
            ),
            AttackScenario(
                name="Email Account Weaponization",
                category="BEC",
                description="Compromised email used for internal phishing and wire fraud",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.EMAIL_ACCOUNT_TAKEOVER, "details": {"method": "password_spray"}},
                    {"type": EventType.EMAIL_RULE_CHANGE, "delay_hours": 0.1, "details": {"rule": "hide_replies_from_victim"}},
                    {"type": EventType.EMAIL_FORWARD, "delay_hours": 1, "details": {"forwarding_to": "attacker@lookalike.com"}},
                    {"type": EventType.WIRE_TRANSFER_REQUEST, "delay_hours": 48, "details": {"amount": 890000}},
                ],
                real_world_example="2024 law firm BEC attacks targeting IOLTA accounts"
            ),
            AttackScenario(
                name="Executive Whaling",
                category="BEC",
                description="Targeted C-suite phishing with fake M&A urgency",
                difficulty="HARD",
                events=[
                    {"type": EventType.EXECUTIVE_WHALING, "details": {"target": "managing_partner", "pretext": "urgent_acquisition"}},
                    {"type": EventType.EMAIL_IMPERSONATION, "delay_hours": 0.5, "details": {"domain": "f1rm-name.com"}},
                    {"type": EventType.WIRE_TRANSFER_REQUEST, "delay_hours": 2, "details": {"amount": 5000000, "pretext": "escrow_deposit"}},
                ],
                real_world_example="Crelan Bank $75M CEO fraud 2016"
            ),
            AttackScenario(
                name="Vendor Invoice Redirect",
                category="BEC",
                description="Hijacked vendor email redirects payment to attacker",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.INVOICE_MANIPULATION, "details": {"vendor": "legal_software_inc", "changed_field": "bank_account"}},
                    {"type": EventType.PAYMENT_REDIRECT, "delay_hours": 24, "details": {"new_account": "offshore_bank"}},
                    {"type": EventType.WIRE_TRANSFER_REQUEST, "delay_hours": 48, "details": {"amount": 175000}},
                ],
                real_world_example="Toyota $37M vendor invoice fraud 2019"
            ),
            
            # ============================================================
            # IDENTITY & ACCESS FEDERATION ATTACKS
            # ============================================================
            AttackScenario(
                name="SSO Token Hijack",
                category="IDENTITY",
                description="Stolen SSO token used for cross-application data theft",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.SSO_ANOMALY, "details": {"anomaly": "token_from_unknown_ip"}},
                    {"type": EventType.IMPOSSIBLE_TRAVEL, "delay_hours": 0.01, "details": {"from": "Dallas", "to": "Lagos"}},
                    {"type": EventType.CLOUD_STORAGE_ACCESS, "delay_hours": 0.1, "details": {"accessed": "all_client_drives"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.5, "details": {"file_count": 3000}},
                ],
                real_world_example="Okta breach 2022 - Lapsus$ SSO abuse"
            ),
            AttackScenario(
                name="OAuth Consent Phishing",
                category="IDENTITY",
                description="Malicious app gets granted email/file access via OAuth",
                difficulty="HARD",
                events=[
                    {"type": EventType.PHISHING_CLICK, "details": {"url": "oauth-consent-prompt.com"}},
                    {"type": EventType.OAUTH_CONSENT, "delay_hours": 0.01, "details": {"permissions": "Mail.Read, Files.ReadWrite"}},
                    {"type": EventType.EMAIL_FORWARD, "delay_hours": 1, "details": {"auto_forward_enabled": True}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 2, "details": {"via_api": True}},
                ],
                real_world_example="Microsoft OAuth consent phishing campaigns 2023"
            ),
            AttackScenario(
                name="Conditional Access Bypass",
                category="IDENTITY",
                description="Attacker circumvents device compliance policies",
                difficulty="HARD",
                events=[
                    {"type": EventType.CONDITIONAL_ACCESS_BYPASS, "details": {"method": "legacy_auth_protocol"}},
                    {"type": EventType.VPN_NEW_DEVICE, "delay_hours": 0.01, "details": {"device": "unmanaged_linux"}},
                    {"type": EventType.GEOGRAPHIC_ANOMALY, "delay_hours": 0.05, "details": {"country": "Iran"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.5, "details": {"target": "client_database"}},
                ],
                real_world_example="Azure AD conditional access bypass via legacy protocols"
            ),
            AttackScenario(
                name="Password Spray to Takeover",
                category="IDENTITY",
                description="Low-and-slow password spray followed by MFA enrollment",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.PASSWORD_SPRAY, "details": {"accounts_targeted": 5000, "rate": "1_attempt_per_30min"}},
                    {"type": EventType.MFA_REGISTRATION_CHANGE, "delay_hours": 24, "details": {"new_device": "attacker_phone"}},
                    {"type": EventType.VPN_ACCESS, "delay_hours": 25, "details": {"with_new_mfa": True}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 26, "details": {"file_count": 500}},
                ],
                real_world_example="Midnight Blizzard Microsoft attack 2024"
            ),
            
            # ============================================================
            # LAW FIRM COMPLIANCE VIOLATIONS
            # ============================================================
            AttackScenario(
                name="Chinese Wall Breach",
                category="COMPLIANCE",
                description="Attorney accessing conflicting client matters",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.ETHICS_WALL_VIOLATION, "details": {"conflict": "opposing_parties_in_same_case"}},
                    {"type": EventType.CLIENT_MATTER_CROSSOVER, "delay_hours": 1, "details": {"matter_a": "Acme_v_Globex", "matter_b": "Globex_defense"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 2, "details": {"files": "opposing_party_strategies"}},
                ],
                real_world_example="DLA Piper conflict of interest violations"
            ),
            AttackScenario(
                name="Privileged Data Exfil",
                category="COMPLIANCE",
                description="Attorney-client privileged documents stolen",
                difficulty="HARD",
                events=[
                    {"type": EventType.PRIVILEGED_DATA_ACCESS, "details": {"privilege_type": "attorney_client"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.5, "details": {"file_count": 200, "type": "privilege_log"}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 1, "details": {"to": "personal_icloud"}},
                    {"type": EventType.DLP_VIOLATION, "delay_hours": 1.1, "details": {"policy": "privileged_content"}},
                ],
                real_world_example="Jones Day data breach 2021"
            ),
            AttackScenario(
                name="Trust Account Fraud",
                category="COMPLIANCE",
                description="IOLTA trust account accessed with suspicious transfers",
                difficulty="CRITICAL",
                events=[
                    {"type": EventType.TRUST_ACCOUNT_ACCESS, "details": {"account": "IOLTA_main", "after_hours": True}},
                    {"type": EventType.WIRE_TRANSFER_REQUEST, "delay_hours": 0.1, "details": {"amount": 750000, "to": "unknown_account"}},
                    {"type": EventType.BILLING_ANOMALY, "delay_hours": 0.5, "details": {"discrepancy": "transfer_not_in_ledger"}},
                ],
                real_world_example="State bar trust account embezzlement cases"
            ),
            AttackScenario(
                name="eDiscovery Data Theft",
                category="COMPLIANCE",
                description="eDiscovery export sent to unauthorized destination",
                difficulty="HARD",
                events=[
                    {"type": EventType.EDISCOVERY_EXPORT, "details": {"case": "major_litigation", "size_gb": 50}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 1, "details": {"to": "personal_drive"}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 2, "details": {"destination": "unauthorized_cloud"}},
                ],
                real_world_example="Epiq/ISFM eDiscovery breach incidents"
            ),
            
            # ============================================================
            # SUPPLY CHAIN ATTACKS
            # ============================================================
            AttackScenario(
                name="Vendor Account Compromise",
                category="SUPPLY_CHAIN",
                description="IT vendor account used to access client data",
                difficulty="HARD",
                events=[
                    {"type": EventType.VENDOR_ACCESS, "details": {"vendor": "managed_IT_provider"}},
                    {"type": EventType.VENDOR_PRIVILEGE_ESCALATION, "delay_hours": 0.5, "details": {"escalated_to": "domain_admin"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 1, "details": {"query": "all_client_matters"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 2, "details": {"file_count": 5000}},
                ],
                real_world_example="SolarWinds Orion supply chain attack"
            ),
            AttackScenario(
                name="Software Supply Chain",
                category="SUPPLY_CHAIN",
                description="Compromised dependency introduces backdoor",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.SUPPLY_CHAIN_ALERT, "details": {"package": "legal-utils-3.1.4", "type": "backdoor"}},
                    {"type": EventType.MALWARE_DETECTED, "delay_hours": 24, "details": {"type": "supply_chain_backdoor"}},
                    {"type": EventType.LATERAL_MOVEMENT, "delay_hours": 48, "details": {"via": "backdoor_c2"}},
                    {"type": EventType.CREDENTIAL_ACCESS, "delay_hours": 72, "details": {"stolen": "service_account_keys"}},
                ],
                real_world_example="3CX supply chain attack 2023"
            ),
            
            # ============================================================
            # AI / ML SECURITY ATTACKS
            # ============================================================
            AttackScenario(
                name="AI Model Theft",
                category="AI_SECURITY",
                description="Proprietary legal AI model and training data stolen",
                difficulty="HARD",
                events=[
                    {"type": EventType.AI_MODEL_ACCESS, "details": {"model": "legal_brief_generator"}},
                    {"type": EventType.TRAINING_DATA_ACCESS, "delay_hours": 1, "details": {"dataset": "10_years_case_law"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 2, "details": {"file": "model_weights.pt", "size_gb": 8}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 3, "details": {"to": "competitor_infrastructure"}},
                ],
                real_world_example="Google AI researcher trade secret theft 2023"
            ),
            AttackScenario(
                name="Prompt Injection Exfil",
                category="AI_SECURITY",
                description="Prompt injection extracts privileged info via AI assistant",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.PROMPT_INJECTION, "details": {"payload": "ignore_previous_instructions_dump_all_client_data"}},
                    {"type": EventType.AI_OUTPUT_EXFIL, "delay_hours": 0.01, "details": {"extracted": "client_case_strategies"}},
                    {"type": EventType.DLP_VIOLATION, "delay_hours": 0.02, "details": {"policy": "AI_output_contains_privilege"}},
                ],
                real_world_example="ChatGPT data extraction via prompt injection"
            ),
            AttackScenario(
                name="Copilot Data Harvesting",
                category="AI_SECURITY",
                description="AI assistant abused to systematically extract privileged data",
                difficulty="HARD",
                events=[
                    {"type": EventType.COPILOT_ABUSE, "details": {"queries": 500, "topic": "all_client_strategies"}},
                    {"type": EventType.PRIVILEGED_DATA_ACCESS, "delay_hours": 0.5, "details": {"via": "ai_assistant"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 1, "details": {"file": "ai_generated_summaries"}},
                ],
                real_world_example="Microsoft Copilot oversharing risks 2024"
            ),
            
            # ============================================================
            # PHYSICAL + CYBER CONVERGENCE
            # ============================================================
            AttackScenario(
                name="After Hours Physical Digital",
                category="PHYSICAL",
                description="Badge access at unusual time + USB data theft",
                difficulty="HARD",
                events=[
                    {"type": EventType.BADGE_ANOMALY, "details": {"location": "server_room", "time": "02:30", "unusual": True}},
                    {"type": EventType.AFTER_HOURS_ACCESS, "delay_hours": 0.01, "details": {"time": "02:35"}},
                    {"type": EventType.USB_ACTIVITY, "delay_hours": 0.1, "details": {"action": "bulk_copy"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.2, "details": {"to_usb": True, "size_gb": 20}},
                ],
                real_world_example="Physical insider threat at defense contractors"
            ),
            AttackScenario(
                name="BYOD Data Leak",
                category="PHYSICAL",
                description="Personal device syncs sensitive firm data",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.BYOD_DEVICE, "details": {"device": "personal_iphone", "first_seen": True}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 0.5, "details": {"to": "personal_icloud"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 1, "details": {"synced_files": 500}},
                    {"type": EventType.DLP_VIOLATION, "delay_hours": 1.1, "details": {"policy": "sensitive_on_unmanaged"}},
                ],
                real_world_example="BYOD data leakage incidents at law firms"
            ),
            AttackScenario(
                name="Scan and Exfiltrate",
                category="PHYSICAL",
                description="Physical documents scanned and emailed to personal account",
                difficulty="EASY",
                events=[
                    {"type": EventType.BADGE_ACCESS, "details": {"location": "copy_room", "time": "18:45"}},
                    {"type": EventType.SCAN_TO_EMAIL, "delay_hours": 0.05, "details": {"pages": 150, "to": "personal_gmail"}},
                    {"type": EventType.EMAIL_FORWARD, "delay_hours": 0.1, "details": {"to": "personal@gmail.com"}},
                ],
                real_world_example="Paper document exfiltration before departure"
            ),
            
            # ============================================================
            # FINANCIAL FRAUD (LAW FIRM BILLING)
            # ============================================================
            AttackScenario(
                name="Billing Fraud Scheme",
                category="FINANCIAL",
                description="Systematic time entry manipulation for overbilling",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.TIME_ENTRY_MANIPULATION, "details": {"pattern": "inflated_hours", "months": 6}},
                    {"type": EventType.BILLING_ANOMALY, "delay_hours": 48, "details": {"variance": "3x_peer_average"}},
                    {"type": EventType.EXPENSE_FRAUD, "delay_hours": 72, "details": {"fake_receipts": True}},
                ],
                real_world_example="DLA Piper partner billing fraud case"
            ),
            AttackScenario(
                name="Client Payment Hijack",
                category="FINANCIAL",
                description="Payment redirected to attacker-controlled account",
                difficulty="HARD",
                events=[
                    {"type": EventType.PAYMENT_REDIRECT, "details": {"client": "major_corporate_client"}},
                    {"type": EventType.INVOICE_MANIPULATION, "delay_hours": 24, "details": {"changed": "bank_routing_number"}},
                    {"type": EventType.WIRE_TRANSFER_REQUEST, "delay_hours": 72, "details": {"amount": 2100000}},
                ],
                real_world_example="Real estate wire fraud targeting law firms"
            ),
            
            # ============================================================
            # ENDPOINT & ZERO TRUST
            # ============================================================
            AttackScenario(
                name="Non-Compliant Device Attack",
                category="ENDPOINT",
                description="Unpatched device used as attack launchpad",
                difficulty="HARD",
                events=[
                    {"type": EventType.ENDPOINT_COMPLIANCE_FAIL, "details": {"reason": "unpatched_90_days"}},
                    {"type": EventType.ZERO_TRUST_VIOLATION, "delay_hours": 0.1, "details": {"bypassed": "device_health_check"}},
                    {"type": EventType.LATERAL_MOVEMENT, "delay_hours": 1, "details": {"from": "unpatched_laptop"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 2, "details": {"file_count": 1000}},
                ],
                real_world_example="Equifax breach via unpatched Apache Struts"
            ),
            AttackScenario(
                name="Firmware Rootkit",
                category="ENDPOINT",
                description="Firmware-level compromise for persistent invisible access",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.FIRMWARE_TAMPERING, "details": {"target": "UEFI_bootloader"}},
                    {"type": EventType.SECURITY_DISABLE, "delay_hours": 0.01, "details": {"disabled": "secure_boot"}},
                    {"type": EventType.CREDENTIAL_ACCESS, "delay_hours": 1, "details": {"method": "memory_scraping"}},
                ],
                real_world_example="LoJax UEFI rootkit (APT28)"
            ),
        ]
    
    def simulate_attack(self, scenario: AttackScenario) -> Dict:
        """Simulate a single attack scenario"""
        
        user_id = f"attacker_{scenario.name.replace(' ', '_').lower()}@target.com"
        
        # Calculate max delay to set base_time far enough in the past
        max_delay = max(e.get("delay_hours", 0) for e in scenario.events) if scenario.events else 0
        # Start attack in the past, so all events are before "now"
        base_time = datetime.now() - timedelta(hours=max_delay + 1)
        
        # RESET engines for each scenario to avoid cross-scenario interference
        self.temporal = TemporalCorrelationEngine(fast_mode=True)
        self.baseline = BehavioralBaselineEngine(fast_mode=True)
        
        detections = []
        total_time_us = 0
        events_processed = 0
        
        for event_data in scenario.events:
            event_time = base_time + timedelta(hours=event_data.get("delay_hours", 0))
            event = SecurityEvent(
                event_id=f"evt_{events_processed:04d}",
                user_id=user_id,
                event_type=event_data["type"],
                timestamp=event_time,
                source_system="red_team_sim",
                details=event_data.get("details", {})
            )
            
            detect_start = time.perf_counter()
            
            temporal_alerts = self.temporal.ingest_event(event)
            baseline_alerts = self.baseline.record_event(
                user_id=user_id,
                event_type=event_data["type"].value,
                timestamp=event_time,
                details=event_data.get("details", {})
            )
            
            detect_time_us = (time.perf_counter() - detect_start) * 1_000_000
            total_time_us += detect_time_us
            events_processed += 1
            
            for alert in temporal_alerts:
                detections.append({
                    "engine": "TEMPORAL",
                    "pattern": alert.pattern_name,
                    "severity": alert.severity,
                    "at_event": events_processed,
                    "time_us": detect_time_us
                })
            
            for alert in baseline_alerts:
                detections.append({
                    "engine": "BASELINE",
                    "pattern": alert.deviation_type.value,
                    "severity": alert.severity,
                    "at_event": events_processed,
                    "time_us": detect_time_us
                })
        
        return {
            "scenario": scenario.name,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "real_world": scenario.real_world_example,
            "events": events_processed,
            "detections": detections,
            "detected": len(detections) > 0,
            "first_detection_event": detections[0]["at_event"] if detections else None,
            "total_time_us": total_time_us,
            "avg_time_us": total_time_us / events_processed if events_processed else 0
        }
    
    def run_all_scenarios(self):
        """Run all attack scenarios by category"""
        
        print("\n")
        print("=" * 70)
        print("     AION OS - FULL SPECTRUM ATTACK SIMULATION")
        print("=" * 70)
        print(f"\n  Total Scenarios: {len(self.scenarios)}")
        print(f"  Categories: VPN, LATERAL, PERSISTENCE, EVASION, EXTERNAL, INSIDER,")
        print(f"              CLOUD, BEC, IDENTITY, COMPLIANCE, SUPPLY_CHAIN,")
        print(f"              AI_SECURITY, PHYSICAL, FINANCIAL, ENDPOINT")
        print("\n" + "-" * 70)
        
        # Group by category
        categories = {}
        for scenario in self.scenarios:
            if scenario.category not in categories:
                categories[scenario.category] = []
            categories[scenario.category].append(scenario)
        
        category_results = {}
        
        for category, scenarios in categories.items():
            print(f"\n{'='*70}")
            print(f"  CATEGORY: {category} ATTACKS ({len(scenarios)} scenarios)")
            print(f"{'='*70}")
            
            cat_detected = 0
            cat_total = 0
            
            for scenario in scenarios:
                print(f"\n  [{scenario.difficulty}] {scenario.name}")
                print(f"  {scenario.description}")
                
                result = self.simulate_attack(scenario)
                self.results.append(result)
                cat_total += 1
                
                if result["detected"]:
                    cat_detected += 1
                    pct = (result["first_detection_event"] / result["events"]) * 100
                    print(f"  -> DETECTED at event {result['first_detection_event']}/{result['events']} ({pct:.0f}%)")
                    print(f"     Pattern: {result['detections'][0]['pattern']} [{result['detections'][0]['severity']}]")
                    print(f"     Response: {result['avg_time_us']:.1f} microseconds")
                else:
                    print(f"  -> NOT DETECTED (requires LLM analysis)")
            
            category_results[category] = {"detected": cat_detected, "total": cat_total}
            print(f"\n  {category} Results: {cat_detected}/{cat_total} detected")
        
        self._print_summary(category_results)
    
    def _print_summary(self, category_results):
        """Print comprehensive summary"""
        
        total_detected = sum(1 for r in self.results if r["detected"])
        total = len(self.results)
        
        print("\n")
        print("=" * 70)
        print("                    FULL SPECTRUM RESULTS")
        print("=" * 70)
        
        # Category breakdown
        print("\n  DETECTION BY CATEGORY:")
        print(f"  {'-'*50}")
        for cat, stats in category_results.items():
            pct = stats["detected"] / stats["total"] * 100 if stats["total"] else 0
            bar = "#" * int(pct / 5)
            print(f"  {cat:<12}: {stats['detected']}/{stats['total']} ({pct:5.1f}%) {bar}")
        
        # Difficulty breakdown
        by_difficulty = {}
        for r in self.results:
            d = r["difficulty"]
            if d not in by_difficulty:
                by_difficulty[d] = {"total": 0, "detected": 0, "times": []}
            by_difficulty[d]["total"] += 1
            by_difficulty[d]["times"].append(r["avg_time_us"])
            if r["detected"]:
                by_difficulty[d]["detected"] += 1
        
        print(f"\n  DETECTION BY DIFFICULTY:")
        print(f"  {'-'*50}")
        for diff in ["EASY", "MEDIUM", "HARD", "NIGHTMARE"]:
            if diff in by_difficulty:
                stats = by_difficulty[diff]
                pct = stats["detected"] / stats["total"] * 100
                avg_time = sum(stats["times"]) / len(stats["times"])
                print(f"  {diff:<10}: {stats['detected']}/{stats['total']} ({pct:5.1f}%) | Avg {avg_time:.1f}us")
        
        # Performance stats
        total_events = sum(r["events"] for r in self.results)
        total_time_us = sum(r["total_time_us"] for r in self.results)
        avg_per_event = total_time_us / total_events if total_events else 0
        
        print(f"\n  PERFORMANCE:")
        print(f"  {'-'*50}")
        print(f"  Total scenarios:        {total}")
        print(f"  Total events:           {total_events}")
        print(f"  Total processing time:  {total_time_us/1000:.2f}ms")
        print(f"  Average per event:      {avg_per_event:.2f} microseconds")
        print(f"  Equivalent throughput:  {1_000_000/avg_per_event:,.0f} events/second")
        
        # Final verdict
        print(f"\n  OVERALL DETECTION RATE: {total_detected}/{total} ({total_detected/total*100:.1f}%)")
        print("=" * 70)
        
        if total_detected / total >= 0.9:
            print("\n  VERDICT: AION OS provides COMPREHENSIVE PROTECTION")
        elif total_detected / total >= 0.7:
            print("\n  VERDICT: AION OS provides STRONG PROTECTION")
        else:
            print("\n  VERDICT: Additional patterns needed for full coverage")
        
        print("\n  Coverage includes:")
        print("  - VPN breaches (brute force, session hijack, credential stuffing)")
        print("  - Lateral movement (recon, privilege escalation, service abuse)")
        print("  - Persistence (scheduled tasks, email rules, registry)")
        print("  - Evasion (log deletion, Tor, security disable)")
        print("  - External attacks (phishing, malware, shadow IT)")
        print("  - Insider threats (departure theft, after-hours, privilege abuse)")
        print("  - Cloud/SaaS attacks (SharePoint, API keys, OAuth consent)")
        print("  - Business Email Compromise (wire fraud, CEO impersonation)")
        print("  - Identity & SSO abuse (token hijack, conditional access bypass)")
        print("  - Law firm compliance (ethics walls, privilege, trust accounts)")
        print("  - Supply chain attacks (vendor compromise, package backdoors)")
        print("  - AI/ML security (model theft, prompt injection, copilot abuse)")
        print("  - Physical + cyber (badge anomalies, BYOD, scan-to-email)")
        print("  - Financial fraud (billing manipulation, payment redirect)")
        print("  - Endpoint & zero trust (non-compliant devices, firmware)")
        print()
        print("=" * 70)


def main():
    print("\n")
    print("     _    ___ ___  _   _    ___  ___")
    print("    / \\  |_ _/ _ \\| \\ | |  / _ \\/ __|")
    print("   / _ \\  | | | | |  \\| | | | | \\__ \\")
    print("  / ___ \\ | | |_| | |\\  | | |_| |__) |")
    print(" /_/   \\_\\___\\___/|_| \\_|  \\___/____/")
    print()
    print("       FULL SPECTRUM THREAT DETECTION")
    print()
    
    simulator = ExpandedRedTeamSimulator()
    simulator.run_all_scenarios()


if __name__ == "__main__":
    main()
