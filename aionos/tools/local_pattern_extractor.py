"""
AION OS - Local Pattern Extractor
100% LOCAL - Zero LLM dependency

Extracts departure patterns using rule-based NLP + regex patterns.
This is the AION way: proprietary, private, self-contained.
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


@dataclass
class ExtractedPattern:
    """Pattern extracted locally without LLM."""
    id: str
    case_name: str
    case_number: Optional[str]
    date_filed: Optional[str]
    practice_area: str
    attorney_name: str
    years_at_firm: Optional[int]
    destination_firm: Optional[str]
    clients_taken: Optional[int]
    revenue_at_risk: Optional[float]
    vulnerabilities: List[str]
    timeline_events: List[Dict[str, str]]
    keywords: List[str]
    status: str
    confidence_score: float
    extracted_date: str
    source_type: str
    raw_text_hash: str


class LocalPatternExtractor:
    """
    100% LOCAL pattern extraction - Zero LLM calls.
    
    Uses:
    - Regex patterns for entity extraction
    - Keyword matching for vulnerability detection
    - Rule-based timeline parsing
    - Heuristic confidence scoring
    """
    
    def __init__(self):
        self.patterns_file = Path(__file__).parent.parent / "knowledge" / "legal_patterns.json"
        
        # Vulnerability patterns to detect
        self.vulnerability_patterns = {
            "email_forwarding": [
                r"email forward", r"forwarding rule", r"auto-forward",
                r"forward.*personal", r"bcc.*personal"
            ],
            "cloud_sync": [
                r"cloud storage", r"dropbox", r"google drive", r"onedrive",
                r"personal.*cloud", r"sync.*personal", r"cloud sync"
            ],
            "data_download": [
                r"download", r"exfiltrat", r"data.*transfer",
                r"bulk.*access", r"mass.*download", r"copied.*files"
            ],
            "client_solicitation": [
                r"client.*contact", r"solicit", r"poach",
                r"client.*list", r"took.*clients", r"followed.*to"
            ],
            "after_hours_access": [
                r"after.?hours", r"weekend.*access", r"6.*am",
                r"late.*night", r"unusual.*hours"
            ],
            "printing": [
                r"print.*log", r"printed.*pages", r"print.*job",
                r"copier", r"physical.*document"
            ],
            "usb_device": [
                r"usb", r"thumb.*drive", r"external.*drive",
                r"removable.*media", r"flash.*drive"
            ],
            "tro_filed": [
                r"tro", r"temporary.*restraining", r"injunction",
                r"emergency.*motion", r"restraining.*order"
            ],
            "vpn_abuse": [
                r"vpn", r"remote.*access", r"tunnel", r"credential.*abuse",
                r"unauthorized.*access", r"remote.*login", r"accessed.*remotely"
            ],
            "database_theft": [
                r"database", r"sql", r"data.*export", r"bulk.*query",
                r"client.*database", r"customer.*database", r"crm.*access",
                r"stole.*database", r"copied.*database", r"database.*exfil"
            ],
            "credential_retention": [
                r"credential", r"password.*retained", r"login.*after",
                r"access.*after.*departure", r"former.*employee.*access",
                r"unauthorized.*login", r"still.*had.*access"
            ]
        }
        
        # Practice area patterns
        self.practice_patterns = {
            "M&A": [r"m&a", r"merger", r"acquisition", r"corporate", r"transaction"],
            "IP": [r"ip", r"intellectual.*property", r"patent", r"trademark", r"copyright"],
            "Litigation": [r"litigat", r"trial", r"court", r"lawsuit", r"dispute"],
            "Tax": [r"tax", r"irs", r"estate.*planning"],
            "Real Estate": [r"real.*estate", r"property", r"land.*use", r"zoning"],
            "Employment": [r"employment", r"labor", r"hr", r"workplace"],
            "Regulatory": [r"regulat", r"compliance", r"fda", r"sec"],
        }
    
    def extract_from_text(self, raw_text: str, source_type: str = "NEWS_ARTICLE") -> Optional[ExtractedPattern]:
        """
        Extract pattern from raw text using LOCAL rules only.
        
        Args:
            raw_text: The raw document text
            source_type: COURT_DOCUMENT, NEWS_ARTICLE, ACADEMIC
            
        Returns:
            ExtractedPattern object or None if extraction fails
        """
        text_lower = raw_text.lower()
        
        # Extract case name
        case_name = self._extract_case_name(raw_text)
        
        # Extract case number
        case_number = self._extract_case_number(raw_text)
        
        # Extract attorney info
        attorney_name = self._extract_attorney_name(raw_text)
        years = self._extract_years(raw_text)
        destination = self._extract_destination(raw_text)
        
        # Extract practice area
        practice_area = self._detect_practice_area(text_lower)
        
        # Extract financial info
        clients_taken, revenue = self._extract_financials(raw_text)
        
        # Detect vulnerabilities
        vulnerabilities = self._detect_vulnerabilities(text_lower)
        
        # Extract timeline events
        timeline = self._extract_timeline(raw_text)
        
        # Extract keywords
        keywords = self._extract_keywords(text_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            case_name, attorney_name, vulnerabilities, clients_taken, revenue
        )
        
        # Generate ID
        pattern_id = self._generate_id(case_name or attorney_name or "unknown")
        
        # Create pattern
        pattern = ExtractedPattern(
            id=pattern_id,
            case_name=case_name or "Unknown v. Unknown",
            case_number=case_number,
            date_filed=self._extract_date(raw_text),
            practice_area=practice_area,
            attorney_name=attorney_name or "Unknown Attorney",
            years_at_firm=years,
            destination_firm=destination,
            clients_taken=clients_taken,
            revenue_at_risk=revenue,
            vulnerabilities=vulnerabilities,
            timeline_events=timeline,
            keywords=keywords,
            status="EXTRACTED_LOCAL",
            confidence_score=confidence,
            extracted_date=datetime.now().isoformat(),
            source_type=source_type,
            raw_text_hash=str(hash(raw_text))[:16]
        )
        
        return pattern
    
    def _extract_case_name(self, text: str) -> Optional[str]:
        """Extract case name like 'Smith v. Jones'."""
        patterns = [
            r"([A-Z][a-z]+(?:\s+&\s+[A-Z][a-z]+)?(?:\s+(?:LLP|LLC|P\.?C\.?|Inc\.?))?)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"([A-Z][A-Za-z\s&]+)\s+(?:versus|vs\.?|v\.)\s+([A-Z][A-Za-z\s&]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return f"{match.group(1).strip()} v. {match.group(2).strip()}"
        return None
    
    def _extract_case_number(self, text: str) -> Optional[str]:
        """Extract case number like '2024-CV-9832'."""
        patterns = [
            r"(?:Case\s+(?:No\.?|Number)?\s*)?(\d{1,2}:\d{2}-cv-\d+)",
            r"(?:Case\s+(?:No\.?|Number)?\s*)?([\d]{4}-CV-[\d]+)",
            r"(?:Case\s+(?:No\.?|Number)?\s*)?([\d]{4}-cv-[\d]+)",
            r"\(([^)]*\d+.*?cv.*?\d+[^)]*)\)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_attorney_name(self, text: str) -> Optional[str]:
        """Extract departing attorney name."""
        patterns = [
            r"(?:partner|attorney|lawyer)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:departed|left|joined|leaving)",
            r"(?:Senior|Managing|Equity)\s+[Pp]artner\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_years(self, text: str) -> Optional[int]:
        """Extract years at firm."""
        patterns = [
            r"(\d+)\s+years?\s+(?:at|with|of)",
            r"after\s+(\d+)\s+years?",
            r"(\d+)-year\s+(?:tenure|career|stint)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None
    
    def _extract_destination(self, text: str) -> Optional[str]:
        """Extract destination firm."""
        patterns = [
            r"(?:join|joined|joining|to)\s+(?:competitor\s+)?([A-Z][a-zA-Z\s&]+(?:LLP|LLC|P\.?C\.?)?)",
            r"(?:moved|moving)\s+to\s+([A-Z][a-zA-Z\s&]+(?:LLP|LLC)?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                dest = match.group(1).strip()
                if len(dest) < 50:  # Sanity check
                    return dest
        return None
    
    def _detect_practice_area(self, text_lower: str) -> str:
        """Detect practice area from keywords."""
        for practice, patterns in self.practice_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return practice
        return "General Practice"
    
    def _extract_financials(self, text: str) -> Tuple[Optional[int], Optional[float]]:
        """Extract client count and revenue figures."""
        clients = None
        revenue = None
        
        # Client count
        client_patterns = [
            r"(\d+)\s+(?:major\s+)?clients?",
            r"took\s+(\d+)\s+clients?",
        ]
        for pattern in client_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                clients = int(match.group(1))
                break
        
        # Revenue
        revenue_patterns = [
            r"\$?([\d,.]+)\s*(?:M|million)\s*(?:in\s+)?(?:annual\s+)?(?:billings?|revenue)",
            r"\$?([\d,.]+)\s*(?:K|thousand)\s*(?:in\s+)?(?:annual\s+)?(?:billings?|revenue)",
            r"(?:billings?|revenue)\s+(?:of\s+)?\$?([\d,.]+)\s*(?:M|million)",
        ]
        for pattern in revenue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(",", ""))
                if "K" in text[match.start():match.end()].upper() or "thousand" in text[match.start():match.end()].lower():
                    value *= 1000
                else:
                    value *= 1000000  # Assume millions
                revenue = value
                break
        
        return clients, revenue
    
    def _detect_vulnerabilities(self, text_lower: str) -> List[str]:
        """Detect security vulnerabilities mentioned."""
        found = []
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    found.append(vuln_type)
                    break
        return list(set(found))
    
    def _extract_timeline(self, text: str) -> List[Dict[str, str]]:
        """Extract timeline events with days-before-notice markers."""
        events = []
        patterns = [
            (r"(\d+)\s+days?\s+before\s+(?:giving\s+)?notice", "pre_notice"),
            (r"(\d+)\s+days?\s+(?:before|prior)", "pre_event"),
            (r"(?:final|last)\s+(\d+)\s+days?", "final_days"),
            (r"(\d+)\s+weeks?\s+before", "pre_notice_weeks"),
        ]
        
        for pattern, event_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                days = int(match.group(1))
                if event_type == "pre_notice_weeks":
                    days *= 7
                
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                events.append({
                    "days_before": days,
                    "type": event_type,
                    "context": context
                })
        
        return sorted(events, key=lambda x: x["days_before"], reverse=True)
    
    def _extract_keywords(self, text_lower: str) -> List[str]:
        """Extract relevant keywords."""
        keyword_list = [
            "departure", "lateral", "partner", "attorney", "client",
            "theft", "data", "exfiltration", "tro", "injunction",
            "trade secret", "non-compete", "solicitation", "poaching"
        ]
        return [kw for kw in keyword_list if kw in text_lower]
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract filing or event date."""
        patterns = [
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
            r"\d{1,2}/\d{1,2}/\d{4}",
            r"\d{4}-\d{2}-\d{2}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _calculate_confidence(self, case_name, attorney_name, vulnerabilities, 
                             clients, revenue) -> float:
        """Calculate confidence score based on extracted data quality."""
        score = 0.0
        
        if case_name and "v." in case_name:
            score += 0.25
        if attorney_name:
            score += 0.15
        if vulnerabilities:
            score += min(len(vulnerabilities) * 0.1, 0.3)
        if clients:
            score += 0.15
        if revenue:
            score += 0.15
        
        return min(score, 1.0)
    
    def _generate_id(self, name: str) -> str:
        """Generate unique pattern ID."""
        sanitized = re.sub(r'[^a-z0-9]', '_', name.lower())[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"pattern_local_{sanitized}_{timestamp}"
    
    def save_pattern(self, pattern: ExtractedPattern) -> bool:
        """Save pattern to database."""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {"patterns": []}
            
            # Convert to dict format matching existing schema
            pattern_dict = {
                "id": pattern.id,
                "case_name": pattern.case_name,
                "case_number": pattern.case_number,
                "date_filed": pattern.date_filed,
                "vulnerability_type": f"Attorney Departure - {pattern.practice_area}",
                "industry": "Law Firm",
                "attorney_profile": {
                    "name": pattern.attorney_name,
                    "practice_area": pattern.practice_area,
                    "years_at_firm": pattern.years_at_firm,
                    "destination": pattern.destination_firm
                },
                "what_was_missed": ", ".join(pattern.vulnerabilities) if pattern.vulnerabilities else "UNKNOWN",
                "financial_impact": {
                    "clients_taken": pattern.clients_taken,
                    "revenue_at_risk": pattern.revenue_at_risk
                },
                "timeline": pattern.timeline_events,
                "keywords": pattern.keywords,
                "status": pattern.status,
                "confidence_score": pattern.confidence_score,
                "extracted_date": pattern.extracted_date,
                "source_type": pattern.source_type,
                "notes": "Extracted 100% locally - Zero LLM"
            }
            
            data["patterns"].append(pattern_dict)
            
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ Failed to save: {e}")
            return False
    
    def extract_and_save(self, raw_text: str, source_type: str = "NEWS_ARTICLE") -> bool:
        """Extract and immediately save pattern."""
        pattern = self.extract_from_text(raw_text, source_type)
        if pattern and pattern.confidence_score > 0.2:
            return self.save_pattern(pattern)
        return False


def main():
    """Test the local extractor."""
    extractor = LocalPatternExtractor()
    
    sample = """
    Law360 - January 2025
    
    Senior IP partner Margaret Chen departed Wilson & Associates after 18 years 
    to join competitor Morrison LLP. Sources indicate Chen took 12 major clients 
    with her, representing approximately $4.2M in annual billings.
    
    Court documents filed last week show Wilson is seeking a TRO, alleging Chen 
    configured email forwarding rules 45 days before giving notice and downloaded 
    extensive client files to personal cloud storage.
    
    The case (Wilson & Associates v. Chen, Case No. 2024-CV-9832) highlights 
    increasing concerns about partner departures in IP practices.
    """
    
    print("🔍 LOCAL Pattern Extraction (Zero LLM)")
    print("=" * 50)
    
    pattern = extractor.extract_from_text(sample)
    
    if pattern:
        print(f"✅ Case: {pattern.case_name}")
        print(f"   Attorney: {pattern.attorney_name}")
        print(f"   Practice: {pattern.practice_area}")
        print(f"   Years: {pattern.years_at_firm}")
        print(f"   Clients: {pattern.clients_taken}")
        print(f"   Revenue: ${pattern.revenue_at_risk:,.0f}" if pattern.revenue_at_risk else "   Revenue: Unknown")
        print(f"   Vulnerabilities: {pattern.vulnerabilities}")
        print(f"   Confidence: {pattern.confidence_score:.0%}")
        print(f"   Status: {pattern.status}")


if __name__ == "__main__":
    main()
