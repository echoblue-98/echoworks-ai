"""
AION OS - Document Intelligence Test
Tests the contract extraction engine against the Wrecking Zone Records agreement.
"""

import sys
import json
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from aionos.modules.document_intelligence import (
    DocumentIntelligenceEngine, DocumentType, RiskLevel, ClauseType
)
from aionos.knowledge import load_contract_templates, get_contract_template


def test_contract_analysis():
    print("=" * 70)
    print("  AION OS — Document Intelligence Engine")
    print("  Contract Analysis Test")
    print("=" * 70)
    
    # Load proprietary contract template
    template = get_contract_template("wrecking_zone_records_agreement")
    assert template is not None, "Contract template not found"
    print(f"\n[LOADED] {template['title']}")
    print(f"  Parties: {', '.join(template['parties'])}")
    print(f"  Sections: {template['sections_extracted']}")
    
    # Initialize engine
    engine = DocumentIntelligenceEngine(use_llm=False)
    print(f"\n[ENGINE] Initialized (documents in store: {len(engine.list_documents())})")
    
    # Analyze the contract
    analysis = engine.analyze_document(
        text=template["text"],
        doc_type=DocumentType.RECORDING_AGREEMENT,
        title=template["title"],
        parties=template["parties"],
        store=True
    )
    
    # Print results
    print(f"\n{'─' * 70}")
    print(f"  ANALYSIS RESULTS")
    print(f"{'─' * 70}")
    print(f"\n  Document ID:    {analysis.document_id}")
    print(f"  Document Type:  {analysis.document_type.value}")
    print(f"  Overall Risk:   {analysis.overall_risk.value.upper()}")
    print(f"  Risk Score:     {analysis.risk_score}/100")
    print(f"  Clauses Found:  {len(analysis.clauses)}")
    
    # Clauses
    print(f"\n{'─' * 70}")
    print(f"  EXTRACTED CLAUSES")
    print(f"{'─' * 70}")
    for i, c in enumerate(analysis.clauses, 1):
        risk_badge = {
            RiskLevel.CRITICAL: "🔴 CRITICAL",
            RiskLevel.HIGH: "🟠 HIGH",
            RiskLevel.MEDIUM: "🟡 MEDIUM",
            RiskLevel.LOW: "🟢 LOW",
            RiskLevel.INFO: "⚪ INFO",
        }[c.risk_level]
        
        print(f"\n  [{i}] {c.clause_type.value.upper()} — {risk_badge}")
        print(f"      {c.summary}")
        if c.risk_reason != "Standard clause":
            print(f"      Risk: {c.risk_reason}")
        if c.parties_affected:
            print(f"      Affects: {', '.join(c.parties_affected)}")
        if c.recommendations:
            for r in c.recommendations[:2]:
                print(f"      → {r}")
    
    # Red flags
    print(f"\n{'─' * 70}")
    print(f"  RED FLAGS ({len(analysis.red_flags)})")
    print(f"{'─' * 70}")
    for flag in analysis.red_flags:
        print(f"  {flag}")
    
    # Obligations
    if analysis.key_obligations:
        print(f"\n{'─' * 70}")
        print(f"  OBLIGATION MAP")
        print(f"{'─' * 70}")
        for party, obs in analysis.key_obligations.items():
            print(f"\n  {party}:")
            for ob in obs:
                print(f"    • {ob}")
    
    # Recommendations
    print(f"\n{'─' * 70}")
    print(f"  RECOMMENDATIONS ({len(analysis.recommendations)})")
    print(f"{'─' * 70}")
    for rec in analysis.recommendations:
        print(f"  • {rec}")
    
    # Persistence check
    print(f"\n{'─' * 70}")
    print(f"  PERSISTENCE CHECK")
    print(f"{'─' * 70}")
    docs = engine.list_documents()
    print(f"  Documents stored: {len(docs)}")
    for doc in docs:
        print(f"    [{doc['document_id'][:8]}] {doc['title']} (risk: {doc['risk_score']}/100)")
    
    saved = engine.get_document(analysis.document_id)
    assert saved is not None, "Document not persisted!"
    print(f"  Persistence: VERIFIED ✓")
    
    # Knowledge base check
    print(f"\n{'─' * 70}")
    print(f"  KNOWLEDGE BASE")
    print(f"{'─' * 70}")
    templates = load_contract_templates()
    print(f"  Templates loaded: {len(templates)}")
    for t in templates:
        print(f"    [{t.get('document_type', '?')}] {t.get('title', '?')}")
    
    # Assertions
    assert analysis.risk_score >= 60, f"Expected high risk score, got {analysis.risk_score}"
    assert len(analysis.clauses) >= 3, f"Expected 3+ clauses, got {len(analysis.clauses)}"
    assert len(analysis.red_flags) >= 1, f"Expected red flags, got {len(analysis.red_flags)}"
    assert any(c.risk_level == RiskLevel.CRITICAL for c in analysis.clauses), "Expected at least one CRITICAL clause"
    
    print(f"\n{'=' * 70}")
    print(f"  ALL TESTS PASSED ✓")
    print(f"  Risk Score: {analysis.risk_score}/100 — {analysis.overall_risk.value.upper()}")
    print(f"  {len(analysis.clauses)} clauses extracted, {len(analysis.red_flags)} red flags")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    test_contract_analysis()
