"""
Demo: Attorney Departure Security Analysis

Shows how AION OS uses chained adversarial attacks to identify
what departing attorneys could exploit and how to close gaps.
"""

from aionos.modules.attorney_departure import AttorneyDepartureAnalyzer

def main():
    analyzer = AttorneyDepartureAnalyzer()
    
    print("=" * 70)
    print("ATTORNEY DEPARTURE EXIT SECURITY ANALYSIS")
    print("=" * 70)
    print()
    print("Scenario: Senior partner leaving to competitor firm")
    print("Question: What security gaps do we need to close?")
    print()
    print("Running chained adversarial analysis...")
    print("(This will take 30-60 seconds)")
    print()
    
    result = analyzer.analyze_exit_security(
        attorney_name="Robert Martinez",
        practice_area="Intellectual Property Litigation",
        active_cases="""
        - TechCorp v. CompetitorX Patent Infringement (Trial in 90 days)
        - StartupCo Trade Secret Theft Case
        - PharmaCo FDA Strategy (ongoing regulatory work)
        """,
        client_relationships="""
        - TechCorp General Counsel (personal relationship, 8 years)
        - StartupCo CEO (recruited client to firm)
        - PharmaCo VP Legal (weekly calls)
        """,
        system_access="""
        - Email (Outlook with 8 years of correspondence)
        - Document Management System (full access)
        - Westlaw (firm account)
        - Client Portal (admin access)
        - Case Management System
        - Billing system (can see all client financials)
        """,
        years_at_firm=8,
        destination_firm="Competitor & Associates (direct competitor in IP litigation)",
        departure_date="30 days from now"
    )
    
    print()
    print("=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)
    print()
    
    print(f"🚨 RISK SCORE: {result['risk_score']}/100")
    print()
    
    print("VULNERABILITIES IDENTIFIED:")
    print("-" * 70)
    for i, vuln in enumerate(result['vulnerabilities'][:5], 1):
        severity = vuln.get('severity', 'UNKNOWN')
        emoji = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡"
        print(f"{i}. {emoji} [{severity}] {vuln.get('description', 'N/A')}")
    print()
    
    if result.get('executable_attacks'):
        print("EXECUTABLE EXPLOITS IDENTIFIED:")
        print("-" * 70)
        for i, attack in enumerate(result['executable_attacks'][:3], 1):
            print(f"{i}. {attack.get('description', 'N/A')[:100]}...")
        print()
    
    if result.get('attack_paths'):
        print("⚛️  QUANTUM-OPTIMIZED ATTACK PATHS:")
        print("-" * 70)
        print("(Highest probability paths for data exfiltration)")
        print()
        for path in result['attack_paths']:
            print(f"Path {path['rank']}: {path['probability']}% success probability")
            print(f"  Steps: {' → '.join(path['steps'][:4])}")
            print(f"  Detection difficulty: {path['detection_difficulty']}%")
            print(f"  Impact: {path['impact']}")
            print()
    
    print("EXIT SECURITY CHECKLIST:")
    print("-" * 70)
    for item in result.get('recommendations', [])[:12]:
        print(item)
    print()
    
    print(f"Analysis Cost: ${result.get('total_cost', 0):.4f}")
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
