"""
Lateral Hire Due Diligence Gem

Adversarial intelligence for evaluating incoming lateral hires.
Identifies conflicts, stolen data risk, and hidden liabilities
BEFORE you hire someone else's partner.

PRIVACY ARCHITECTURE:
- ALL proprietary risk patterns stored LOCAL ONLY
- ALL conflict detection logic runs LOCAL
- ALL liability scoring runs LOCAL
- LLMs receive ONLY: candidate name, practice area, years
- LLMs receive ZERO: proprietary patterns, scoring logic, red flags

This completes the "full cycle" story:
- Attorney Departure Gem: Defense when YOUR partner leaves
- Lateral Hire Gem: Due diligence when you HIRE someone else's partner
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class RiskCategory(Enum):
    """Categories of lateral hire risk"""
    CONFLICT_OF_INTEREST = "Conflict of Interest"
    STOLEN_DATA = "Potential Stolen Data"
    CLIENT_CONTAMINATION = "Client Contamination"
    NON_COMPETE_VIOLATION = "Non-Compete Violation"
    REPUTATION_RISK = "Reputation Risk"
    CULTURAL_FIT = "Cultural Fit Risk"
    FINANCIAL_LIABILITY = "Financial Liability"


class RiskLevel(Enum):
    """Risk severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class ConflictFinding:
    """Individual conflict or risk finding"""
    category: RiskCategory
    severity: RiskLevel
    title: str
    description: str
    mitigation: str
    liability_estimate: str


@dataclass
class LateralHireAssessment:
    """Complete lateral hire assessment"""
    candidate_name: str
    origin_firm: str
    practice_area: str
    years_experience: int
    book_of_business: str
    
    # Risk scores (LOCAL CALCULATION - never sent to LLM)
    overall_risk_score: int  # 0-100
    conflict_risk: int
    stolen_data_risk: int
    liability_risk: int
    
    # Findings
    findings: List[ConflictFinding]
    
    # Recommendations
    immediate_actions: List[str]
    pre_hire_requirements: List[str]
    
    # Financial
    potential_liability: str
    mitigation_cost: str
    net_value: str


class LateralHireGem:
    """
    Lateral Hire Due Diligence Gem
    
    Evaluates incoming lateral hires for:
    - Conflicts of interest with existing clients
    - Risk of stolen data/trade secrets from origin firm
    - Non-compete and restrictive covenant violations
    - Reputation and cultural fit risks
    - Financial liability exposure
    
    PRIVACY: All scoring and pattern matching is LOCAL.
    LLMs only receive generic candidate profiles.
    """
    
    # =========================================================
    # PROPRIETARY PATTERNS - LOCAL ONLY - NEVER SENT TO LLM
    # =========================================================
    
    # Practice area risk multipliers (based on historical data)
    PRACTICE_RISK_MULTIPLIERS = {
        "M&A": 2.5,  # High client concentration, deal intelligence
        "Corporate": 2.0,
        "IP Litigation": 2.2,  # Trade secrets expertise = knows how to take them
        "Patent Prosecution": 1.8,
        "Private Equity": 2.3,
        "Securities": 2.0,
        "Real Estate": 1.5,
        "Employment": 1.3,
        "Tax": 1.4,
        "Bankruptcy": 1.6,
        "General Litigation": 1.2,
        "Criminal Defense": 1.0,
    }
    
    # Origin firm risk patterns (composite anonymized data)
    ORIGIN_FIRM_PATTERNS = {
        "AmLaw 50": {
            "conflict_probability": 0.75,
            "stolen_data_probability": 0.45,
            "litigation_probability": 0.30,
            "typical_settlement": "$500K-$2M"
        },
        "AmLaw 100": {
            "conflict_probability": 0.60,
            "stolen_data_probability": 0.35,
            "litigation_probability": 0.20,
            "typical_settlement": "$250K-$750K"
        },
        "Regional": {
            "conflict_probability": 0.40,
            "stolen_data_probability": 0.25,
            "litigation_probability": 0.15,
            "typical_settlement": "$100K-$300K"
        },
        "Boutique": {
            "conflict_probability": 0.50,
            "stolen_data_probability": 0.30,
            "litigation_probability": 0.25,
            "typical_settlement": "$150K-$500K"
        }
    }
    
    # Tenure risk patterns
    TENURE_RISK_THRESHOLDS = {
        (0, 3): {"risk": "LOW", "multiplier": 0.5, "note": "Junior, limited client ownership"},
        (3, 7): {"risk": "MEDIUM", "multiplier": 1.0, "note": "Building book, moderate relationships"},
        (7, 15): {"risk": "HIGH", "multiplier": 1.5, "note": "Established rainmaker, deep client ties"},
        (15, 50): {"risk": "CRITICAL", "multiplier": 2.0, "note": "Institutional knowledge, maximum risk"},
    }
    
    # Red flag patterns (LOCAL ONLY)
    RED_FLAG_PATTERNS = [
        {
            "pattern": "quick_departure",
            "condition": lambda years: years < 2,
            "severity": RiskLevel.HIGH,
            "title": "Rapid Departure Pattern",
            "description": "Left origin firm within 2 years - may indicate forced exit or pattern of instability",
            "mitigation": "Request detailed exit circumstances, contact origin firm HR"
        },
        {
            "pattern": "competitor_direct",
            "condition": lambda practice: practice in ["M&A", "IP Litigation", "Private Equity"],
            "severity": RiskLevel.CRITICAL,
            "title": "Direct Competitor Intelligence",
            "description": "Candidate from direct competitor with access to deal intelligence and client strategies",
            "mitigation": "Implement ethical wall, restrict access to competing matters for 12 months"
        },
        {
            "pattern": "rainmaker_target",
            "condition": lambda book: book and int(book.replace("$", "").replace("M", "000000").replace(",", "")) > 1000000,
            "severity": RiskLevel.HIGH,
            "title": "High-Value Rainmaker Target",
            "description": "Origin firm likely to pursue litigation to retain clients and enforce non-competes",
            "mitigation": "Engage outside counsel for pre-hire analysis of restrictive covenants"
        }
    ]
    
    def __init__(self):
        """Initialize the Lateral Hire Due Diligence Gem"""
        pass  # All processing is local - no API connections needed
    
    def assess_lateral_hire(
        self,
        candidate_name: str,
        origin_firm: str,
        practice_area: str,
        years_at_origin: int,
        book_of_business: str = "Unknown",
        origin_firm_type: str = "AmLaw 100",
        known_clients: Optional[List[str]] = None,
        non_compete_exists: bool = True,
        garden_leave_required: bool = False
    ) -> LateralHireAssessment:
        """
        Assess lateral hire risk - ALL PROCESSING LOCAL
        
        Args:
            candidate_name: Full name of candidate
            origin_firm: Name of firm they're leaving
            practice_area: Their practice area
            years_at_origin: Years at origin firm
            book_of_business: Estimated portable book (e.g., "$2.5M")
            origin_firm_type: "AmLaw 50", "AmLaw 100", "Regional", "Boutique"
            known_clients: List of clients they're expected to bring
            non_compete_exists: Whether they have non-compete agreement
            garden_leave_required: Whether garden leave is contractually required
        
        Returns:
            LateralHireAssessment with full risk analysis
        """
        
        # =========================================================
        # ALL CALCULATIONS ARE LOCAL - ZERO LLM INVOLVEMENT
        # =========================================================
        
        # Calculate base risk scores
        conflict_risk = self._calculate_conflict_risk(
            practice_area, origin_firm_type, years_at_origin, known_clients
        )
        
        stolen_data_risk = self._calculate_stolen_data_risk(
            practice_area, years_at_origin, book_of_business
        )
        
        liability_risk = self._calculate_liability_risk(
            origin_firm_type, non_compete_exists, garden_leave_required, book_of_business
        )
        
        # Overall risk score (weighted average)
        overall_risk = int(
            (conflict_risk * 0.35) + 
            (stolen_data_risk * 0.35) + 
            (liability_risk * 0.30)
        )
        
        # Generate findings based on local pattern matching
        findings = self._generate_findings(
            candidate_name, origin_firm, practice_area,
            years_at_origin, book_of_business, origin_firm_type,
            non_compete_exists, garden_leave_required
        )
        
        # Generate actions
        immediate_actions = self._generate_immediate_actions(
            overall_risk, non_compete_exists, origin_firm_type
        )
        
        pre_hire_requirements = self._generate_pre_hire_requirements(
            overall_risk, findings
        )
        
        # Calculate financials
        potential_liability = self._estimate_liability(origin_firm_type, book_of_business)
        mitigation_cost = self._estimate_mitigation_cost(overall_risk)
        net_value = self._calculate_net_value(book_of_business, potential_liability)
        
        return LateralHireAssessment(
            candidate_name=candidate_name,
            origin_firm=origin_firm,
            practice_area=practice_area,
            years_experience=years_at_origin,
            book_of_business=book_of_business,
            overall_risk_score=overall_risk,
            conflict_risk=conflict_risk,
            stolen_data_risk=stolen_data_risk,
            liability_risk=liability_risk,
            findings=findings,
            immediate_actions=immediate_actions,
            pre_hire_requirements=pre_hire_requirements,
            potential_liability=potential_liability,
            mitigation_cost=mitigation_cost,
            net_value=net_value
        )
    
    def _calculate_conflict_risk(
        self, practice_area: str, origin_firm_type: str, 
        years: int, known_clients: Optional[List[str]]
    ) -> int:
        """Calculate conflict of interest risk score (0-100) - LOCAL ONLY"""
        
        base_score = 30
        
        # Practice area multiplier
        practice_mult = self.PRACTICE_RISK_MULTIPLIERS.get(practice_area, 1.2)
        base_score *= practice_mult
        
        # Origin firm type
        origin_pattern = self.ORIGIN_FIRM_PATTERNS.get(origin_firm_type, {})
        conflict_prob = origin_pattern.get("conflict_probability", 0.5)
        base_score *= (1 + conflict_prob)
        
        # Tenure multiplier
        for (min_y, max_y), data in self.TENURE_RISK_THRESHOLDS.items():
            if min_y <= years < max_y:
                base_score *= data["multiplier"]
                break
        
        # Known clients add risk
        if known_clients:
            base_score += len(known_clients) * 5
        
        return min(100, int(base_score))
    
    def _calculate_stolen_data_risk(
        self, practice_area: str, years: int, book: str
    ) -> int:
        """Calculate stolen data/trade secret risk (0-100) - LOCAL ONLY"""
        
        base_score = 25
        
        # Practice areas with high data sensitivity
        high_data_practices = ["M&A", "IP Litigation", "Private Equity", "Patent Prosecution"]
        if practice_area in high_data_practices:
            base_score += 30
        
        # Years = more institutional knowledge
        base_score += min(years * 2, 30)
        
        # Large book = more client data exposure
        try:
            book_value = float(book.replace("$", "").replace("M", "").replace(",", ""))
            if book_value > 5:
                base_score += 20
            elif book_value > 2:
                base_score += 10
        except:
            base_score += 10  # Unknown = assume moderate
        
        return min(100, int(base_score))
    
    def _calculate_liability_risk(
        self, origin_type: str, non_compete: bool, 
        garden_leave: bool, book: str
    ) -> int:
        """Calculate financial liability risk (0-100) - LOCAL ONLY"""
        
        base_score = 20
        
        # Origin firm litigation probability
        origin_pattern = self.ORIGIN_FIRM_PATTERNS.get(origin_type, {})
        lit_prob = origin_pattern.get("litigation_probability", 0.2)
        base_score += int(lit_prob * 50)
        
        # Non-compete increases risk significantly
        if non_compete:
            base_score += 25
        
        # Garden leave violation risk
        if garden_leave:
            base_score += 15
        
        # Large book = larger damages claim
        try:
            book_value = float(book.replace("$", "").replace("M", "").replace(",", ""))
            if book_value > 3:
                base_score += 20
            elif book_value > 1:
                base_score += 10
        except:
            pass
        
        return min(100, int(base_score))
    
    def _generate_findings(
        self, name: str, origin: str, practice: str,
        years: int, book: str, origin_type: str,
        non_compete: bool, garden_leave: bool
    ) -> List[ConflictFinding]:
        """Generate risk findings based on LOCAL patterns"""
        
        findings = []
        
        # Check red flag patterns
        for pattern in self.RED_FLAG_PATTERNS:
            # Evaluate conditions based on pattern type
            if pattern["pattern"] == "quick_departure":
                if years < 2:
                    findings.append(ConflictFinding(
                        category=RiskCategory.REPUTATION_RISK,
                        severity=pattern["severity"],
                        title=pattern["title"],
                        description=pattern["description"],
                        mitigation=pattern["mitigation"],
                        liability_estimate="$25K-$50K investigation cost"
                    ))
            
            elif pattern["pattern"] == "competitor_direct":
                if practice in ["M&A", "IP Litigation", "Private Equity"]:
                    findings.append(ConflictFinding(
                        category=RiskCategory.CONFLICT_OF_INTEREST,
                        severity=pattern["severity"],
                        title=pattern["title"],
                        description=pattern["description"],
                        mitigation=pattern["mitigation"],
                        liability_estimate="$100K-$500K ethical wall cost"
                    ))
            
            elif pattern["pattern"] == "rainmaker_target":
                try:
                    book_val = float(book.replace("$", "").replace("M", "").replace(",", ""))
                    if book_val > 1:
                        findings.append(ConflictFinding(
                            category=RiskCategory.FINANCIAL_LIABILITY,
                            severity=pattern["severity"],
                            title=pattern["title"],
                            description=pattern["description"],
                            mitigation=pattern["mitigation"],
                            liability_estimate=self.ORIGIN_FIRM_PATTERNS.get(origin_type, {}).get("typical_settlement", "$200K-$500K")
                        ))
                except:
                    pass
        
        # Non-compete finding
        if non_compete:
            findings.append(ConflictFinding(
                category=RiskCategory.NON_COMPETE_VIOLATION,
                severity=RiskLevel.HIGH,
                title="Active Non-Compete Agreement",
                description=f"Candidate has non-compete with {origin}. Hiring may trigger litigation.",
                mitigation="Obtain copy of agreement, engage employment counsel for enforceability analysis",
                liability_estimate="$150K-$750K defense + potential damages"
            ))
        
        # Garden leave finding
        if garden_leave:
            findings.append(ConflictFinding(
                category=RiskCategory.NON_COMPETE_VIOLATION,
                severity=RiskLevel.CRITICAL,
                title="Garden Leave Requirement",
                description="Candidate contractually required to observe garden leave period before starting new position",
                mitigation="Verify garden leave dates, do not allow candidate to start until period expires",
                liability_estimate="$50K-$200K breach of contract exposure"
            ))
        
        # High-tenure finding
        if years >= 15:
            findings.append(ConflictFinding(
                category=RiskCategory.STOLEN_DATA,
                severity=RiskLevel.HIGH,
                title="Institutional Knowledge Concentration",
                description=f"{years} years tenure = deep institutional knowledge including client strategies, pricing models, and competitive intelligence",
                mitigation="Implement clean-start protocol - no access to origin firm data for 90 days",
                liability_estimate="$200K-$1M if data exfiltration discovered"
            ))
        
        # Practice-specific findings
        if practice == "M&A":
            findings.append(ConflictFinding(
                category=RiskCategory.CLIENT_CONTAMINATION,
                severity=RiskLevel.HIGH,
                title="Active Deal Intelligence Risk",
                description="M&A practitioners have visibility into live transactions. Candidate may have confidential deal information.",
                mitigation="Screen for active matters at origin firm, implement conflict checks before any M&A assignment",
                liability_estimate="$500K-$2M if deal information compromised"
            ))
        
        return findings
    
    def _generate_immediate_actions(
        self, risk_score: int, non_compete: bool, origin_type: str
    ) -> List[str]:
        """Generate immediate action items - LOCAL ONLY"""
        
        actions = []
        
        if risk_score >= 70:
            actions.append("CRITICAL: Engage outside employment counsel before extending offer")
            actions.append("Obtain and review all restrictive covenants from candidate")
            actions.append("Run comprehensive conflict check against origin firm clients")
        elif risk_score >= 50:
            actions.append("HIGH: Request copies of all employment agreements from candidate")
            actions.append("Conduct conflict check against known client list")
            actions.append("Prepare ethical wall procedures for first 90 days")
        else:
            actions.append("Standard: Confirm no restrictive covenants or obtain waiver")
            actions.append("Standard conflict check before start date")
        
        if non_compete:
            actions.insert(0, "MANDATORY: Do not extend formal offer until non-compete reviewed by counsel")
        
        if origin_type == "AmLaw 50":
            actions.append("RECOMMENDED: Anticipate demand letter from origin firm, prepare response")
        
        return actions
    
    def _generate_pre_hire_requirements(
        self, risk_score: int, findings: List[ConflictFinding]
    ) -> List[str]:
        """Generate pre-hire requirements - LOCAL ONLY"""
        
        requirements = [
            "Conflict clearance from all practice groups",
            "Signed acknowledgment of firm data policies",
            "Written confirmation candidate has not retained origin firm documents"
        ]
        
        if risk_score >= 60:
            requirements.insert(0, "Outside counsel opinion on restrictive covenant enforceability")
            requirements.append("Executive committee approval required")
        
        if any(f.category == RiskCategory.NON_COMPETE_VIOLATION for f in findings):
            requirements.insert(0, "Employment counsel clearance letter")
        
        if any(f.category == RiskCategory.STOLEN_DATA for f in findings):
            requirements.append("Device certification - no origin firm data on personal devices")
            requirements.append("Cloud storage audit before start date")
        
        return requirements
    
    def _estimate_liability(self, origin_type: str, book: str) -> str:
        """Estimate potential liability - LOCAL ONLY"""
        
        base = self.ORIGIN_FIRM_PATTERNS.get(origin_type, {}).get("typical_settlement", "$200K-$500K")
        
        try:
            book_val = float(book.replace("$", "").replace("M", "").replace(",", ""))
            if book_val > 5:
                return "$750K-$3M"
            elif book_val > 2:
                return "$400K-$1.5M"
        except:
            pass
        
        return base
    
    def _estimate_mitigation_cost(self, risk_score: int) -> str:
        """Estimate mitigation cost - LOCAL ONLY"""
        
        if risk_score >= 70:
            return "$75K-$150K (counsel + ethical walls + monitoring)"
        elif risk_score >= 50:
            return "$25K-$75K (counsel review + conflict management)"
        else:
            return "$5K-$15K (standard onboarding protocols)"
    
    def _calculate_net_value(self, book: str, liability: str) -> str:
        """Calculate net value proposition - LOCAL ONLY"""
        
        try:
            book_val = float(book.replace("$", "").replace("M", "").replace(",", ""))
            
            # Parse liability range
            liability_low = float(liability.split("-")[0].replace("$", "").replace("K", "").replace("M", "000"))
            if "K" in liability.split("-")[0]:
                liability_low /= 1000
            
            net = book_val - (liability_low / 1000)
            
            if net > 0:
                return f"${net:.1f}M net value (after risk mitigation)"
            else:
                return "NEGATIVE - liability exceeds portable book"
        except:
            return "Unable to calculate - review book and liability manually"


def format_lateral_assessment(assessment: LateralHireAssessment) -> str:
    """Format assessment as executive text report - LOCAL ONLY"""
    
    lines = []
    
    lines.append("=" * 80)
    lines.append("LATERAL HIRE DUE DILIGENCE ASSESSMENT".center(80))
    lines.append("=" * 80)
    lines.append("")
    
    # Candidate info
    lines.append("CANDIDATE PROFILE")
    lines.append("-" * 80)
    lines.append(f"Name:               {assessment.candidate_name}")
    lines.append(f"Origin Firm:        {assessment.origin_firm}")
    lines.append(f"Practice Area:      {assessment.practice_area}")
    lines.append(f"Years at Origin:    {assessment.years_experience}")
    lines.append(f"Book of Business:   {assessment.book_of_business}")
    lines.append("")
    
    # Risk scores
    lines.append("RISK ASSESSMENT")
    lines.append("-" * 80)
    lines.append(f"Overall Risk Score:     {assessment.overall_risk_score}/100")
    lines.append(f"Conflict Risk:          {assessment.conflict_risk}/100")
    lines.append(f"Stolen Data Risk:       {assessment.stolen_data_risk}/100")
    lines.append(f"Liability Risk:         {assessment.liability_risk}/100")
    lines.append("")
    
    # Financials
    lines.append("FINANCIAL ANALYSIS")
    lines.append("-" * 80)
    lines.append(f"Potential Liability:    {assessment.potential_liability}")
    lines.append(f"Mitigation Cost:        {assessment.mitigation_cost}")
    lines.append(f"Net Value:              {assessment.net_value}")
    lines.append("")
    
    # Findings
    lines.append("RISK FINDINGS")
    lines.append("-" * 80)
    for i, finding in enumerate(assessment.findings, 1):
        lines.append(f"{i}. [{finding.severity.value}] {finding.title}")
        lines.append(f"   Category: {finding.category.value}")
        lines.append(f"   Liability: {finding.liability_estimate}")
        lines.append(f"   Mitigation: {finding.mitigation}")
        lines.append("")
    
    # Immediate actions
    lines.append("IMMEDIATE ACTIONS")
    lines.append("-" * 80)
    for i, action in enumerate(assessment.immediate_actions, 1):
        lines.append(f"{i}. {action}")
    lines.append("")
    
    # Pre-hire requirements
    lines.append("PRE-HIRE REQUIREMENTS")
    lines.append("-" * 80)
    for i, req in enumerate(assessment.pre_hire_requirements, 1):
        lines.append(f"{i}. {req}")
    lines.append("")
    
    lines.append("=" * 80)
    lines.append("AION OS - Lateral Hire Due Diligence Gem")
    lines.append("100% Local Processing - Zero Data Sent to LLMs")
    lines.append("=" * 80)
    
    return "\n".join(lines)
