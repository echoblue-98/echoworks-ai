"""
AION OS - Local Security Attacker Agent
100% LOCAL - Zero LLM dependency

Provides the same defensive security analysis as the Claude-powered version,
but using rule-based intelligence derived from the pattern database.

This is the AION way: proprietary, private, self-contained.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ThreatAssessment:
    """Structured threat assessment output"""
    threat_type: str
    severity: str
    confidence: float
    attack_objective: str
    immediate_actions: List[str]
    forensic_preservation: List[str]
    notifications: List[str]
    prevention_recommendations: List[str]


class LocalSecurityAttacker:
    """
    Local Security Attacker Agent - Zero LLM dependency.
    
    Uses pattern-based intelligence to provide defensive security analysis.
    Derived from real attack patterns in the AION pattern database.
    """
    
    def __init__(self):
        # Attack pattern → response mappings (from real cases)
        self.attack_responses = {
            "vpn_database_theft": {
                "threat_type": "Remote Database Exfiltration via VPN",
                "severity": "CRITICAL",
                "attack_objective": "Bulk extraction of client/billing database for competitive intelligence or client poaching",
                "immediate_actions": [
                    "REVOKE: Disable user account across all systems immediately",
                    "REVOKE: Terminate all active VPN sessions for this user",
                    "REVOKE: Disable database access privileges",
                    "LOCK: Set affected database tables to read-only",
                    "LOCK: Block VPN connections from source IP range",
                    "LOCK: Enable enhanced DLP policies on sensitive data",
                ],
                "forensic_preservation": [
                    "CAPTURE: Full VPN logs (last 30 days) for affected user",
                    "CAPTURE: Database audit logs showing all queries executed",
                    "CAPTURE: Network traffic captures from source IPs",
                    "SNAPSHOT: Database transaction log backup",
                    "SNAPSHOT: Virtual machine snapshots of affected systems",
                    "PRESERVE: Email server logs for data exfiltration routes",
                ],
                "notifications": [
                    "IMMEDIATE: Chief Information Security Officer",
                    "IMMEDIATE: Managing Partner / General Counsel",
                    "WITHIN 1 HOUR: IT Director",
                    "WITHIN 24 HOURS: Cyber insurance carrier",
                    "AS NEEDED: External incident response firm",
                ],
                "prevention_recommendations": [
                    "Implement privileged access management (PAM) for database access",
                    "Require MFA for all VPN connections",
                    "Deploy geographic access restrictions with whitelist approach",
                    "Set database query volume thresholds with immediate alerting",
                    "Implement user behavior analytics (UBA) baseline monitoring",
                ]
            },
            "pre_departure_exfil": {
                "threat_type": "Pre-Departure Data Exfiltration",
                "severity": "HIGH",
                "attack_objective": "Systematic extraction of valuable data before giving notice of departure",
                "immediate_actions": [
                    "MONITOR: Place user on enhanced monitoring watchlist",
                    "AUDIT: Review all file access for past 60 days",
                    "RESTRICT: Limit access to sensitive client data",
                    "DISABLE: Remove bulk download capabilities",
                    "ALERT: Set up real-time alerts for any large file operations",
                ],
                "forensic_preservation": [
                    "CAPTURE: File server access logs (60 days)",
                    "CAPTURE: Cloud storage sync logs (OneDrive, Dropbox, Google Drive)",
                    "CAPTURE: Email attachment history",
                    "CAPTURE: Print server logs",
                    "SNAPSHOT: Current state of user's accessible file shares",
                ],
                "notifications": [
                    "IMMEDIATE: IT Security team",
                    "WITHIN 4 HOURS: HR Department (potential departure indicator)",
                    "WITHIN 24 HOURS: Direct supervisor (discretely)",
                ],
                "prevention_recommendations": [
                    "Implement DLP with content inspection on all egress points",
                    "Set baseline file access patterns and alert on deviations",
                    "Restrict bulk download capabilities for departing employees",
                    "Enable watermarking on sensitive documents",
                ]
            },
            "email_cloud_combo": {
                "threat_type": "External Data Channel Setup",
                "severity": "HIGH",
                "attack_objective": "Establishing persistent data exfiltration channels via email forwarding and cloud sync",
                "immediate_actions": [
                    "DISABLE: Remove all email forwarding rules immediately",
                    "DISABLE: Revoke personal cloud storage sync permissions",
                    "AUDIT: Review all forwarding rules set in past 90 days",
                    "AUDIT: Check for BCC rules to personal addresses",
                    "BLOCK: Prevent new forwarding rule creation for this user",
                ],
                "forensic_preservation": [
                    "CAPTURE: Email transport logs showing all forwards",
                    "CAPTURE: Cloud sync connection history",
                    "CAPTURE: List of external recipients from forwarding",
                    "EXPORT: All email rules configured by user",
                ],
                "notifications": [
                    "IMMEDIATE: IT Security team",
                    "WITHIN 4 HOURS: User's supervisor",
                    "WITHIN 24 HOURS: HR if departure suspected",
                ],
                "prevention_recommendations": [
                    "Block personal email forwarding at the organization level",
                    "Require approval for cloud storage sync connections",
                    "Monitor for new forwarding rules in real-time",
                    "Implement email DLP to detect sensitive data in forwards",
                ]
            },
            "geographic_vpn_abuse": {
                "threat_type": "Credential Compromise or Location Masking",
                "severity": "CRITICAL",
                "attack_objective": "Accessing systems from unusual geographic location, indicating stolen credentials or intentional location masking",
                "immediate_actions": [
                    "FORCE: Require immediate password reset",
                    "REVOKE: Terminate all active sessions",
                    "ENABLE: Force MFA re-enrollment",
                    "VERIFY: Contact user through known-good channel to verify identity",
                    "BLOCK: Temporarily block access pending verification",
                ],
                "forensic_preservation": [
                    "CAPTURE: All authentication logs for user (30 days)",
                    "CAPTURE: VPN connection history with IP geolocation",
                    "CAPTURE: List of devices used for authentication",
                    "ANALYZE: Check for credential stuffing or brute force attempts",
                ],
                "notifications": [
                    "IMMEDIATE: IT Security team",
                    "IMMEDIATE: User (to verify they initiated access)",
                    "WITHIN 1 HOUR: Security operations center",
                ],
                "prevention_recommendations": [
                    "Implement impossible travel detection",
                    "Require location-based access policies",
                    "Deploy risk-based authentication",
                    "Maintain list of approved access countries",
                ]
            },
            "physical_exfil_prep": {
                "threat_type": "Physical Document Exfiltration Preparation",
                "severity": "MEDIUM",
                "attack_objective": "Preparing physical copies of sensitive data via printing for removal from premises",
                "immediate_actions": [
                    "AUDIT: Review all print jobs for user (past 14 days)",
                    "RESTRICT: Limit printing privileges to supervised areas",
                    "MONITOR: Enable detailed print logging with content capture",
                    "CHECK: Review building access logs for after-hours activity",
                ],
                "forensic_preservation": [
                    "CAPTURE: Print server logs with job details",
                    "CAPTURE: Copier/scanner logs",
                    "CAPTURE: Building access badge logs",
                    "CAPTURE: CCTV footage near printers (if available)",
                ],
                "notifications": [
                    "WITHIN 4 HOURS: IT Security team",
                    "WITHIN 24 HOURS: Facilities/Physical security",
                ],
                "prevention_recommendations": [
                    "Require badge swipe for print job release",
                    "Implement content-aware printing restrictions",
                    "Disable printing of client lists and billing data",
                    "Log all print jobs with document fingerprinting",
                ]
            }
        }
        
        # Generic high-risk response for unknown patterns
        self.default_response = {
            "threat_type": "Anomalous Activity - Classification Pending",
            "severity": "HIGH",
            "attack_objective": "Unknown - requires manual investigation",
            "immediate_actions": [
                "MONITOR: Enable enhanced logging for affected user",
                "AUDIT: Review recent access patterns",
                "VERIFY: Confirm activity with user if appropriate",
                "RESTRICT: Consider temporary access reduction pending investigation",
            ],
            "forensic_preservation": [
                "CAPTURE: All available logs for affected systems",
                "CAPTURE: User authentication history",
                "SNAPSHOT: Current access permissions",
            ],
            "notifications": [
                "IMMEDIATE: IT Security team for triage",
            ],
            "prevention_recommendations": [
                "Conduct root cause analysis after investigation",
                "Update detection rules based on findings",
            ]
        }
    
    def analyze(
        self,
        user_id: str,
        risk_score: float,
        pattern_matches: List[str],
        alert_summary: List[Dict]
    ) -> ThreatAssessment:
        """
        Generate threat assessment for detected patterns.
        
        100% local - no LLM calls.
        """
        # Use the highest severity pattern for primary response
        primary_pattern = None
        primary_response = self.default_response
        
        for pattern in pattern_matches:
            if pattern in self.attack_responses:
                response = self.attack_responses[pattern]
                if primary_pattern is None or self._severity_rank(response["severity"]) > self._severity_rank(primary_response["severity"]):
                    primary_pattern = pattern
                    primary_response = response
        
        # Calculate confidence based on pattern match and risk score
        confidence = min(0.95, (risk_score / 100) * 0.7 + (len(pattern_matches) * 0.1) + 0.2)
        
        # Build contextualized output
        context_additions = self._add_context(user_id, alert_summary, pattern_matches)
        
        return ThreatAssessment(
            threat_type=primary_response["threat_type"],
            severity=primary_response["severity"],
            confidence=confidence,
            attack_objective=primary_response["attack_objective"],
            immediate_actions=primary_response["immediate_actions"] + context_additions.get("actions", []),
            forensic_preservation=primary_response["forensic_preservation"],
            notifications=primary_response["notifications"],
            prevention_recommendations=primary_response["prevention_recommendations"]
        )
    
    def _severity_rank(self, severity: str) -> int:
        """Rank severity for comparison"""
        ranks = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return ranks.get(severity.upper(), 0)
    
    def _add_context(self, user_id: str, alerts: List[Dict], patterns: List[str]) -> Dict:
        """Add context-specific actions based on alert details"""
        additions = {"actions": []}
        
        # Check for specific indicators in alerts
        for alert in alerts:
            location = alert.get("source_location", "")
            if location and "unknown" in location.lower():
                additions["actions"].append(f"INVESTIGATE: Unknown location detected - {location}")
            
            action = alert.get("action", "")
            if "select *" in action.lower() or "bulk" in action.lower():
                additions["actions"].append("CRITICAL: Bulk data query detected - immediate database lockdown recommended")
        
        return additions
    
    def format_report(self, assessment: ThreatAssessment, user_id: str, risk_score: float) -> str:
        """Format assessment as readable report"""
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║            AION SECURITY ATTACKER AGENT - LOCAL ANALYSIS         ║
║                    100% LOCAL - ZERO LLM CALLS                   ║
╚══════════════════════════════════════════════════════════════════╝

USER: {user_id}
RISK SCORE: {risk_score:.0f}/100
CONFIDENCE: {assessment.confidence * 100:.0f}%

════════════════════════════════════════════════════════════════════
THREAT ASSESSMENT
════════════════════════════════════════════════════════════════════
Type: {assessment.threat_type}
Severity: {assessment.severity}
Objective: {assessment.attack_objective}

════════════════════════════════════════════════════════════════════
IMMEDIATE ACTIONS (Next 15 Minutes)
════════════════════════════════════════════════════════════════════
"""
        for action in assessment.immediate_actions:
            report += f"  □ {action}\n"
        
        report += """
════════════════════════════════════════════════════════════════════
FORENSIC PRESERVATION
════════════════════════════════════════════════════════════════════
"""
        for item in assessment.forensic_preservation:
            report += f"  □ {item}\n"
        
        report += """
════════════════════════════════════════════════════════════════════
NOTIFICATIONS
════════════════════════════════════════════════════════════════════
"""
        for notify in assessment.notifications:
            report += f"  □ {notify}\n"
        
        report += """
════════════════════════════════════════════════════════════════════
PREVENTION RECOMMENDATIONS
════════════════════════════════════════════════════════════════════
"""
        for rec in assessment.prevention_recommendations:
            report += f"  • {rec}\n"
        
        report += """
════════════════════════════════════════════════════════════════════
This analysis was generated 100% locally by AION OS.
No data was sent to any external LLM provider.
════════════════════════════════════════════════════════════════════
"""
        return report


# Singleton instance
_local_attacker: Optional[LocalSecurityAttacker] = None


def get_local_attacker() -> LocalSecurityAttacker:
    """Get or create local attacker singleton"""
    global _local_attacker
    if _local_attacker is None:
        _local_attacker = LocalSecurityAttacker()
    return _local_attacker
