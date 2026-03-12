"""
Compare Local vs Cloud LLM for AION OS Analysis

PURPOSE: Run parallel comparisons to measure LM Studio accuracy vs Claude/Gemini.
GOAL: Hit 85%+ accuracy before switching to sovereign local inference.

USAGE:
    # Run a single comparison
    python compare_local_vs_cloud.py
    
    # Run with specific scenario
    python compare_local_vs_cloud.py --scenario departing_attorney
    
    # View accuracy stats only
    python compare_local_vs_cloud.py --stats

PREREQUISITES:
    1. LM Studio running with a model loaded (http://localhost:1234)
    2. Claude API key in .env (ANTHROPIC_API_KEY)
    
Author: AION OS Team
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from aionos.api.lmstudio_client import LMStudioClient, check_lmstudio_available
from aionos.utils.accuracy_tracker import AccuracyTracker, print_accuracy_report


# =============================================================================
# TEST SCENARIOS - Known attorney departure patterns for consistent testing
# =============================================================================

SCENARIOS = {
    "departing_attorney": {
        "id": "departing_attorney_001",
        "brief": """
Attorney Profile Analysis Request:
- Name: Michael Chen (Senior Partner)
- Practice: Intellectual Property
- Tenure: 15 years
- Notice: Gave 2-week notice yesterday
- Destination: Starting own firm with 3 associates

Behavioral Signals:
- Bulk downloaded 2,400 client files last week
- Forwarded billing reports to personal Gmail
- Accessed matter files for clients not assigned to him
- Connected personal USB drive to workstation

Request: Identify all data exfiltration risks and recommended countermeasures.
""",
        "expected_vulnerabilities": [
            {"title": "Bulk file download", "severity": "critical"},
            {"title": "Personal email forwarding", "severity": "high"},
            {"title": "Unauthorized matter access", "severity": "high"},
            {"title": "USB data transfer", "severity": "critical"}
        ]
    },
    
    "bec_fraud": {
        "id": "bec_fraud_001",
        "brief": """
Incident Analysis Request:
- Firm received wire transfer request appearing from Managing Partner
- Email header shows external origin but display name matches partner
- Request is for $450,000 to "new vendor" for office renovation
- Partner is currently traveling internationally

Analyze this potential Business Email Compromise attack.
""",
        "expected_vulnerabilities": [
            {"title": "Email spoofing", "severity": "critical"},
            {"title": "Wire fraud attempt", "severity": "critical"},
            {"title": "Executive impersonation", "severity": "high"},
            {"title": "Timing exploitation", "severity": "medium"}
        ]
    },
    
    "insider_threat": {
        "id": "insider_threat_001",
        "brief": """
Behavioral Analysis Request:
- IT Administrator with 5 years tenure
- Recently passed over for promotion
- After-hours building access: 11pm-3am (3 nights this week)
- Ran queries against HR database (salary data)
- Created new admin account not in ticketing system

Assess insider threat risk level and recommended actions.
""",
        "expected_vulnerabilities": [
            {"title": "Unauthorized admin account", "severity": "critical"},
            {"title": "HR data access", "severity": "high"},
            {"title": "Unusual access patterns", "severity": "high"},
            {"title": "Privilege abuse", "severity": "high"}
        ]
    }
}


def run_cloud_analysis(brief: str, intensity: int = 3) -> dict:
    """Run analysis via Claude (cloud)"""
    
    try:
        from aionos.core.adversarial_engine import AdversarialEngine
        engine = AdversarialEngine()
        
        # Check if Claude is available
        if engine.client is None:
            return {
                "vulnerabilities": [],
                "error": "Claude API not configured. Set ANTHROPIC_API_KEY in .env",
                "provider": "claude"
            }
        
        result = engine.analyze_departure_risk({
            "name": "Test Attorney",
            "practice": "General",
            "years": 10
        })
        
        return {
            "vulnerabilities": result.get("vulnerabilities", []),
            "provider": "claude",
            "cost": result.get("cost", 0)
        }
        
    except Exception as e:
        # Fallback to Gemini if Claude fails
        try:
            from aionos.api.gemini_client import GeminiClient
            gemini = GeminiClient()
            result = gemini.analyze(brief, {}, intensity)
            return {
                "vulnerabilities": result.get("vulnerabilities", []),
                "provider": "gemini",
                "cost": 0
            }
        except Exception as e2:
            return {
                "vulnerabilities": [],
                "error": f"Both Claude and Gemini failed: {str(e)}, {str(e2)}",
                "provider": "none"
            }


def run_single_comparison(scenario_key: str) -> dict:
    """Run a single comparison between local and cloud"""
    
    if scenario_key not in SCENARIOS:
        print(f"Unknown scenario: {scenario_key}")
        print(f"Available: {list(SCENARIOS.keys())}")
        return None
    
    scenario = SCENARIOS[scenario_key]
    print(f"\n{'='*60}")
    print(f"🔬 COMPARING: {scenario_key}")
    print(f"{'='*60}")
    
    # Check LM Studio availability
    lm_client = LMStudioClient()
    if not lm_client.is_available:
        print("❌ LM Studio not running. Start it and load a model.")
        print("   Expected at: http://localhost:1234")
        return None
    
    model = lm_client.get_loaded_model()
    print(f"📦 Local Model: {model}")
    
    # Run local analysis
    print("\n⏳ Running local analysis (LM Studio)...")
    local_result = lm_client.analyze(
        scenario["brief"],
        context={"scenario": scenario_key},
        intensity=4
    )
    
    if "error" in local_result:
        print(f"❌ Local error: {local_result['error']}")
    else:
        print(f"✅ Local: Found {len(local_result['vulnerabilities'])} vulnerabilities")
        print(f"   Latency: {local_result.get('latency_ms', 0):.0f}ms")
    
    # Run cloud analysis
    print("\n⏳ Running cloud analysis (Claude/Gemini)...")
    cloud_result = run_cloud_analysis(scenario["brief"])
    
    if "error" in cloud_result:
        print(f"❌ Cloud error: {cloud_result['error']}")
    else:
        print(f"✅ Cloud ({cloud_result['provider']}): Found {len(cloud_result['vulnerabilities'])} vulnerabilities")
    
    # Log comparison
    tracker = AccuracyTracker()
    comparison = tracker.log_comparison(
        scenario_id=scenario["id"],
        cloud_result=cloud_result,
        local_result=local_result,
        ground_truth={"expected_vulnerabilities": scenario["expected_vulnerabilities"]},
        cloud_provider=cloud_result.get("provider", "unknown"),
        local_provider="lmstudio"
    )
    
    # Print results
    print(f"\n{'─'*60}")
    print("📊 COMPARISON RESULTS:")
    print(f"   Similarity Score:    {comparison['similarity_score']}%")
    print(f"   Severity Alignment:  {comparison['severity_alignment']}%")
    print(f"   Title Overlap:       {comparison['title_overlap']}%")
    
    if comparison.get('local_accuracy'):
        print(f"   Local Accuracy:      {comparison['local_accuracy']}%")
    
    # Check threshold
    if comparison['similarity_score'] >= 85:
        print("\n✅ PASS: Meets 85% threshold!")
    else:
        gap = 85 - comparison['similarity_score']
        print(f"\n⏳ TESTING: {gap:.1f}% below 85% threshold")
    
    return comparison


def run_all_scenarios():
    """Run all test scenarios"""
    
    print("\n" + "="*60)
    print("🚀 RUNNING ALL SCENARIOS")
    print("="*60)
    
    results = []
    for scenario_key in SCENARIOS:
        result = run_single_comparison(scenario_key)
        if result:
            results.append(result)
    
    # Print summary
    if results:
        avg_similarity = sum(r['similarity_score'] for r in results) / len(results)
        print("\n" + "="*60)
        print("📊 OVERALL SUMMARY")
        print("="*60)
        print(f"Scenarios tested:  {len(results)}")
        print(f"Average accuracy:  {avg_similarity:.1f}%")
        print(f"Target threshold:  85%")
        
        if avg_similarity >= 85:
            print("\n✅ READY FOR SOVEREIGN INFERENCE!")
        else:
            print(f"\n⏳ Gap to threshold: {85 - avg_similarity:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Compare LM Studio vs Cloud LLM accuracy"
    )
    parser.add_argument(
        "--scenario", "-s",
        choices=list(SCENARIOS.keys()) + ["all"],
        default="departing_attorney",
        help="Scenario to test (default: departing_attorney)"
    )
    parser.add_argument(
        "--stats", 
        action="store_true",
        help="Show accuracy stats only (no new tests)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all logged comparisons"
    )
    
    args = parser.parse_args()
    
    if args.clear:
        AccuracyTracker().clear_logs()
        print("Logs cleared.")
        return
    
    if args.stats:
        print_accuracy_report()
        return
    
    # Check LM Studio first
    if not check_lmstudio_available():
        print("\n❌ LM Studio not running!")
        print("   1. Open LM Studio")
        print("   2. Load a model (e.g., Mistral 7B, Llama 3 8B)")
        print("   3. Start the local server (should be on port 1234)")
        print("   4. Run this script again")
        return
    
    if args.scenario == "all":
        run_all_scenarios()
    else:
        run_single_comparison(args.scenario)
    
    # Always show updated stats
    print("\n")
    print_accuracy_report()


if __name__ == "__main__":
    main()
