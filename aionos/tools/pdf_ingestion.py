"""
AION OS - Secure PDF Ingestion
100% LOCAL - Zero Cloud - Zero API Calls

Ingests court documents, complaints, and legal filings into the local pattern database.
All processing happens on YOUR machine. Nothing leaves your environment.

Usage:
    python -m aionos.tools.pdf_ingestion "path/to/complaint.pdf"
    python -m aionos.tools.pdf_ingestion "path/to/complaint.pdf" --output summary.json
"""

import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import logging

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  Install PyMuPDF: pip install pymupdf")

logger = logging.getLogger(__name__)


@dataclass
class CourtDocument:
    """Extracted court document data - stored 100% locally."""
    document_id: str
    file_hash: str
    case_name: str
    case_number: str
    court: str
    date_filed: Optional[str]
    document_type: str  # Complaint, Answer, Motion, etc.
    
    # Parties
    plaintiff: str
    defendant: str
    plaintiff_counsel: Optional[str]
    defendant_counsel: Optional[str]
    
    # Claims
    claims: List[str]
    damages_sought: Optional[str]
    jury_demand: bool
    
    # Timeline
    key_dates: List[Dict[str, str]]
    
    # Allegations
    allegations: List[str]
    
    # For pattern extraction
    vulnerabilities_mentioned: List[str]
    attack_vectors: List[str]
    
    # Metadata
    page_count: int
    extracted_date: str
    source_file: str
    

class SecurePDFIngestion:
    """
    100% LOCAL PDF ingestion.
    
    Security Guarantees:
    - No cloud APIs called
    - No data sent anywhere
    - All processing on local machine
    - File hash for integrity verification
    """
    
    def __init__(self):
        if not PDF_AVAILABLE:
            raise ImportError("PyMuPDF required. Run: pip install pymupdf")
        
        self.knowledge_dir = Path(__file__).parent.parent / "knowledge"
        self.patterns_file = self.knowledge_dir / "legal_patterns.json"
        self.documents_file = self.knowledge_dir / "court_documents.json"
        
        # Vulnerability keywords to extract
        self.vulnerability_patterns = {
            "vpn_abuse": [
                r"vpn", r"remote access", r"virtual private network",
                r"unauthorized access", r"login remotely", r"remote login"
            ],
            "database_theft": [
                r"database", r"client list", r"customer list", r"contact list",
                r"client database", r"proprietary data", r"trade secret",
                r"confidential information", r"business records"
            ],
            "credential_abuse": [
                r"password", r"credential", r"login", r"access code",
                r"authentication", r"unauthorized use"
            ],
            "data_exfiltration": [
                r"download", r"copy", r"transfer", r"exfiltrat",
                r"took", r"stole", r"misappropriat", r"convert"
            ],
            "email_forwarding": [
                r"email", r"forward", r"bcc", r"personal email",
                r"gmail", r"yahoo", r"hotmail"
            ],
            "client_solicitation": [
                r"solicit", r"contact", r"client", r"customer",
                r"relationship", r"poach", r"induce"
            ]
        }
        
        # Claim patterns
        self.claim_patterns = [
            r"computer fraud",
            r"cfaa",  # Computer Fraud and Abuse Act
            r"misappropriation",
            r"trade secret",
            r"breach of contract",
            r"breach of fiduciary",
            r"tortious interference",
            r"unfair competition",
            r"conversion",
            r"unjust enrichment",
            r"civil conspiracy",
            r"lanham act"
        ]

    def _hash_file(self, file_path: Path) -> str:
        """Create SHA-256 hash of file for integrity."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]

    def _extract_text(self, pdf_path: Path) -> tuple[str, int]:
        """Extract text from PDF using PyMuPDF (100% local)."""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        page_count = len(doc)
        doc.close()
        return text, page_count

    def _extract_case_name(self, text: str) -> tuple[str, str, str]:
        """Extract case name, plaintiff, defendant."""
        # Pattern: "PLAINTIFF v. DEFENDANT" or "PLAINTIFF vs. DEFENDANT"
        patterns = [
            r"([A-Z][A-Z\s,\.\&]+(?:LLC|INC|CORP|LLP|LP|PC)?)\s*[,\s]*(?:Plaintiff|PLAINTIFF)[,\s]*v[s]?\.?\s*([A-Z][A-Z\s,\.\&]+(?:LLC|INC|CORP|LLP|LP|PC)?)\s*[,\s]*(?:Defendant|DEFENDANT)",
            r"([A-Z][A-Za-z\s,\.\&]+)\s+v\.?\s+([A-Z][A-Za-z\s,\.\&]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                plaintiff = match.group(1).strip()
                defendant = match.group(2).strip()
                case_name = f"{plaintiff} v. {defendant}"
                return case_name, plaintiff, defendant
        
        return "Unknown Case", "Unknown Plaintiff", "Unknown Defendant"

    def _extract_case_number(self, text: str) -> str:
        """Extract case number."""
        patterns = [
            r"(?:Case\s*(?:No\.?|Number)?:?\s*)(\d+[:-]cv[:-]\d+)",
            r"(?:No\.?\s*)(\d+[:-]cv[:-]\d+)",
            r"(\d+[:-]cv[:-]\d+(?:[:-][A-Z]+)?)",
            r"(\d+:\d+[:-]cv[:-]\d+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"

    def _extract_court(self, text: str) -> str:
        """Extract court name."""
        patterns = [
            r"(?:IN THE\s+)?(UNITED STATES DISTRICT COURT[^)]+(?:DISTRICT OF [A-Z]+))",
            r"(DISTRICT COURT[^)]+)",
            r"(?:Filed in\s+)?([A-Z][a-z]+\s+District\s+Court)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Court"

    def _extract_date_filed(self, text: str) -> Optional[str]:
        """Extract filing date."""
        patterns = [
            r"(?:Filed|FILED)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(?:Filed|FILED)[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(?:Filed|FILED)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None

    def _extract_claims(self, text: str) -> List[str]:
        """Extract legal claims from complaint."""
        claims = []
        text_lower = text.lower()
        
        for claim in self.claim_patterns:
            if re.search(claim, text_lower):
                claims.append(claim.upper().replace(r"\s", " "))
        
        # Also look for numbered counts
        count_pattern = r"(?:COUNT|CLAIM)\s+(?:I{1,3}|IV|V|VI|VII|VIII|IX|X|\d+)[:\s]+([A-Za-z\s]+?)(?:\n|$)"
        for match in re.finditer(count_pattern, text, re.IGNORECASE):
            claim = match.group(1).strip()
            if len(claim) > 5 and len(claim) < 100:
                claims.append(claim)
        
        return list(set(claims))

    def _extract_damages(self, text: str) -> Optional[str]:
        """Extract damages sought."""
        patterns = [
            r"(?:damages|PRAY).*?(\$[\d,]+(?:\.\d{2})?)",
            r"(?:not less than|exceeding|excess of)\s+(\$[\d,]+)",
            r"(\$[\d,]+(?:\s*million)?)\s+(?:in\s+)?damages",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def _extract_jury_demand(self, text: str) -> bool:
        """Check for jury demand."""
        return bool(re.search(r"jury\s+(?:demand|trial)", text, re.IGNORECASE))

    def _extract_key_dates(self, text: str) -> List[Dict[str, str]]:
        """Extract key dates mentioned in document."""
        dates = []
        
        # Pattern: Date followed by description
        date_patterns = [
            r"(?:on|On|ON)\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})[,\s]+([^.]+\.)",
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*[:-]?\s*([^.]+\.)",
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, text):
                event = match.group(2).strip()[:200]  # Limit length
                dates.append({
                    "date": match.group(1),
                    "event": event
                })
        
        return dates[:20]  # Limit to 20 dates

    def _extract_allegations(self, text: str) -> List[str]:
        """Extract numbered allegations."""
        allegations = []
        
        # Pattern: Numbered paragraphs
        pattern = r"(\d+)\.\s+([A-Z][^.]+(?:\.[^.]+)*\.)"
        
        for match in re.finditer(pattern, text):
            para_num = match.group(1)
            content = match.group(2).strip()
            if len(content) > 50 and len(content) < 1000:
                allegations.append(f"¶{para_num}: {content[:500]}")
        
        return allegations[:50]  # Limit to 50 allegations

    def _extract_vulnerabilities(self, text: str) -> List[str]:
        """Extract security vulnerabilities mentioned."""
        vulnerabilities = []
        text_lower = text.lower()
        
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    vulnerabilities.append(vuln_type)
                    break
        
        return list(set(vulnerabilities))

    def _extract_attack_vectors(self, text: str) -> List[str]:
        """Extract specific attack vectors described."""
        vectors = []
        text_lower = text.lower()
        
        # Look for specific attack descriptions
        attack_patterns = [
            (r"accessed.*?(?:database|system|network|server)", "System Access"),
            (r"download.*?(?:file|document|record|data)", "Data Download"),
            (r"forward.*?(?:email|message)", "Email Forwarding"),
            (r"(?:copy|copied|copying).*?(?:file|document|record|data)", "Data Copying"),
            (r"(?:stole|stolen|stealing).*?(?:data|information|file)", "Data Theft"),
            (r"vpn.*?(?:access|login|connect)", "VPN Access"),
            (r"remote.*?(?:access|login|connect)", "Remote Access"),
            (r"(?:usb|thumb drive|external drive)", "USB Device"),
            (r"personal.*?(?:email|device|account)", "Personal Device/Account"),
        ]
        
        for pattern, vector_name in attack_patterns:
            if re.search(pattern, text_lower):
                vectors.append(vector_name)
        
        return list(set(vectors))

    def ingest_pdf(self, pdf_path: str) -> CourtDocument:
        """
        Ingest a PDF court document into the local database.
        
        100% LOCAL - Zero cloud calls.
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")
        
        print(f"\n🔒 AION SECURE PDF INGESTION")
        print(f"   100% Local Processing - Zero Cloud")
        print(f"   ─────────────────────────────────")
        print(f"   📄 File: {pdf_path.name}")
        
        # Hash file for integrity
        file_hash = self._hash_file(pdf_path)
        print(f"   🔐 Hash: {file_hash}")
        
        # Extract text
        text, page_count = self._extract_text(pdf_path)
        print(f"   📖 Pages: {page_count}")
        print(f"   📝 Characters: {len(text):,}")
        
        # Extract all components
        case_name, plaintiff, defendant = self._extract_case_name(text)
        case_number = self._extract_case_number(text)
        court = self._extract_court(text)
        date_filed = self._extract_date_filed(text)
        claims = self._extract_claims(text)
        damages = self._extract_damages(text)
        jury_demand = self._extract_jury_demand(text)
        key_dates = self._extract_key_dates(text)
        allegations = self._extract_allegations(text)
        vulnerabilities = self._extract_vulnerabilities(text)
        attack_vectors = self._extract_attack_vectors(text)
        
        # Determine document type
        doc_type = "Complaint"
        if "amended complaint" in text.lower():
            doc_type = "Amended Complaint"
        elif "first amended" in text.lower():
            doc_type = "First Amended Complaint"
        elif "answer" in text.lower()[:500]:
            doc_type = "Answer"
        elif "motion" in text.lower()[:500]:
            doc_type = "Motion"
        
        # Generate document ID
        doc_id = f"doc_{file_hash}_{datetime.now().strftime('%Y%m%d')}"
        
        # Create document object
        document = CourtDocument(
            document_id=doc_id,
            file_hash=file_hash,
            case_name=case_name,
            case_number=case_number,
            court=court,
            date_filed=date_filed,
            document_type=doc_type,
            plaintiff=plaintiff,
            defendant=defendant,
            plaintiff_counsel=None,  # Could be extracted
            defendant_counsel=None,
            claims=claims,
            damages_sought=damages,
            jury_demand=jury_demand,
            key_dates=key_dates,
            allegations=allegations,
            vulnerabilities_mentioned=vulnerabilities,
            attack_vectors=attack_vectors,
            page_count=page_count,
            extracted_date=datetime.now().isoformat(),
            source_file=str(pdf_path.absolute())
        )
        
        # Print summary
        print(f"\n   ✅ EXTRACTION COMPLETE")
        print(f"   ─────────────────────────────────")
        print(f"   📋 Case: {case_name[:60]}")
        print(f"   📁 Number: {case_number}")
        print(f"   🏛️  Court: {court[:50]}")
        print(f"   📅 Filed: {date_filed or 'Unknown'}")
        print(f"   ⚖️  Claims: {len(claims)}")
        print(f"   🔴 Vulnerabilities: {', '.join(vulnerabilities) or 'None detected'}")
        print(f"   🎯 Attack Vectors: {', '.join(attack_vectors) or 'None detected'}")
        print(f"   👥 Jury Demand: {'Yes' if jury_demand else 'No'}")
        
        return document

    def save_to_database(self, document: CourtDocument) -> bool:
        """Save document to local database."""
        # Ensure knowledge directory exists
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create documents database
        if self.documents_file.exists():
            with open(self.documents_file, 'r') as f:
                db = json.load(f)
        else:
            db = {"documents": [], "metadata": {"created": datetime.now().isoformat()}}
        
        # Add document
        db["documents"].append(asdict(document))
        db["metadata"]["last_updated"] = datetime.now().isoformat()
        db["metadata"]["document_count"] = len(db["documents"])
        
        # Save
        with open(self.documents_file, 'w') as f:
            json.dump(db, f, indent=2)
        
        print(f"\n   💾 SAVED TO LOCAL DATABASE")
        print(f"   📁 {self.documents_file}")
        print(f"   📊 Total Documents: {len(db['documents'])}")
        
        return True

    def create_pattern_from_document(self, document: CourtDocument) -> Dict[str, Any]:
        """Convert court document into a pattern for the pattern database."""
        
        pattern = {
            "id": f"pattern_{document.file_hash}",
            "case_name": document.case_name,
            "case_number": document.case_number,
            "date_filed": document.date_filed,
            "court": document.court,
            "document_type": document.document_type,
            "vulnerability_type": "Court Filing - " + ", ".join(document.vulnerabilities_mentioned),
            "industry": "Unknown - Pending Analysis",
            
            "what_was_missed": f"Case involves: {', '.join(document.attack_vectors)}. Claims filed: {', '.join(document.claims[:5])}",
            
            "why_dangerous": f"Litigation filed with {len(document.claims)} claims. Jury demand: {'Yes' if document.jury_demand else 'No'}. {len(document.allegations)} allegations documented.",
            
            "attack_vector": "; ".join(document.attack_vectors) if document.attack_vectors else "Details in court filing",
            
            "vulnerabilities_identified": [
                {
                    "vulnerability": v.replace("_", " ").title(),
                    "severity": "HIGH",
                    "source": "Court Filing"
                }
                for v in document.vulnerabilities_mentioned
            ],
            
            "key_dates": document.key_dates[:10],
            
            "claims": document.claims,
            
            "damages_sought": document.damages_sought,
            
            "status": "INGESTED_FROM_COURT_DOCUMENT",
            "confidence_score": 0.95,  # High confidence - it's a court document
            "extracted_date": document.extracted_date,
            "source_type": "COURT_DOCUMENT",
            "source_file_hash": document.file_hash
        }
        
        return pattern

    def add_to_pattern_database(self, pattern: Dict[str, Any]) -> bool:
        """Add pattern to the main pattern database."""
        
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                db = json.load(f)
        else:
            db = {"patterns": []}
        
        # Check for duplicates
        for existing in db["patterns"]:
            if existing.get("id") == pattern["id"]:
                print(f"\n   ⚠️  Pattern already exists: {pattern['id']}")
                return False
        
        # Add pattern
        db["patterns"].append(pattern)
        
        # Save
        with open(self.patterns_file, 'w') as f:
            json.dump(db, f, indent=2)
        
        print(f"\n   🎯 PATTERN ADDED TO DATABASE")
        print(f"   📁 {self.patterns_file}")
        print(f"   📊 Total Patterns: {len(db['patterns'])}")
        
        return True


def main():
    """Command-line interface for PDF ingestion."""
    import sys
    
    if len(sys.argv) < 2:
        print("\nUsage: python -m aionos.tools.pdf_ingestion <pdf_path>")
        print("\nExample:")
        print('  python -m aionos.tools.pdf_ingestion "path/to/complaint.pdf"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    ingestion = SecurePDFIngestion()
    
    # Ingest PDF
    document = ingestion.ingest_pdf(pdf_path)
    
    # Save to document database
    ingestion.save_to_database(document)
    
    # Create and add pattern
    pattern = ingestion.create_pattern_from_document(document)
    ingestion.add_to_pattern_database(pattern)
    
    print("\n" + "=" * 50)
    print("✅ INGESTION COMPLETE - 100% LOCAL")
    print("=" * 50)
    print("\n🔒 Data Privacy:")
    print("   • Zero API calls made")
    print("   • Zero cloud uploads")
    print("   • All data stored locally")
    print(f"   • Pattern database: {ingestion.patterns_file}")
    print(f"   • Document database: {ingestion.documents_file}")


if __name__ == "__main__":
    main()
