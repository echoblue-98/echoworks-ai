"""
AION OS - Hybrid Detection Demo
===============================

Uses LOCAL detection + GEMINI fallback for novel patterns.
Goal: Reach 1M local patterns, then Gemini becomes optional.

SETUP:
1. Get free Gemini API key: https://aistudio.google.com/apikey
2. Set environment: $env:GEMINI_API_KEY = "your-key-here"
3. Run this demo: python demo_hybrid_gemini.py
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("\n" + "=" * 70)
    print("     _    ___ ___  _   _    ___  ___")
    print("    / \\  |_ _/ _ \\| \\ | |  / _ \\/ __|")
    print("   / _ \\  | | | | |  \\| | | | | \\__ \\")
    print("  / ___ \\ | | |_| | |\\  | | |_| |__) |")
    print(" /_/   \\_\\___\\___/|_| \\_|  \\___/____/")
    print()
    print("        HYBRID DETECTION ENGINE")
    print("    Local (66 patterns) + Gemini Fallback")
    print("=" * 70)
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("\n! GEMINI_API_KEY not set - running in LOCAL-ONLY mode")
        print("  To enable Gemini fallback:")
        print("  1. Get free key: https://aistudio.google.com/apikey")
        print("  2. Set: $env:GEMINI_API_KEY = 'your-key-here'")
        print()
    else:
        print(f"\n✓ Gemini API key found: {api_key[:8]}...")
    
    from aionos.core.hybrid_engine import HybridDetectionEngine
    from aionos.core.temporal_engine import SecurityEvent, EventType
    
    # Initialize hybrid engine
    engine = HybridDetectionEngine(enable_gemini=True)
    
    print(f"\n  Local patterns loaded:   {len(engine.local_engine.attack_sequences)}")
    print(f"  Learned patterns:        {len(engine._learned_patterns)}")
    print(f"  Gemini enabled:          {engine.gemini.enabled if engine.gemini else False}")
    print(f"  Target patterns:         1,000,000")
    print(f"  Progress:                {engine.stats['progress_to_target']}")
    
    # Demo 1: Known attack (local detection)
    print(f"\n{'='*70}")
    print("DEMO 1: Known Attack - VPN Credential Compromise")
    print("(Should be detected LOCALLY, no Gemini call)")
    print(f"{'='*70}")
    
    known_events = [
        SecurityEvent(
            event_id="k001",
            user_id="known_attack_user@firm.com",
            event_type=EventType.VPN_BRUTE_FORCE,
            timestamp=datetime.now() - timedelta(hours=2),
            source_system="vpn",
            details={"attempts": 5000}
        ),
        SecurityEvent(
            event_id="k002",
            user_id="known_attack_user@firm.com",
            event_type=EventType.VPN_ACCESS,
            timestamp=datetime.now() - timedelta(hours=1),
            source_system="vpn",
            details={"success": True}
        ),
        SecurityEvent(
            event_id="k003",
            user_id="known_attack_user@firm.com",
            event_type=EventType.GEOGRAPHIC_ANOMALY,
            timestamp=datetime.now(),
            source_system="vpn",
            details={"country": "Russia"}
        ),
    ]
    
    for event in known_events:
        alerts = engine.ingest_event(event)
        print(f"\n  Event: {event.event_type.value}")
        if alerts:
            for alert in alerts:
                print(f"  ✓ DETECTED [{alert.source.value.upper()}]: {alert.alert.pattern_name}")
                print(f"    Severity: {alert.alert.severity}")
                print(f"    Latency: {alert.latency_us:.1f}μs")
    
    # Demo 2: Novel attack (should go to Gemini)
    print(f"\n{'='*70}")
    print("DEMO 2: Novel Event Sequence")
    print("(No local match - queued for Gemini analysis)")
    print(f"{'='*70}")
    
    # These events don't match any known pattern
    novel_events = [
        SecurityEvent(
            event_id="n001",
            user_id="novel_attack_user@firm.com",
            event_type=EventType.BADGE_ACCESS,
            timestamp=datetime.now() - timedelta(hours=3),
            source_system="physical",
            details={"location": "datacenter"}
        ),
        SecurityEvent(
            event_id="n002",
            user_id="novel_attack_user@firm.com",
            event_type=EventType.FIRMWARE_TAMPERING,
            timestamp=datetime.now() - timedelta(hours=2),
            source_system="endpoint",
            details={"target": "BIOS"}
        ),
        SecurityEvent(
            event_id="n003",
            user_id="novel_attack_user@firm.com",
            event_type=EventType.REMOVABLE_MEDIA_MOUNT,
            timestamp=datetime.now() - timedelta(hours=1),
            source_system="endpoint",
            details={"device": "USB-unknown"}
        ),
    ]
    
    for event in novel_events:
        alerts = engine.ingest_event(event)
        print(f"\n  Event: {event.event_type.value}")
        if alerts:
            for alert in alerts:
                print(f"  ✓ DETECTED: {alert.alert.pattern_name}")
        else:
            print(f"  → No local match - queued for Gemini")
    
    # Force Gemini analysis (if enabled)
    if engine.gemini and engine.gemini.enabled:
        print(f"\n{'='*70}")
        print("TRIGGERING GEMINI ANALYSIS")
        print(f"{'='*70}")
        
        patterns = engine.force_gemini_analysis()
        
        if patterns:
            for p in patterns:
                print(f"\n  NEW PATTERN LEARNED: {p.name}")
                print(f"  Description: {p.description}")
                print(f"  Severity: {p.severity}")
                print(f"  Confidence: {p.confidence:.1%}")
                print(f"  Stages: {' → '.join(p.stages)}")
        else:
            print("\n  Gemini did not identify a new pattern from this sequence.")
    
    # Final stats
    print(f"\n{'='*70}")
    print("ENGINE STATISTICS")
    print(f"{'='*70}")
    
    stats = engine.stats
    print(f"\n  Local detections:    {stats['local_detections']}")
    print(f"  Gemini detections:   {stats['gemini_detections']}")
    print(f"  Events to Gemini:    {stats['events_to_gemini']}")
    print(f"  Patterns learned:    {stats['patterns_learned']}")
    print(f"  Queue size:          {stats['queue_size']}")
    
    print(f"\n  Total patterns:      {stats['local_patterns']}")
    print(f"  Progress to 1M:      {stats['progress_to_target']}")
    
    # Explain the architecture
    print(f"\n{'='*70}")
    print("HOW IT WORKS")
    print(f"{'='*70}")
    print("""
  ┌─────────────────────────────────────────────────────────────┐
  │                     EVENT STREAM                            │
  └────────────────────────┬────────────────────────────────────┘
                           │
                           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              LOCAL ENGINE (66+ patterns)                    │
  │              ~120μs per event, FREE, PRIVATE                │
  └────────────────────────┬────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                │   PATTERN MATCH?    │
                └──────────┬──────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │ YES             │                 │ NO
         ▼                 │                 ▼
  ┌──────────────┐         │        ┌──────────────────────┐
  │ ALERT NOW!   │         │        │ QUEUE FOR GEMINI     │
  │ (no API)     │         │        │ (batch every 60s)    │
  └──────────────┘         │        └──────────┬───────────┘
                           │                   │
                           │                   ▼
                           │        ┌──────────────────────┐
                           │        │ GEMINI ANALYSIS      │
                           │        │ (anonymized types)   │
                           │        └──────────┬───────────┘
                           │                   │
                           │                   ▼
                           │        ┌──────────────────────┐
                           │        │ NEW PATTERN FOUND?   │
                           │        └──────────┬───────────┘
                           │                   │ YES
                           │                   ▼
                           │        ┌──────────────────────┐
                           │        │ SAVE TO LOCAL DB     │
                           │        │ Engine learns it!    │
                           └────────┴──────────────────────┘

  PRIVACY: Only event TYPES sent to Gemini, never client data.
  GOAL: Reach 1,000,000 patterns, then Gemini becomes optional.
""")
    
    engine.shutdown()
    print("\nHybrid engine shut down cleanly.\n")


if __name__ == "__main__":
    main()
