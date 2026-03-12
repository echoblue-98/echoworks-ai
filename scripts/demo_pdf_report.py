"""
Demo: PDF Report Generation

Demonstrates generating professional PDF reports from adversarial analysis.
"""

from aionos.modules.legal_analyzer import LegalAnalyzer
from aionos.modules.report_generator import generate_legal_report
from pathlib import Path
import json

def demo_pdf_report():
    """Generate a sample PDF report from legal analysis."""
    
    print("=" * 60)
    print("AION OS - PDF Report Generation Demo")
    print("=" * 60)
    print()
    
    # Sample legal brief
    sample_brief = """
    MOTION TO DISMISS
    
    Defendant moves to dismiss the complaint on grounds that:
    
    1. Plaintiff lacks standing to bring this action
    2. The court lacks subject matter jurisdiction
    3. The complaint fails to state a claim upon which relief can be granted
    
    ARGUMENT
    
    I. PLAINTIFF LACKS STANDING
    
    Plaintiff has not alleged any concrete injury traceable to Defendant's 
    conduct. The alleged harm is speculative and hypothetical. Under Article III, 
    standing requires: (1) injury in fact, (2) causation, and (3) redressability.
    
    Plaintiff fails all three prongs. The injury alleged is not particularized 
    to Plaintiff, but rather affects the public generally. This does not constitute 
    a cognizable injury for standing purposes.
    
    II. LACK OF SUBJECT MATTER JURISDICTION
    
    This court lacks jurisdiction because the controversy is not ripe for 
    adjudication. Plaintiff seeks an advisory opinion on hypothetical future events.
    
    III. FAILURE TO STATE A CLAIM
    
    Even if the court has jurisdiction, the complaint fails to allege sufficient 
    facts to support the elements of the claimed cause of action. Plaintiff's 
    conclusory allegations are insufficient under modern pleading standards.
    
    CONCLUSION
    
    For the foregoing reasons, Defendant respectfully requests that this Court 
    grant the Motion to Dismiss with prejudice.
    """
    
    print("Step 1: Running adversarial analysis on legal brief...")
    print()
    
    # Run legal analysis
    analyzer = LegalAnalyzer()
    result = analyzer.analyze_brief(sample_brief)
    
    print(f"✓ Analysis complete! {len(result.get('vulnerabilities', []))} findings identified")
    print()
    
    # Create structured result for PDF
    pdf_data = {
        'agents_used': [
            'Legal Opponent',
            'Security Attacker',
            'Business Competitor',
            'Technical Auditor',
            'Ethics Critic'
        ],
        'vulnerabilities': [
            {
                'title': 'Weak Standing Argument',
                'description': 'The standing argument relies on conclusory assertions without '
                              'addressing recent circuit court precedents that have expanded '
                              'the definition of "injury in fact" in similar cases.',
                'severity': 'high',
                'impact': 'Opposing counsel can easily distinguish this motion from binding '
                         'precedent, leading to denial of the motion.',
                'exploitation': 'Plaintiff will cite recent cases where courts found standing '
                               'based on similar factual patterns, undermining this entire section.',
                'remediation': 'Add detailed analysis of controlling case law. Distinguish '
                              'adverse precedents explicitly. Strengthen injury-in-fact argument '
                              'with specific facts from the record.',
                'agent': 'Legal Opponent'
            },
            {
                'title': 'Ripeness Doctrine Misapplication',
                'description': 'The ripeness argument contradicts the standing argument. '
                              'Cannot simultaneously claim no injury (standing) and premature '
                              'injury (ripeness).',
                'severity': 'critical',
                'impact': 'Court will view this as sloppy legal reasoning. Reduces credibility '
                         'of entire motion.',
                'exploitation': 'Opposing counsel will highlight this logical inconsistency '
                               'in their response brief.',
                'remediation': 'Remove the ripeness argument or restructure to avoid logical '
                              'contradiction. Pick one theory and commit.',
                'agent': 'Technical Auditor'
            },
            {
                'title': 'Insufficient Factual Development',
                'description': 'The failure-to-state-a-claim argument lacks specific references '
                              'to which factual allegations are deficient.',
                'severity': 'medium',
                'impact': 'Court cannot evaluate argument without element-by-element analysis. '
                         'May deny motion as inadequately briefed.',
                'exploitation': 'Plaintiff can argue motion is conclusory and should be denied '
                               'without prejudice to file a proper motion.',
                'remediation': 'Add table mapping each element of each claim to specific '
                              'paragraphs of complaint. Identify which elements lack factual support.',
                'agent': 'Legal Opponent'
            },
            {
                'title': 'Missing Alternative Arguments',
                'description': 'No alternative grounds for dismissal (venue, statute of '
                              'limitations, failure to join necessary parties).',
                'severity': 'medium',
                'impact': 'If primary arguments fail, motion is entirely unsuccessful. '
                         'Missed opportunities to win on alternative grounds.',
                'exploitation': 'After motion denied, may be precluded from raising these '
                               'arguments later under law of the case doctrine.',
                'remediation': 'Add section analyzing all possible grounds for dismissal. '
                              'Include alternative arguments in abundance of caution.',
                'agent': 'Business Competitor'
            }
        ],
        'recommendations': [
            {
                'title': 'Restructure Argument Section',
                'description': 'Lead with strongest argument (likely failure to state claim). '
                              'Remove contradictory ripeness argument. Add detailed case law analysis.',
                'priority': 'High'
            },
            {
                'title': 'Add Factual Development',
                'description': 'Create element-by-element comparison table. Cite specific '
                              'paragraph numbers from complaint. Show precisely where each element fails.',
                'priority': 'High'
            },
            {
                'title': 'Include Alternative Grounds',
                'description': 'Add sections on venue, statute of limitations, necessary parties. '
                              'Even if not primary arguments, preserve for appeal.',
                'priority': 'Medium'
            }
        ],
        'cost': 0.06
    }
    
    print("Step 2: Generating professional PDF report...")
    print()
    
    # Generate PDF
    output_path = "reports/legal_motion_analysis.pdf"
    Path("reports").mkdir(exist_ok=True)
    
    report_path = generate_legal_report(
        pdf_data,
        output_path=output_path,
        customer_name="Acme Law Firm LLP",
        project_name="Smith v. Johnson - Motion to Dismiss Analysis"
    )
    
    print(f"✓ PDF report generated: {report_path}")
    print()
    print("Report Contents:")
    print("  • Cover Page (with customer branding)")
    print("  • Executive Summary (key metrics)")
    print("  • Critical Findings (1 identified)")
    print("  • High Severity Findings (1 identified)")
    print("  • Medium Severity Findings (2 identified)")
    print("  • Recommendations (3 prioritized actions)")
    print("  • Appendix (methodology & technical details)")
    print()
    print("=" * 60)
    print("PDF report ready for client delivery!")
    print("=" * 60)

if __name__ == "__main__":
    demo_pdf_report()
