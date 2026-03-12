"""
Attorney Departure Risk Assessment Gem

Executive-ready analysis of attorney departure risk with professional
formatting, ROI calculations, and shareable deliverables.

This is the "productized" version of HeistPlanner - designed for demos,
client deliverables, and C-suite presentations.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..modules.heist_planner import HeistPlanner


class RiskLevel(Enum):
    """Risk severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class ExecutiveSummary:
    """Executive summary for C-suite presentation"""
    attorney_name: str
    practice_area: str
    years_tenure: int
    destination: str
    
    # Financial
    total_risk: str
    expected_loss: str
    aion_cost: str
    roi_multiple: str
    
    # Risk profile
    critical_vulnerabilities: int
    high_vulnerabilities: int
    total_vulnerabilities: int
    
    # Timeline
    departure_date: str
    days_until_departure: int
    urgency_level: str
    
    # Pattern match
    pattern_match: Optional[str]
    pattern_similarity: Optional[str]


@dataclass
class RiskFinding:
    """Individual risk finding"""
    severity: RiskLevel
    title: str
    description: str
    impact: str
    recommendation: str


@dataclass
class ImmediateAction:
    """Immediate action item"""
    priority: str
    action: str
    timeline: str
    owner: str


class AttorneyDepartureGem:
    """
    Attorney Departure Risk Assessment Gem
    
    Produces executive-ready, professional risk assessments for
    attorney departures. Designed for demos, client deliverables,
    and C-suite presentations.
    """
    
    def __init__(self, use_gemini: bool = True):
        """
        Initialize the Attorney Departure Risk Gem
        
        Args:
            use_gemini: Use Gemini API instead of Claude
        """
        self.use_gemini = use_gemini
    
    def assess_departure_risk(
        self,
        attorney_name: str,
        practice_area: str,
        years_tenure: int,
        destination: str = "Unknown",
        notice_days: int = 30,
        key_clients: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform comprehensive attorney departure risk assessment
        
        Args:
            attorney_name: Full name and title (e.g., "Sarah Mitchell (Managing Partner)")
            practice_area: Practice area (e.g., "Corporate M&A")
            years_tenure: Years at firm
            destination: Destination firm (if known)
            notice_days: Days until departure
            key_clients: List of key client names (optional)
        
        Returns:
            Dictionary with executive_summary, risk_findings, immediate_actions,
            timeline, pattern_match, and full_report
        """
        # Run HeistPlanner analysis
        planner = HeistPlanner(use_gemini=self.use_gemini)
        
        # Build attorney profile dict
        attorney_profile = {
            "name": attorney_name,
            "practice_area": practice_area,
            "years_tenure": years_tenure,
            "destination": destination,
            "notice_days": notice_days
        }
        
        result = planner.analyze_departure_risk(attorney_profile)
        
        # Extract and format components
        executive_summary = self._build_executive_summary(
            result, attorney_name, practice_area, years_tenure, 
            destination, notice_days
        )
        
        risk_findings = self._extract_risk_findings(result)
        immediate_actions = self._build_immediate_actions(result, notice_days)
        timeline = self._build_timeline(result, notice_days)
        pattern_match = self._extract_pattern_match(result)
        
        return {
            "executive_summary": executive_summary,
            "risk_findings": risk_findings,
            "immediate_actions": immediate_actions,
            "timeline": timeline,
            "pattern_match": pattern_match,
            "raw_analysis": result,
            "generated_at": datetime.now().isoformat()
        }
    
    def _build_executive_summary(
        self,
        result: Dict,
        attorney_name: str,
        practice_area: str,
        years_tenure: int,
        destination: str,
        notice_days: int
    ) -> ExecutiveSummary:
        """Build executive summary from analysis results"""
        
        # Extract financial data
        financial = result.get("financial_analysis", {})
        total_risk = financial.get("total_risk", "Unknown")
        expected_loss = financial.get("expected_loss", "Unknown")
        
        # Count vulnerabilities by severity
        vulnerabilities = result.get("vulnerabilities", [])
        critical_count = 0
        high_count = 0
        
        for v in vulnerabilities:
            analysis_text = str(v.get("agent_analysis") or v.get("analysis") or v.get("description", "")).upper()
            if "CRITICAL" in analysis_text:
                critical_count += 1
            elif "HIGH" in analysis_text:
                high_count += 1
        
        # Calculate urgency
        if notice_days <= 7:
            urgency = "EXTREME - Final Week"
        elif notice_days <= 14:
            urgency = "CRITICAL - 2 Weeks Remaining"
        elif notice_days <= 30:
            urgency = "HIGH - 30 Day Window"
        else:
            urgency = "MODERATE - Proactive Assessment"
        
        # Pattern match
        pattern = result.get("pattern_match")
        pattern_name = None
        pattern_sim = None
        if pattern:
            pattern_name = pattern.get("pattern_name")
            similarity_value = pattern.get('similarity', 0)
            # Handle both float and string similarity values
            if isinstance(similarity_value, str):
                pattern_sim = similarity_value if '%' in similarity_value else f"{similarity_value}%"
            else:
                pattern_sim = f"{int(similarity_value * 100)}%"
        
        # Departure date
        departure_date = (datetime.now() + timedelta(days=notice_days)).strftime("%B %d, %Y")
        
        return ExecutiveSummary(
            attorney_name=attorney_name,
            practice_area=practice_area,
            years_tenure=years_tenure,
            destination=destination,
            total_risk=total_risk,
            expected_loss=expected_loss,
            aion_cost="$20,000",
            roi_multiple=f"{financial.get('roi_multiple', 0):.1f}x" if isinstance(financial.get('roi_multiple'), (int, float)) else str(financial.get('roi_multiple', 'N/A')),
            critical_vulnerabilities=critical_count,
            high_vulnerabilities=high_count,
            total_vulnerabilities=len(vulnerabilities),
            departure_date=departure_date,
            days_until_departure=notice_days,
            urgency_level=urgency,
            pattern_match=pattern_name,
            pattern_similarity=pattern_sim
        )
    
    def _extract_risk_findings(self, result: Dict) -> List[RiskFinding]:
        """Extract and format risk findings"""
        findings = []
        
        vulnerabilities = result.get("vulnerabilities", [])
        
        for vuln in vulnerabilities[:10]:  # Top 10 for executive summary
            # Handle both possible structures
            analysis = vuln.get("agent_analysis") or vuln.get("analysis") or vuln.get("description", "")
            
            # If it's an empty analysis, try getting text from other fields
            if not analysis:
                analysis = str(vuln)[:250]
            
            # Determine severity
            if "CRITICAL" in analysis.upper():
                severity = RiskLevel.CRITICAL
            elif "HIGH" in analysis.upper():
                severity = RiskLevel.HIGH
            elif "MEDIUM" in analysis.upper():
                severity = RiskLevel.MEDIUM
            else:
                severity = RiskLevel.LOW
            
            # Extract key info
            title = self._extract_title_from_analysis(analysis)
            description = analysis[:250] + "..." if len(analysis) > 250 else analysis
            
            findings.append(RiskFinding(
                severity=severity,
                title=title if title else "Risk identified",
                description=description,
                impact=self._assess_impact(severity),
                recommendation=self._generate_recommendation(analysis)
            ))
        
        return findings
    
    def _build_immediate_actions(self, result: Dict, notice_days: int) -> List[ImmediateAction]:
        """Build immediate action items"""
        actions = []
        
        # Always include these critical actions
        if notice_days <= 7:
            actions.append(ImmediateAction(
                priority="CRITICAL",
                action="Disable VPN access outside business hours",
                timeline="Within 24 hours",
                owner="IT Security"
            ))
            actions.append(ImmediateAction(
                priority="CRITICAL",
                action="Review all email forwarding rules and cloud sync settings",
                timeline="Within 24 hours",
                owner="IT Security"
            ))
            actions.append(ImmediateAction(
                priority="HIGH",
                action="Schedule exit interview with General Counsel present",
                timeline="Within 48 hours",
                owner="HR / Legal"
            ))
        elif notice_days <= 30:
            actions.append(ImmediateAction(
                priority="HIGH",
                action="Audit file access logs for past 60 days",
                timeline="Within 72 hours",
                owner="IT Security"
            ))
            actions.append(ImmediateAction(
                priority="HIGH",
                action="Review email forwarding rules and BCC configurations",
                timeline="Within 72 hours",
                owner="IT Security"
            ))
            actions.append(ImmediateAction(
                priority="MEDIUM",
                action="Identify key clients for retention outreach",
                timeline="Within 1 week",
                owner="Client Relations"
            ))
        else:
            actions.append(ImmediateAction(
                priority="MEDIUM",
                action="Establish baseline monitoring for high-risk partners",
                timeline="Within 2 weeks",
                owner="IT Security"
            ))
            actions.append(ImmediateAction(
                priority="MEDIUM",
                action="Review and update data loss prevention policies",
                timeline="Within 2 weeks",
                owner="IT Security / Legal"
            ))
        
        return actions
    
    def _build_timeline(self, result: Dict, notice_days: int) -> Dict:
        """Build timeline analysis"""
        timeline = result.get("timeline_analysis", {})
        
        return {
            "departure_date": (datetime.now() + timedelta(days=notice_days)).strftime("%Y-%m-%d"),
            "current_phase": timeline.get("current_phase", "Unknown"),
            "high_risk_windows": timeline.get("high_risk_windows", []),
            "critical_audit_dates": timeline.get("critical_dates", [])
        }
    
    def _extract_pattern_match(self, result: Dict) -> Optional[Dict]:
        """Extract pattern match information"""
        pattern = result.get("pattern_match")
        
        if pattern and pattern.get("similarity", 0) > 0.3:
            return {
                "pattern_name": pattern.get("pattern_name"),
                "similarity": f"{int(pattern.get('similarity', 0) * 100)}%",
                "previous_outcome": pattern.get("outcome", "Unknown"),
                "lessons_learned": pattern.get("lessons", [])
            }
        
        return None
    
    def _extract_title_from_analysis(self, analysis: str) -> str:
        """Extract concise title from analysis text"""
        # Take first sentence or first 80 chars
        first_sentence = analysis.split('.')[0]
        if len(first_sentence) > 80:
            return first_sentence[:77] + "..."
        return first_sentence
    
    def _assess_impact(self, severity: RiskLevel) -> str:
        """Assess financial/operational impact"""
        impact_map = {
            RiskLevel.CRITICAL: "Potential loss $500K-$2M per incident",
            RiskLevel.HIGH: "Potential loss $100K-$500K per incident",
            RiskLevel.MEDIUM: "Potential loss $25K-$100K per incident",
            RiskLevel.LOW: "Potential loss <$25K per incident",
            RiskLevel.INFO: "Informational - monitor for escalation"
        }
        return impact_map.get(severity, "Unknown impact")
    
    def _generate_recommendation(self, analysis: str) -> str:
        """Generate action recommendation"""
        # Simple heuristic-based recommendations
        analysis_lower = analysis.lower()
        
        if "email" in analysis_lower and "forward" in analysis_lower:
            return "Audit email forwarding rules and disable automatic forwarding to external addresses"
        elif "client" in analysis_lower and "relationship" in analysis_lower:
            return "Prepare client retention strategy and schedule proactive outreach"
        elif "access" in analysis_lower or "vpn" in analysis_lower:
            return "Review access logs and implement time-based access restrictions"
        elif "data" in analysis_lower or "document" in analysis_lower:
            return "Enable enhanced DLP monitoring and audit file download activity"
        else:
            return "Implement monitoring and periodic review of this risk factor"


def format_executive_report(assessment: Dict) -> str:
    """
    Format assessment as executive text report
    
    Args:
        assessment: Output from assess_departure_risk()
    
    Returns:
        Formatted text report suitable for terminal or email
    """
    summary = assessment["executive_summary"]
    findings = assessment["risk_findings"]
    actions = assessment["immediate_actions"]
    pattern = assessment.get("pattern_match")
    
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("ATTORNEY DEPARTURE RISK ASSESSMENT".center(80))
    lines.append("=" * 80)
    lines.append("")
    
    # Executive Summary
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Attorney:          {summary.attorney_name}")
    lines.append(f"Practice Area:     {summary.practice_area}")
    lines.append(f"Tenure:            {summary.years_tenure} years")
    lines.append(f"Destination:       {summary.destination}")
    lines.append(f"Departure Date:    {summary.departure_date} ({summary.days_until_departure} days)")
    lines.append(f"Urgency Level:     {summary.urgency_level}")
    lines.append("")
    
    # Financial Risk
    lines.append("FINANCIAL RISK ANALYSIS")
    lines.append("-" * 80)
    lines.append(f"Expected Loss:     {summary.expected_loss}")
    lines.append(f"AION Analysis:     {summary.aion_cost}")
    lines.append(f"ROI Multiple:      {summary.roi_multiple}")
    lines.append("")
    
    # Risk Profile
    lines.append("RISK PROFILE")
    lines.append("-" * 80)
    lines.append(f"Critical Vulnerabilities:  {summary.critical_vulnerabilities}")
    lines.append(f"High Vulnerabilities:      {summary.high_vulnerabilities}")
    lines.append(f"Total Vulnerabilities:     {summary.total_vulnerabilities}")
    lines.append("")
    
    # Pattern Match
    if pattern:
        lines.append("HISTORICAL PATTERN MATCH")
        lines.append("-" * 80)
        lines.append(f"Similar Case:      {pattern['pattern_name']}")
        lines.append(f"Similarity:        {pattern['similarity']}")
        lines.append(f"Previous Outcome:  {pattern['previous_outcome']}")
        lines.append("")
    
    # Top Risk Findings
    lines.append("TOP RISK FINDINGS")
    lines.append("-" * 80)
    for i, finding in enumerate(findings[:5], 1):
        lines.append(f"{i}. [{finding.severity.value}] {finding.title}")
        lines.append(f"   Impact: {finding.impact}")
        lines.append(f"   Recommendation: {finding.recommendation}")
        lines.append("")
    
    # Immediate Actions
    lines.append("IMMEDIATE ACTIONS")
    lines.append("-" * 80)
    for i, action in enumerate(actions, 1):
        lines.append(f"{i}. [{action.priority}] {action.action}")
        lines.append(f"   Timeline: {action.timeline} | Owner: {action.owner}")
        lines.append("")
    
    # Footer
    lines.append("=" * 80)
    lines.append(f"Report generated: {assessment['generated_at']}")
    lines.append("AION OS - Adversarial Intelligence for Attorney Departure Risk")
    lines.append("=" * 80)
    
    return "\n".join(lines)
