# AION OS Integration Architecture

## Overview

AION OS is the **intelligence layer** that detects threats and decides on responses. It integrates with your existing security infrastructure to execute those responses.

```
┌─────────────────────────────────────────────────────────────────┐
│                        AION OS (Brain)                          │
│  • Pattern Detection (29 attack signatures)                     │
│  • Behavioral Baselines (per-user anomaly detection)            │
│  • Decision Engine (what actions to take)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ REST API / Webhooks
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Layer                            │
├─────────────┬─────────────┬─────────────┬─────────────┬────────┤
│  Endpoint   │  Identity   │  Network    │  SIEM/SOAR  │  ITSM  │
│  Agents     │  Providers  │  Security   │             │        │
└─────────────┴─────────────┴─────────────┴─────────────┴────────┘
```

---

## Supported Integrations

### 1. Endpoint Detection & Response (EDR)

| Vendor | API Endpoint | Actions AION Can Command |
|--------|--------------|--------------------------|
| **CrowdStrike Falcon** | `api.crowdstrike.com` | Isolate host, kill process, disable USB, forensic snapshot |
| **Microsoft Defender** | `api.securitycenter.microsoft.com` | Isolate machine, run AV scan, collect investigation package |
| **Carbon Black** | `defense.conferdeploy.net` | Quarantine device, kill process, ban hash |
| **SentinelOne** | `usea1.sentinelone.net` | Disconnect from network, initiate rollback, fetch logs |

**Example: CrowdStrike USB Disable**
```python
# AION sends this command to CrowdStrike
POST https://api.crowdstrike.com/policy/entities/device-control/v1

Headers:
  Authorization: Bearer {oauth_token}
  Content-Type: application/json

Body:
{
  "device_id": "abc123def456",
  "action": "contain",
  "policy_update": {
    "usb_storage": "block"
  }
}
```

---

### 2. Identity Providers

| Vendor | API Endpoint | Actions AION Can Command |
|--------|--------------|--------------------------|
| **Okta** | `{tenant}.okta.com/api/v1` | Suspend user, revoke sessions, clear MFA, force password reset |
| **Azure AD** | `graph.microsoft.com` | Disable account, revoke tokens, remove group membership |
| **Duo Security** | `api-{host}.duosecurity.com` | Lock user, invalidate sessions, require re-enrollment |
| **Ping Identity** | `api.pingone.com` | Disable user, expire sessions |

**Example: Okta Session Termination**
```python
# AION sends this command to Okta
DELETE https://{tenant}.okta.com/api/v1/users/{userId}/sessions

Headers:
  Authorization: SSWS {api_token}
  Content-Type: application/json

# Response: All active sessions for user terminated
```

---

### 3. VPN Gateways

| Vendor | API Endpoint | Actions AION Can Command |
|--------|--------------|--------------------------|
| **Cisco AnyConnect** | ISE API / AnyConnect Management | Terminate session, revoke certificate, block IP |
| **Palo Alto GlobalProtect** | `firewall.api/restapi` | Disconnect user, update HIP profile, block |
| **Zscaler ZPA** | `api.zscaler.com` | Revoke access, update policy, terminate session |
| **Fortinet FortiClient** | FortiManager API | Kill VPN tunnel, update profile |

**Example: Palo Alto VPN Termination**
```python
# AION sends this command to Palo Alto
POST https://{firewall}/restapi/v10.1/GlobalProtect/Users/disconnect

Headers:
  X-PAN-KEY: {api_key}
  Content-Type: application/json

Body:
{
  "user": "jsmith.terminated@firm.com",
  "reason": "AION: Threat detected - credential compromise"
}
```

---

### 4. Network Security

| Vendor | API Endpoint | Actions AION Can Command |
|--------|--------------|--------------------------|
| **Palo Alto Firewall** | `{firewall}/restapi` | Block IP, isolate segment, update security policy |
| **Cisco Firepower** | FMC REST API | Create block rule, quarantine host |
| **Fortinet FortiGate** | `{firewall}/api/v2` | Add to blocklist, isolate VLAN |
| **Zscaler ZIA** | `api.zscaler.com` | Update URL category, block destination |

**Example: Network Segment Isolation**
```python
# AION sends this command to Palo Alto
POST https://{firewall}/restapi/v10.1/Policies/SecurityRules

Body:
{
  "entry": {
    "name": "AION-ISOLATE-{timestamp}",
    "from": {"member": ["compromised-segment"]},
    "to": {"member": ["any"]},
    "action": "deny",
    "description": "AION auto-isolation: lateral movement detected"
  }
}
```

---

### 5. SIEM / SOAR

| Vendor | API Endpoint | Actions AION Can Command |
|--------|--------------|--------------------------|
| **Splunk** | `{splunk}:8089/services` | Create notable event, trigger playbook, preserve logs |
| **Microsoft Sentinel** | `management.azure.com` | Create incident, run playbook, update entity |
| **IBM QRadar** | `{qradar}/api` | Create offense, add to reference set |
| **Palo Alto Cortex XSOAR** | `{xsoar}/xsoar/public_api` | Create incident, run playbook |

**Example: Splunk Notable Event**
```python
# AION sends this to Splunk
POST https://{splunk}:8089/services/notable_event

Body:
{
  "rule_name": "AION: Attorney Departure Exfiltration",
  "security_domain": "access",
  "severity": "critical",
  "user": "rchen.partner@firm.com",
  "src": "workstation-042",
  "description": "AION detected pre-departure data staging. 520% download spike.",
  "recommended_actions": "Review HR status, check USB logs, preserve evidence"
}
```

---

### 6. IT Service Management (ITSM)

| Vendor | API Endpoint | Actions AION Can Command |
|--------|--------------|--------------------------|
| **ServiceNow** | `{instance}.service-now.com/api` | Create incident, create HR case, page on-call |
| **Jira Service Management** | `{site}.atlassian.net/rest/api` | Create ticket, assign priority |
| **PagerDuty** | `api.pagerduty.com` | Trigger incident, page team |
| **Slack** | `slack.com/api` | Send alert to security channel, create incident channel |

**Example: ServiceNow Security Incident**
```python
# AION sends this to ServiceNow
POST https://{instance}.service-now.com/api/now/table/sn_si_incident

Headers:
  Authorization: Basic {base64_creds}
  Content-Type: application/json

Body:
{
  "short_description": "AION: VPN Credential Compromise - jsmith.terminated",
  "priority": "1",
  "category": "Security",
  "subcategory": "Account Compromise",
  "description": "Former employee accessed VPN from Eastern Europe...",
  "assignment_group": "Security Operations",
  "caller_id": "aion-system"
}
```

---

### 7. Physical Security

| Vendor | API Endpoint | Actions AION Can Command |
|--------|--------------|--------------------------|
| **Lenel OnGuard** | OnGuard API | Suspend badge, alert security desk |
| **CCure 9000** | CCure API | Disable card, trigger alarm |
| **Genetec** | Security Center SDK | Lock doors, notify security |

**Example: Badge Suspension**
```python
# AION sends this to Lenel OnGuard
POST https://{server}/api/access/cardholder/{id}/badge/suspend

Body:
{
  "badge_id": "BADGE-12345",
  "reason": "AION: After-hours anomaly detected",
  "effective_immediately": true,
  "notify_security_desk": true
}
```

---

## Integration Setup for Pilot

### What We Need From the Law Firm

1. **API Credentials** (read/write access):
   - EDR platform (CrowdStrike, Defender, etc.)
   - Identity provider (Okta, Azure AD, etc.)
   - VPN gateway (Cisco, Palo Alto, etc.)
   - SIEM (Splunk, Sentinel, etc.)
   - ITSM (ServiceNow, etc.)

2. **Webhook Endpoint** (for AION to push events):
   - HTTPS endpoint in their network
   - Or use cloud relay (AWS API Gateway, Azure Functions)

3. **Test Accounts**:
   - Non-production user for testing
   - Sandbox/dev environment preferred

### Integration Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Discovery** | 1 day | Map existing security stack |
| **API Setup** | 2-3 days | Configure API credentials, test connectivity |
| **Integration Build** | 3-5 days | Connect AION to each system |
| **Testing** | 2-3 days | End-to-end threat simulation |
| **Go-Live** | 1 day | Enable production monitoring |

**Total: 10-14 business days**

---

## Architecture Diagram

```
                    ┌──────────────────────┐
                    │    Security Events   │
                    │  (VPN, EDR, DLP,     │
                    │   Badge, Email...)   │
                    └──────────┬───────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                         AION OS                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Temporal Correlation Engine (29 patterns, 17μs/event) │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Behavioral Baseline Engine (per-user anomaly scores)  │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Decision Engine (what actions + which systems)        │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ CrowdStrike│  │   Okta     │  │ ServiceNow │
    │ (Endpoint) │  │ (Identity) │  │   (ITSM)   │
    └────────────┘  └────────────┘  └────────────┘
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Disable   │  │  Revoke    │  │  Create    │
    │    USB     │  │  Sessions  │  │  Incident  │
    └────────────┘  └────────────┘  └────────────┘
```

---

## Security Considerations

1. **Least Privilege**: AION only requests permissions it needs
2. **Credential Storage**: API keys stored in HashiCorp Vault or AWS Secrets Manager
3. **Audit Trail**: All API calls logged to immutable storage
4. **Kill Switch**: Manual override to disable auto-actions
5. **Approval Workflows**: Optional human-in-the-loop for high-impact actions

---

## Questions for Dan

1. What EDR platform does the pilot firm use?
2. What identity provider (Okta, Azure AD, etc.)?
3. Do they have a SIEM? Which one?
4. Is there a ServiceNow or similar ITSM?
5. Do they want AION to auto-execute or just recommend?
