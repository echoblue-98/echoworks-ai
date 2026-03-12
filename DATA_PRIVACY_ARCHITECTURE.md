# AION OS — Data Privacy Architecture

**One-Pager for Firm Security Teams & CISOs**

---

## Zero-Trust Data Architecture

AION OS is designed with a **zero-data-leakage** architecture. Every component is built to ensure that sensitive firm data never leaves the on-premises environment.

```
┌─────────────────────────────────────────────────────────┐
│                    FIRM NETWORK                          │
│                                                         │
│  ┌──────────┐    ┌──────────────────────────────────┐   │
│  │   SIEM   │───▶│          AION OS                  │   │
│  │ (Splunk/ │    │                                   │   │
│  │  QRadar) │    │  ┌─────────┐   ┌──────────────┐  │   │
│  └──────────┘    │  │Detection│   │  Encrypted   │  │   │
│                  │  │ Engine  │──▶│  Data Store   │  │   │
│  ┌──────────┐    │  └─────────┘   │ (AES-256-GCM)│  │   │
│  │ Identity │───▶│                └──────────────┘  │   │
│  │ Provider │    │  ┌─────────┐                     │   │
│  │(Okta/AAD)│    │  │REST API │◄── SOC Analysts     │   │
│  └──────────┘    │  │ (RBAC)  │                     │   │
│                  │  └─────────┘                     │   │
│                  └──────────────────────────────────┘   │
│                                                         │
│                    ╳ NO OUTBOUND DATA ╳                  │
└─────────────────────────────────────────────────────────┘
```

---

## Six Privacy Guarantees

### 1. On-Premises Only — No Cloud Dependencies

| Property | Implementation |
|----------|---------------|
| Deployment | Docker container or bare-metal on firm infrastructure |
| Data storage | Local filesystem (`AION_DATA_DIR`) on firm-controlled disks |
| LLM inference | Local model (Ollama/LM Studio) — no API calls to OpenAI/Anthropic required |
| DNS/CDN | Self-hosted fonts and static assets — zero external HTTP requests |
| Telemetry | **No phone-home, no usage analytics, no crash reporting** |

**Verification**: Run `netstat` during operation — zero outbound connections (except IdP if SSO enabled).

### 2. AES-256-GCM Encryption at Rest

| Specification | Value |
|---------------|-------|
| Algorithm | AES-256-GCM (NIST SP 800-38D, FIPS 197) |
| Key size | 256-bit (32 bytes) |
| Nonce | 96-bit, cryptographically random per operation |
| Authentication | 128-bit GCM tag (integrity + confidentiality) |
| Key derivation | PBKDF2-HMAC-SHA256, 600,000 iterations (exceeds OWASP 2023) |
| Key storage | Environment variable or file — never in code or logs |

**What's encrypted**: All event data, user profiles, forensic reports, risk scores, and audit logs stored on disk.

### 3. Role-Based Access Control (RBAC)

| Role | Capabilities | Cannot |
|------|-------------|--------|
| **Admin** | Full system control, policy management, improvement cycles | — |
| **Analyst** | View alerts, submit feedback, ingest events | Change policies, run improvement cycles |
| **Viewer** | Read-only dashboards and metrics | Submit feedback, ingest events |
| **Anonymous** | Health check only | Access any data endpoint |

**Authentication methods** (in priority order):
1. API key (`X-API-Key` header) — for service accounts and scripts
2. Bearer token (`Authorization: Bearer <JWT>`) — for SSO/IdP users
3. Demo mode (no keys configured) — admin access for evaluation only

### 4. Attorney-Client Privilege Protection

| Safeguard | Detail |
|-----------|--------|
| **Content-blind analysis** | AION processes behavioral metadata only (access times, volume, patterns) — never document content |
| **No full-text indexing** | Email subjects and filenames are hashed, not stored in plaintext |
| **Privilege boundary** | Detection patterns flag behavior (e.g., "bulk download of client files") without reading file contents |
| **Audit trail** | Every data access is logged with user, timestamp, and scope |

### 5. Complete Audit Trail

Every action in AION OS is logged:

| Audited Action | Data Recorded |
|----------------|---------------|
| API authentication | User/key identity, role, IP, timestamp |
| Event ingestion | Source, event count, processing time |
| Alert generation | Triggered pattern, risk score, user affected |
| Analyst feedback | Feedback type, analyst ID, timestamp |
| Policy changes | Old policy, new policy, who approved, when |
| System access | Login/logout, session duration, endpoints accessed |

**Log retention**: Configurable, default 365 days. Logs are encrypted at rest.

### 6. Data Minimization & Retention

| Principle | Implementation |
|-----------|---------------|
| Collect only what's needed | 92 event types defined — no raw packet capture |
| TTL-based expiration | Events auto-expire per configurable retention policy |
| Selective deletion | Per-user event deletion via API (`delete_user_events`) |
| No data copies | Single source of truth in encrypted store — no replicas |

---

## Compliance Alignment

| Framework | AION OS Coverage |
|-----------|-----------------|
| **ABA Model Rule 1.6** | Confidentiality of client information protected by on-prem deployment + encryption |
| **NIST CSF** | Identify → Protect → Detect → Respond coverage across detection engine |
| **SOC 2 Type II** | Access controls (RBAC), encryption (AES-256), audit logging, monitoring |
| **GDPR Art. 32** | Encryption at rest, access controls, data minimization, right to erasure |
| **CCPA** | No sale of data, data deletion capability, access logging |
| **NIST SP 800-171** | Controlled access, encryption, audit, incident response |
| **ISO 27001** | A.8 Asset management, A.9 Access control, A.10 Cryptography, A.12 Operations security |

---

## Penetration Testing & Validation

| Test | Result |
|------|--------|
| **Automated test suite** | 119 tests passing (RBAC, encryption, edge cases, API) |
| **Red team simulation** | Validates detection against 69 attack patterns |
| **Tampered ciphertext** | Correctly rejected (GCM authentication) |
| **Truncated ciphertext** | Correctly rejected |
| **Concurrent access** | No race conditions under 20-analyst load |
| **Unicode / special chars** | Handled correctly in all storage layers |
| **10K+ event volume** | Sustained without degradation |

---

## Frequently Asked Questions

**Q: Does AION OS send any data to the cloud?**  
A: No. Zero outbound connections. All processing is local. Verify with network monitoring tools.

**Q: Can CodeTyphoons access our data remotely?**  
A: Not unless your firm grants VPN/SSH access for support. The system has no remote access built in.

**Q: What happens if the encryption key is lost?**  
A: Encrypted data becomes inaccessible. We recommend storing the key in your firm's existing secrets management system (HashiCorp Vault, Azure Key Vault, etc.) with backup.

**Q: Does AION OS read email content or document text?**  
A: No. AION processes only metadata — event types, timestamps, volumes, access patterns. Document and email content is never ingested.

**Q: How is data deleted at the end of the pilot?**  
A: Delete the `AION_DATA_DIR` directory and the encryption key. Container removal erases all runtime state. We provide a documented decommission procedure.

**Q: Is the source code available for security review?**  
A: Source code review can be arranged under NDA for firms requiring it as part of vendor due diligence.

---

*For technical deployment details, see PILOT_DEPLOYMENT_GUIDE.md*  
*For success criteria and SLAs, see PILOT_SUCCESS_CRITERIA.md*
