"""
AION OS - Red Team Simulation

Simulates a multi-stage insider threat attack to test all 3 detection engines:
1. Pattern Engine - Known attack signatures
2. Baseline Engine - Statistical deviations  
3. Reasoning Engine - Novel semantic patterns

Scenario: "Operation Typhoon Replay"
An employee planning to leave and steal client data over 2 weeks.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import time
from datetime import datetime, timedelta
from dataclasses import asdict

# Suppress debug output during imports
import os
os.environ['PYTHONWARNINGS'] = 'ignore'

# Import all engines
from aionos.core.temporal_engine import (
    TemporalCorrelationEngine, SecurityEvent, EventType, get_temporal_engine
)
from aionos.core.baseline_engine import (
    BehavioralBaselineEngine, get_baseline_engine
)
from aionos.core.reasoning_engine import (
    LLMReasoningEngine, get_reasoning_engine, LLMProvider
)
from aionos.api.alert_webhook import AlertIngestionEngine

# Fix Windows encoding for emojis
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_phase(num, name):
    print(f"\n{'-' * 70}")
    print(f"  [PHASE {num}]: {name}")
    print(f"{'-' * 70}")


def print_detection(engine, detected, details=""):
    icon = "🚨" if detected else "✅"
    status = "DETECTED" if detected else "clear"
    print(f"  {icon} {engine}: {status} {details}")


def red_team_simulation():
    """Run a comprehensive red team simulation."""
    
    print_header("🔴 AION OS RED TEAM SIMULATION")
    print("\nScenario: Attorney departure with data theft (Typhoon pattern)")
    print("Attacker: srevino@typhoon.com")
    print("Timeline: 14 days of escalating activity")
    
    # Initialize engines
    temporal_engine = get_temporal_engine()
    baseline_engine = get_baseline_engine()
    reasoning_engine = LLMReasoningEngine(provider=LLMProvider.MOCK)
    pattern_engine = AlertIngestionEngine()
    
    print(f"\n📊 Engines Loaded:")
    print(f"   • Pattern Engine: {len(pattern_engine.patterns)} patterns")
    print(f"   • Temporal Engine: {len(temporal_engine.attack_sequences)} attack sequences")
    print(f"   • Baseline Engine: Ready")
    print(f"   • Reasoning Engine: {reasoning_engine.provider.value}")
    
    user_id = "srevino@typhoon.com"
    base_date = datetime(2026, 1, 10)  # Start 2 weeks ago
    
    # =========================================================================
    # PHASE 0: Establish Normal Baseline (30 days of normal activity)
    # =========================================================================
    print_phase(0, "ESTABLISHING BASELINE (30 days of normal activity)")
    print("  Building behavioral baseline from historical 'normal' activity...")
    
    # Simulate 30 days of normal activity BEFORE the attack
    # Need ~100+ data points for reliable baseline (50%+ confidence)
    normal_start = base_date - timedelta(days=35)
    for day in range(30):
        ts = normal_start + timedelta(days=day, hours=10)
        # Normal daily activity: 3-4 file downloads per day
        for i in range(3):
            baseline_engine.record_event(
                user_id=user_id,
                event_type="file_download",
                timestamp=ts + timedelta(hours=i),
                details={"path": f"/work/project_{day % 10}_{i}.docx", "size_mb": 0.5}
            )
        # Daily VPN access
        baseline_engine.record_event(
            user_id=user_id,
            event_type="vpn_access",
            timestamp=ts,
            details={"location": "Austin, TX"}
        )
        # Occasional database query (every 2 days)
        if day % 2 == 0:
            baseline_engine.record_event(
                user_id=user_id,
                event_type="database_query",
                timestamp=ts + timedelta(hours=2),
                details={"query": "SELECT name FROM clients LIMIT 10"}
            )
    
    profile = baseline_engine.get_user_profile(user_id)
    if profile:
        print(f"  ✅ Baseline established: {profile.get('data_points', 0)} data points")
        print(f"     Confidence: {profile.get('confidence', 'N/A')}")
        print(f"     Typical hours: {profile.get('typical_hours', [])[:5]}")
    else:
        print("  ⚠️ Baseline not established")
    
    all_detections = {
        "pattern": [],
        "temporal": [],
        "baseline": [],
        "reasoning": []
    }
    
    # =========================================================================
    # PHASE 1: Reconnaissance (Days 1-3) - Should be subtle
    # =========================================================================
    print_phase(1, "RECONNAISSANCE (Days 1-3)")
    print("  Attacker gathering intel, updating LinkedIn, browsing job sites")
    
    recon_events = [
        # Day 1 - LinkedIn update
        {"day": 1, "hour": 9, "type": EventType.CLOUD_SYNC, 
         "details": {"service": "linkedin", "action": "profile_update", "status": "Open to Work"}},
        # Day 2 - Job site visits (would be browser logs)
        {"day": 2, "hour": 12, "type": EventType.CLOUD_SYNC,
         "details": {"service": "indeed.com", "action": "search", "query": "partner law firm"}},
        # Day 3 - Org chart download
        {"day": 3, "hour": 14, "type": EventType.FILE_DOWNLOAD,
         "details": {"path": "/hr/org_chart_2026.pdf", "size_mb": 0.5}},
    ]
    
    for event in recon_events:
        ts = base_date + timedelta(days=event["day"], hours=event["hour"])
        
        # Feed to temporal engine
        sec_event = SecurityEvent(
            event_id=f"recon_{event['day']}",
            user_id=user_id,
            event_type=event["type"],
            timestamp=ts,
            source_system="simulation",
            details=event["details"],
            risk_score=0.2
        )
        temporal_alerts = temporal_engine.ingest_event(sec_event)
        if temporal_alerts:
            all_detections["temporal"].extend(temporal_alerts)
        
        # Feed to baseline engine
        baseline_alerts = baseline_engine.record_event(
            user_id=user_id,
            event_type=event["type"].value,
            timestamp=ts,
            details=event["details"]
        )
        if baseline_alerts:
            all_detections["baseline"].extend(baseline_alerts)
    
    print_detection("Pattern Engine", False, "(no known pattern match yet)")
    print_detection("Temporal Engine", len(all_detections["temporal"]) > 0, 
                   f"({len(all_detections['temporal'])} alerts)")
    print_detection("Baseline Engine", len(all_detections["baseline"]) > 0,
                   f"({len(all_detections['baseline'])} alerts)")
    
    # Run reasoning on accumulated events
    timeline = temporal_engine.get_user_timeline(user_id, days=14)
    reasoning_result = reasoning_engine.analyze_events(user_id, timeline)
    if reasoning_result.threat_detected:
        all_detections["reasoning"].append(reasoning_result)
    print_detection("Reasoning Engine", reasoning_result.threat_detected,
                   f"(confidence: {reasoning_result.confidence:.0%})")
    
    # =========================================================================
    # PHASE 2: Data Collection (Days 4-7) - Getting serious
    # =========================================================================
    print_phase(2, "DATA COLLECTION (Days 4-7)")
    print("  Attacker downloading client files, querying databases")
    
    collection_events = [
        # Day 4 - Start downloading client files
        {"day": 4, "hour": 10, "type": EventType.FILE_DOWNLOAD,
         "details": {"path": "/clients/top_accounts/", "file_count": 15, "size_mb": 45}},
        # Day 5 - Database queries
        {"day": 5, "hour": 11, "type": EventType.DATABASE_QUERY,
         "details": {"query": "SELECT * FROM clients WHERE revenue > 500000", "rows": 247}},
        # Day 6 - More downloads
        {"day": 6, "hour": 14, "type": EventType.FILE_DOWNLOAD,
         "details": {"path": "/matters/active/", "file_count": 32, "size_mb": 120}},
        # Day 7 - Email forwarding setup
        {"day": 7, "hour": 16, "type": EventType.EMAIL_FORWARD,
         "details": {"rule": "auto-forward", "to": "personal@gmail.com"}},
    ]
    
    for event in collection_events:
        ts = base_date + timedelta(days=event["day"], hours=event["hour"])
        
        sec_event = SecurityEvent(
            event_id=f"collect_{event['day']}",
            user_id=user_id,
            event_type=event["type"],
            timestamp=ts,
            source_system="simulation",
            details=event["details"],
            risk_score=0.5
        )
        temporal_alerts = temporal_engine.ingest_event(sec_event)
        if temporal_alerts:
            all_detections["temporal"].extend(temporal_alerts)
        
        baseline_alerts = baseline_engine.record_event(
            user_id=user_id,
            event_type=event["type"].value,
            timestamp=ts,
            details=event["details"]
        )
        if baseline_alerts:
            all_detections["baseline"].extend(baseline_alerts)
    
    # Check pattern matching
    alert = {"type": "bulk_download", "user": user_id, "details": {"file_count": 47}}
    pattern_analysis = pattern_engine.analyze_alert(alert)
    pattern_detected = pattern_analysis.pattern_similarity > 0.3
    if pattern_detected:
        all_detections["pattern"].append(pattern_analysis)
    
    print_detection("Pattern Engine", pattern_detected,
                   f"(similarity: {pattern_analysis.pattern_similarity:.0%})")
    print_detection("Temporal Engine", len(all_detections["temporal"]) > 0,
                   f"({len(all_detections['temporal'])} total alerts)")
    print_detection("Baseline Engine", len(all_detections["baseline"]) > 0,
                   f"({len(all_detections['baseline'])} total alerts)")
    
    timeline = temporal_engine.get_user_timeline(user_id, days=14)
    reasoning_result = reasoning_engine.analyze_events(user_id, timeline)
    if reasoning_result.threat_detected:
        all_detections["reasoning"].append(reasoning_result)
    print_detection("Reasoning Engine", reasoning_result.threat_detected,
                   f"(type: {reasoning_result.threat_type})")
    
    # =========================================================================
    # PHASE 3: Exfiltration (Days 8-10) - Active theft
    # =========================================================================
    print_phase(3, "EXFILTRATION (Days 8-10)")
    print("  Attacker moving data out - USB, cloud, printing")
    
    exfil_events = [
        # Day 8 - VPN from unusual location
        {"day": 8, "hour": 23, "type": EventType.VPN_ACCESS,
         "details": {"location": "Zurich, Switzerland", "ip": "185.42.33.100"}},
        # Day 8 - After hours access
        {"day": 8, "hour": 23, "type": EventType.AFTER_HOURS_ACCESS,
         "details": {"action": "file_access", "systems": ["DMS", "CRM"]}},
        # Day 9 - USB activity
        {"day": 9, "hour": 7, "type": EventType.USB_ACTIVITY,
         "details": {"device": "SanDisk USB", "files_copied": 156, "size_gb": 2.3}},
        # Day 10 - Cloud sync to personal
        {"day": 10, "hour": 15, "type": EventType.CLOUD_SYNC,
         "details": {"service": "personal_dropbox", "files": 89, "size_gb": 1.8}},
    ]
    
    for event in exfil_events:
        ts = base_date + timedelta(days=event["day"], hours=event["hour"])
        
        sec_event = SecurityEvent(
            event_id=f"exfil_{event['day']}_{event['hour']}",
            user_id=user_id,
            event_type=event["type"],
            timestamp=ts,
            source_system="simulation",
            details=event["details"],
            risk_score=0.8
        )
        temporal_alerts = temporal_engine.ingest_event(sec_event)
        if temporal_alerts:
            all_detections["temporal"].extend(temporal_alerts)
        
        baseline_alerts = baseline_engine.record_event(
            user_id=user_id,
            event_type=event["type"].value,
            timestamp=ts,
            details=event["details"]
        )
        if baseline_alerts:
            all_detections["baseline"].extend(baseline_alerts)
    
    # Check pattern - should definitely match Typhoon now
    alert = {"type": "unusual_login", "user": user_id, 
             "details": {"location": "Eastern Europe", "vpn_detected": True}}
    pattern_analysis = pattern_engine.analyze_alert(alert)
    if pattern_analysis.pattern_similarity > 0.3:
        all_detections["pattern"].append(pattern_analysis)
    
    print_detection("Pattern Engine", pattern_analysis.pattern_similarity > 0.5,
                   f"(match: {pattern_analysis.pattern_match}, {pattern_analysis.pattern_similarity:.0%})")
    print_detection("Temporal Engine", len(all_detections["temporal"]) > 0,
                   f"({len(all_detections['temporal'])} total alerts)")
    print_detection("Baseline Engine", len(all_detections["baseline"]) > 0,
                   f"({len(all_detections['baseline'])} total alerts)")
    
    # =========================================================================
    # PHASE 4: Cover-up (Days 11-14) - Destruction
    # =========================================================================
    print_phase(4, "COVER-UP (Days 11-14)")
    print("  Attacker deleting evidence, wiping traces")
    
    coverup_events = [
        # Day 11 - Mass deletion
        {"day": 11, "hour": 6, "type": EventType.BULK_OPERATION,
         "details": {"action": "delete", "files_deleted": 5200000, "folders": 12000}},
        # Day 12 - Email deletion
        {"day": 12, "hour": 7, "type": EventType.BULK_OPERATION,
         "details": {"action": "email_purge", "emails_deleted": 15000}},
        # Day 14 - Final access after termination
        {"day": 14, "hour": 22, "type": EventType.VPN_ACCESS,
         "details": {"location": "Austin, TX", "status": "terminated_employee"}},
    ]
    
    for event in coverup_events:
        ts = base_date + timedelta(days=event["day"], hours=event["hour"])
        
        sec_event = SecurityEvent(
            event_id=f"coverup_{event['day']}",
            user_id=user_id,
            event_type=event["type"],
            timestamp=ts,
            source_system="simulation",
            details=event["details"],
            risk_score=0.95
        )
        temporal_alerts = temporal_engine.ingest_event(sec_event)
        if temporal_alerts:
            all_detections["temporal"].extend(temporal_alerts)
        
        baseline_alerts = baseline_engine.record_event(
            user_id=user_id,
            event_type=event["type"].value,
            timestamp=ts,
            details=event["details"]
        )
        if baseline_alerts:
            all_detections["baseline"].extend(baseline_alerts)
    
    # Final pattern check
    alert = {"type": "bulk_delete", "user": user_id,
             "details": {"files_deleted": 5200000}}
    pattern_analysis = pattern_engine.analyze_alert(alert)
    
    print_detection("Pattern Engine", pattern_analysis.pattern_similarity > 0.6,
                   f"(phase: {pattern_analysis.attack_phase})")
    print_detection("Temporal Engine", len(all_detections["temporal"]) > 0,
                   f"({len(all_detections['temporal'])} total alerts)")
    print_detection("Baseline Engine", len(all_detections["baseline"]) > 0,
                   f"({len(all_detections['baseline'])} total alerts)")
    
    # =========================================================================
    # FINAL REPORT
    # =========================================================================
    print_header("📊 RED TEAM SIMULATION RESULTS")
    
    print(f"\n  Attack Scenario: Typhoon-style attorney departure theft")
    print(f"  Duration: 14 days")
    print(f"  Events Simulated: {len(recon_events) + len(collection_events) + len(exfil_events) + len(coverup_events)}")
    
    print(f"\n  ┌{'─' * 50}┐")
    print(f"  │ {'ENGINE':<25} {'ALERTS':>10} {'STATUS':>12} │")
    print(f"  ├{'─' * 50}┤")
    
    pattern_count = len(all_detections["pattern"])
    temporal_count = len(all_detections["temporal"])
    baseline_count = len(all_detections["baseline"])
    reasoning_count = len(all_detections["reasoning"])
    
    print(f"  │ {'Pattern Engine':<25} {pattern_count:>10} {'✅ WORKING' if pattern_count > 0 else '⚠️ MISSED':>12} │")
    print(f"  │ {'Temporal Engine':<25} {temporal_count:>10} {'✅ WORKING' if temporal_count > 0 else '⚠️ MISSED':>12} │")
    print(f"  │ {'Baseline Engine':<25} {baseline_count:>10} {'✅ WORKING' if baseline_count > 0 else '⚠️ MISSED':>12} │")
    print(f"  │ {'Reasoning Engine':<25} {reasoning_count:>10} {'✅ WORKING' if reasoning_count > 0 else '⚠️ MISSED':>12} │")
    print(f"  └{'─' * 50}┘")
    
    total_detections = pattern_count + temporal_count + baseline_count + reasoning_count
    
    if total_detections >= 3:
        print(f"\n  🎯 OVERALL: ATTACK DETECTED by multiple engines")
    elif total_detections >= 1:
        print(f"\n  ⚠️  OVERALL: PARTIAL DETECTION - some engines missed")
    else:
        print(f"\n  ❌ OVERALL: ATTACK MISSED - critical failure")
    
    # Show sample alerts
    if all_detections["temporal"]:
        print(f"\n  📋 Sample Temporal Alert:")
        alert = all_detections["temporal"][0]
        print(f"     Pattern: {alert.pattern_name}")
        print(f"     Severity: {alert.severity}")
        print(f"     Completion: {alert.completion_percent}%")
    
    if all_detections["pattern"]:
        print(f"\n  📋 Sample Pattern Alert:")
        analysis = all_detections["pattern"][0]
        print(f"     Match: {analysis.pattern_match}")
        print(f"     Phase: {analysis.attack_phase}")
        print(f"     Severity: {analysis.severity}")
    
    print("\n" + "=" * 70)
    print("  ✅ RED TEAM SIMULATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    red_team_simulation()
