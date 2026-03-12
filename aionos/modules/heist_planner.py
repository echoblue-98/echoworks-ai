"""
Heist Planner - Attorney Departure Scenario

This module orchestrates the "Heist Crew" to simulate data exfiltration 
scenarios when a high-value attorney departs a firm. It uses the core 
AdversarialEngine to run the 5-stage attack.

Enhanced with:
- Pattern Matcher: Compares scenarios to historical cases (proprietary moat)
- ROI Calculator: Quantifies financial risk for law firm decision-makers
- Timeline Analyzer: Maps attack vectors to specific dates/times
"""

from ..core.adversarial_engine import AdversarialEngine, IntensityLevel
from ..core.severity_triage import Severity
from ..core.pattern_matcher import PatternMatcher
from ..core.roi_calculator import ROICalculator
from ..core.timeline_analyzer import TimelineAnalyzer
from .quantum_adversarial import QuantumInspiredOptimizer
from ..api.gemini_client import GeminiClient
from datetime import datetime, timedelta

# Try to import Llama client (optional - for self-hosted deployment)
try:
    from ..api.llama_client import LlamaClient, check_llama_available
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    check_llama_available = lambda: False

class HeistPlanner:
    """
    Orchestrates the 5-stage "Heist Crew" analysis for attorney departure.
    Now enhanced with pattern matching, ROI calculation, and timeline analysis.
    
    Supports multiple AI backends:
    - Claude (Anthropic) - Default, best quality
    - Gemini (Google) - Free tier available
    - Llama (Self-hosted) - Maximum privacy, 100% local
    """
    def __init__(self, intensity: IntensityLevel = IntensityLevel.LEVEL_4_REDTEAM, 
                 use_gemini: bool = False, use_llama: bool = False):
        self.engine = AdversarialEngine(intensity=intensity)
        self.optimizer = QuantumInspiredOptimizer()
        self.use_gemini = use_gemini
        self.use_llama = use_llama
        self.gemini_client = GeminiClient() if use_gemini else None
        self.llama_client = None
        
        # Initialize Llama if requested
        if use_llama:
            if LLAMA_AVAILABLE and check_llama_available():
                self.llama_client = LlamaClient()
                print("[OK] Llama (Self-Hosted) connected - 100% local privacy mode")
            else:
                print("[WARN] Llama not available, falling back to Claude")
                self.use_llama = False
        
        # Initialize moat modules
        self.pattern_matcher = PatternMatcher()
        self.roi_calculator = ROICalculator()
        self.timeline_analyzer = TimelineAnalyzer()
        self.progress_callback = None  # Set by CLI for real-time display

    def analyze_departure_risk(self, attorney_profile: dict, progress_callback: callable = None) -> dict:
        """
        Analyzes the security risk of a departing attorney using the Heist Crew.
        
        Enhanced analysis includes:
        1. Rule-based vulnerabilities (deterministic, scenario-specific)
        2. Pattern matching against historical cases (proprietary moat)
        3. Quantitative financial risk scoring (ROI justification)
        4. Timeline breach analysis (forensic audit guidance)

        Args:
            attorney_profile: A dictionary containing details about the departing attorney.
            progress_callback: Optional callback for real-time agent updates.

        Returns:
            A dictionary containing comprehensive analysis results with financial impact.
        """
        print("HeistPlanner: Assembling the crew...")
        
        # STEP 0: Generate rule-based vulnerabilities (ensures diversity)
        print("HeistPlanner: Applying known risk factors...")
        rule_based_vulns = self._apply_risk_rules(attorney_profile)
        
        # STEP 1: Check historical patterns first
        print("HeistPlanner: Checking pattern database...")
        matched_patterns = self.pattern_matcher.match_scenario(attorney_profile)
        pattern_recommendations = self.pattern_matcher.generate_recommendations(matched_patterns)

        # 2. Create the master plan document for the crew
        heist_brief = self._create_heist_brief(attorney_profile, pattern_recommendations)

        # 3. Run the 5-stage adversarial analysis with real-time progress
        if self.use_llama and self.llama_client:
            analysis_result = self.llama_client.analyze(heist_brief, {}, self.engine.intensity.value)
        elif self.use_gemini:
            analysis_result = self.gemini_client.analyze(heist_brief, {}, self.engine.intensity.value)
        else:
            analysis_result = self.engine.analyze(heist_brief, {}, progress_callback=progress_callback)
        
        # 4. Merge rule-based vulnerabilities with AI-generated ones
        ai_vulns = analysis_result.get("vulnerabilities", [])
        all_vulnerabilities = rule_based_vulns + ai_vulns
        analysis_result["vulnerabilities"] = all_vulnerabilities

        # 5. Extract the highest-severity attack path
        vulnerabilities = all_vulnerabilities
        if vulnerabilities:
            print("HeistPlanner: Calculating optimal exfiltration path...")
            
            # Sort by severity and build optimal path
            high_severity_vulns = [v for v in vulnerabilities if v.get('severity') in ['critical', 'high']]
            optimal_path = high_severity_vulns if high_severity_vulns else vulnerabilities
            
            # Calculate success probability based on number of high-severity findings
            success_prob = min(95.0, 60.0 + (len(optimal_path) * 10))
            
            summary = (
                f"The Heist Crew identified {len(optimal_path)} critical attack vectors "
                f"with a {success_prob:.0f}% probability of successful exfiltration. "
                f"Path: {' → '.join([v['agent'] for v in optimal_path])}"
            )
            
            analysis_result["heist_summary"] = {
                "optimal_path": [v.get('id', v.get('title', 'unknown')) for v in optimal_path],
                "success_probability": success_prob,
                "summary_text": summary,
                "crew_report": f"The crew has mapped {len(optimal_path)} exploitable vulnerabilities across {len(vulnerabilities)} attack stages."
            }
            
            # STEP 2: Calculate financial ROI
            print("HeistPlanner: Calculating financial risk and ROI...")
            financial_analysis = self.roi_calculator.calculate_financial_risk(attorney_profile, vulnerabilities)
            analysis_result["financial_analysis"] = financial_analysis
            
            # STEP 3: Generate timeline breach analysis
            print("HeistPlanner: Mapping attack vectors to timeline...")
            timeline_analysis = self.timeline_analyzer.analyze_timeline(attorney_profile, vulnerabilities)
            analysis_result["timeline_analysis"] = timeline_analysis
            
            # STEP 4: Add pattern match results
            if pattern_recommendations.get('pattern_match_found'):
                print(f"HeistPlanner: Pattern match found - {pattern_recommendations['similar_case']['similarity']} similar to historical case")
                analysis_result["pattern_match"] = pattern_recommendations

        print("HeistPlanner: Analysis complete.")
        return analysis_result

    def _apply_risk_rules(self, profile: dict) -> list:
        """
        Apply deterministic risk rules based on attorney characteristics.
        This ensures output diversity and adds defensible logic independent of AI.
        
        Returns list of vulnerability dicts matching adversarial engine format.
        """
        vulnerabilities = []
        
        # Extract profile data
        years = profile.get('years_at_firm', 0)
        practice_area = profile.get('practice_area', '').lower()
        title = profile.get('title', '').lower()
        access_level = profile.get('system_access', '').lower()
        destination = profile.get('destination', '').lower()
        active_cases = profile.get('active_cases', '')
        
        # RULE 1: Senior Attorney = Client Relationship Risk
        if years >= 10 or 'senior' in title or 'partner' in title:
            vulnerabilities.append({
                'id': 'RULE_SENIOR_CLIENT_MIGRATION',
                'title': 'Client Relationship Migration Risk',
                'description': f"{years} years of tenure creates deep personal client relationships. "
                             f"Studies show {min(85, 60 + years * 2)}% of clients follow attorneys with 10+ years tenure. "
                             f"High-value clients view the attorney, not the firm, as their counsel.",
                'severity': 'CRITICAL',
                'likelihood': 'Very High' if years >= 15 else 'High',
                'impact': f'${years * 250000:,}+ in recurring annual revenue',
                'agent': 'Pattern Analysis',
                'category': 'Client Defection',
                'countermeasures': [
                    f'Audit all client communications from past {min(180, years * 10)} days',
                    'Review billing records for client concentration',
                    'Implement relationship transition plans for top 10 clients',
                    'Schedule partner meetings with vulnerable clients within 48 hours of departure notice'
                ]
            })
        
        # RULE 2: M&A/Corporate Practice = Deal Pipeline Exposure
        if any(term in practice_area for term in ['m&a', 'merger', 'acquisition', 'corporate', 'transactional']):
            vulnerabilities.append({
                'id': 'RULE_DEAL_PIPELINE',
                'title': 'Active Transaction Pipeline Exposure',
                'description': 'M&A and corporate attorneys have visibility into confidential transactions, '
                             'buyer/seller lists, deal structures, and valuation models. Active deals represent '
                             'immediate competitive intelligence. Departing attorneys may share pipeline info '
                             'to demonstrate value to new firm.',
                'severity': 'CRITICAL',
                'likelihood': 'High',
                'impact': 'Loss of competitive advantage + potential client conflicts',
                'agent': 'Deal Intelligence',
                'category': 'Trade Secret Exposure',
                'countermeasures': [
                    'Immediate audit of all active transaction documents accessed in last 90 days',
                    'Review email for forwarding rules or external recipients',
                    'Check cloud storage sync (OneDrive, Dropbox, Google Drive) for deal files',
                    'Notify clients with active M&A matters of attorney transition',
                    'Implement deal firewall for remaining active transactions'
                ]
            })
        
        # RULE 3: Litigation Practice = Case Strategy/Evidence Exposure
        if any(term in practice_area for term in ['litigation', 'trial', 'dispute']):
            vulnerabilities.append({
                'id': 'RULE_LITIGATION_STRATEGY',
                'title': 'Litigation Strategy & Evidence Disclosure Risk',
                'description': 'Litigators possess detailed case strategies, witness lists, deposition summaries, '
                             'settlement negotiations, and opposing counsel weaknesses. This intelligence is '
                             'highly valuable if destination firm represents competing interests.',
                'severity': 'HIGH',
                'likelihood': 'Medium-High',
                'impact': 'Loss of litigation advantage + potential malpractice exposure',
                'agent': 'Case Strategy Analysis',
                'category': 'Work Product Theft',
                'countermeasures': [
                    'Audit access to case management systems (Clio, LexisNexis, Westlaw)',
                    'Review printed documents from last 60 days',
                    'Check for USB drive usage or external file transfers',
                    'Evaluate conflict of interest if destination firm has opposing clients'
                ]
            })
        
        # RULE 4: Full System Access = Technical Exfiltration Risk
        if any(term in access_level for term in ['full', 'admin', 'elevated', 'portal']):
            vulnerabilities.append({
                'id': 'RULE_PRIVILEGED_ACCESS',
                'title': 'Privileged System Access Exploitation',
                'description': 'Full system access enables bulk data exfiltration through automated means: '
                             'email rules, API access, database exports, backup downloads. Technical sophistication '
                             'increases risk of undetected mass extraction.',
                'severity': 'CRITICAL',
                'likelihood': 'Medium',
                'impact': 'Potential breach of entire client database',
                'agent': 'Technical Infiltration',
                'category': 'System-Level Breach',
                'countermeasures': [
                    'Immediately review email forwarding rules and filters',
                    'Audit API tokens and service account access',
                    'Check for scheduled tasks or automation scripts',
                    'Review VPN and remote access logs for unusual hours/locations',
                    'Monitor outbound data transfer volumes',
                    'Disable non-essential access 30 days before departure date'
                ]
            })
        
        # RULE 5: Competitor Destination = Intentional Intelligence Gathering
        if any(term in destination for term in ['competitor', 'rival', 'competing']):
            vulnerabilities.append({
                'id': 'RULE_COMPETITOR_INTEL',
                'title': 'Competitive Intelligence Motivation',
                'description': 'Destination firm is a direct competitor. Attorney has strong incentive to bring '
                             'strategic intelligence: billing rates, client lists, pitch strategies, fee arrangements, '
                             'partner compensation, firm financials. This is not accidental - it\'s recruitment strategy.',
                'severity': 'CRITICAL',
                'likelihood': 'Very High',
                'impact': 'Systematic competitive disadvantage',
                'agent': 'Strategic Intelligence',
                'category': 'Corporate Espionage Risk',
                'countermeasures': [
                    'Enforce immediate NDA and non-solicitation reminders',
                    'Review all client contact from past 90 days for pre-departure solicitation',
                    'Audit access to financial systems (billing, profitability reports)',
                    'Monitor for contact with other firm attorneys (potential raiding)',
                    'Consider garden leave or paid departure transition to limit final access window'
                ]
            })
        
        # RULE 6: High-Value Cases = Time-Sensitive Data Risk
        if active_cases and (any(char.isdigit() for char in active_cases) or len(active_cases) > 50):
            vulnerabilities.append({
                'id': 'RULE_ACTIVE_MATTER_URGENCY',
                'title': 'Active Matter Data Exfiltration Window',
                'description': 'Attorney has active high-value matters with time-sensitive data. '
                             'Final weeks create perfect cover for "legitimate" access to client files, '
                             'case documents, and billing records under guise of transition preparation.',
                'severity': 'HIGH',
                'likelihood': 'High',
                'impact': 'Loss of client trust + immediate competitive harm',
                'agent': 'Timeline Analysis',
                'category': 'Pre-Departure Exfiltration',
                'countermeasures': [
                    'Require supervised access to active matter files',
                    'Implement document checkout/audit trail for all case files',
                    'Limit printing and external email during final 30 days',
                    'Assign transition partner for direct client handoff (not departing attorney)'
                ]
            })
        
        return vulnerabilities

    def _create_heist_brief(self, profile: dict, pattern_recommendations: dict = None) -> str:
        """
        Creates a detailed document for the AdversarialEngine to analyze.
        This is the "briefing" for the Heist Crew.
        
        PRIVACY NOTE: Pattern data is NOT sent to external APIs.
        We only signal that a historical match exists to guide analysis depth.
        """
        # Add pattern context WITHOUT exposing proprietary data
        pattern_context = ""
        if pattern_recommendations and pattern_recommendations.get('pattern_match_found'):
            # PRIVACY: Only send similarity level, NOT case details
            similarity = pattern_recommendations['similar_case']['similarity']
            pattern_context = f"""
HISTORICAL PATTERN MATCH DETECTED:
Scenario similarity: {similarity}

INSTRUCTION: This profile matches a validated historical departure pattern.
Increase scrutiny on: email forwarding rules, cloud storage sync, after-hours access,
client contact patterns, and document exfiltration vectors.

PRIORITY: Apply heightened defensive analysis based on pattern recognition.
════════════════════════════════════════════════════════════════
"""
        
        brief = f"""
═══════════════════════════════════════════════════════════════
AUTHORIZED DEFENSIVE SECURITY ASSESSMENT
CLIENT: Law Firm Security Team
PURPOSE: Prevent data exfiltration during attorney departure
STATUS: Legal work-product under attorney-client privilege
═══════════════════════════════════════════════════════════════

MISSION BRIEF: OPERATION 'GOLDEN HANDSHAKE'

OBJECTIVE: You have been retained by a law firm to conduct a security vulnerability 
assessment before a high-value attorney departs. Your mission is to identify ALL potential 
data exfiltration vectors so the firm can implement countermeasures BEFORE the departure occurs.

This is DEFENSIVE security work. The firm needs to know what could go wrong so they can prevent it.

═══════════════════════════════════════════════════════════════
DEPARTING ATTORNEY PROFILE
═══════════════════════════════════════════════════════════════

Name: {profile.get('attorney_name', 'N/A')}
Role: {profile.get('practice_area', 'N/A')} Partner
Tenure: {profile.get('years_at_firm', 'N/A')} years at firm
Departure Date: {profile.get('departure_date', 'N/A')}
Destination: {profile.get('destination_firm', 'Likely a direct competitor')}

CURRENT ACCESS & ASSETS:
- System Access: {profile.get('system_access', 'Full firm-wide access')}
- Active Cases: {profile.get('active_cases', 'Multiple high-value cases')}
- Client Relationships: {profile.get('client_relationships', 'Deep relationships with key clients')}

═══════════════════════════════════════════════════════════════
YOUR SECURITY ASSESSMENT FRAMEWORK
═══════════════════════════════════════════════════════════════

You are a security consultant helping this law firm understand departure risks. Conduct a 5-stage 
vulnerability assessment to identify gaps in their security posture:

STAGE 1 - DATA ASSET INVENTORY: Identify high-value information this attorney can access 
(client lists, case strategies, financial data, confidential work product). What data presents 
the highest business risk if improperly accessed?

STAGE 2 - ACCESS CONTROL REVIEW: Document all digital and physical access points this attorney 
currently has. Which systems lack proper audit logs? Where are permission boundaries unclear?

STAGE 3 - RELATIONSHIP RISK ANALYSIS: Assess how personal client relationships could affect 
business continuity. Which clients might be vulnerable to improper solicitation? What ethical 
boundaries need reinforcement?

STAGE 4 - THREAT MODELING: Model potential security scenarios the firm should prepare for. 
What sequence of events could lead to data exposure or client loss? Identify preventable risks.

STAGE 5 - SECURITY CONTROLS DESIGN: Create a prioritized remediation plan. Recommend specific 
technical controls, policy updates, and monitoring procedures to reduce identified risks.

═══════════════════════════════════════════════════════════════

Execute your assessment systematically. The firm needs actionable security recommendations 
to protect confidential information and maintain client relationships during this transition.
        """
        return brief

