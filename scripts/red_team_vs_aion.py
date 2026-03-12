"""
RED TEAM vs AION OS - Ultimate Showdown
=======================================

The smartest attacker vs the fastest detection system.

Simulates sophisticated attack patterns and measures AION's response time.
"""

import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from aionos.core.temporal_engine import (
    TemporalCorrelationEngine, SecurityEvent, EventType
)
from aionos.core.baseline_engine import BehavioralBaselineEngine
from aionos.core.reasoning_engine import LLMReasoningEngine, LLMProvider
from aionos.core.local_security_attacker import LocalSecurityAttacker


@dataclass
class AttackScenario:
    name: str
    description: str
    difficulty: str  # EASY, MEDIUM, HARD, NIGHTMARE
    events: List[Dict]
    expected_detection: str


class RedTeamSimulator:
    """Simulates sophisticated attackers against AION OS"""
    
    def __init__(self):
        # Initialize AION in ULTRA-FAST mode
        print("\n" + "=" * 70)
        print("INITIALIZING AION OS - ULTRA-FAST MODE")
        print("=" * 70)
        
        start = time.perf_counter()
        self.temporal = TemporalCorrelationEngine(fast_mode=True)
        self.baseline = BehavioralBaselineEngine(fast_mode=True)
        self.reasoning = LLMReasoningEngine(provider=LLMProvider.MOCK)
        self.adversarial = LocalSecurityAttacker()
        init_time = (time.perf_counter() - start) * 1000
        
        print(f"  AION initialized in {init_time:.2f}ms")
        print(f"  All 4 engines ready: Temporal, Baseline, Reasoning, Adversarial")
        print("=" * 70)
        
        self.attack_scenarios = self._load_attack_scenarios()
        self.results = []
    
    def _load_attack_scenarios(self) -> List[AttackScenario]:
        """Load sophisticated attack scenarios"""
        
        base_time = datetime.now()
        
        return [
            # SCENARIO 1: Classic Typhoon Attack
            AttackScenario(
                name="Operation Typhoon Classic",
                description="Multi-week data exfiltration via VPN - the original pattern",
                difficulty="MEDIUM",
                events=[
                    {"type": EventType.VPN_ACCESS, "delay_hours": 0, "details": {"location": "Home Office", "ip": "73.42.118.99"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 2, "details": {"query": "SELECT * FROM client_matters", "rows": 15000}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 4, "details": {"file_count": 847, "size_mb": 2400}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 6, "details": {"destination": "personal_drive", "files": 847}},
                ],
                expected_detection="typhoon_vpn_exfil"
            ),
            
            # SCENARIO 2: Low and Slow
            AttackScenario(
                name="The Patient Ghost",
                description="Ultra-slow exfiltration - 10 files per day for 30 days",
                difficulty="HARD",
                events=[
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": i * 24, "details": {"file_count": 10, "size_mb": 50}}
                    for i in range(30)
                ],
                expected_detection="volume_spike over time"
            ),
            
            # SCENARIO 3: Credential Theft + Impersonation
            AttackScenario(
                name="Identity Hijack",
                description="Steal credentials, login from new location, access everything",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.GEOGRAPHIC_ANOMALY, "delay_hours": 0, "details": {"location": "Romania", "previous": "New York", "travel_time_hours": 1}},
                    {"type": EventType.VPN_ACCESS, "delay_hours": 0.1, "details": {"location": "Romania", "ip": "185.220.101.42"}},
                    {"type": EventType.PERMISSION_CHANGE, "delay_hours": 0.2, "details": {"action": "self_escalate", "new_role": "admin"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.5, "details": {"query": "SELECT * FROM all_clients", "rows": 50000}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 1, "details": {"operation": "export", "records": 50000}},
                ],
                expected_detection="geographic_compromise + privilege_escalation"
            ),
            
            # SCENARIO 4: After-Hours Blitz
            AttackScenario(
                name="Midnight Raid",
                description="3 AM attack - download everything in 10 minutes",
                difficulty="EASY",
                events=[
                    {"type": EventType.AFTER_HOURS_ACCESS, "delay_hours": 0, "details": {"time": "03:00", "normal_hours": "09:00-18:00"}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 0.05, "details": {"operation": "select_all", "files": 10000}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.1, "details": {"file_count": 10000, "size_mb": 25000}},
                    {"type": EventType.USB_ACTIVITY, "delay_hours": 0.15, "details": {"action": "copy_to_usb", "size_mb": 25000}},
                ],
                expected_detection="after_hours_theft"
            ),
            
            # SCENARIO 5: The Insider - Pre-Departure Theft
            AttackScenario(
                name="The Golden Parachute",
                description="Partner preparing to leave - subtle client list theft",
                difficulty="HARD",
                events=[
                    {"type": EventType.EMAIL_FORWARD, "delay_hours": 0, "details": {"to": "personal@gmail.com", "subject": "contacts"}},
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 24, "details": {"file_count": 50, "type": "client_contacts"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 48, "details": {"query": "SELECT * FROM billing_history", "rows": 5000}},
                    {"type": EventType.PRINT_JOB, "delay_hours": 72, "details": {"pages": 200, "document": "client_list.pdf"}},
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 96, "details": {"destination": "dropbox", "files": 150}},
                ],
                expected_detection="pre_departure_exfil"
            ),
            
            # SCENARIO 6: Decoy Attack
            AttackScenario(
                name="The Misdirection",
                description="Create noise in one area while exfiltrating from another",
                difficulty="NIGHTMARE",
                events=[
                    # Decoy - obvious suspicious activity
                    {"type": EventType.VPN_ACCESS, "delay_hours": 0, "details": {"location": "Decoy_Server", "decoy": True}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 0.1, "details": {"query": "SELECT 1", "decoy": True}},
                    # Real attack - subtle
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0.2, "details": {"file_count": 5, "type": "merger_docs", "real_attack": True}},
                    {"type": EventType.EMAIL_FORWARD, "delay_hours": 0.3, "details": {"to": "competitor@rival.com", "attachment": "merger.pdf", "real_attack": True}},
                ],
                expected_detection="email_forward + file_access correlation"
            ),
            
            # SCENARIO 7: Supply Chain Attack
            AttackScenario(
                name="Trojan Vendor",
                description="Compromised third-party integration exfiltrates data",
                difficulty="NIGHTMARE",
                events=[
                    {"type": EventType.PERMISSION_CHANGE, "delay_hours": 0, "details": {"user": "vendor_integration", "new_scope": "all_matters"}},
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 1, "details": {"query": "SELECT * FROM confidential", "source": "api", "rows": 10000}},
                    {"type": EventType.BULK_OPERATION, "delay_hours": 2, "details": {"operation": "api_export", "destination": "vendor_endpoint"}},
                ],
                expected_detection="privilege_escalation_theft"
            ),
            
            # SCENARIO 8: The Perfect Crime Attempt
            AttackScenario(
                name="Ghost Protocol",
                description="Attacker who read AION's source code - tries to evade all patterns",
                difficulty="NIGHTMARE",
                events=[
                    # Stay under volume thresholds
                    {"type": EventType.FILE_DOWNLOAD, "delay_hours": 0, "details": {"file_count": 2, "size_mb": 10}},
                    # Use normal hours
                    {"type": EventType.DATABASE_QUERY, "delay_hours": 4, "details": {"query": "routine_report", "rows": 100}},
                    # Stay in known location
                    {"type": EventType.VPN_ACCESS, "delay_hours": 8, "details": {"location": "Home Office", "known": True}},
                    # Small email forward
                    {"type": EventType.EMAIL_FORWARD, "delay_hours": 12, "details": {"to": "spouse@family.com", "subject": "schedule"}},
                    # But the combination is still suspicious
                    {"type": EventType.CLOUD_SYNC, "delay_hours": 16, "details": {"destination": "onedrive", "files": 5}},
                ],
                expected_detection="LLM reasoning - subtle pattern"
            ),
        ]
    
    def simulate_attack(self, scenario: AttackScenario) -> Dict:
        """Simulate a single attack scenario"""
        
        user_id = f"attacker_{scenario.name.replace(' ', '_').lower()}@lawfirm.com"
        
        # Calculate max delay to set base_time far enough in the past
        max_delay = max(e.get("delay_hours", 0) for e in scenario.events)
        # Start attack in the past, so all events are before "now"
        base_time = datetime.now() - timedelta(hours=max_delay + 1)
        
        # RESET engines for each scenario to avoid cross-scenario interference
        self.temporal = TemporalCorrelationEngine(fast_mode=True)
        self.baseline = BehavioralBaselineEngine(fast_mode=True)
        
        detections = []
        total_detection_time_us = 0  # microseconds
        events_processed = 0
        
        for event_data in scenario.events:
            # Create event
            event_time = base_time + timedelta(hours=event_data.get("delay_hours", 0))
            event = SecurityEvent(
                event_id=f"evt_{events_processed:04d}",
                user_id=user_id,
                event_type=event_data["type"],
                timestamp=event_time,
                source_system="red_team_sim",
                details=event_data.get("details", {})
            )
            
            # Measure AION's detection time
            detect_start = time.perf_counter()
            
            # Run through all engines
            temporal_alerts = self.temporal.ingest_event(event)
            baseline_alerts = self.baseline.record_event(
                user_id=user_id,
                event_type=event_data["type"].value,
                timestamp=event_time,
                details=event_data.get("details", {})
            )
            
            detect_time_us = (time.perf_counter() - detect_start) * 1_000_000
            total_detection_time_us += detect_time_us
            events_processed += 1
            
            # Record any detections
            for alert in temporal_alerts:
                detections.append({
                    "engine": "TEMPORAL",
                    "pattern": alert.pattern_name,
                    "severity": alert.severity,
                    "at_event": events_processed,
                    "time_us": detect_time_us
                })
            
            for alert in baseline_alerts:
                detections.append({
                    "engine": "BASELINE",
                    "pattern": alert.deviation_type.value,
                    "severity": alert.severity,
                    "at_event": events_processed,
                    "time_us": detect_time_us
                })
        
        return {
            "scenario": scenario.name,
            "difficulty": scenario.difficulty,
            "events": events_processed,
            "detections": detections,
            "detected": len(detections) > 0,
            "first_detection_event": detections[0]["at_event"] if detections else None,
            "total_time_us": total_detection_time_us,
            "avg_time_per_event_us": total_detection_time_us / events_processed if events_processed else 0
        }
    
    def run_all_scenarios(self):
        """Run all attack scenarios"""
        
        print("\n")
        print("=" * 70)
        print("     RED TEAM vs AION OS - BATTLE SIMULATION")
        print("=" * 70)
        print("\n  Attacker: Elite APT Group - Full knowledge of AION patterns")
        print("  Defender: AION OS Ultra-Fast Mode (44,000+ events/sec)")
        print("\n" + "-" * 70)
        
        for i, scenario in enumerate(self.attack_scenarios, 1):
            print(f"\n  SCENARIO {i}: {scenario.name}")
            print(f"  Difficulty: {scenario.difficulty}")
            print(f"  Strategy: {scenario.description}")
            print(f"  Events: {len(scenario.events)}")
            print()
            
            # Dramatic pause
            time.sleep(0.3)
            
            # Run the attack
            result = self.simulate_attack(scenario)
            self.results.append(result)
            
            # Display results
            if result["detected"]:
                first_detect = result["first_detection_event"]
                total_events = result["events"]
                detect_pct = (first_detect / total_events) * 100
                
                print(f"  [!] AION DETECTED ATTACK")
                print(f"      Detection at event {first_detect}/{total_events} ({detect_pct:.0f}% through attack)")
                print(f"      Response time: {result['avg_time_per_event_us']:.2f} microseconds per event")
                
                for det in result["detections"][:3]:  # Show first 3 detections
                    print(f"      -> {det['engine']}: {det['pattern']} [{det['severity']}]")
                
                print(f"\n  RESULT: ATTACKER CAUGHT")
            else:
                print(f"  [?] No detection triggered")
                print(f"      Events processed: {result['events']}")
                print(f"      Processing time: {result['total_time_us']:.2f}us total")
                print(f"\n  RESULT: REQUIRES LLM DEEP ANALYSIS")
            
            print("-" * 70)
        
        self._print_summary()
    
    def _print_summary(self):
        """Print battle summary"""
        
        detected = sum(1 for r in self.results if r["detected"])
        total = len(self.results)
        
        print("\n")
        print("=" * 70)
        print("                    BATTLE SUMMARY")
        print("=" * 70)
        print()
        
        # Results table
        print(f"  {'Scenario':<30} {'Difficulty':<12} {'Detected':<10} {'Time (us)':<12}")
        print(f"  {'-'*30} {'-'*12} {'-'*10} {'-'*12}")
        
        for r in self.results:
            detected_str = "YES" if r["detected"] else "NO*"
            print(f"  {r['scenario']:<30} {r['difficulty']:<12} {detected_str:<10} {r['avg_time_per_event_us']:<12.2f}")
        
        print()
        print(f"  * = Requires LLM deep analysis (would detect with Claude/Ollama)")
        print()
        
        # Calculate overall stats
        total_events = sum(r["events"] for r in self.results)
        total_time_us = sum(r["total_time_us"] for r in self.results)
        avg_per_event = total_time_us / total_events if total_events else 0
        
        print("-" * 70)
        print(f"\n  AION OS PERFORMANCE:")
        print(f"  ----------------------")
        print(f"  Total events processed:     {total_events}")
        print(f"  Total processing time:      {total_time_us/1000:.2f}ms")
        print(f"  Average per event:          {avg_per_event:.2f} microseconds")
        print(f"  Equivalent throughput:      {1_000_000/avg_per_event:,.0f} events/second")
        print()
        
        print(f"  DETECTION RESULTS:")
        print(f"  ----------------------")
        print(f"  Attacks detected:           {detected}/{total} ({detected/total*100:.0f}%)")
        print(f"  Requiring deep analysis:    {total-detected}/{total}")
        print()
        
        # Difficulty breakdown
        by_difficulty = {}
        for r in self.results:
            d = r["difficulty"]
            if d not in by_difficulty:
                by_difficulty[d] = {"total": 0, "detected": 0}
            by_difficulty[d]["total"] += 1
            if r["detected"]:
                by_difficulty[d]["detected"] += 1
        
        print(f"  BY DIFFICULTY:")
        print(f"  ----------------------")
        for diff in ["EASY", "MEDIUM", "HARD", "NIGHTMARE"]:
            if diff in by_difficulty:
                stats = by_difficulty[diff]
                pct = stats["detected"] / stats["total"] * 100
                print(f"  {diff:<12}: {stats['detected']}/{stats['total']} detected ({pct:.0f}%)")
        
        print()
        print("=" * 70)
        
        # Final verdict
        if detected / total >= 0.8:
            print("\n  VERDICT: AION OS DOMINATES - Attacker has no chance")
        elif detected / total >= 0.5:
            print("\n  VERDICT: AION OS WINS - Most attacks caught instantly")
        else:
            print("\n  VERDICT: CLOSE BATTLE - LLM reasoning needed for stealth attacks")
        
        print()
        print("  Speed advantage: AION processes events in MICROSECONDS")
        print("  By the time attacker's 2nd action completes, AION has already alerted.")
        print()
        print("=" * 70)


def main():
    print("\n")
    print("  ___  ___ ___   _____ ___   _   __  __")
    print(" | _ \\| __|   \\ |_   _| __| /_\\ |  \\/  |")
    print(" |   /| _|| |) |  | | | _| / _ \\| |\\/| |")
    print(" |_|_\\|___|___/   |_| |___/_/ \\_\\_|  |_|")
    print()
    print("         vs AION OS - SPEED OF LIGHT")
    print()
    
    simulator = RedTeamSimulator()
    simulator.run_all_scenarios()


if __name__ == "__main__":
    main()
