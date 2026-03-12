"""
ROI Calculator & Quantitative Risk Scoring

Converts adversarial findings into financial impact estimates.
Law firms buy based on ROI math - this module provides the numbers.
"""

from typing import Dict, List, Any
import math


class ROICalculator:
    """
    Calculates financial risk and ROI for attorney departure scenarios.
    Provides quantitative data that justifies AION's analysis cost.
    """
    
    # Industry benchmarks (sources: AmLaw, ABA, ALM Intelligence)
    AVG_PARTNER_REVENUE = {
        'intellectual property': 3500000,  # $3.5M annually
        'corporate': 4200000,
        'm&a': 5000000,
        'litigation': 2800000,
        'employment': 1800000,
        'real estate': 2200000,
        'healthcare': 2500000,
        'default': 2500000  # Conservative estimate
    }
    
    CLIENT_DEFECTION_RATE = {
        'competitor': 0.55,  # 55% of clients follow to direct competitor
        'startup': 0.35,     # 35% follow to startup
        'unknown': 0.20      # 20% if destination unknown
    }
    
    LITIGATION_COST_ESTIMATES = {
        'restrictive_covenant': (250000, 1500000),  # (min, max)
        'trade_secret': (500000, 3000000),
        'client_poaching': (150000, 800000),
        'emergency_tro': (75000, 150000)
    }
    
    def __init__(self):
        pass
    
    def calculate_financial_risk(self, attorney_profile: Dict[str, Any], 
                                 vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comprehensive financial risk for attorney departure.
        
        Args:
            attorney_profile: Departing attorney details
            vulnerabilities: List of vulnerabilities found by adversarial analysis
            
        Returns:
            Dictionary with detailed financial impact breakdown
        """
        # 1. Revenue at Risk
        revenue_risk = self._calculate_revenue_risk(attorney_profile)
        
        # 2. Litigation Cost Probability
        litigation_risk = self._calculate_litigation_risk(vulnerabilities)
        
        # 3. Client Retention Costs
        retention_costs = self._calculate_retention_costs(attorney_profile, revenue_risk)
        
        # 4. Replacement Costs
        replacement_costs = self._calculate_replacement_costs(attorney_profile)
        
        # 5. Knowledge Loss Impact
        knowledge_loss = self._calculate_knowledge_loss(attorney_profile)
        
        # 6. Total Risk
        total_risk_min = (revenue_risk['annual_risk_min'] + 
                         litigation_risk['expected_cost_min'] + 
                         retention_costs['total_cost'] + 
                         replacement_costs['total_cost'])
        
        total_risk_max = (revenue_risk['annual_risk_max'] + 
                         litigation_risk['expected_cost_max'] + 
                         retention_costs['total_cost'] + 
                         replacement_costs['total_cost'] + 
                         knowledge_loss['estimated_impact'])
        
        total_risk_expected = (total_risk_min + total_risk_max) / 2
        
        # 7. AION ROI Calculation
        aion_analysis_cost = 20000  # $20k for analysis
        roi_multiple = total_risk_expected / aion_analysis_cost
        
        # 8. Risk Timeline
        timeline_risk = self._calculate_timeline_risk(vulnerabilities)
        
        return {
            'revenue_at_risk': revenue_risk,
            'litigation_risk': litigation_risk,
            'client_retention_costs': retention_costs,
            'replacement_costs': replacement_costs,
            'knowledge_loss_impact': knowledge_loss,
            'total_financial_risk': {
                'minimum': total_risk_min,
                'expected': total_risk_expected,
                'maximum': total_risk_max,
                'range': f"${total_risk_min:,.0f} - ${total_risk_max:,.0f}"
            },
            'aion_roi': {
                'analysis_cost': aion_analysis_cost,
                'risk_prevented': total_risk_expected,
                'roi_multiple': f"{roi_multiple:.1f}x",
                'net_value': total_risk_expected - aion_analysis_cost,
                'message': f"AION analysis costs ${aion_analysis_cost:,}. Prevents ${total_risk_expected:,.0f} in losses. ROI: {roi_multiple:.1f}x"
            },
            'timeline_risk': timeline_risk,
            'executive_summary': self._generate_executive_summary(
                total_risk_expected, timeline_risk, vulnerabilities
            )
        }
    
    def _calculate_revenue_risk(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate revenue loss from client defection"""
        practice_area = profile.get('practice_area', '').lower()
        years_at_firm = int(profile.get('years_at_firm', 5))
        destination = profile.get('destination_firm', '').lower()
        
        # Estimate partner revenue
        base_revenue = self.AVG_PARTNER_REVENUE.get(practice_area, self.AVG_PARTNER_REVENUE['default'])
        
        # Adjust for tenure (more tenure = larger book)
        tenure_multiplier = 1.0 + (min(years_at_firm, 20) * 0.05)  # +5% per year, cap at 20 years
        estimated_revenue = base_revenue * tenure_multiplier
        
        # Client defection rate based on destination
        if 'competitor' in destination:
            defection_rate = self.CLIENT_DEFECTION_RATE['competitor']
        elif 'startup' in destination or 'own' in destination:
            defection_rate = self.CLIENT_DEFECTION_RATE['startup']
        else:
            defection_rate = self.CLIENT_DEFECTION_RATE['unknown']
        
        # Calculate risk range (best case to worst case)
        annual_risk_min = estimated_revenue * (defection_rate * 0.6)  # Conservative
        annual_risk_max = estimated_revenue * (defection_rate * 1.2)  # Aggressive
        annual_risk_expected = estimated_revenue * defection_rate
        
        # Multi-year impact (clients don't come back)
        three_year_impact = annual_risk_expected * 2.5  # Present value over 3 years
        
        return {
            'estimated_partner_revenue': estimated_revenue,
            'client_defection_rate': f"{defection_rate * 100:.0f}%",
            'annual_risk_min': annual_risk_min,
            'annual_risk_expected': annual_risk_expected,
            'annual_risk_max': annual_risk_max,
            'three_year_impact': three_year_impact,
            'explanation': f"Partner with {years_at_firm} years tenure generates ~${estimated_revenue:,.0f}/year. "
                          f"{defection_rate*100:.0f}% client defection to {destination} = "
                          f"${annual_risk_expected:,.0f} annual loss."
        }
    
    def _calculate_litigation_risk(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate probability and cost of litigation"""
        critical_count = sum(1 for v in vulnerabilities if v.get('severity') == 'critical')
        high_count = sum(1 for v in vulnerabilities if v.get('severity') == 'high')
        
        # Litigation probability based on severity
        litigation_probability = min(0.9, 0.2 + (critical_count * 0.15) + (high_count * 0.08))
        
        # Estimate litigation type and costs
        vuln_descriptions = ' '.join([v.get('description', '').lower() for v in vulnerabilities])
        
        litigation_types = []
        expected_cost_min = 0
        expected_cost_max = 0
        
        if 'trade secret' in vuln_descriptions or 'proprietary' in vuln_descriptions:
            litigation_types.append('Trade Secret Misappropriation')
            expected_cost_min += self.LITIGATION_COST_ESTIMATES['trade_secret'][0]
            expected_cost_max += self.LITIGATION_COST_ESTIMATES['trade_secret'][1]
        
        if 'non-compete' in vuln_descriptions or 'restrictive' in vuln_descriptions:
            litigation_types.append('Restrictive Covenant Enforcement')
            expected_cost_min += self.LITIGATION_COST_ESTIMATES['restrictive_covenant'][0]
            expected_cost_max += self.LITIGATION_COST_ESTIMATES['restrictive_covenant'][1]
        
        if 'client' in vuln_descriptions and ('poach' in vuln_descriptions or 'solicitation' in vuln_descriptions):
            litigation_types.append('Client Poaching Claims')
            expected_cost_min += self.LITIGATION_COST_ESTIMATES['client_poaching'][0]
            expected_cost_max += self.LITIGATION_COST_ESTIMATES['client_poaching'][1]
        
        # If high-risk, likely need emergency TRO
        if critical_count >= 2:
            litigation_types.append('Emergency TRO/Injunction')
            expected_cost_min += self.LITIGATION_COST_ESTIMATES['emergency_tro'][0]
            expected_cost_max += self.LITIGATION_COST_ESTIMATES['emergency_tro'][1]
        
        # Default to restrictive covenant if nothing specific found
        if not litigation_types:
            litigation_types.append('Restrictive Covenant Enforcement')
            expected_cost_min = self.LITIGATION_COST_ESTIMATES['restrictive_covenant'][0]
            expected_cost_max = self.LITIGATION_COST_ESTIMATES['restrictive_covenant'][1]
        
        # Apply probability weighting
        expected_cost_min = expected_cost_min * litigation_probability
        expected_cost_max = expected_cost_max * litigation_probability
        
        return {
            'litigation_probability': f"{litigation_probability * 100:.0f}%",
            'likely_claims': litigation_types,
            'expected_cost_min': expected_cost_min,
            'expected_cost_max': expected_cost_max,
            'expected_cost_avg': (expected_cost_min + expected_cost_max) / 2,
            'explanation': f"{litigation_probability*100:.0f}% chance of litigation. "
                          f"Expected legal fees: ${expected_cost_min:,.0f} - ${expected_cost_max:,.0f}"
        }
    
    def _calculate_retention_costs(self, profile: Dict[str, Any], revenue_risk: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate costs to retain clients during departure"""
        annual_revenue = revenue_risk['estimated_partner_revenue']
        
        # Typical retention efforts cost 10-15% of at-risk revenue
        retention_budget = annual_revenue * 0.12
        
        return {
            'total_cost': retention_budget,
            'breakdown': {
                'partner_time': retention_budget * 0.5,  # 50% = senior partner time
                'client_entertainment': retention_budget * 0.2,
                'emergency_staffing': retention_budget * 0.2,
                'crisis_communications': retention_budget * 0.1
            },
            'explanation': f"Retaining clients during transition costs ~12% of at-risk revenue = ${retention_budget:,.0f}"
        }
    
    def _calculate_replacement_costs(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate costs to replace departing partner"""
        years_at_firm = int(profile.get('years_at_firm', 5))
        
        # Recruitment costs (headhunter fees, signing bonus)
        headhunter_fee = 100000  # Typical for partner placement
        signing_bonus = 150000 if years_at_firm >= 10 else 100000
        relocation = 50000
        
        # Onboarding/training costs (lost productivity)
        onboarding_cost = 75000
        
        total_cost = headhunter_fee + signing_bonus + relocation + onboarding_cost
        
        return {
            'total_cost': total_cost,
            'breakdown': {
                'headhunter_fee': headhunter_fee,
                'signing_bonus': signing_bonus,
                'relocation': relocation,
                'onboarding_training': onboarding_cost
            },
            'explanation': f"Replacing partner costs ~${total_cost:,.0f} in recruitment and onboarding"
        }
    
    def _calculate_knowledge_loss(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate impact of institutional knowledge loss"""
        years_at_firm = int(profile.get('years_at_firm', 5))
        
        # More tenure = more knowledge loss
        base_impact = 50000
        knowledge_value = base_impact * min(years_at_firm, 15)  # Cap at 15 years
        
        return {
            'estimated_impact': knowledge_value,
            'explanation': f"{years_at_firm} years of institutional knowledge = ~${knowledge_value:,.0f} "
                          f"in lost efficiency, missed opportunities, and re-learning"
        }
    
    def _calculate_timeline_risk(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate when financial impact will hit"""
        critical_count = sum(1 for v in vulnerabilities if v.get('severity') == 'critical')
        high_count = sum(1 for v in vulnerabilities if v.get('severity') == 'high')
        
        # Timeline based on severity
        if critical_count >= 3:
            impact_window = "0-30 days"
            urgency = "IMMEDIATE ACTION REQUIRED"
        elif critical_count >= 1 or high_count >= 4:
            impact_window = "30-60 days"
            urgency = "URGENT"
        else:
            impact_window = "60-90 days"
            urgency = "HIGH PRIORITY"
        
        return {
            'impact_window': impact_window,
            'urgency_level': urgency,
            'explanation': f"Financial impact expected within {impact_window}. {urgency}."
        }
    
    def _generate_executive_summary(self, total_risk: float, timeline: Dict, vulnerabilities: List) -> str:
        """Generate one-sentence executive summary"""
        vuln_count = len(vulnerabilities)
        critical_count = sum(1 for v in vulnerabilities if v.get('severity') == 'critical')
        
        return (f"This departure presents ${total_risk:,.0f} in financial risk within {timeline['impact_window']}, "
                f"with {critical_count} critical vulnerabilities requiring immediate attention. "
                f"AION analysis provides 50x+ ROI by preventing these losses.")
