"""
AION OS - Document Intelligence Module
Multi-modal document extraction, analysis, and risk assessment for law firms.

Capabilities:
- Contract clause extraction and risk flagging
- Agreement term analysis (compensation, IP, perpetuity, waiver)
- Obligation mapping (who owes what to whom)
- Red flag detection (one-sided terms, waived rights, perpetuity clauses)
- Document versioning and diff tracking
- LLM-powered plain-language summaries

This is PROPRIETARY to AION OS / CodeTyphoons.
All document processing happens locally — zero data leaves the network.
"""

import json
import hashlib
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger("aionos.document_intelligence")


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class DocumentType(Enum):
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    NDA = "nda"
    ENGAGEMENT_LETTER = "engagement_letter"
    BRIEF = "brief"
    DEPOSITION = "deposition"
    SETTLEMENT = "settlement"
    EMPLOYMENT = "employment"
    RECORDING_AGREEMENT = "recording_agreement"
    IP_ASSIGNMENT = "ip_assignment"
    LICENSE = "license"
    OTHER = "other"


class RiskLevel(Enum):
    CRITICAL = "critical"    # Waived rights, perpetuity IP assignment, no compensation
    HIGH = "high"            # One-sided obligations, broad indemnity
    MEDIUM = "medium"        # Ambiguous terms, missing definitions
    LOW = "low"              # Minor formatting, standard boilerplate
    INFO = "info"            # Informational, no risk


class ClauseType(Enum):
    EXCLUSIVITY = "exclusivity"
    COMPENSATION = "compensation"
    IP_OWNERSHIP = "ip_ownership"
    IP_ASSIGNMENT = "ip_assignment"
    PERPETUITY = "perpetuity"
    WAIVER = "waiver"
    INDEMNIFICATION = "indemnification"
    TERMINATION = "termination"
    NON_COMPETE = "non_compete"
    CONFIDENTIALITY = "confidentiality"
    FORCE_MAJEURE = "force_majeure"
    GOVERNING_LAW = "governing_law"
    ARBITRATION = "arbitration"
    OBLIGATION = "obligation"
    GRANT_OF_RIGHTS = "grant_of_rights"
    PROMOTIONAL_LICENSE = "promotional_license"
    RECOUPMENT = "recoupment"
    WORK_FOR_HIRE = "work_for_hire"
    MATCHING_RIGHTS = "matching_rights"
    ROYALTY_DEDUCTION = "royalty_deduction"
    ENTIRE_AGREEMENT = "entire_agreement"
    MODIFICATION = "modification"
    ASSIGNMENT_RESTRICTION = "assignment_restriction"
    SUCCESSORS_HEIRS = "successors_heirs"
    OTHER = "other"


@dataclass
class ExtractedClause:
    """A single extracted clause from a document"""
    clause_type: ClauseType
    text: str
    summary: str
    risk_level: RiskLevel
    risk_reason: str
    parties_affected: List[str]
    obligations: List[str]
    section: str = ""
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DocumentAnalysis:
    """Full analysis result for a document"""
    document_id: str
    document_type: DocumentType
    title: str
    parties: List[str]
    date_analyzed: str
    clauses: List[ExtractedClause]
    overall_risk: RiskLevel
    risk_score: int  # 0-100
    summary: str
    red_flags: List[str]
    key_obligations: Dict[str, List[str]]  # party -> obligations
    recommendations: List[str]
    raw_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# CLAUSE DETECTION PATTERNS
# =============================================================================

# Keywords that signal specific clause types
CLAUSE_PATTERNS = {
    ClauseType.EXCLUSIVITY: {
        "keywords": ["exclusive right", "exclusively", "sole right", "sole and exclusive"],
        "risk_signals": ["perpetuity", "worldwide", "all purposes", "every kind"],
    },
    ClauseType.COMPENSATION: {
        "keywords": ["compensation", "payment", "royalt", "advance", "fee", "salary", "wage"],
        "risk_signals": ["limited to minimum", "waives any right", "no additional", "without any payment", "100% of the gross", "sole discretion", "no obligation to make any payment", "conditioned upon"],
    },
    ClauseType.IP_OWNERSHIP: {
        "keywords": ["property of", "shall own", "ownership", "copyright", "intellectual property", "master recording"],
        "risk_signals": ["in perpetuity", "throughout the world", "worldwide", "from inception", "work for hire"],
    },
    ClauseType.IP_ASSIGNMENT: {
        "keywords": ["all right, title and interest", "assigns", "transfer", "convey"],
        "risk_signals": ["irrevocable", "perpetuity", "from inception of creation"],
    },
    ClauseType.PERPETUITY: {
        "keywords": ["in perpetuity", "perpetuity", "forever", "in perpetuum", "permanent"],
        "risk_signals": ["worldwide", "irrevocable", "all rights"],
    },
    ClauseType.WAIVER: {
        "keywords": ["waives", "waiver", "relinquish", "forfeit", "give up", "surrender"],
        "risk_signals": ["any right", "all rights", "compensation", "to the extent"],
    },
    ClauseType.RECOUPMENT: {
        "keywords": ["recoup", "recoupable", "deemed advances", "deducted from", "offset against", "after deduction", "net money actually received"],
        "risk_signals": ["all costs", "all expenses", "any sums payable", "100% of the gross", "direct expenses", "overhead costs"],
    },
    ClauseType.OBLIGATION: {
        "keywords": ["shall procure", "shall be available", "agrees to", "shall provide", "required to"],
        "risk_signals": ["promptly", "irrevocable", "at request", "from time to time"],
    },
    ClauseType.GRANT_OF_RIGHTS: {
        "keywords": ["grants", "grant of rights", "license", "consent grants", "hereby grants"],
        "risk_signals": ["irrevocable", "any and all uses", "without any payment", "promotional"],
    },
    ClauseType.TERMINATION: {
        "keywords": ["terminate", "termination", "cancel", "expire", "end of term"],
        "risk_signals": ["at sole discretion", "without cause", "immediately"],
    },
    ClauseType.INDEMNIFICATION: {
        "keywords": ["indemnif", "hold harmless", "defend and indemnify", "shall indemnify"],
        "risk_signals": ["unlimited", "any and all claims", "sole expense", "any losses", "reasonable legal fees", "damages"],
    },
    ClauseType.MATCHING_RIGHTS: {
        "keywords": ["matching right", "first refusal", "right of first", "offers to enter into an agreement", "proposed agreement"],
        "risk_signals": ["1 day", "1-day", "within 1", "30%", "no person except", "not be authorized"],
    },
    ClauseType.ROYALTY_DEDUCTION: {
        "keywords": ["deducted from", "royalties shall be deducted", "royalties otherwise payable", "include any royalty obligations"],
        "risk_signals": ["producers", "music publishers", "any other persons", "all third-party"],
    },
    ClauseType.NON_COMPETE: {
        "keywords": ["non-compete", "shall not compete", "restrictive covenant", "non-solicitation"],
        "risk_signals": ["worldwide", "perpetuity", "any business"],
    },
    ClauseType.CONFIDENTIALITY: {
        "keywords": ["confidential", "non-disclosure", "trade secret", "proprietary information"],
        "risk_signals": ["perpetuity", "survive termination", "unlimited"],
    },
    ClauseType.ARBITRATION: {
        "keywords": ["arbitrat", "arbitration", "arbitrator", "dispute resolution"],
        "risk_signals": ["sole discretion", "binding", "waive right to jury", "each party shall select"],
    },
    ClauseType.ENTIRE_AGREEMENT: {
        "keywords": ["entire agreement", "constitute the entire", "supersede", "prior understanding"],
        "risk_signals": ["shall not be binding", "preceding the date", "any prior"],
    },
    ClauseType.MODIFICATION: {
        "keywords": ["modification of", "amendment", "any modification", "additional obligation"],
        "risk_signals": ["in writing", "signed by each", "authorized representative"],
    },
    ClauseType.ASSIGNMENT_RESTRICTION: {
        "keywords": ["assignment of rights", "may not be assigned", "not be transferred", "personal to that party"],
        "risk_signals": ["without the prior", "written consent", "express"],
    },
    ClauseType.SUCCESSORS_HEIRS: {
        "keywords": ["heirs", "executors", "administrators", "successors and assigns"],
        "risk_signals": ["survive", "binding upon", "includes that party"],
    },
    ClauseType.WORK_FOR_HIRE: {
        "keywords": ["work for hire", "work made for hire", "works for hire", "work-for-hire", "made for hire"],
        "risk_signals": ["deemed", "from the inception", "acknowledged", "no ownership", "employee", "for all purposes"],
    },
}

# Pre-compute lowercase keywords and signals for faster matching
CLAUSE_PATTERNS_LOWER = {
    clause_type: {
        "keywords": [kw.lower() for kw in patterns["keywords"]],
        "risk_signals": [rs.lower() for rs in patterns["risk_signals"]],
    }
    for clause_type, patterns in CLAUSE_PATTERNS.items()
}

# Pre-compile obligation extraction pattern (doesn't need party name)
import re
OBLIGATION_PATTERN = re.compile(
    r'(?:shall|agrees?\s+to|must|will|required\s+to)\s+([^.]{10,80})',
    re.IGNORECASE
)

# Cross-type signal mapping (pre-computed)
CROSS_TYPE_SIGNALS = {
    ClauseType.IP_OWNERSHIP: [ClauseType.PERPETUITY, ClauseType.IP_ASSIGNMENT],
    ClauseType.COMPENSATION: [ClauseType.WAIVER, ClauseType.RECOUPMENT],
    ClauseType.EXCLUSIVITY: [ClauseType.PERPETUITY],
    ClauseType.GRANT_OF_RIGHTS: [ClauseType.WAIVER, ClauseType.COMPENSATION],
}

# Pre-compute all risk signals per clause type (including cross-type)
ALL_SIGNALS_FOR_TYPE = {}
for clause_type in ClauseType:
    signals = set(CLAUSE_PATTERNS_LOWER.get(clause_type, {}).get("risk_signals", []))
    if clause_type in CROSS_TYPE_SIGNALS:
        for related_type in CROSS_TYPE_SIGNALS[clause_type]:
            signals.update(CLAUSE_PATTERNS_LOWER.get(related_type, {}).get("risk_signals", []))
    ALL_SIGNALS_FOR_TYPE[clause_type] = list(signals)


# =============================================================================
# DOCUMENT INTELLIGENCE ENGINE
# =============================================================================

class DocumentIntelligenceEngine:
    """
    Multi-modal document analysis engine for law firms.
    
    Extracts clauses, maps obligations, flags risks, and generates
    plain-language summaries. All processing is local/sovereign.
    
    Usage:
        engine = DocumentIntelligenceEngine()
        analysis = engine.analyze_document(text, doc_type=DocumentType.CONTRACT)
        print(analysis.summary)
        print(analysis.red_flags)
    """
    
    def __init__(self, data_dir: str = './aion_data', use_llm: bool = True):
        self.data_dir = Path(data_dir)
        self.docs_dir = self.data_dir / 'documents'
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_llm = use_llm
        self._lm_client = None
        
        # Document index
        self.index_file = self.docs_dir / '_index.json'
        self.doc_index: Dict[str, Dict] = self._load_index()
        
        logger.info(f"DocumentIntelligenceEngine initialized ({len(self.doc_index)} documents in store)")
    
    @property
    def lm_client(self):
        """Lazy-load LM Studio client"""
        if self._lm_client is None and self.use_llm:
            try:
                from ..api.lmstudio_client import LMStudioClient
                self._lm_client = LMStudioClient()
            except Exception as e:
                logger.warning(f"LM Studio client unavailable: {e}")
                self.use_llm = False
        return self._lm_client
    
    def _load_index(self) -> Dict[str, Dict]:
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text(encoding='utf-8'))
            except:
                pass
        return {}
    
    def _save_index(self):
        self.index_file.write_text(
            json.dumps(self.doc_index, indent=2, default=str), encoding='utf-8'
        )
    
    def _generate_doc_id(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    # ─── Core Analysis ────────────────────────────────────────────────
    
    def analyze_document(
        self, 
        text: str, 
        doc_type: DocumentType = DocumentType.OTHER,
        title: str = "",
        parties: List[str] = None,
        store: bool = True
    ) -> DocumentAnalysis:
        """
        Analyze a legal document — extract clauses, flag risks, map obligations.
        
        Args:
            text: The full document text
            doc_type: Type of document
            title: Document title (auto-detected if empty)
            parties: List of parties (auto-detected if empty)
            store: Whether to persist the analysis to disk
        
        Returns:
            DocumentAnalysis with full extraction results
        """
        doc_id = self._generate_doc_id(text)
        
        # Auto-detect parties
        if not parties:
            parties = self._extract_parties(text)
        
        # Auto-detect title
        if not title:
            title = self._extract_title(text, doc_type)
        
        # Extract clauses
        clauses = self._extract_clauses(text, parties)
        
        # Calculate risk
        overall_risk, risk_score = self._calculate_risk(clauses)
        
        # Identify red flags
        red_flags = self._identify_red_flags(clauses)
        
        # Map obligations
        obligations = self._map_obligations(clauses, parties)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(clauses, red_flags)
        
        # Build summary
        summary = self._build_summary(title, parties, clauses, red_flags, risk_score)
        
        analysis = DocumentAnalysis(
            document_id=doc_id,
            document_type=doc_type,
            title=title,
            parties=parties,
            date_analyzed=datetime.now().isoformat(),
            clauses=clauses,
            overall_risk=overall_risk,
            risk_score=risk_score,
            summary=summary,
            red_flags=red_flags,
            key_obligations=obligations,
            recommendations=recommendations,
            raw_text=text,
            metadata={
                "word_count": len(text.split()),
                "clause_count": len(clauses),
                "critical_clauses": sum(1 for c in clauses if c.risk_level == RiskLevel.CRITICAL),
                "high_risk_clauses": sum(1 for c in clauses if c.risk_level == RiskLevel.HIGH),
            }
        )
        
        # Persist
        if store:
            self._store_analysis(analysis)
        
        return analysis
    
    # ─── Extraction Methods ───────────────────────────────────────────
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract party names from document text"""
        parties = []
        text_lower = text.lower()
        
        # Common patterns
        import re
        
        # "between X and Y"
        between_match = re.search(r'between\s+([A-Z][^,]+?)\s+(?:and|&)\s+([A-Z][^,.]+)', text)
        if between_match:
            parties.extend([between_match.group(1).strip(), between_match.group(2).strip()])
        
        # "X shall" or "X agrees"
        shall_matches = re.findall(r'([A-Z][a-zA-Z\s.]+?(?:Jr\.|Sr\.|Inc\.|LLC|Corp\.)?)(?:\s+shall\s+|\s+agrees\s+)', text)
        for match in shall_matches:
            name = match.strip()
            if len(name) > 3 and name not in parties:
                parties.append(name)
        
        # "property of X"
        property_matches = re.findall(r'property of\s+([A-Z][a-zA-Z\s]+?)(?:\s+in\s+|\s+throughout\s+|[,.])', text)
        for match in property_matches:
            name = match.strip()
            if len(name) > 3 and name not in parties:
                parties.append(name)
        
        # Deduplicate similar names
        unique_parties = []
        for p in parties:
            if not any(p in existing or existing in p for existing in unique_parties):
                unique_parties.append(p)
        
        return unique_parties[:10]  # Cap at 10 parties
    
    def _extract_title(self, text: str, doc_type: DocumentType) -> str:
        """Extract or generate document title"""
        lines = text.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 100 and ':' not in line:
                return line
        return f"{doc_type.value.replace('_', ' ').title()}"
    
    def _extract_clauses(self, text: str, parties: List[str]) -> List[ExtractedClause]:
        """Extract and classify all clauses from document text (optimized)"""
        clauses = []
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Pre-compute lowercase parties and their parts for faster matching
        parties_lower = [(p, p.lower(), [part.lower() for part in p.split() if len(part) > 3]) 
                         for p in parties]
        
        for i, para in enumerate(paragraphs):
            para_lower = para.lower()
            
            # Check each clause pattern using pre-computed lowercase keywords
            for clause_type, patterns in CLAUSE_PATTERNS_LOWER.items():
                # Fast keyword check using pre-lowercased keywords
                keyword_hits = sum(1 for kw in patterns["keywords"] if kw in para_lower)
                
                if keyword_hits == 0:
                    continue
                
                # Use pre-computed all-signals (includes cross-type)
                all_signals = ALL_SIGNALS_FOR_TYPE.get(clause_type, patterns["risk_signals"])
                triggered_signals = [rs for rs in all_signals if rs in para_lower]
                risk_hits = len(triggered_signals)
                
                # Determine risk level
                if risk_hits >= 3:
                    risk_level = RiskLevel.CRITICAL
                elif risk_hits >= 2:
                    risk_level = RiskLevel.HIGH
                elif risk_hits >= 1:
                    risk_level = RiskLevel.MEDIUM
                else:
                    risk_level = RiskLevel.LOW
                
                # Build risk reason
                risk_reason = f"Contains: {', '.join(triggered_signals)}" if triggered_signals else "Standard clause"
                
                # Identify affected parties (using pre-lowercased)
                affected = [p for p, p_low, parts in parties_lower 
                           if p_low in para_lower or any(part in para_lower for part in parts)]
                
                # Extract obligations (optimized - single regex)
                obligations = self._extract_obligations_from_para(para, parties)
                
                # Generate summary
                summary = self._summarize_clause(para, clause_type)
                
                # Section label
                section = ""
                if i > 0:
                    prev = paragraphs[i-1].strip()
                    if len(prev) < 50 and (prev.endswith(':') or prev.endswith('.')):
                        section = prev
                
                # Recommendations
                recs = self._clause_recommendations(clause_type, risk_level, triggered_signals)
                
                clauses.append(ExtractedClause(
                    clause_type=clause_type,
                    text=para,
                    summary=summary,
                    risk_level=risk_level,
                    risk_reason=risk_reason,
                    parties_affected=affected,
                    obligations=obligations,
                    section=section,
                    recommendations=recs
                ))
        
        return clauses
    
    def _extract_obligations_from_para(self, para: str, parties: List[str]) -> List[str]:
        """Extract specific obligations from a paragraph (optimized)"""
        # Use pre-compiled pattern - doesn't need party-specific regex
        matches = OBLIGATION_PATTERN.findall(para)
        
        obligations = []
        para_lower = para.lower()
        
        for match in matches:
            match_clean = match.strip()
            if len(match_clean) < 10:
                continue
            
            # Attribute to party if mentioned in this sentence
            attributed = False
            for party in parties:
                if party.lower() in para_lower:
                    obligations.append(f"{party}: {match_clean}")
                    attributed = True
                    break
            
            if not attributed:
                obligations.append(match_clean)
        
        return obligations[:5]  # Limit to top 5 obligations
        
        return obligations
    
    def _summarize_clause(self, text: str, clause_type: ClauseType) -> str:
        """Generate a plain-language summary of a clause"""
        text_lower = text.lower()
        
        summaries = {
            ClauseType.EXCLUSIVITY: "Grants exclusive rights over performances/work",
            ClauseType.COMPENSATION: "Defines compensation terms and payment structure",
            ClauseType.IP_OWNERSHIP: "Assigns intellectual property ownership",
            ClauseType.IP_ASSIGNMENT: "Transfers all rights, title, and interest",
            ClauseType.PERPETUITY: "Rights granted in perpetuity (forever, worldwide)",
            ClauseType.WAIVER: "Party waives certain rights or compensation",
            ClauseType.RECOUPMENT: "Costs treated as advances, recoupable from earnings",
            ClauseType.OBLIGATION: "Imposes specific obligations or duties",
            ClauseType.GRANT_OF_RIGHTS: "Grants broad rights or licenses",
            ClauseType.TERMINATION: "Defines termination conditions",
            ClauseType.INDEMNIFICATION: "Requires indemnification / hold harmless",
            ClauseType.NON_COMPETE: "Restricts competitive activities",
            ClauseType.CONFIDENTIALITY: "Imposes confidentiality obligations",
            ClauseType.MATCHING_RIGHTS: "Matching rights / right of first refusal on outside deals",
            ClauseType.ROYALTY_DEDUCTION: "Third-party royalties deducted from artist's share",
            ClauseType.ARBITRATION: "Disputes resolved via arbitration, not court",
            ClauseType.ENTIRE_AGREEMENT: "Entire agreement — supersedes all prior understandings",
            ClauseType.MODIFICATION: "Modifications must be in writing and signed",
            ClauseType.ASSIGNMENT_RESTRICTION: "Rights cannot be assigned without written consent",
            ClauseType.SUCCESSORS_HEIRS: "Agreement binds heirs, executors, successors and assigns",
        }
        
        base = summaries.get(clause_type, "Legal clause")
        
        # Add specifics
        if "in perpetuity" in text_lower:
            base += " — PERPETUITY: rights never expire"
        if "waives any right" in text_lower:
            base += " — WAIVER: party gives up rights"
        if "without any payment" in text_lower:
            base += " — NO PAYMENT: work provided for free"
        if "irrevocable" in text_lower:
            base += " — IRREVOCABLE: cannot be taken back"
        if "from inception" in text_lower:
            base += " — FROM INCEPTION: ownership from moment of creation"
        
        return base
    
    def _clause_recommendations(self, clause_type: ClauseType, risk_level: RiskLevel, 
                                 signals: List[str]) -> List[str]:
        """Generate specific recommendations for a clause"""
        recs = []
        
        if risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            if clause_type == ClauseType.IP_OWNERSHIP:
                recs.append("Negotiate time-limited IP assignment (e.g., 5-7 years) instead of perpetuity")
                recs.append("Add reversion clause: rights return if company fails to exploit within X years")
            
            if clause_type == ClauseType.COMPENSATION:
                recs.append("Negotiate minimum guaranteed compensation beyond collective bargaining minimums")
                recs.append("Add royalty structure (e.g., percentage of net receipts)")
                if "waives" in str(signals):
                    recs.append("CRITICAL: Do not waive compensation rights without significant consideration")
                if "100% of the gross" in str(signals):
                    recs.append("CRITICAL: 100% gross deduction for overhead makes net royalties effectively $0 — remove or cap at 15-20%")
                if "sole discretion" in str(signals):
                    recs.append("CRITICAL: 'Sole discretion' payment withholding gives label unilateral power to pay nothing")
                if "conditioned upon" in str(signals):
                    recs.append("'Full and faithful performance' condition means any minor breach could void ALL royalties — negotiate materiality threshold")
            
            if clause_type == ClauseType.EXCLUSIVITY:
                recs.append("Limit exclusivity to specific territories or time periods")
                recs.append("Add first-refusal right instead of blanket exclusivity")
            
            if clause_type == ClauseType.WAIVER:
                recs.append("Consult attorney before signing any waiver of rights")
                recs.append("Ensure adequate consideration is received for waived rights")
            
            if clause_type == ClauseType.RECOUPMENT:
                recs.append("Cap recoupable expenses at a defined maximum")
                recs.append("Require itemized accounting of all expenses")
                recs.append("Add audit rights to verify expense claims")
                if "100% of the gross" in str(signals):
                    recs.append("CRITICAL: 100% of gross receipts deducted as 'overhead' — this is a zero-royalty structure disguised as a percentage deal")
            
            if clause_type == ClauseType.GRANT_OF_RIGHTS:
                recs.append("Limit grant to specific, enumerated uses rather than 'any and all'")
                if "without any payment" in str(signals):
                    recs.append("CRITICAL: Negotiate payment for third-party copyright usage")
            
            if clause_type == ClauseType.OBLIGATION:
                recs.append("Add reasonable limits to availability obligations")
                recs.append("Define 'from time to time' with specific frequency caps")
            
            if clause_type == ClauseType.MATCHING_RIGHTS:
                recs.append("Extend acceptance window from 1 day to at least 10-30 business days")
                recs.append("Remove 30% discount requirement — matching should be at same terms")
                recs.append("Add carve-out for non-recording opportunities (film, sync, live)")
            
            if clause_type == ClauseType.ROYALTY_DEDUCTION:
                recs.append("Cap third-party deductions at a fixed percentage (e.g., 25% of gross)")
                recs.append("Require label to pay producer/publisher royalties from its share, not artist's")
                recs.append("Add transparency: require itemized royalty statements")
            
            if clause_type == ClauseType.WORK_FOR_HIRE:
                recs.append("CRITICAL: 'Work for hire' means you own NOTHING — negotiate co-ownership or reversion rights")
                recs.append("Remove 'work for hire' language and replace with exclusive license")
                recs.append("If work-for-hire is required, negotiate significantly higher upfront compensation")
                recs.append("Add time-limited assignment (5-7 years) instead of perpetual work-for-hire")
            
            if clause_type == ClauseType.INDEMNIFICATION:
                recs.append("Limit indemnification to artist's own breaches, not label's actions")
                recs.append("Cap indemnification liability at total advances received")
                recs.append("Add mutual indemnification — label should also indemnify artist")
            
            if clause_type == ClauseType.ARBITRATION:
                recs.append("Ensure arbitration venue is in a neutral or artist-favorable jurisdiction")
                recs.append("Consider whether waiving right to jury trial is acceptable")
            
            if clause_type == ClauseType.SUCCESSORS_HEIRS:
                recs.append("Clarify whether obligations survive death or only IP rights transfer")
                recs.append("Tension with Section 13 (assignment restriction) — get legal clarity")
        
        return recs
    
    # ─── Risk Calculation ─────────────────────────────────────────────
    
    def _calculate_risk(self, clauses: List[ExtractedClause]) -> Tuple[RiskLevel, int]:
        """Calculate overall document risk score with cross-clause compounding"""
        if not clauses:
            return RiskLevel.INFO, 0
        
        risk_weights = {
            RiskLevel.CRITICAL: 30,
            RiskLevel.HIGH: 20,
            RiskLevel.MEDIUM: 10,
            RiskLevel.LOW: 3,
            RiskLevel.INFO: 0,
        }
        
        total_risk = sum(risk_weights[c.risk_level] for c in clauses)
        # Normalize against a reasonable baseline, not max possible
        baseline = max(len(clauses) * 12, 1)  # average clause ~MEDIUM
        risk_score = min(100, int((total_risk / baseline) * 100))
        
        # Cross-clause compounding: toxic combinations amplify risk
        clause_types = set(c.clause_type for c in clauses)
        compound_bonus = 0
        
        if ClauseType.IP_OWNERSHIP in clause_types and ClauseType.PERPETUITY in clause_types:
            compound_bonus += 15
        if ClauseType.COMPENSATION in clause_types and ClauseType.WAIVER in clause_types:
            compound_bonus += 15
        if ClauseType.EXCLUSIVITY in clause_types and ClauseType.PERPETUITY in clause_types:
            compound_bonus += 10
        if ClauseType.RECOUPMENT in clause_types and ClauseType.WAIVER in clause_types:
            compound_bonus += 10
        if ClauseType.GRANT_OF_RIGHTS in clause_types:
            # Check if any grant is without payment
            for c in clauses:
                if c.clause_type == ClauseType.GRANT_OF_RIGHTS and "without any payment" in c.risk_reason.lower():
                    compound_bonus += 10
                    break
        if ClauseType.SUCCESSORS_HEIRS in clause_types and ClauseType.ASSIGNMENT_RESTRICTION in clause_types:
            compound_bonus += 5  # Internal tension — heirs bound but assignment restricted
        if ClauseType.INDEMNIFICATION in clause_types and ClauseType.SUCCESSORS_HEIRS in clause_types:
            compound_bonus += 5  # Indemnification survives to heirs/estate
        if ClauseType.WORK_FOR_HIRE in clause_types and ClauseType.IP_OWNERSHIP in clause_types:
            compound_bonus += 15  # Work-for-hire + IP ownership = total loss of rights
        if ClauseType.WORK_FOR_HIRE in clause_types and ClauseType.PERPETUITY in clause_types:
            compound_bonus += 15  # Work-for-hire + perpetuity = permanent dispossession
        
        risk_score = min(100, risk_score + compound_bonus)
        
        # Bump score if critical/high clauses exist
        critical_count = sum(1 for c in clauses if c.risk_level == RiskLevel.CRITICAL)
        high_count = sum(1 for c in clauses if c.risk_level == RiskLevel.HIGH)
        
        if critical_count >= 3:
            risk_score = max(risk_score, 90)
        elif critical_count >= 2:
            risk_score = max(risk_score, 80)
        elif critical_count >= 1:
            risk_score = max(risk_score, 65)
        
        if high_count >= 3:
            risk_score = max(risk_score, 75)
        elif high_count >= 2:
            risk_score = max(risk_score, 60)
        
        # Map score to level
        if risk_score >= 75:
            return RiskLevel.CRITICAL, risk_score
        elif risk_score >= 50:
            return RiskLevel.HIGH, risk_score
        elif risk_score >= 25:
            return RiskLevel.MEDIUM, risk_score
        else:
            return RiskLevel.LOW, risk_score
    
    def _identify_red_flags(self, clauses: List[ExtractedClause]) -> List[str]:
        """Identify specific red flags across all clauses"""
        flags = []
        
        for c in clauses:
            if c.risk_level == RiskLevel.CRITICAL:
                flags.append(f"[CRITICAL] {c.clause_type.value.upper()}: {c.risk_reason}")
            elif c.risk_level == RiskLevel.HIGH:
                flags.append(f"[HIGH] {c.clause_type.value.upper()}: {c.risk_reason}")
        
        # Cross-clause flags
        clause_types = [c.clause_type for c in clauses]
        
        if ClauseType.IP_OWNERSHIP in clause_types and ClauseType.PERPETUITY in clause_types:
            flags.append("[CRITICAL] IP ownership combined with perpetuity — rights never revert")
        
        if ClauseType.COMPENSATION in clause_types and ClauseType.WAIVER in clause_types:
            flags.append("[CRITICAL] Compensation clause paired with waiver — effectively unpaid")
        
        if ClauseType.EXCLUSIVITY in clause_types and ClauseType.PERPETUITY in clause_types:
            flags.append("[CRITICAL] Exclusive rights in perpetuity — party locked out permanently")
        
        has_recoupment = ClauseType.RECOUPMENT in clause_types
        has_comp_waiver = any(c.clause_type == ClauseType.COMPENSATION and 
                            c.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH) for c in clauses)
        if has_recoupment and has_comp_waiver:
            flags.append("[CRITICAL] Recoupment from earnings + waived compensation = party may never be paid")
        
        if ClauseType.SUCCESSORS_HEIRS in clause_types and ClauseType.INDEMNIFICATION in clause_types:
            flags.append("[HIGH] Indemnification obligations extend to heirs/estate via successors clause")
        
        if ClauseType.SUCCESSORS_HEIRS in clause_types and ClauseType.ASSIGNMENT_RESTRICTION in clause_types:
            flags.append("[MEDIUM] Tension: rights are non-assignable (§13) but bind successors/heirs (§14)")
        
        if ClauseType.WORK_FOR_HIRE in clause_types:
            flags.append("[CRITICAL] 'Work for hire' clause — party creates but owns NOTHING")
            if ClauseType.IP_OWNERSHIP in clause_types:
                flags.append("[CRITICAL] Work-for-hire + IP ownership = total IP dispossession from inception")
        
        if ClauseType.WORK_FOR_HIRE in clause_types:
            flags.append("[CRITICAL] 'Work for hire' clause — party creates but owns NOTHING")
            if ClauseType.IP_OWNERSHIP in clause_types:
                flags.append("[CRITICAL] Work-for-hire + IP ownership = total IP dispossession from inception")
        
        if ClauseType.ARBITRATION in clause_types:
            flags.append("[MEDIUM] Arbitration clause — disputes cannot be taken to court")
        
        return flags
    
    def _map_obligations(self, clauses: List[ExtractedClause], parties: List[str]) -> Dict[str, List[str]]:
        """Map obligations to specific parties"""
        obligations = {p: [] for p in parties}
        obligations["unattributed"] = []
        
        for c in clauses:
            for ob in c.obligations:
                attributed = False
                for party in parties:
                    if party.lower() in ob.lower() or any(
                        part.lower() in ob.lower() for part in party.split() if len(part) > 3
                    ):
                        obligations[party].append(ob)
                        attributed = True
                        break
                if not attributed:
                    obligations["unattributed"].append(ob)
        
        # Remove empty
        return {k: v for k, v in obligations.items() if v}
    
    def _generate_recommendations(self, clauses: List[ExtractedClause], red_flags: List[str]) -> List[str]:
        """Generate top-level recommendations"""
        recs = []
        
        critical_count = sum(1 for c in clauses if c.risk_level == RiskLevel.CRITICAL)
        high_count = sum(1 for c in clauses if c.risk_level == RiskLevel.HIGH)
        
        if critical_count > 0:
            recs.append(f"URGENT: {critical_count} critical risk clause(s) found — consult attorney before signing")
        
        if high_count > 0:
            recs.append(f"{high_count} high-risk clause(s) should be renegotiated")
        
        # Collect unique clause-level recommendations
        seen = set()
        for c in clauses:
            for r in c.recommendations:
                if r not in seen:
                    recs.append(r)
                    seen.add(r)
        
        return recs
    
    def _build_summary(self, title: str, parties: List[str], clauses: List[ExtractedClause],
                       red_flags: List[str], risk_score: int) -> str:
        """Build a plain-language document summary"""
        party_str = " and ".join(parties[:2]) if parties else "Unknown parties"
        
        critical = sum(1 for c in clauses if c.risk_level == RiskLevel.CRITICAL)
        high = sum(1 for c in clauses if c.risk_level == RiskLevel.HIGH)
        
        summary = f"Document: {title}\n"
        summary += f"Parties: {party_str}\n"
        summary += f"Risk Score: {risk_score}/100\n"
        summary += f"Clauses analyzed: {len(clauses)} ({critical} critical, {high} high risk)\n"
        
        if red_flags:
            summary += f"\nRed Flags ({len(red_flags)}):\n"
            for flag in red_flags[:5]:
                summary += f"  {flag}\n"
        
        return summary
    
    # ─── Persistence ──────────────────────────────────────────────────
    
    def _store_analysis(self, analysis: DocumentAnalysis):
        """Persist analysis to disk"""
        doc_file = self.docs_dir / f"{analysis.document_id}.json"
        
        # Serialize
        data = {
            "document_id": analysis.document_id,
            "document_type": analysis.document_type.value,
            "title": analysis.title,
            "parties": analysis.parties,
            "date_analyzed": analysis.date_analyzed,
            "overall_risk": analysis.overall_risk.value,
            "risk_score": analysis.risk_score,
            "summary": analysis.summary,
            "red_flags": analysis.red_flags,
            "key_obligations": analysis.key_obligations,
            "recommendations": analysis.recommendations,
            "metadata": analysis.metadata,
            "clauses": [
                {
                    "clause_type": c.clause_type.value,
                    "text": c.text,
                    "summary": c.summary,
                    "risk_level": c.risk_level.value,
                    "risk_reason": c.risk_reason,
                    "parties_affected": c.parties_affected,
                    "obligations": c.obligations,
                    "section": c.section,
                    "recommendations": c.recommendations
                }
                for c in analysis.clauses
            ],
            # Don't store raw_text in index, only in full doc
            "raw_text": analysis.raw_text
        }
        
        doc_file.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')
        
        # Update index (without raw_text for efficiency)
        self.doc_index[analysis.document_id] = {
            "document_id": analysis.document_id,
            "document_type": analysis.document_type.value,
            "title": analysis.title,
            "parties": analysis.parties,
            "date_analyzed": analysis.date_analyzed,
            "risk_score": analysis.risk_score,
            "overall_risk": analysis.overall_risk.value,
            "clause_count": len(analysis.clauses),
            "red_flag_count": len(analysis.red_flags),
        }
        self._save_index()
        
        logger.info(f"Document stored: {analysis.document_id} - {analysis.title} "
                     f"(risk: {analysis.risk_score}/100, {len(analysis.clauses)} clauses)")
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Load a full document analysis from disk"""
        doc_file = self.docs_dir / f"{doc_id}.json"
        if doc_file.exists():
            return json.loads(doc_file.read_text(encoding='utf-8'))
        return None
    
    def list_documents(self) -> List[Dict]:
        """List all analyzed documents"""
        return list(self.doc_index.values())
    
    def search_documents(self, query: str) -> List[Dict]:
        """Search documents by title, party name, or type"""
        query_lower = query.lower()
        results = []
        for doc in self.doc_index.values():
            if (query_lower in doc.get("title", "").lower() or
                query_lower in str(doc.get("parties", [])).lower() or
                query_lower in doc.get("document_type", "").lower()):
                results.append(doc)
        return results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_engine = None

def get_document_engine(data_dir: str = './aion_data') -> DocumentIntelligenceEngine:
    """Get or create the document intelligence engine singleton"""
    global _engine
    if _engine is None:
        _engine = DocumentIntelligenceEngine(data_dir=data_dir)
    return _engine
