"""
Attorney Departure Risk Analyzer

Critical enterprise feature for law firms:
When attorneys leave, massive vulnerability windows open:
- Knowledge walks out the door
- Active cases may have undocumented weaknesses
- Security credentials need immediate revocation
- Client relationships at risk
- Compliance gaps emerge
- Opposing counsel may exploit transition period

This module performs adversarial analysis of attorney departures
to close the gap before problems arise.
"""

from typing import List, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..core.severity_triage import Vulnerability, Severity, SeverityTriage
from ..core.adversarial_engine import AdversarialEngine, AgentPerspective, IntensityLevel
from .quantum_adversarial import QuantumInspiredOptimizer


class DepartureRiskCategory(Enum):
    """Categories of risk when attorney leaves"""
    KNOWLEDGE_LOSS = "knowledge_loss"
    ACTIVE_CASE_RISK = "active_case_risk"
    SECURITY_ACCESS = "security_access"
    CLIENT_RELATIONSHIP = "client_relationship"
    COMPLIANCE_GAP = "compliance_gap"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"


@dataclass
class AttorneyProfile:
    """Profile of departing attorney"""
    attorney_id: str
    name: str
    practice_area: str
    years_at_firm: int
    active_cases: List[str]
    client_relationships: List[str]
    specialized_knowledge: List[str]
    system_access: List[str]
    departure_date: datetime
    destination_firm: str = "Unknown"
    notice_period_days: int = 30


@dataclass
class ActiveCase:
    """Active case potentially affected by departure"""
    case_id: str
    case_name: str
    client: str
    lead_attorney: str
    supporting_attorneys: List[str]
    trial_date: datetime = None
    critical_deadlines: List[datetime] = field(default_factory=list)
    case_value: float = 0.0
    complexity_score: int = 5  # 1-10
    documentation_completeness: float = 0.5  # 0-1


class AttorneyDepartureAnalyzer:
    """
    Adversarial analysis of attorney departure risks.
    
    Identifies vulnerabilities and provides action items to close gaps.
    
    Enterprise pricing: $10k-$50k per partner departure analysis
    """
    
    def __init__(self):
        self.severity_triage = SeverityTriage()
        self.adversarial_engine = AdversarialEngine(
            intensity=IntensityLevel.LEVEL_4_REDTEAM
        )
        self.quantum_optimizer = QuantumInspiredOptimizer(temperature=1.0)
    
    def analyze_exit_security(
        self,
        attorney_name: str,
        practice_area: str,
        active_cases: str,
        client_relationships: str,
        system_access: str,
        years_at_firm: int = 5,
        departure_date: str = "30 days",
        destination_firm: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        SECURITY-FOCUSED chained adversarial analysis of attorney departure.
        
        Identifies what the departing attorney could exploit and how to close gaps.
        
        Args:
            attorney_name: Attorney's name
            practice_area: Practice area (e.g., "Corporate M&A")
            active_cases: Cases they're currently working on
            client_relationships: Client contacts they have
            system_access: Systems they can currently access
            years_at_firm: Years at firm (more = more institutional knowledge)
            departure_date: When they're leaving
            destination_firm: Where they're going (competitor analysis)
        
        Returns:
            {
                'vulnerabilities': List of security gaps exposed,
                'executable_attacks': What they could do with their access,
                'defense_checklist': Action items to close gaps,
                'risk_score': 0-100 (100 = critical risk),
                'total_cost': Analysis cost
            }
        """
        
        query = f"""
DEPARTING ATTORNEY SECURITY ANALYSIS

Attorney: {attorney_name}
Practice Area: {practice_area}
Years at Firm: {years_at_firm}
Departure Date: {departure_date}
Destination: {destination_firm}

CURRENT ACCESS & KNOWLEDGE:

Active Cases:
{active_cases}

Client Relationships:
{client_relationships}

System Access:
{system_access}

SECURITY QUESTION:
What can this attorney do with their current access and knowledge that could harm the firm?
What gaps do we need to close before they leave?
"""
        
        context = {
            "use_case_type": "attorney_departure_security",
            "attorney_name": attorney_name,
            "years_at_firm": years_at_firm,
            "destination_firm": destination_firm
        }
        
        # Run chained adversarial analysis
        result = self.adversarial_engine.analyze(
            query=query,
            context=context
        )
        
        # Calculate risk score based on findings
        risk_score = self._calculate_exit_risk_score(
            vulnerabilities=result.get('vulnerabilities', []),
            years_at_firm=years_at_firm,
            active_cases_count=len(active_cases.split('\n')) if active_cases else 0
        )
        
        # Quantum-inspired attack path optimization
        attack_paths = self._optimize_attack_paths(
            system_access=system_access,
            years_at_firm=years_at_firm,
            destination_firm=destination_firm
        )
        
        return {
            'vulnerabilities': result.get('vulnerabilities', []),
            'attack_chain': result.get('attack_chain', []),
            'executable_attacks': result.get('executable_attacks', []),
            'attack_paths': attack_paths,  # Quantum-optimized paths
            'risk_score': risk_score,
            'total_cost': result.get('cost', 0.0),  # Fixed: was looking for 'total_cost', engine returns 'cost'
            'recommendations': self._generate_exit_checklist(result.get('vulnerabilities', []))
        }
    
    def _calculate_exit_risk_score(
        self,
        vulnerabilities: List[Dict],
        years_at_firm: int,
        active_cases_count: int
    ) -> int:
        """Calculate 0-100 risk score for attorney exit"""
        
        base_score = 30
        
        # More years = more institutional knowledge
        base_score += min(30, years_at_firm * 3)
        
        # More active cases = more immediate risk
        base_score += min(20, active_cases_count * 2)
        
        # High severity vulnerabilities increase score
        for vuln in vulnerabilities:
            if vuln.get('severity') == 'HIGH':
                base_score += 5
            elif vuln.get('severity') == 'CRITICAL':
                base_score += 10
        
        return min(100, base_score)
    
    def _optimize_attack_paths(
        self,
        system_access: str,
        years_at_firm: int,
        destination_firm: str
    ) -> List[Dict[str, Any]]:
        """
        Use quantum-inspired optimization to find optimal attack paths.
        Shows the highest probability paths the departing attorney could take.
        """
        # Parse available access points
        access_points = [a.strip() for a in system_access.split(',')]
        
        # Define possible attack actions
        possible_actions = [
            "Download case files",
            "Export client database",
            "Forward emails to personal account",
            "Screenshot confidential documents",
            "Copy precedent library",
            "Clone document templates",
            "Extract financial data",
            "Save client contact lists",
            "Backup case strategies",
            "Download billing records"
        ]
        
        # Run quantum-inspired optimization
        paths = self.quantum_optimizer.optimize_attack_path(
            initial_state="Authenticated User",
            target_state="Data Exfiltrated",
            possible_actions=possible_actions,
            max_iterations=500
        )
        
        # Format for output
        formatted_paths = []
        for i, path in enumerate(paths[:3], 1):  # Top 3 paths
            formatted_paths.append({
                'rank': i,
                'probability': round(path.probability * 100, 1),
                'steps': path.steps[:5],  # First 5 steps
                'impact': path.impact,
                'detection_difficulty': round(path.detection_difficulty * 100, 1)
            })
        
        return formatted_paths
    
    def _generate_exit_checklist(self, vulnerabilities: List[Dict]) -> List[str]:
        """Generate prioritized action checklist from vulnerabilities"""
        
        checklist = [
            "🚨 IMMEDIATE (Day 1):",
            "- Revoke all system access credentials",
            "- Change passwords for shared accounts",
            "- Disable email forwarding rules",
            "- Remove from client communication lists",
            "",
            "📋 WITHIN 48 HOURS:",
            "- Document all active case knowledge",
            "- Transfer client relationships to new lead",
            "- Review all recent document access logs",
            "- Notify clients of transition plan",
            "",
            "🔒 BEFORE DEPARTURE DATE:",
        ]
        
        # Add vulnerability-specific items
        for vuln in vulnerabilities:
            if vuln.get('severity') in ['HIGH', 'CRITICAL']:
                checklist.append(f"- Address: {vuln.get('description', '')[:80]}")
        
        return checklist
    
    def analyze_departure_simple(
        self,
        attorney_name: str,
        practice_area: str,
        active_cases: str,
        client_relationships: str,
        years_at_firm: int = 5,
        departure_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Simplified departure analysis that accepts string inputs (for Streamlit).
        
        Args:
            attorney_name: Attorney's name
            practice_area: Practice area (e.g., "Corporate M&A")
            active_cases: Text description of active cases
            client_relationships: Text description of client relationships
            years_at_firm: Years attorney has been at firm
            departure_context: Additional context (title, departure_date, etc.)
        
        Returns:
            Departure risk analysis with vulnerabilities
        """
        departure_context = departure_context or {}
        
        # Use adversarial engine to analyze the departure scenario
        analysis_text = f"""
DEPARTING ATTORNEY PROFILE:
- Name: {attorney_name}
- Practice Area: {practice_area}
- Years at Firm: {years_at_firm}
- Title: {departure_context.get('title', 'Unknown')}
- Departure Date: {departure_context.get('departure_date', 'Unknown')}
- Voluntary: {departure_context.get('is_voluntary', True)}

ACTIVE CASES/MATTERS:
{active_cases}

CLIENT RELATIONSHIPS:
{client_relationships}

Analyze this attorney departure scenario for vulnerabilities, knowledge loss risks, 
active case risks, security access concerns, client retention risks, and competitive intelligence exposure.
"""
        
        result = self.adversarial_engine.analyze(
            query=analysis_text,
            context={
                "analysis_type": "attorney_departure",
                "use_case_type": "attorney_departure",
                "attorney_name": attorney_name,
                "practice_area": practice_area,
                "years_at_firm": years_at_firm
            }
        )
        
        # Calculate risk score based on years and active cases
        risk_score = min(100, 40 + (years_at_firm * 3) + (len(active_cases) // 10))
        
        # Add risk scoring and structured output
        result['overall_risk_score'] = risk_score
        result['risk_level'] = 'High' if risk_score > 70 else 'Medium' if risk_score > 40 else 'Low'
        result['cases_at_risk'] = [line.strip() for line in active_cases.split('\n') if line.strip()]
        
        return result
    
    def analyze_departure(
        self,
        attorney: AttorneyProfile,
        active_cases: List[ActiveCase],
        firm_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive adversarial analysis of attorney departure.
        
        Returns vulnerabilities and action plan.
        """
        firm_context = firm_context or {}
        self.severity_triage.clear()
        
        # Analyze each risk category
        self._analyze_knowledge_loss(attorney, active_cases)
        self._analyze_active_case_risks(attorney, active_cases)
        self._analyze_security_access(attorney, firm_context)
        self._analyze_client_relationships(attorney, active_cases)
        self._analyze_compliance_gaps(attorney, active_cases, firm_context)
        self._analyze_competitive_intelligence(attorney, firm_context)
        
        # Generate transition plan
        transition_plan = self._generate_transition_plan(attorney, active_cases)
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(attorney, active_cases)
        
        return {
            "attorney": {
                "name": attorney.name,
                "practice_area": attorney.practice_area,
                "departure_date": attorney.departure_date.isoformat(),
                "notice_period_days": attorney.notice_period_days
            },
            "risk_score": risk_score,
            "risk_level": self._risk_level_from_score(risk_score),
            "vulnerabilities": self.severity_triage.get_summary(),
            "critical_actions": self._get_critical_actions(),
            "transition_plan": transition_plan,
            "formatted_output": self.severity_triage.format_output(max_shown=15)
        }
    
    def _analyze_knowledge_loss(
        self,
        attorney: AttorneyProfile,
        cases: List[ActiveCase]
    ):
        """Analyze knowledge walking out the door"""
        
        # Critical if highly specialized knowledge
        if len(attorney.specialized_knowledge) > 0:
            knowledge_areas = ", ".join(attorney.specialized_knowledge[:3])
            
            self.severity_triage.add_vulnerability(Vulnerability(
                id=f"knowledge_loss_{attorney.attorney_id}",
                title="Critical Specialized Knowledge Departure",
                description=(
                    f"{attorney.name} possesses specialized knowledge in {knowledge_areas} "
                    f"that may not be documented. {len(cases)} active cases depend on this expertise."
                ),
                severity=Severity.P0_CRITICAL,
                confidence=0.95,
                impact=(
                    f"Loss of {attorney.years_at_firm} years of institutional knowledge. "
                    f"Active cases may suffer from knowledge gaps. Opposing counsel may "
                    f"exploit transition period to challenge prior work."
                ),
                exploitation_scenario=(
                    "Opposing counsel discovers attorney departure during discovery. "
                    "Files motion to challenge prior strategy. New attorney lacks context "
                    "to defend adequately. Case weakened or lost."
                ),
                remediation_steps=[
                    f"URGENT: Schedule knowledge transfer sessions (minimum 10 hours)",
                    "Document all case strategies, theories, and key decisions",
                    "Create detailed handoff memos for each active case",
                    "Record video walkthroughs of complex case elements",
                    "Identify and document all undocumented precedents used",
                    f"Complete within {attorney.notice_period_days} days"
                ]
            ))
        
        # Undocumented case strategies
        high_complexity_cases = [c for c in cases if c.complexity_score > 7]
        if high_complexity_cases:
            self.severity_triage.add_vulnerability(Vulnerability(
                id=f"undocumented_strategy_{attorney.attorney_id}",
                title="High-Complexity Cases May Have Undocumented Strategies",
                description=(
                    f"{len(high_complexity_cases)} high-complexity cases may have undocumented "
                    f"legal strategies, arguments, or tactical decisions known only to {attorney.name}."
                ),
                severity=Severity.P1_HIGH,
                confidence=0.88,
                impact=(
                    "Successor attorney may miss critical strategic elements. "
                    "Cases may proceed with incomplete understanding of legal theory."
                ),
                exploitation_scenario=(
                    "Opposing counsel identifies inconsistency in approach after attorney change. "
                    "Exploits gap in case strategy. Client loses confidence in firm."
                ),
                remediation_steps=[
                    "Mandatory strategy documentation for all high-complexity cases",
                    "Review each case file for completeness (target: 90%+ documented)",
                    "Conduct case-by-case handoff meetings with successor",
                    "Client notification and reassurance calls"
                ]
            ))
    
    def _analyze_active_case_risks(
        self,
        attorney: AttorneyProfile,
        cases: List[ActiveCase]
    ):
        """Analyze risks to active cases"""
        
        # Cases near critical deadlines
        days_to_departure = (attorney.departure_date - datetime.now()).days
        at_risk_cases = []
        
        for case in cases:
            if case.trial_date:
                days_to_trial = (case.trial_date - datetime.now()).days
                if days_to_trial < days_to_departure + 60:  # 60-day buffer
                    at_risk_cases.append(case)
        
        if at_risk_cases:
            case_names = ", ".join([c.case_name for c in at_risk_cases[:3]])
            
            self.severity_triage.add_vulnerability(Vulnerability(
                id=f"case_deadline_{attorney.attorney_id}",
                title="Active Cases with Critical Deadlines During Transition",
                description=(
                    f"{len(at_risk_cases)} cases have trial dates or critical deadlines "
                    f"within 60 days of departure: {case_names}..."
                ),
                severity=Severity.P0_CRITICAL,
                confidence=0.92,
                impact=(
                    f"Cases worth ${sum(c.case_value for c in at_risk_cases):,.0f} at risk. "
                    f"Transition during critical period increases chance of missed deadlines, "
                    f"inadequate preparation, or strategic errors."
                ),
                exploitation_scenario=(
                    "Opposing counsel monitors court filings, discovers attorney change close "
                    "to trial. Files complex pre-trial motions to exploit transition. "
                    "New attorney unprepared to respond effectively."
                ),
                remediation_steps=[
                    f"IMMEDIATE: Assign co-counsel to all {len(at_risk_cases)} at-risk cases",
                    "Accelerate transition timeline for deadline-critical cases",
                    "Consider continuance requests if transition is insufficient",
                    "Daily status meetings during transition period",
                    "Client notification with reassurance plan"
                ]
            ))
        
        # Poorly documented cases
        poorly_documented = [c for c in cases if c.documentation_completeness < 0.6]
        if poorly_documented:
            self.severity_triage.add_vulnerability(Vulnerability(
                id=f"poor_docs_{attorney.attorney_id}",
                title="Inadequate Case Documentation",
                description=(
                    f"{len(poorly_documented)} cases have documentation completeness below 60%. "
                    f"Critical information may exist only in {attorney.name}'s notes or memory."
                ),
                severity=Severity.P1_HIGH,
                confidence=0.85,
                impact=(
                    "Successor attorney will have incomplete case understanding. "
                    "May miss critical facts, arguments, or strategic considerations."
                ),
                exploitation_scenario=(
                    "Successor reviews file, misses undocumented impeachment evidence. "
                    "Opposing witness testifies unchallenged. Case outcome affected."
                ),
                remediation_steps=[
                    "Mandate immediate case file review and documentation",
                    "Extract all information from departing attorney's notes",
                    "Digital evidence audit (emails, research, drafts)",
                    "Create comprehensive case summaries",
                    f"Target: 90%+ documentation before {attorney.departure_date.strftime('%Y-%m-%d')}"
                ]
            ))
    
    def _analyze_security_access(
        self,
        attorney: AttorneyProfile,
        firm_context: Dict[str, Any]
    ):
        """Analyze security and access control risks"""
        
        if len(attorney.system_access) > 0:
            systems = ", ".join(attorney.system_access[:5])
            
            self.severity_triage.add_vulnerability(Vulnerability(
                id=f"access_revocation_{attorney.attorney_id}",
                title="System Access Requires Immediate Revocation",
                description=(
                    f"{attorney.name} has access to {len(attorney.system_access)} firm systems: "
                    f"{systems}... Access must be revoked to prevent data exfiltration or "
                    f"unauthorized use."
                ),
                severity=Severity.P0_CRITICAL,
                confidence=0.98,
                impact=(
                    "Attorney could access confidential client data, case files, billing "
                    "information after departure. If joining competitor firm, poses serious "
                    "confidentiality and conflict risk."
                ),
                exploitation_scenario=(
                    f"Attorney departs to {attorney.destination_firm}. Access not revoked. "
                    "Downloads client files on last day. Uses information at new firm. "
                    "Ethical violation, potential malpractice claim, client loss."
                ),
                remediation_steps=[
                    f"ON DEPARTURE DATE: Revoke ALL system access at EOD",
                    "Change passwords for shared accounts attorney knew",
                    "Audit file access logs for unusual activity (30 days pre-departure)",
                    "Disable email forwarding rules",
                    "Collect all firm devices and keys",
                    "Monitor for unauthorized access attempts post-departure"
                ]
            ))
        
        # Client data access
        self.severity_triage.add_vulnerability(Vulnerability(
            id=f"data_exfiltration_{attorney.attorney_id}",
            title="Risk of Client Data Exfiltration",
            description=(
                f"{attorney.name} has access to sensitive client data for "
                f"{len(attorney.client_relationships)} clients. Risk of copying data "
                f"before departure, especially if joining competing firm."
            ),
            severity=Severity.P1_HIGH,
            confidence=0.80,
            impact=(
                "Confidential client information, work product, or case strategies "
                "could be taken to competitor firm. Ethical violations, conflicts of interest."
            ),
            exploitation_scenario=(
                "Attorney systematically downloads client files in weeks before departure. "
                "Uses information to solicit clients or assist opposing parties at new firm. "
                "Firm faces malpractice claims and ethics complaints."
            ),
            remediation_steps=[
                "Enable detailed audit logging of all file access",
                "Monitor for bulk downloads or unusual access patterns",
                "Implement DLP (data loss prevention) for departing attorneys",
                "Review sent emails for confidential attachments",
                "Exit interview with confidentiality reminder and NDA review",
                "Consider forensic analysis if suspicious activity detected"
            ]
        ))
    
    def _analyze_client_relationships(
        self,
        attorney: AttorneyProfile,
        cases: List[ActiveCase]
    ):
        """Analyze client relationship risks"""
        
        if len(attorney.client_relationships) > 0:
            clients = ", ".join(attorney.client_relationships[:3])
            
            self.severity_triage.add_vulnerability(Vulnerability(
                id=f"client_risk_{attorney.attorney_id}",
                title="Client Relationship Transfer Risk",
                description=(
                    f"{attorney.name} has established relationships with "
                    f"{len(attorney.client_relationships)} clients: {clients}... "
                    f"Risk of clients following attorney to new firm."
                ),
                severity=Severity.P1_HIGH,
                confidence=0.75,
                impact=(
                    f"Potential loss of {len(attorney.client_relationships)} client relationships "
                    f"representing ${sum(c.case_value for c in cases):,.0f} in active cases. "
                    f"Long-term revenue impact if clients leave."
                ),
                exploitation_scenario=(
                    "Attorney departs, contacts clients claiming firm cannot properly handle "
                    "their cases. Clients terminate firm engagement, transfer cases to "
                    f"{attorney.destination_firm}. Firm loses cases and future business."
                ),
                remediation_steps=[
                    "IMMEDIATE: Partner-level outreach to all affected clients",
                    "Introduce successor attorney with credentials and transition plan",
                    "Review non-solicitation agreements and enforceability",
                    "Strengthen remaining client relationships",
                    "Consider temporary fee adjustments to retain at-risk clients",
                    "Monitor for client contact/solicitation violations"
                ]
            ))
    
    def _analyze_compliance_gaps(
        self,
        attorney: AttorneyProfile,
        cases: List[ActiveCase],
        firm_context: Dict[str, Any]
    ):
        """Analyze compliance and ethical risks"""
        
        self.severity_triage.add_vulnerability(Vulnerability(
            id=f"compliance_{attorney.attorney_id}",
            title="Compliance and Conflict Check Gaps",
            description=(
                f"Attorney departure creates compliance risks: conflicts of interest, "
                f"improper file transfers, confidentiality breaches, bar ethics violations."
            ),
            severity=Severity.P2_MEDIUM,
            confidence=0.90,
            impact=(
                "Firm could face ethics complaints, malpractice claims, or professional "
                "responsibility violations if departure not handled properly."
            ),
            exploitation_scenario=(
                "Attorney joins opposing counsel's firm on active case. Conflict not "
                "identified. Representing opposing party while possessing confidential "
                "information. Ethics complaint filed. Firm sanctioned."
            ),
            remediation_steps=[
                "Run conflict checks: all active cases vs. destination firm",
                "Implement ethical walls if conflicts identified",
                "Document all conflict resolutions",
                "Review client files for attorney work product to protect",
                "Verify compliance with bar rules on attorney departure",
                "Exit interview covering professional responsibility obligations"
            ]
        ))
    
    def _analyze_competitive_intelligence(
        self,
        attorney: AttorneyProfile,
        firm_context: Dict[str, Any]
    ):
        """Analyze competitive intelligence risks"""
        
        if attorney.destination_firm != "Unknown":
            self.severity_triage.add_vulnerability(Vulnerability(
                id=f"competitive_intel_{attorney.attorney_id}",
                title="Competitive Intelligence and Strategic Information at Risk",
                description=(
                    f"Attorney departing to known competitor {attorney.destination_firm}. "
                    f"Possesses knowledge of firm strategies, pricing, client targeting, "
                    f"and operational weaknesses."
                ),
                severity=Severity.P2_MEDIUM,
                confidence=0.85,
                impact=(
                    f"Competitor {attorney.destination_firm} gains insider knowledge of "
                    f"firm operations, pricing models, client vulnerabilities, and strategic plans."
                ),
                exploitation_scenario=(
                    f"{attorney.destination_firm} uses insider information to undercut pricing, "
                    f"target vulnerable clients, and exploit operational weaknesses. "
                    f"Firm loses competitive position."
                ),
                remediation_steps=[
                    "Review restrictive covenants and enforceability",
                    "Cease discussion of strategic plans around departing attorney",
                    "Change key operational procedures attorney knows",
                    "Monitor competitor for unusual competitive moves",
                    "Consider expedited departure if risk is high",
                    "Legal review of non-compete enforcement options"
                ]
            ))
    
    def _generate_transition_plan(
        self,
        attorney: AttorneyProfile,
        cases: List[ActiveCase]
    ) -> Dict[str, List[str]]:
        """Generate day-by-day transition action plan"""
        
        days_remaining = (attorney.departure_date - datetime.now()).days
        
        plan = {
            "immediate_actions": [],
            "week_1": [],
            "week_2": [],
            "week_3_4": [],
            "departure_day": [],
            "post_departure": []
        }
        
        # Immediate actions (within 24 hours)
        plan["immediate_actions"] = [
            "Notify firm leadership and practice group",
            "Assign transition coordinator",
            "Begin conflict check process",
            "Schedule all client notification calls",
            "Identify successor attorneys for each case",
            "Enable enhanced access logging on attorney accounts"
        ]
        
        # Week 1
        plan["week_1"] = [
            "Complete conflict checks",
            f"Begin knowledge transfer sessions (schedule {len(cases) * 2} hours)",
            "Start case file documentation review",
            "Prepare client communication letters",
            "Review all system access and create revocation checklist",
            "First partner meeting with key clients"
        ]
        
        # Week 2
        plan["week_2"] = [
            "Continue knowledge transfer (50% complete)",
            "Complete case documentation audit",
            "Successor attorney shadow meetings/depositions",
            "Review and extract information from personal notes",
            "Prepare detailed handoff memos for each case",
            "Second round of client reassurance calls"
        ]
        
        # Weeks 3-4
        plan["week_3_4"] = [
            "Finalize knowledge transfer (100% complete)",
            "Complete all handoff documentation",
            "Final case status meetings with successors",
            "Last client touchpoints before departure",
            "Collect all firm property and keys",
            "Exit interview covering confidentiality and ethics"
        ]
        
        # Departure day
        plan["departure_day"] = [
            "Revoke ALL system access at 5:00 PM",
            "Change passwords for shared resources",
            "Disable email forwarding",
            "Final accounting reconciliation",
            "Collect firm credit cards and building access",
            "Document formal departure and access revocation"
        ]
        
        # Post-departure
        plan["post_departure"] = [
            "Monitor for unauthorized access attempts",
            "Follow up with clients (1 week, 1 month, 3 months)",
            "Review cases for transition quality",
            "Monitor for client solicitation violations",
            "Assess competitive intelligence risks materialized",
            "30-day transition quality review"
        ]
        
        return plan
    
    def _calculate_risk_score(
        self,
        attorney: AttorneyProfile,
        cases: List[ActiveCase]
    ) -> int:
        """Calculate overall risk score (0-100)"""
        
        risk = 0
        
        # Base risk from seniority
        risk += min(attorney.years_at_firm * 2, 30)
        
        # Case volume risk
        risk += min(len(cases) * 3, 25)
        
        # High-value case risk
        total_value = sum(c.case_value for c in cases)
        if total_value > 1000000:
            risk += 20
        elif total_value > 500000:
            risk += 10
        
        # Deadline proximity risk
        near_deadline = any(
            c.trial_date and (c.trial_date - datetime.now()).days < 90
            for c in cases
        )
        if near_deadline:
            risk += 15
        
        # Destination firm risk
        if attorney.destination_firm != "Unknown" and "competitor" in attorney.destination_firm.lower():
            risk += 10
        
        return min(risk, 100)
    
    def _risk_level_from_score(self, score: int) -> str:
        """Convert risk score to level"""
        if score >= 70:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        elif score >= 30:
            return "MODERATE"
        else:
            return "LOW"
    
    def _get_critical_actions(self) -> List[str]:
        """Get list of critical actions from P0/P1 vulnerabilities"""
        critical_vulns = self.severity_triage.get_actionable()
        
        actions = []
        for vuln in critical_vulns:
            if vuln.remediation_steps:
                actions.extend(vuln.remediation_steps[:2])  # Top 2 steps per vuln
        
        return actions[:10]  # Return top 10 critical actions


# Example usage
if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    console.print(Panel.fit(
        "[bold red]Attorney Departure Risk Analysis[/bold red]\n"
        "Enterprise Adversarial Analysis for Law Firms",
        border_style="red"
    ))
    
    # Example departing attorney
    attorney = AttorneyProfile(
        attorney_id="ATT001",
        name="Senior Partner",
        practice_area="Complex Commercial Litigation",
        years_at_firm=12,
        active_cases=["CASE001", "CASE002", "CASE003", "CASE004", "CASE005"],
        client_relationships=["MegaCorp", "TechStartup", "Finance Inc"],
        specialized_knowledge=[
            "Securities litigation",
            "Class action defense",
            "Expert witness cross-examination"
        ],
        system_access=[
            "Case Management System",
            "Document Repository",
            "Client Portal",
            "Billing System",
            "Email",
            "VPN"
        ],
        departure_date=datetime.now() + timedelta(days=30),
        destination_firm="Competing Firm LLP",
        notice_period_days=30
    )
    
    # Example active cases
    cases = [
        ActiveCase(
            case_id="CASE001",
            case_name="MegaCorp v. Competitor",
            client="MegaCorp",
            lead_attorney="Senior Partner",
            supporting_attorneys=["Junior Associate"],
            trial_date=datetime.now() + timedelta(days=45),
            case_value=5000000,
            complexity_score=9,
            documentation_completeness=0.45
        ),
        ActiveCase(
            case_id="CASE002",
            case_name="Class Action Defense",
            client="TechStartup",
            lead_attorney="Senior Partner",
            supporting_attorneys=[],
            trial_date=datetime.now() + timedelta(days=120),
            case_value=3000000,
            complexity_score=8,
            documentation_completeness=0.55
        ),
    ]
    
    # Run analysis
    analyzer = AttorneyDepartureAnalyzer()
    result = analyzer.analyze_departure(attorney, cases)
    
    console.print(result["formatted_output"])
    
    console.print("\n" + "="*70)
    console.print(f"[bold]Overall Risk Score: {result['risk_score']}/100[/bold]")
    console.print(f"[bold]Risk Level: {result['risk_level']}[/bold]")
    console.print("="*70)
