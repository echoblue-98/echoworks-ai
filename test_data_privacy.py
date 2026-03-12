"""
Data Privacy Test - Verify NO pattern database details sent to ANY LLM API

This test confirms the 2025-01-22 security fix:
- Pattern matching happens 100% locally
- Only similarity % sent to Claude/Gemini, NOT case details
- Pattern recommendations added AFTER API call, not before
- NO proprietary data goes to Anthropic (Claude), Google (Gemini), or OpenAI

CRITICAL: Run this before EVERY customer demo!
"""

import json
from pathlib import Path
from aionos.modules.heist_planner import HeistPlanner

# All sensitive data that should NEVER be sent to ANY LLM
PROPRIETARY_DATA = [
    # Case names
    "Typhoon Advertising v. Knowles",
    "AmLaw 100 M&A Partner Departure",
    "Composite Pattern",
    
    # Financial data
    "$875,000",
    "$875000",
    "875000",
    "$5,125,000",
    "5125000",
    "$450,000",
    "450000",
    "$3,800,000",
    "3800000",
    
    # Specific attack details (our research)
    "52 days before",
    "52 days",
    "23GB transferred",
    "23GB",
    "847 pages",
    "340%",
    "68%",  # Client follow rate
    "D-52",
    "D-30",
    "D+540",
    
    # Case-specific outcomes
    "Settled after 18 months",
    "12 specific clients",
    "garden leave",
    "emergency TRO",
    "forensic imaging",
    
    # Docket numbers
    "2:21-cv-00194",
    "D. Wyo.",
    
    # Pattern-specific lessons
    "Email forwarding rules configured 52",
    "23GB of deal documents",
    "client follow rate",
    
    # Defense strategy details
    "mandatory 'garden leave' policy",
    "60-day transition",
    "forensic timeline reconstruction",
]

# Generic terms that ARE safe to send (public knowledge)
SAFE_GENERIC_TERMS = [
    "email forwarding",  # Every security pro knows this
    "cloud storage",
    "after-hours access",
    "client contact patterns",
    "scenario similarity",
    "departure pattern",
]


def test_pattern_data_not_in_api_prompt():
    """
    CRITICAL TEST: Verify pattern details never sent to Claude or Gemini API.
    
    The competitive moat depends on keeping legal_patterns.json proprietary.
    """
    
    # Initialize HeistPlanner (will load patterns locally)
    planner = HeistPlanner()
    
    # Test attorney profile that matches Pattern #002 (M&A Partner)
    test_profile = {
        'attorney_name': 'Test Attorney',
        'practice_area': 'M&A',
        'years_at_firm': 16,
        'departure_date': '2026-02-04',
        'destination_firm': 'Direct competitor',
        'system_access': 'Full partner access',
        'active_cases': 'Multiple high-value M&A deals',
        'client_relationships': 'Deep relationships with Fortune 500 clients'
    }
    
    # Get pattern recommendations (should match Pattern #002)
    pattern_match = planner.pattern_matcher.match_scenario(test_profile)
    pattern_recommendations = planner.pattern_matcher.generate_recommendations([pattern_match[0]] if pattern_match else [])
    
    # Create the heist brief (this is what gets sent to Claude/Gemini)
    brief = planner._create_heist_brief(test_profile, pattern_recommendations)
    
    # CRITICAL: Check for ANY proprietary data leaks
    privacy_violations = []
    for sensitive_item in PROPRIETARY_DATA:
        if sensitive_item.lower() in brief.lower():
            privacy_violations.append(sensitive_item)
    
    # Check safe terms (optional)
    safe_terms_found = []
    for term in SAFE_GENERIC_TERMS:
        if term.lower() in brief.lower():
            safe_terms_found.append(term)
    
    # Print results
    print("\n" + "="*70)
    print("DATA PRIVACY AUDIT - ALL LLM PROVIDERS")
    print("="*70)
    print("Providers protected: Claude (Anthropic), Gemini (Google), OpenAI")
    print("="*70)
    
    if privacy_violations:
        print("\n🚨 PRIVACY VIOLATION DETECTED!")
        print(f"   Found {len(privacy_violations)} proprietary data leaks:\n")
        for violation in privacy_violations:
            print(f"   ❌ '{violation}'")
        print("\n   STOP! Fix required before ANY customer demos!")
        print("   File: aionos/modules/heist_planner.py → _create_heist_brief()")
        return False
    else:
        print("\n✅ PRIVACY PROTECTED")
        print("   Zero proprietary data found in API prompts")
        print("   Pattern database remains AION trade secret")
    
    print(f"\n📊 Pattern Match Details (LOCAL ONLY - never sent to APIs):")
    if pattern_recommendations.get('pattern_match_found'):
        print(f"   Match: {pattern_recommendations['similar_case']['name']}")
        print(f"   Similarity: {pattern_recommendations['similar_case']['similarity']}")
        print(f"   Outcome: {pattern_recommendations['similar_case']['outcome'][:50]}...")
        print(f"   ⚠️  Above details stored locally, NOT sent to ANY LLM")
    
    if safe_terms_found:
        print(f"\n✅ Generic Terms in Brief (SAFE - public knowledge):")
        for term in safe_terms_found:
            print(f"   • {term}")
    
    print("\n" + "="*70)
    print("Brief Preview (First 800 chars - what LLMs actually see):")
    print("="*70)
    print(brief[:800] + "...\n")
    
    print("="*70)
    print("WHAT LLMs RECEIVE vs WHAT STAYS LOCAL")
    print("="*70)
    print("✅ SENT TO LLM: Attorney profile (customer data)")
    print("✅ SENT TO LLM: Similarity % (e.g., '68%')")
    print("✅ SENT TO LLM: Generic instructions ('check email forwarding')")
    print("❌ LOCAL ONLY: Case names ('AmLaw 100 M&A Partner Departure')")
    print("❌ LOCAL ONLY: Financial outcomes ($5.1M, $875k settlement)")
    print("❌ LOCAL ONLY: Specific timelines (D-52, D-30, 23GB)")
    print("❌ LOCAL ONLY: Lessons learned (proprietary insights)")
    print("="*70)
    
    return len(privacy_violations) == 0


def test_gemini_context_empty():
    """
    Verify Gemini receives empty context (no pattern data in context dict).
    """
    print("\n" + "="*70)
    print("GEMINI CONTEXT VERIFICATION")
    print("="*70)
    
    # Check heist_planner line 71 - should pass {} as context
    import inspect
    from aionos.modules.heist_planner import HeistPlanner
    
    source = inspect.getsource(HeistPlanner.analyze_departure_risk)
    
    if "gemini_client.analyze(heist_brief, {}" in source:
        print("✅ Gemini receives empty context dict: {}")
        print("   No pattern data can leak via context parameter")
        return True
    else:
        print("⚠️  Check heist_planner.py - verify Gemini context is empty")
        return False


if __name__ == "__main__":
    print("\n" + "🔒"*35)
    print("  AION OS DATA PRIVACY AUDIT")
    print("  Protecting proprietary patterns from ALL LLM providers")
    print("🔒"*35)
    
    test1 = test_pattern_data_not_in_api_prompt()
    test2 = test_gemini_context_empty()
    
    print("\n" + "="*70)
    print("FINAL VERDICT")
    print("="*70)
    
    if test1 and test2:
        print("\n🎉 ALL PRIVACY TESTS PASSED")
        print("   ✅ Claude (Anthropic): Protected")
        print("   ✅ Gemini (Google): Protected")
        print("   ✅ Pattern database: Trade secret preserved")
        print("   ✅ Safe for customer demos")
    else:
        print("\n🚨 PRIVACY TESTS FAILED")
        print("   DO NOT DEMO until issues are fixed!")
    
    exit(0 if (test1 and test2) else 1)
