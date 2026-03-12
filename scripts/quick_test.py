"""Quick test to verify AION OS is working"""

from aionos.modules.legal_analyzer import LegalAnalyzer
from aionos.modules.security_redteam import SecurityRedTeam
from aionos.modules.attorney_departure import AttorneyDepartureAnalyzer

print("=" * 60)
print("AION OS - Quick System Test")
print("=" * 60)

# Test 1: Legal Analyzer
print("\n[1/3] Testing Legal Analyzer...")
try:
    analyzer = LegalAnalyzer()
    result = analyzer.analyze_brief(
        "Plaintiff claims defendant was negligent in maintaining the property.",
        {"jurisdiction": "California"}
    )
    print(f"[OK] Legal Analyzer working")
    print(f"  - Vulnerabilities found: {len(result.get('vulnerabilities', []))}")
    print(f"  - Cost: ${result.get('cost', 0):.4f}")
except Exception as e:
    print(f"[FAIL] Legal Analyzer FAILED: {e}")

# Test 2: Security Red Team
print("\n[2/3] Testing Security Red Team...")
try:
    redteam = SecurityRedTeam()
    result = redteam.scan_infrastructure(
        "Web application on AWS with PostgreSQL database, no WAF deployed.",
        context={"scope": ["Network", "Applications"]}
    )
    print(f"[OK] Security Red Team working")
    print(f"  - Vulnerabilities found: {len(result.get('vulnerabilities', []))}")
    print(f"  - Cost: ${result.get('cost', 0):.4f}")
except Exception as e:
    print(f"[FAIL] Security Red Team FAILED: {e}")

# Test 3: Attorney Departure
print("\n[3/3] Testing Attorney Departure...")
try:
    departure = AttorneyDepartureAnalyzer()
    result = departure.analyze_departure_simple(
        attorney_name="John Doe",
        practice_area="Corporate M&A",
        active_cases="Acme Corp acquisition closing in 30 days",
        client_relationships="Brought in 3 major clients",
        years_at_firm=8
    )
    print(f"[OK] Attorney Departure working")
    print(f"  - Risk score: {result.get('overall_risk_score', 0)}/100")
    print(f"  - Cost: ${result.get('cost', 0):.4f}")
except Exception as e:
    print(f"[FAIL] Attorney Departure FAILED: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
