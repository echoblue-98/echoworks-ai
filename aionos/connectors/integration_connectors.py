"""
AION OS Integration Connectors

Stub connectors that demonstrate how AION would integrate with
enterprise security systems. These log the API calls that would
be made in production.

For pilot deployment, replace stub implementations with real API calls.

GEMINI FIX: Added granular permissions (allow_read vs allow_write)
"""

import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('aionos.connectors')


class ActionResult(Enum):
    """Result of an integration action"""
    SUCCESS = "success"
    FAILED = "failed"
    SIMULATED = "simulated"  # Stub mode
    BLOCKED = "blocked"      # GEMINI: Permission denied


class ActionType(Enum):
    """GEMINI FIX: Categorize actions as read or write"""
    READ = "read"    # Fetch data, query logs
    WRITE = "write"  # Modify state, suspend users, isolate hosts


@dataclass
class ConnectorPermissions:
    """
    GEMINI FIX: Granular permissions per connector.
    
    In production, you often want:
    - allow_read=True: Fetch logs, query status
    - allow_write=False: Require manual approval for suspensions
    """
    allow_read: bool = True
    allow_write: bool = False  # Default to manual approval
    require_approval_for: List[str] = field(default_factory=list)  # Specific actions needing approval


@dataclass
class IntegrationResponse:
    """Response from an integration call"""
    system: str
    action: str
    target: str
    result: ActionResult
    timestamp: datetime
    details: Dict[str, Any]
    api_call: str  # The API call that would be made


class BaseConnector(ABC):
    """Base class for all integration connectors"""
    
    def __init__(
        self, 
        config: Dict[str, Any] = None, 
        stub_mode: bool = True,
        permissions: ConnectorPermissions = None  # GEMINI FIX
    ):
        self.config = config or {}
        self.stub_mode = stub_mode
        self.permissions = permissions or ConnectorPermissions()
        self.system_name = "BaseConnector"
    
    def _check_permission(self, action_type: ActionType, action_name: str) -> bool:
        """GEMINI FIX: Check if action is permitted"""
        if action_type == ActionType.READ:
            if not self.permissions.allow_read:
                logger.warning(f"Permission denied: {action_name} (read disabled)")
                return False
        elif action_type == ActionType.WRITE:
            if not self.permissions.allow_write:
                logger.warning(f"Permission denied: {action_name} (write disabled - requires manual approval)")
                return False
            if action_name in self.permissions.require_approval_for:
                logger.warning(f"Permission denied: {action_name} (requires explicit approval)")
                return False
        return True
    
    def log_action(
        self, 
        action: str, 
        target: str, 
        api_call: str, 
        details: Dict = None,
        action_type: ActionType = ActionType.WRITE  # GEMINI FIX
    ) -> IntegrationResponse:
        """Log an action that would be taken"""
        
        # GEMINI FIX: Check permissions before executing
        if not self._check_permission(action_type, action):
            return IntegrationResponse(
                system=self.system_name,
                action=action,
                target=target,
                result=ActionResult.BLOCKED,
                timestamp=datetime.now(),
                details={"reason": "Permission denied"},
                api_call=api_call
            )
        
        response = IntegrationResponse(
            system=self.system_name,
            action=action,
            target=target,
            result=ActionResult.SIMULATED if self.stub_mode else ActionResult.SUCCESS,
            timestamp=datetime.now(),
            details=details or {},
            api_call=api_call
        )
        
        mode = "STUB" if self.stub_mode else "LIVE"
        logger.info(f"[{mode}] {self.system_name}: {action} -> {target}")
        logger.debug(f"  API Call: {api_call}")
        
        return response


# =============================================================================
# ENDPOINT DETECTION & RESPONSE (EDR)
# =============================================================================

class CrowdStrikeConnector(BaseConnector):
    """
    CrowdStrike Falcon integration
    
    Real API: https://api.crowdstrike.com
    Docs: https://falcon.crowdstrike.com/documentation
    
    GEMINI FIX: Supports granular permissions (read vs write)
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True, permissions: ConnectorPermissions = None):
        super().__init__(config, stub_mode, permissions)
        self.system_name = "CrowdStrike Falcon"
        self.base_url = config.get('base_url', 'https://api.crowdstrike.com') if config else 'https://api.crowdstrike.com'
    
    def get_device_details(self, device_id: str) -> IntegrationResponse:
        """GEMINI FIX: Read operation - get device info"""
        api_call = f"GET {self.base_url}/devices/entities/devices/v2?ids={device_id}"
        return self.log_action(
            action="Get Device Details",
            target=device_id,
            api_call=api_call,
            details={"operation": "query"},
            action_type=ActionType.READ  # GEMINI: Read operation
        )
    
    def isolate_host(self, device_id: str, reason: str) -> IntegrationResponse:
        """Isolate a host from the network (WRITE operation)"""
        api_call = f"POST {self.base_url}/devices/entities/devices-actions/v2"
        return self.log_action(
            action="Isolate Host",
            target=device_id,
            api_call=api_call,
            details={
                "action_name": "contain",
                "reason": reason,
                "body": {"ids": [device_id], "action_parameters": [{"name": "reason", "value": reason}]}
            },
            action_type=ActionType.WRITE  # GEMINI: Write operation
        )
    
    def disable_usb(self, device_id: str) -> IntegrationResponse:
        """Disable USB storage on device (WRITE operation)"""
        api_call = f"PATCH {self.base_url}/policy/entities/device-control/v1"
        return self.log_action(
            action="Disable USB Storage",
            target=device_id,
            api_call=api_call,
            details={
                "policy_update": {"usb_storage": "block"},
                "device_id": device_id
            },
            action_type=ActionType.WRITE  # GEMINI: Write operation
        )
    
    def kill_process(self, device_id: str, process_name: str) -> IntegrationResponse:
        """Kill a running process"""
        api_call = f"POST {self.base_url}/real-time-response/entities/command/v1"
        return self.log_action(
            action="Kill Process",
            target=f"{device_id}:{process_name}",
            api_call=api_call,
            details={
                "command": "kill",
                "process_name": process_name
            }
        )
    
    def forensic_snapshot(self, device_id: str) -> IntegrationResponse:
        """Initiate forensic data collection"""
        api_call = f"POST {self.base_url}/real-time-response/entities/sessions/v1"
        return self.log_action(
            action="Forensic Snapshot",
            target=device_id,
            api_call=api_call,
            details={
                "commands": ["memdump", "filelist", "regread", "eventlog"]
            }
        )


class MicrosoftDefenderConnector(BaseConnector):
    """
    Microsoft Defender for Endpoint integration
    
    Real API: https://api.securitycenter.microsoft.com
    Docs: https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "Microsoft Defender"
        self.base_url = 'https://api.securitycenter.microsoft.com/api'
    
    def isolate_machine(self, machine_id: str, reason: str) -> IntegrationResponse:
        """Isolate machine from network"""
        api_call = f"POST {self.base_url}/machines/{machine_id}/isolate"
        return self.log_action(
            action="Isolate Machine",
            target=machine_id,
            api_call=api_call,
            details={
                "IsolationType": "Full",
                "Comment": reason
            }
        )
    
    def run_av_scan(self, machine_id: str) -> IntegrationResponse:
        """Run antivirus scan"""
        api_call = f"POST {self.base_url}/machines/{machine_id}/runAntiVirusScan"
        return self.log_action(
            action="Run AV Scan",
            target=machine_id,
            api_call=api_call,
            details={"ScanType": "Full"}
        )


# =============================================================================
# IDENTITY PROVIDERS
# =============================================================================

class OktaConnector(BaseConnector):
    """
    Okta identity provider integration
    
    Real API: https://{tenant}.okta.com/api/v1
    Docs: https://developer.okta.com/docs/reference/
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "Okta"
        self.tenant = config.get('tenant', 'example') if config else 'example'
        self.base_url = f"https://{self.tenant}.okta.com/api/v1"
    
    def suspend_user(self, user_id: str, reason: str) -> IntegrationResponse:
        """Suspend user account"""
        api_call = f"POST {self.base_url}/users/{user_id}/lifecycle/suspend"
        return self.log_action(
            action="Suspend User",
            target=user_id,
            api_call=api_call,
            details={"reason": reason}
        )
    
    def terminate_sessions(self, user_id: str) -> IntegrationResponse:
        """Terminate all active sessions"""
        api_call = f"DELETE {self.base_url}/users/{user_id}/sessions"
        return self.log_action(
            action="Terminate All Sessions",
            target=user_id,
            api_call=api_call,
            details={}
        )
    
    def revoke_tokens(self, user_id: str) -> IntegrationResponse:
        """Revoke all OAuth tokens"""
        api_call = f"DELETE {self.base_url}/users/{user_id}/grants"
        return self.log_action(
            action="Revoke OAuth Tokens",
            target=user_id,
            api_call=api_call,
            details={}
        )
    
    def reset_mfa(self, user_id: str) -> IntegrationResponse:
        """Reset MFA factors"""
        api_call = f"DELETE {self.base_url}/users/{user_id}/factors"
        return self.log_action(
            action="Reset MFA",
            target=user_id,
            api_call=api_call,
            details={"require_re_enrollment": True}
        )


class AzureADConnector(BaseConnector):
    """
    Azure Active Directory integration
    
    Real API: https://graph.microsoft.com/v1.0
    Docs: https://docs.microsoft.com/en-us/graph/api/resources/users
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "Azure AD"
        self.base_url = "https://graph.microsoft.com/v1.0"
    
    def disable_account(self, user_id: str, reason: str) -> IntegrationResponse:
        """Disable user account"""
        api_call = f"PATCH {self.base_url}/users/{user_id}"
        return self.log_action(
            action="Disable Account",
            target=user_id,
            api_call=api_call,
            details={
                "accountEnabled": False,
                "reason": reason
            }
        )
    
    def revoke_sign_in_sessions(self, user_id: str) -> IntegrationResponse:
        """Revoke all sign-in sessions"""
        api_call = f"POST {self.base_url}/users/{user_id}/revokeSignInSessions"
        return self.log_action(
            action="Revoke Sign-In Sessions",
            target=user_id,
            api_call=api_call,
            details={}
        )
    
    def remove_from_group(self, user_id: str, group_id: str) -> IntegrationResponse:
        """Remove user from security group"""
        api_call = f"DELETE {self.base_url}/groups/{group_id}/members/{user_id}/$ref"
        return self.log_action(
            action="Remove from Group",
            target=f"{user_id} from {group_id}",
            api_call=api_call,
            details={"group_id": group_id}
        )


# =============================================================================
# VPN GATEWAYS
# =============================================================================

class CiscoAnyConnectConnector(BaseConnector):
    """
    Cisco AnyConnect / ISE integration
    
    Real API: Cisco ISE REST API
    Docs: https://developer.cisco.com/docs/identity-services-engine/
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "Cisco AnyConnect"
        self.ise_host = config.get('ise_host', 'ise.example.com') if config else 'ise.example.com'
        self.base_url = f"https://{self.ise_host}:9060/ers/config"
    
    def terminate_session(self, user_id: str, session_id: str) -> IntegrationResponse:
        """Terminate VPN session"""
        api_call = f"DELETE {self.base_url}/sessionservicenodegroup/{session_id}"
        return self.log_action(
            action="Terminate VPN Session",
            target=user_id,
            api_call=api_call,
            details={"session_id": session_id}
        )
    
    def quarantine_user(self, user_id: str, reason: str) -> IntegrationResponse:
        """Move user to quarantine group"""
        api_call = f"PUT {self.base_url}/endpointgroup"
        return self.log_action(
            action="Quarantine User",
            target=user_id,
            api_call=api_call,
            details={
                "group": "AION_Quarantine",
                "reason": reason
            }
        )


class PaloAltoGlobalProtectConnector(BaseConnector):
    """
    Palo Alto GlobalProtect / Firewall integration
    
    Real API: https://{firewall}/restapi/v10.1
    Docs: https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-panorama-api
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "Palo Alto"
        self.firewall = config.get('firewall', 'firewall.example.com') if config else 'firewall.example.com'
        self.base_url = f"https://{self.firewall}/restapi/v10.1"
    
    def disconnect_user(self, user_id: str, reason: str) -> IntegrationResponse:
        """Disconnect user from GlobalProtect"""
        api_call = f"POST {self.base_url}/GlobalProtect/Users/disconnect"
        return self.log_action(
            action="Disconnect VPN User",
            target=user_id,
            api_call=api_call,
            details={"reason": reason}
        )
    
    def isolate_segment(self, segment: str, reason: str) -> IntegrationResponse:
        """Isolate network segment"""
        api_call = f"POST {self.base_url}/Policies/SecurityRules"
        return self.log_action(
            action="Isolate Network Segment",
            target=segment,
            api_call=api_call,
            details={
                "rule_name": f"AION-ISOLATE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "from": segment,
                "to": "any",
                "action": "deny",
                "reason": reason
            }
        )
    
    def block_ip(self, ip_address: str, reason: str) -> IntegrationResponse:
        """Block IP address"""
        api_call = f"POST {self.base_url}/Objects/Addresses"
        return self.log_action(
            action="Block IP Address",
            target=ip_address,
            api_call=api_call,
            details={
                "name": f"AION-BLOCK-{ip_address.replace('.', '-')}",
                "ip-netmask": f"{ip_address}/32",
                "description": reason
            }
        )


# =============================================================================
# SIEM / SOAR
# =============================================================================

class SplunkConnector(BaseConnector):
    """
    Splunk SIEM integration
    
    Real API: https://{splunk}:8089/services
    Docs: https://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTprolog
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "Splunk"
        self.splunk_host = config.get('host', 'splunk.example.com') if config else 'splunk.example.com'
        self.base_url = f"https://{self.splunk_host}:8089/services"
    
    def create_notable_event(self, title: str, description: str, severity: str, user: str) -> IntegrationResponse:
        """Create a notable event in Splunk ES"""
        api_call = f"POST {self.base_url}/notable_event"
        return self.log_action(
            action="Create Notable Event",
            target=title,
            api_call=api_call,
            details={
                "rule_name": title,
                "security_domain": "access",
                "severity": severity,
                "user": user,
                "description": description
            }
        )
    
    def preserve_logs(self, search_query: str, retention_days: int = 365) -> IntegrationResponse:
        """Preserve logs with extended retention"""
        api_call = f"POST {self.base_url}/saved/searches"
        return self.log_action(
            action="Preserve Logs",
            target=search_query[:50],
            api_call=api_call,
            details={
                "search": search_query,
                "retention_days": retention_days,
                "purpose": "AION forensic preservation"
            }
        )


# =============================================================================
# IT SERVICE MANAGEMENT (ITSM)
# =============================================================================

class ServiceNowConnector(BaseConnector):
    """
    ServiceNow ITSM integration
    
    Real API: https://{instance}.service-now.com/api/now
    Docs: https://docs.servicenow.com/bundle/rome-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "ServiceNow"
        self.instance = config.get('instance', 'example') if config else 'example'
        self.base_url = f"https://{self.instance}.service-now.com/api/now"
    
    def create_security_incident(self, title: str, description: str, priority: str, user: str) -> IntegrationResponse:
        """Create a security incident"""
        api_call = f"POST {self.base_url}/table/sn_si_incident"
        return self.log_action(
            action="Create Security Incident",
            target=title,
            api_call=api_call,
            details={
                "short_description": title,
                "description": description,
                "priority": priority,
                "category": "Security",
                "caller_id": user,
                "assignment_group": "Security Operations"
            }
        )
    
    def create_hr_case(self, employee: str, issue: str, priority: str) -> IntegrationResponse:
        """Create an HR case for employee review"""
        api_call = f"POST {self.base_url}/table/sn_hr_core_case"
        return self.log_action(
            action="Create HR Case",
            target=employee,
            api_call=api_call,
            details={
                "opened_for": employee,
                "short_description": issue,
                "priority": priority,
                "category": "Security Investigation"
            }
        )


class PagerDutyConnector(BaseConnector):
    """
    PagerDuty integration for alerting
    
    Real API: https://api.pagerduty.com
    Docs: https://developer.pagerduty.com/api-reference/
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "PagerDuty"
        self.base_url = "https://api.pagerduty.com"
    
    def trigger_incident(self, title: str, description: str, severity: str, service_id: str) -> IntegrationResponse:
        """Trigger a PagerDuty incident"""
        api_call = f"POST {self.base_url}/incidents"
        return self.log_action(
            action="Trigger Incident",
            target=title,
            api_call=api_call,
            details={
                "incident": {
                    "type": "incident",
                    "title": title,
                    "service": {"id": service_id, "type": "service_reference"},
                    "urgency": "high" if severity == "CRITICAL" else "low",
                    "body": {"type": "incident_body", "details": description}
                }
            }
        )


# =============================================================================
# PHYSICAL SECURITY
# =============================================================================

class LenelConnector(BaseConnector):
    """
    Lenel OnGuard physical access control
    
    Real API: Lenel OnGuard API
    """
    
    def __init__(self, config: Dict = None, stub_mode: bool = True):
        super().__init__(config, stub_mode)
        self.system_name = "Lenel OnGuard"
        self.server = config.get('server', 'lenel.example.com') if config else 'lenel.example.com'
        self.base_url = f"https://{self.server}/api/access"
    
    def suspend_badge(self, badge_id: str, reason: str) -> IntegrationResponse:
        """Suspend a badge"""
        api_call = f"POST {self.base_url}/cardholder/badge/suspend"
        return self.log_action(
            action="Suspend Badge",
            target=badge_id,
            api_call=api_call,
            details={
                "badge_id": badge_id,
                "reason": reason,
                "effective_immediately": True,
                "notify_security_desk": True
            }
        )
    
    def alert_security_desk(self, message: str, priority: str) -> IntegrationResponse:
        """Send alert to security desk"""
        api_call = f"POST {self.base_url}/alerts"
        return self.log_action(
            action="Alert Security Desk",
            target="Security Desk",
            api_call=api_call,
            details={
                "message": message,
                "priority": priority,
                "requires_acknowledgment": True
            }
        )


# =============================================================================
# ORCHESTRATOR - Coordinates Multiple Connectors
# =============================================================================

class AIONOrchestrator:
    """
    Orchestrates actions across multiple integrated systems.
    
    This is the main entry point for AION's automated responses.
    """
    
    def __init__(self, stub_mode: bool = True):
        self.stub_mode = stub_mode
        
        # Initialize all connectors
        self.crowdstrike = CrowdStrikeConnector(stub_mode=stub_mode)
        self.defender = MicrosoftDefenderConnector(stub_mode=stub_mode)
        self.okta = OktaConnector(stub_mode=stub_mode)
        self.azure_ad = AzureADConnector(stub_mode=stub_mode)
        self.cisco = CiscoAnyConnectConnector(stub_mode=stub_mode)
        self.palo_alto = PaloAltoGlobalProtectConnector(stub_mode=stub_mode)
        self.splunk = SplunkConnector(stub_mode=stub_mode)
        self.servicenow = ServiceNowConnector(stub_mode=stub_mode)
        self.pagerduty = PagerDutyConnector(stub_mode=stub_mode)
        self.lenel = LenelConnector(stub_mode=stub_mode)
        
        self.action_log: List[IntegrationResponse] = []
    
    def respond_to_vpn_compromise(self, user_id: str, device_id: str, session_id: str) -> List[IntegrationResponse]:
        """
        Respond to VPN credential compromise.
        
        Actions:
        1. Terminate VPN session (Cisco)
        2. Revoke credentials (Azure AD)
        3. Isolate endpoint (CrowdStrike)
        4. Create SIEM event (Splunk)
        5. Create incident ticket (ServiceNow)
        """
        logger.info(f"=== AION RESPONSE: VPN Compromise for {user_id} ===")
        
        actions = [
            self.cisco.terminate_session(user_id, session_id),
            self.azure_ad.disable_account(user_id, "AION: VPN credential compromise detected"),
            self.azure_ad.revoke_sign_in_sessions(user_id),
            self.crowdstrike.isolate_host(device_id, "AION: VPN compromise - containing threat"),
            self.crowdstrike.forensic_snapshot(device_id),
            self.splunk.create_notable_event(
                title=f"AION: VPN Credential Compromise - {user_id}",
                description="Former employee accessed VPN from suspicious location",
                severity="critical",
                user=user_id
            ),
            self.servicenow.create_security_incident(
                title=f"VPN Credential Compromise - {user_id}",
                description="AION detected unauthorized VPN access",
                priority="1",
                user=user_id
            )
        ]
        
        self.action_log.extend(actions)
        return actions
    
    def respond_to_attorney_departure(self, user_id: str, device_id: str) -> List[IntegrationResponse]:
        """
        Respond to attorney departure exfiltration risk.
        
        Actions:
        1. Disable USB (CrowdStrike)
        2. Downgrade to read-only (Azure AD)
        3. Block cloud sync (Defender)
        4. Create HR case (ServiceNow)
        5. Preserve evidence (Splunk)
        """
        logger.info(f"=== AION RESPONSE: Attorney Departure Risk for {user_id} ===")
        
        actions = [
            self.crowdstrike.disable_usb(device_id),
            self.azure_ad.remove_from_group(user_id, "FullAccessGroup"),
            self.splunk.preserve_logs(f'user="{user_id}"', retention_days=365),
            self.servicenow.create_hr_case(
                employee=user_id,
                issue="AION: Pre-departure data staging detected",
                priority="2"
            )
        ]
        
        self.action_log.extend(actions)
        return actions
    
    def respond_to_mfa_fatigue(self, user_id: str) -> List[IntegrationResponse]:
        """
        Respond to MFA fatigue attack.
        
        Actions:
        1. Terminate all sessions (Okta)
        2. Lock account (Okta)
        3. Revoke tokens (Okta)
        4. Page security team (PagerDuty)
        5. Reset MFA (Okta)
        """
        logger.info(f"=== AION RESPONSE: MFA Fatigue Attack for {user_id} ===")
        
        actions = [
            self.okta.terminate_sessions(user_id),
            self.okta.suspend_user(user_id, "AION: MFA fatigue attack detected"),
            self.okta.revoke_tokens(user_id),
            self.pagerduty.trigger_incident(
                title=f"AION: MFA Fatigue Attack - {user_id}",
                description="User accepted MFA prompt after 47 push notifications",
                severity="CRITICAL",
                service_id="security-ops"
            ),
            self.okta.reset_mfa(user_id)
        ]
        
        self.action_log.extend(actions)
        return actions
    
    def respond_to_after_hours_theft(self, user_id: str, device_id: str, badge_id: str) -> List[IntegrationResponse]:
        """
        Respond to after-hours insider theft.
        
        Actions:
        1. Disable USB (CrowdStrike)
        2. Suspend badge (Lenel)
        3. Lock workstation (Defender)
        4. Alert security desk (Lenel)
        5. Create security incident (ServiceNow)
        """
        logger.info(f"=== AION RESPONSE: After-Hours Theft for {user_id} ===")
        
        actions = [
            self.crowdstrike.disable_usb(device_id),
            self.lenel.suspend_badge(badge_id, "AION: After-hours anomaly detected"),
            self.lenel.alert_security_desk(
                message=f"AION ALERT: {user_id} detected copying files at 02:30 AM. Badge suspended.",
                priority="high"
            ),
            self.servicenow.create_security_incident(
                title=f"After-Hours Data Theft Attempt - {user_id}",
                description="AION detected mass file copy to USB at 02:30 AM",
                priority="1",
                user=user_id
            )
        ]
        
        self.action_log.extend(actions)
        return actions
    
    def respond_to_lateral_movement(self, user_id: str, device_id: str, segment: str) -> List[IntegrationResponse]:
        """
        Respond to lateral movement / privilege escalation.
        
        Actions:
        1. Disable account (Azure AD)
        2. Kill sessions (CrowdStrike)
        3. Isolate segment (Palo Alto)
        4. Create critical incident (ServiceNow)
        5. Page IR team (PagerDuty)
        """
        logger.info(f"=== AION RESPONSE: Lateral Movement for {user_id} ===")
        
        actions = [
            self.azure_ad.disable_account(user_id, "AION: Lateral movement detected"),
            self.azure_ad.revoke_sign_in_sessions(user_id),
            self.crowdstrike.isolate_host(device_id, "AION: APT-style lateral movement"),
            self.palo_alto.isolate_segment(segment, "AION: Containing lateral movement"),
            self.servicenow.create_security_incident(
                title=f"APT-Style Lateral Movement - {user_id}",
                description="AION detected privilege escalation to Domain Admin",
                priority="1",
                user=user_id
            ),
            self.pagerduty.trigger_incident(
                title=f"AION CRITICAL: Lateral Movement - {user_id}",
                description="Intern account escalated to Domain Admin. 8 systems accessed.",
                severity="CRITICAL",
                service_id="incident-response"
            )
        ]
        
        self.action_log.extend(actions)
        return actions
    
    def get_action_log(self) -> List[Dict]:
        """Get log of all actions taken"""
        return [
            {
                "system": action.system,
                "action": action.action,
                "target": action.target,
                "result": action.result.value,
                "timestamp": action.timestamp.isoformat(),
                "api_call": action.api_call
            }
            for action in self.action_log
        ]


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AION OS Integration Connectors Demo")
    print("=" * 60)
    print()
    
    # Create orchestrator in stub mode
    orchestrator = AIONOrchestrator(stub_mode=True)
    
    # Simulate VPN compromise response
    print("\n--- Scenario: VPN Credential Compromise ---")
    orchestrator.respond_to_vpn_compromise(
        user_id="jsmith.terminated@firm.com",
        device_id="DEVICE-ABC123",
        session_id="VPN-SESSION-789"
    )
    
    # Simulate attorney departure response
    print("\n--- Scenario: Attorney Departure Risk ---")
    orchestrator.respond_to_attorney_departure(
        user_id="rchen.partner@firm.com",
        device_id="DEVICE-DEF456"
    )
    
    # Simulate MFA fatigue response
    print("\n--- Scenario: MFA Fatigue Attack ---")
    orchestrator.respond_to_mfa_fatigue(
        user_id="jdoe@firm.com"
    )
    
    # Print action summary
    print("\n" + "=" * 60)
    print("ACTION SUMMARY")
    print("=" * 60)
    
    action_log = orchestrator.get_action_log()
    print(f"\nTotal actions: {len(action_log)}")
    
    for action in action_log:
        print(f"  [{action['result'].upper()}] {action['system']}: {action['action']} -> {action['target']}")
