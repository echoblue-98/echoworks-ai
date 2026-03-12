"""
Pattern Matching Engine

Compares current attorney departure scenarios against historical patterns
in legal_patterns.json to identify similar cases and recommend countermeasures.

This is AION's proprietary moat - competitors can't access this validated case database.
"""

import json
import os
from typing import Dict, List, Any, Tuple
from pathlib import Path


class PatternMatcher:
    """
    Loads historical legal patterns and matches them to current scenarios.
    Returns similarity scores and actionable recommendations based on validated cases.
    """
    
    def __init__(self):
        self.patterns = []
        self.patterns_file = Path(__file__).parent.parent / "knowledge" / "legal_patterns.json"
        self._load_patterns()
    
    def _load_patterns(self):
        """Load historical patterns from legal_patterns.json"""
        if not self.patterns_file.exists():
            print(f"[Pattern Matcher] Warning: {self.patterns_file} not found")
            return
        
        try:
            with open(self.patterns_file, 'r') as f:
                data = json.load(f)
                self.patterns = data.get('patterns', [])
                print(f"[Pattern Matcher] Loaded {len(self.patterns)} historical patterns")
        except Exception as e:
            print(f"[Pattern Matcher] Error loading patterns: {e}")
    
    def match_scenario(self, attorney_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Match current scenario against historical patterns.
        
        Args:
            attorney_profile: Current departing attorney details
            
        Returns:
            List of matched patterns with similarity scores and recommendations
        """
        if not self.patterns:
            return []
        
        matched_patterns = []
        
        for pattern in self.patterns:
            similarity_score = self._calculate_similarity(attorney_profile, pattern)
            
            if similarity_score > 0.3:  # 30% threshold
                matched_patterns.append({
                    'pattern_id': pattern.get('id'),
                    'case_name': pattern.get('case_name'),
                    'similarity_score': similarity_score,
                    'matched_attributes': self._get_matched_attributes(attorney_profile, pattern),
                    'vulnerability_type': pattern.get('vulnerability_type'),
                    'what_was_missed': pattern.get('what_was_missed'),
                    'real_outcome': pattern.get('real_outcome'),
                    'defense_strategy': pattern.get('defense_strategy'),
                    'financial_impact': pattern.get('financial_impact'),
                    'lessons_learned': pattern.get('lessons_learned', [])
                })
        
        # Sort by similarity score (highest first)
        matched_patterns.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return matched_patterns
    
    def _calculate_similarity(self, profile: Dict[str, Any], pattern: Dict[str, Any]) -> float:
        """
        Calculate similarity score between current scenario and historical pattern.
        
        Scoring factors:
        - Industry match (0.3 weight)
        - Practice area match (0.2 weight)
        - Years of tenure similarity (0.15 weight)
        - Destination type (competitor vs startup vs unknown) (0.15 weight)
        - Access level similarity (0.1 weight)
        - Keyword overlap (0.1 weight)
        """
        score = 0.0
        max_score = 1.0
        
        # Industry match (advertising, law firm, consulting, etc.)
        profile_industry = self._infer_industry(profile)
        pattern_industry = pattern.get('industry', '').lower()
        
        if profile_industry == pattern_industry:
            score += 0.3
        elif profile_industry and pattern_industry and \
             any(word in pattern_industry for word in profile_industry.split()):
            score += 0.15
        
        # Practice area / role match
        profile_practice = profile.get('practice_area', '').lower()
        pattern_keywords = [k.lower() for k in pattern.get('keywords', [])]
        
        if profile_practice and any(profile_practice in keyword for keyword in pattern_keywords):
            score += 0.2
        
        # Years of tenure similarity
        profile_years = int(profile.get('years_at_firm', 0))
        pattern_duration = pattern.get('litigation_duration_months', 0)
        
        # More years = higher risk (institutional knowledge)
        if profile_years >= 10:
            score += 0.15
        elif profile_years >= 5:
            score += 0.1
        elif profile_years >= 2:
            score += 0.05
        
        # Destination type (competitor is highest risk)
        destination = profile.get('destination_firm', '').lower()
        if 'competitor' in destination or 'direct competitor' in destination:
            score += 0.15
        elif destination and destination != 'unknown':
            score += 0.075
        
        # Access level (more access = more risk)
        access = profile.get('system_access', '').lower()
        high_risk_systems = ['full', 'document management', 'billing', 'client portal', 'email']
        access_count = sum(1 for sys in high_risk_systems if sys in access)
        
        if access_count >= 4:
            score += 0.1
        elif access_count >= 2:
            score += 0.05
        
        # Keyword overlap
        profile_text = f"{profile.get('practice_area', '')} {profile.get('active_cases', '')} " \
                      f"{profile.get('client_relationships', '')}".lower()
        
        keyword_matches = sum(1 for keyword in pattern_keywords if keyword in profile_text)
        if keyword_matches > 0:
            score += min(0.1, keyword_matches * 0.025)
        
        return min(score, max_score)
    
    def _infer_industry(self, profile: Dict[str, Any]) -> str:
        """Infer industry from profile context"""
        practice = profile.get('practice_area', '').lower()
        
        # Law firm indicators
        if any(term in practice for term in ['intellectual property', 'litigation', 'corporate', 'm&a', 
                                              'patent', 'trademark', 'employment law']):
            return 'law firm'
        
        # Advertising/Marketing indicators
        if any(term in practice for term in ['advertising', 'marketing', 'creative', 'media', 'brand']):
            return 'advertising'
        
        # Consulting indicators
        if any(term in practice for term in ['consulting', 'advisory', 'strategy', 'management']):
            return 'consulting'
        
        return 'professional services'
    
    def _get_matched_attributes(self, profile: Dict[str, Any], pattern: Dict[str, Any]) -> List[str]:
        """Get list of specific attributes that matched between scenario and pattern"""
        matches = []
        
        profile_industry = self._infer_industry(profile)
        pattern_industry = pattern.get('industry', '').lower()
        
        if profile_industry == pattern_industry:
            matches.append(f"Industry: {profile_industry}")
        
        profile_practice = profile.get('practice_area', '').lower()
        pattern_keywords = pattern.get('keywords', [])
        
        for keyword in pattern_keywords:
            if keyword.lower() in profile_practice:
                matches.append(f"Practice area: {keyword}")
        
        destination = profile.get('destination_firm', '').lower()
        if 'competitor' in destination:
            matches.append("Destination: Direct competitor (highest risk)")
        
        profile_years = int(profile.get('years_at_firm', 0))
        if profile_years >= 10:
            matches.append(f"Tenure: {profile_years} years (high institutional knowledge risk)")
        
        return matches
    
    def generate_recommendations(self, matched_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate actionable recommendations based on matched patterns.
        
        Returns:
            Dictionary with prioritized actions, forensic audit checklist, and expected outcomes
        """
        if not matched_patterns:
            return {
                'pattern_match_found': False,
                'message': 'No historical patterns match this scenario. Proceeding with standard adversarial analysis.'
            }
        
        top_match = matched_patterns[0]
        
        recommendations = {
            'pattern_match_found': True,
            'similar_case': {
                'name': top_match['case_name'],
                'similarity': f"{top_match['similarity_score'] * 100:.0f}%",
                'outcome': top_match['real_outcome']
            },
            'what_firms_miss': top_match['what_was_missed'],
            'priority_actions': self._extract_actions(matched_patterns),
            'expected_impact': top_match.get('financial_impact', 'Unknown'),
            'lessons_from_history': top_match.get('lessons_learned', []),
            'defense_strategy': top_match.get('defense_strategy'),
            'pattern_count': len(matched_patterns)
        }
        
        return recommendations
    
    def _extract_actions(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Extract prioritized action items from matched patterns"""
        actions = []
        
        # Collect unique defense strategies from all matched patterns
        for pattern in patterns[:3]:  # Top 3 matches only
            strategy = pattern.get('defense_strategy')
            if strategy and strategy not in actions:
                actions.append(strategy)
        
        # Add generic high-priority actions based on pattern type
        for pattern in patterns[:3]:
            vuln_type = pattern.get('vulnerability_type', '').lower()
            
            if 'departure' in vuln_type or 'employee' in vuln_type:
                actions.extend([
                    "IMMEDIATE: Audit all system access logs (past 30 days)",
                    "IMMEDIATE: Check cloud storage sync settings (Dropbox, OneDrive, Google Drive)",
                    "URGENT: Review email forwarding rules and auto-forward settings",
                    "URGENT: Disable VPN access outside normal business hours",
                    "HIGH: Monitor printer logs for bulk document printing",
                    "HIGH: Implement data loss prevention (DLP) software before departure date"
                ])
                break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_actions = []
        for action in actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)
        
        return unique_actions[:8]  # Top 8 priority actions
