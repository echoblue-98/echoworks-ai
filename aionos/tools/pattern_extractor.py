"""
AION OS - Departure Pattern Extractor
Processes real departure documents and extracts validated patterns for the proprietary database.

This tool ingests:
- Court documents (complaints, settlements, TRO filings)
- News articles (Law360, AmLaw, Above The Law)
- Academic research papers
- Industry reports

And outputs structured patterns for legal_patterns.json
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class VulnerabilityDetail:
    """A specific security vulnerability identified in a departure case."""
    vulnerability: str
    detection_window: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    exploitation: str


@dataclass
class DeparturePattern:
    """Structured pattern extracted from a real departure case."""
    id: str
    case_name: str
    case_number: Optional[str]
    date_filed: Optional[str]
    date_terminated: Optional[str]
    litigation_duration_months: Optional[int]
    vulnerability_type: str
    industry: str
    attorney_profile: Dict[str, str]
    what_was_missed: str
    why_dangerous: str
    attack_vector: str
    defense_strategy: str
    real_outcome: str
    financial_impact: Dict[str, int]
    vulnerabilities_identified: List[Dict[str, str]]
    timeline: Dict[str, str]
    lessons_learned: List[str]
    aion_application: str
    keywords: List[str]
    status: str
    notes: str
    extracted_date: str
    source_type: str  # COURT_DOCUMENT, NEWS_ARTICLE, ACADEMIC, COMPOSITE
    source_url: Optional[str]
    confidence_score: float  # 0.0-1.0, how validated is this pattern


class PatternExtractor:
    """Extracts structured departure patterns from raw documents."""
    
    def __init__(self, gemini_client=None):
        """Initialize with optional Gemini client for AI-assisted extraction."""
        self.gemini_client = gemini_client
        self.patterns_file = Path(__file__).parent.parent / "knowledge" / "legal_patterns.json"
    
    def extract_from_text(self, raw_text: str, source_type: str = "NEWS_ARTICLE", 
                         source_url: Optional[str] = None) -> Optional[DeparturePattern]:
        """
        Extract structured pattern from raw text using AI.
        
        Args:
            raw_text: The raw document text (article, complaint, etc.)
            source_type: COURT_DOCUMENT, NEWS_ARTICLE, ACADEMIC, COMPOSITE
            source_url: Original source URL if available
            
        Returns:
            DeparturePattern object or None if extraction fails
        """
        if not self.gemini_client:
            raise ValueError("Gemini client required for AI extraction. Initialize with gemini_client.")
        
        extraction_prompt = f"""
You are a legal intelligence analyst extracting attorney departure patterns from real cases.

DOCUMENT TO ANALYZE:
{raw_text}

EXTRACT THE FOLLOWING (mark as UNKNOWN if not present):

1. CASE IDENTIFICATION:
   - Case name (e.g., "Smith v. Jones & Associates")
   - Case number (if available)
   - Date filed and terminated
   - Litigation duration in months

2. ATTORNEY PROFILE:
   - Title (Partner, Senior Partner, etc.)
   - Practice area
   - Years at firm
   - System access level
   - Destination firm

3. WHAT WAS MISSED (Pre-Departure Red Flags):
   - Specific actions/data access patterns that should have been flagged
   - Timeline: X days before notice, Y was detected
   - Be SPECIFIC: "Email forwarding configured 52 days before notice"

4. ATTACK VECTOR (How the Theft Happened):
   - Step-by-step timeline of data exfiltration
   - Methods used (email forwarding, cloud sync, printing, etc.)
   - What data was taken

5. FINANCIAL IMPACT:
   - Litigation costs
   - Settlement amount (if any)
   - Lost annual revenue
   - Number of client defections
   - Total financial impact

6. VULNERABILITIES (List 3-5):
   For each: vulnerability description, detection window, severity (CRITICAL/HIGH/MEDIUM/LOW), how it was exploited

7. LESSONS LEARNED:
   - 3-5 key takeaways for AION's pattern database

8. KEYWORDS:
   - 5-10 relevant keywords

Return ONLY valid JSON matching this structure:
{{
    "case_name": "...",
    "case_number": "...",
    "date_filed": "YYYY-MM-DD or UNKNOWN",
    "date_terminated": "YYYY-MM-DD or UNKNOWN",
    "litigation_duration_months": 0,
    "vulnerability_type": "Attorney Departure - [Practice Area]",
    "industry": "Law Firm - [Type]",
    "attorney_profile": {{
        "title": "...",
        "practice_area": "...",
        "years_at_firm": 0,
        "system_access": "...",
        "destination": "..."
    }},
    "what_was_missed": "...",
    "why_dangerous": "...",
    "attack_vector": "...",
    "defense_strategy": "...",
    "real_outcome": "...",
    "financial_impact": {{
        "litigation_cost": 0,
        "settlement_paid": 0,
        "lost_annual_revenue": 0,
        "client_defections": 0,
        "total_financial_impact": 0
    }},
    "vulnerabilities_identified": [
        {{
            "vulnerability": "...",
            "detection_window": "...",
            "severity": "CRITICAL",
            "exploitation": "..."
        }}
    ],
    "timeline": {{
        "recruitment_begins": "...",
        "first_suspicious_activity": "...",
        "notice_given": "...",
        "departure_effective": "...",
        "litigation_filed": "..."
    }},
    "lessons_learned": ["...", "...", "..."],
    "keywords": ["...", "...", "..."]
}}

CRITICAL: Return ONLY the JSON object, no markdown formatting, no explanations.
If critical information is missing, mark as "UNKNOWN" but still extract what you can.
"""
        
        try:
            # Single Gemini call with the structured extraction prompt
            # (previously made two calls — the analyze() call was redundant)
            import requests
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "contents": [{
                    "parts": [{"text": extraction_prompt}]
                }]
            }
            
            api_response = requests.post(
                f"{api_url}?key={self.gemini_client.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            api_response.raise_for_status()
            
            response_data = api_response.json()
            response_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            extracted_json = response_text.strip()
            
            # Remove markdown formatting if present
            if extracted_json.startswith("```json"):
                extracted_json = extracted_json.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            pattern_data = json.loads(extracted_json)
            
            # Generate pattern ID
            pattern_id = self._generate_pattern_id(pattern_data.get("case_name", "unknown"))
            
            # Build pattern object
            pattern = DeparturePattern(
                id=pattern_id,
                case_name=pattern_data.get("case_name", "UNKNOWN"),
                case_number=pattern_data.get("case_number"),
                date_filed=pattern_data.get("date_filed"),
                date_terminated=pattern_data.get("date_terminated"),
                litigation_duration_months=pattern_data.get("litigation_duration_months"),
                vulnerability_type=pattern_data.get("vulnerability_type", "Attorney Departure"),
                industry=pattern_data.get("industry", "Law Firm"),
                attorney_profile=pattern_data.get("attorney_profile", {}),
                what_was_missed=pattern_data.get("what_was_missed", ""),
                why_dangerous=pattern_data.get("why_dangerous", ""),
                attack_vector=pattern_data.get("attack_vector", ""),
                defense_strategy=pattern_data.get("defense_strategy", ""),
                real_outcome=pattern_data.get("real_outcome", ""),
                financial_impact=pattern_data.get("financial_impact", {}),
                vulnerabilities_identified=pattern_data.get("vulnerabilities_identified", []),
                timeline=pattern_data.get("timeline", {}),
                lessons_learned=pattern_data.get("lessons_learned", []),
                aion_application=self._generate_aion_application(pattern_data),
                keywords=pattern_data.get("keywords", []),
                status="EXTRACTED",
                notes=f"Extracted from {source_type} on {datetime.now().strftime('%Y-%m-%d')}",
                extracted_date=datetime.now().isoformat(),
                source_type=source_type,
                source_url=source_url,
                confidence_score=self._calculate_confidence(pattern_data)
            )
            
            return pattern
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Response: {extracted_json[:500]}")
            return None
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return None
    
    def _generate_pattern_id(self, case_name: str) -> str:
        """Generate unique pattern ID from case name."""
        # Sanitize case name for ID
        sanitized = case_name.lower().replace(" ", "_").replace(".", "")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"pattern_{sanitized[:30]}_{timestamp}"
    
    def _generate_aion_application(self, pattern_data: Dict) -> str:
        """Generate AION application guidance from pattern data."""
        practice = pattern_data.get("attorney_profile", {}).get("practice_area", "legal")
        vulnerabilities = pattern_data.get("vulnerabilities_identified", [])
        
        vuln_list = ", ".join([f"({i+1}) {v['vulnerability']}" 
                               for i, v in enumerate(vulnerabilities[:5])])
        
        return (f"When analyzing {practice} departures, AION should flag: {vuln_list}. "
                f"Priority monitoring windows identified in this pattern: "
                f"{pattern_data.get('timeline', {}).get('first_suspicious_activity', 'pre-notice period')}.")
    
    def _calculate_confidence(self, pattern_data: Dict) -> float:
        """Calculate confidence score based on data completeness."""
        required_fields = [
            "case_name", "what_was_missed", "attack_vector", 
            "vulnerabilities_identified", "financial_impact"
        ]
        
        score = 0.0
        for field in required_fields:
            value = pattern_data.get(field)
            if value and value != "UNKNOWN":
                if isinstance(value, list) and len(value) > 0:
                    score += 0.2
                elif isinstance(value, dict) and len(value) > 0:
                    score += 0.2
                elif isinstance(value, str) and len(value) > 20:
                    score += 0.2
        
        return min(score, 1.0)
    
    def save_pattern(self, pattern: DeparturePattern) -> bool:
        """Save pattern to legal_patterns.json database."""
        try:
            # Load existing patterns
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {"patterns": []}
            
            # Convert pattern to dict
            pattern_dict = asdict(pattern)
            
            # Check for duplicates
            existing_ids = [p.get("id") for p in data["patterns"]]
            if pattern.id in existing_ids:
                print(f"⚠️  Pattern {pattern.id} already exists. Skipping.")
                return False
            
            # Add pattern
            data["patterns"].append(pattern_dict)
            
            # Save
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Pattern saved: {pattern.id}")
            print(f"   Case: {pattern.case_name}")
            print(f"   Confidence: {pattern.confidence_score:.1%}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save pattern: {e}")
            return False
    
    def extract_and_save(self, raw_text: str, source_type: str = "NEWS_ARTICLE",
                        source_url: Optional[str] = None) -> bool:
        """Extract pattern from text and immediately save to database."""
        pattern = self.extract_from_text(raw_text, source_type, source_url)
        if pattern:
            return self.save_pattern(pattern)
        return False
    
    def list_patterns(self) -> List[Dict]:
        """List all patterns in database with summary info."""
        if not self.patterns_file.exists():
            return []
        
        with open(self.patterns_file, 'r') as f:
            data = json.load(f)
        
        return [
            {
                "id": p["id"],
                "case_name": p["case_name"],
                "status": p.get("status", "UNKNOWN"),
                "confidence": p.get("confidence_score", 0.0),
                "source_type": p.get("source_type", "UNKNOWN"),
                "extracted_date": p.get("extracted_date", "UNKNOWN")
            }
            for p in data.get("patterns", [])
        ]


def main():
    """Example usage."""
    from aionos.api.gemini_client import GeminiClient
    
    # Initialize
    gemini = GeminiClient()
    extractor = PatternExtractor(gemini_client=gemini.model)
    
    # Example: Extract from text
    sample_article = """
    Law360 - January 2025
    
    Senior IP partner Margaret Chen departed Wilson & Associates after 18 years 
    to join competitor Morrison LLP. Sources indicate Chen took 12 major clients 
    with her, representing approximately $4.2M in annual billings.
    
    Court documents filed last week show Wilson is seeking a TRO, alleging Chen 
    configured email forwarding rules 45 days before giving notice and downloaded 
    extensive client files to personal cloud storage.
    
    The case (Wilson & Associates v. Chen, Case No. 2024-CV-9832) highlights 
    increasing concerns about partner departures in IP practices, where client 
    relationships are highly personal and portable.
    """
    
    print("🔍 Extracting pattern from sample article...")
    pattern = extractor.extract_from_text(
        sample_article, 
        source_type="NEWS_ARTICLE",
        source_url="https://law360.com/example"
    )
    
    if pattern:
        print(f"\n✅ Pattern extracted: {pattern.id}")
        print(f"   Confidence: {pattern.confidence_score:.1%}")
        print(f"   Vulnerabilities: {len(pattern.vulnerabilities_identified)}")


if __name__ == "__main__":
    main()
