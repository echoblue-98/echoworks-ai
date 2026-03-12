"""
AION OS - GEMS INTEGRATION DEMO
================================

Live demonstration of how Dan's gems feed into AION for real-time correlation.

Shows:
1. Simulated gem alerts arriving via webhook
2. AION's real-time pattern matching
3. Individual signals → Connected attack chain
4. Actionable intelligence output

Run this demo during the Dan Roland meeting to show the integration flow.

Usage:
    python demo_gems_integration.py
"""

import sys
import time
import json
import threading
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from queue import Queue
import http.server
import socketserver

import warnings
warnings.filterwarnings("ignore")

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from aionos.core.temporal_engine import (
    TemporalCorrelationEngine, SecurityEvent, EventType
)
from aionos.core.baseline_engine import BehavioralBaselineEngine


# ============================================================================
# SIMULATED GEMS (Dan's Detection Tools)
# ============================================================================

@dataclass
class GemAlert:
    """Alert from one of Dan's detection gems"""
    gem_name: str
    gem_icon: str
    alert_type: str
    user: str
    timestamp: datetime
    details: Dict
    raw_signal: str


class CloudflareGem:
    """Simulates Cloudflare-based access monitoring"""
    name = "Cloudflare Access Gem"
    icon = "🌐"
    
    @staticmethod
    def detect_unusual_login(user: str) -> GemAlert:
        return GemAlert(
            gem_name=CloudflareGem.name,
            gem_icon=CloudflareGem.icon,
            alert_type="unusual_login",
            user=user,
            timestamp=datetime.now(),
            details={"location": "Eastern Europe", "ip": "185.xx.xx.xx", "vpn_detected": True},
            raw_signal="VPN login from unusual geographic location"
        )
    
    @staticmethod
    def detect_impossible_travel(user: str) -> GemAlert:
        return GemAlert(
            gem_name=CloudflareGem.name,
            gem_icon=CloudflareGem.icon,
            alert_type="impossible_travel",
            user=user,
            timestamp=datetime.now(),
            details={"from": "New York", "to": "Singapore", "time_diff_min": 15},
            raw_signal="Login from Singapore 15 min after New York session"
        )


class EmailGem:
    """Simulates email monitoring gem"""
    name = "Email Security Gem"
    icon = "📧"
    
    @staticmethod
    def detect_forward_rule(user: str) -> GemAlert:
        return GemAlert(
            gem_name=EmailGem.name,
            gem_icon=EmailGem.icon,
            alert_type="email_forward",
            user=user,
            timestamp=datetime.now(),
            details={"forward_to": "personal.backup@gmail.com", "scope": "all_incoming"},
            raw_signal="New email forwarding rule to external address"
        )
    
    @staticmethod
    def detect_bulk_export(user: str) -> GemAlert:
        return GemAlert(
            gem_name=EmailGem.name,
            gem_icon=EmailGem.icon,
            alert_type="bulk_email_export",
            user=user,
            timestamp=datetime.now(),
            details={"emails_exported": 2500, "format": "PST", "destination": "local"},
            raw_signal="Bulk email export to local PST file"
        )


class DMSGem:
    """Simulates Document Management System monitoring"""
    name = "DMS Monitor Gem"
    icon = "📁"
    
    @staticmethod
    def detect_bulk_download(user: str) -> GemAlert:
        return GemAlert(
            gem_name=DMSGem.name,
            gem_icon=DMSGem.icon,
            alert_type="bulk_download",
            user=user,
            timestamp=datetime.now(),
            details={"files": 847, "size_gb": 12.5, "matter_types": ["client_contracts", "litigation"]},
            raw_signal="Bulk download of 847 files (12.5 GB)"
        )
    
    @staticmethod
    def detect_permission_check(user: str) -> GemAlert:
        return GemAlert(
            gem_name=DMSGem.name,
            gem_icon=DMSGem.icon,
            alert_type="permission_enumeration",
            user=user,
            timestamp=datetime.now(),
            details={"matters_checked": 156, "includes_restricted": True},
            raw_signal="User checked permissions on 156 matters including restricted"
        )


class HRGem:
    """Simulates HR/Identity monitoring"""
    name = "HR Identity Gem"
    icon = "👤"
    
    @staticmethod
    def detect_linkedin_update(user: str) -> GemAlert:
        return GemAlert(
            gem_name=HRGem.name,
            gem_icon=HRGem.icon,
            alert_type="linkedin_update",
            user=user,
            timestamp=datetime.now(),
            details={"changes": ["headline", "experience"], "headline": "Open to opportunities"},
            raw_signal="LinkedIn profile updated: 'Open to opportunities'"
        )
    
    @staticmethod
    def detect_recruiter_contact(user: str) -> GemAlert:
        return GemAlert(
            gem_name=HRGem.name,
            gem_icon=HRGem.icon,
            alert_type="recruiter_contact",
            user=user,
            timestamp=datetime.now(),
            details={"recruiter": "Legal Eagles Search", "messages": 3},
            raw_signal="Multiple messages with legal recruiter detected"
        )


class CloudGem:
    """Simulates cloud storage monitoring"""
    name = "Cloud Sync Gem"
    icon = "☁️"
    
    @staticmethod
    def detect_personal_cloud(user: str) -> GemAlert:
        return GemAlert(
            gem_name=CloudGem.name,
            gem_icon=CloudGem.icon,
            alert_type="personal_cloud_sync",
            user=user,
            timestamp=datetime.now(),
            details={"service": "Dropbox Personal", "files_synced": 523, "contains_client_data": True},
            raw_signal="Client files synced to personal Dropbox account"
        )


class PrintGem:
    """Simulates print monitoring"""
    name = "Print Monitor Gem"
    icon = "🖨️"
    
    @staticmethod
    def detect_bulk_print(user: str) -> GemAlert:
        return GemAlert(
            gem_name=PrintGem.name,
            gem_icon=PrintGem.icon,
            alert_type="bulk_print",
            user=user,
            timestamp=datetime.now(),
            details={"pages": 340, "after_hours": True, "includes": "client_contacts"},
            raw_signal="340 pages printed after hours including client contacts"
        )


# ============================================================================
# AION CORRELATION ENGINE
# ============================================================================

class AIONCorrelator:
    """AION's real-time correlation engine"""
    
    def __init__(self):
        self.temporal = TemporalCorrelationEngine(fast_mode=True)
        self.baseline = BehavioralBaselineEngine(fast_mode=True)
        self.alert_history = []
        self.correlations = []
    
    def _map_gem_to_event_type(self, alert_type: str) -> EventType:
        """Map gem alert types to AION event types"""
        mapping = {
            "unusual_login": EventType.GEOGRAPHIC_ANOMALY,
            "impossible_travel": EventType.IMPOSSIBLE_TRAVEL,
            "email_forward": EventType.EMAIL_FORWARD,
            "bulk_email_export": EventType.BULK_OPERATION,
            "bulk_download": EventType.FILE_DOWNLOAD,
            "permission_enumeration": EventType.DATABASE_QUERY,
            "linkedin_update": EventType.PERMISSION_CHANGE,  # Signals departure intent
            "recruiter_contact": EventType.PERMISSION_CHANGE,
            "personal_cloud_sync": EventType.CLOUD_SYNC,
            "bulk_print": EventType.PRINT_JOB,
        }
        return mapping.get(alert_type, EventType.ADMIN_ACTION)
    
    def ingest_gem_alert(self, gem_alert: GemAlert) -> Dict:
        """
        Ingest a gem alert and return AION's correlation analysis
        """
        self.alert_history.append(gem_alert)
        
        # Convert to AION SecurityEvent
        event_type = self._map_gem_to_event_type(gem_alert.alert_type)
        
        event = SecurityEvent(
            event_id=f"gem_{len(self.alert_history):04d}",
            user_id=gem_alert.user,
            event_type=event_type,
            timestamp=gem_alert.timestamp,
            source_system=gem_alert.gem_name,
            details=gem_alert.details
        )
        
        # Process through engines
        start = time.perf_counter()
        temporal_alerts = self.temporal.ingest_event(event)
        baseline_alerts = self.baseline.record_event(
            user_id=gem_alert.user,
            event_type=event_type.value,
            timestamp=gem_alert.timestamp,
            details=gem_alert.details
        )
        process_time_us = (time.perf_counter() - start) * 1_000_000
        
        result = {
            "gem_alert": gem_alert,
            "event_type": event_type.value,
            "process_time_us": process_time_us,
            "temporal_alerts": temporal_alerts,
            "baseline_alerts": baseline_alerts,
            "correlation_detected": len(temporal_alerts) > 0 or len(baseline_alerts) > 0
        }
        
        if result["correlation_detected"]:
            self.correlations.append(result)
        
        return result


# ============================================================================
# LIVE DEMO
# ============================================================================

def print_banner():
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║              GEMS → AION INTEGRATION DEMO                         ║
    ║                                                                   ║
    ║         Your Detection Tools + Our Correlation Engine             ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)


def print_gem_alert(alert: GemAlert, index: int):
    """Display incoming gem alert"""
    print(f"\n  ┌─────────────────────────────────────────────────────────────┐")
    print(f"  │  {alert.gem_icon} INCOMING: {alert.gem_name:<42} │")
    print(f"  ├─────────────────────────────────────────────────────────────┤")
    print(f"  │  Signal: {alert.raw_signal:<50} │")
    print(f"  │  User: {alert.user:<52} │")
    print(f"  │  Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<52} │")
    print(f"  └─────────────────────────────────────────────────────────────┘")


def print_aion_correlation(result: Dict):
    """Display AION's correlation analysis"""
    if not result["correlation_detected"]:
        print(f"     └─ AION: Signal logged. Monitoring for patterns... ({result['process_time_us']:.0f}μs)")
        return
    
    # We have a correlation!
    alert = result["temporal_alerts"][0] if result["temporal_alerts"] else None
    
    if alert:
        severity_colors = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        icon = severity_colors.get(alert.severity, "⚪")
        
        print(f"\n  ╔═══════════════════════════════════════════════════════════════╗")
        print(f"  ║  {icon} AION CORRELATION DETECTED                              ║")
        print(f"  ╠═══════════════════════════════════════════════════════════════╣")
        print(f"  ║  Pattern: {alert.pattern_name:<49} ║")
        print(f"  ║  Severity: {alert.severity:<48} ║")
        print(f"  ║  Detection Time: {result['process_time_us']:.0f} microseconds{' '*30} ║")
        print(f"  ╠═══════════════════════════════════════════════════════════════╣")
        print(f"  ║  RECOMMENDED ACTIONS:                                         ║")
        print(f"  ║  → Preserve email and DMS logs immediately                    ║")
        print(f"  ║  → Review user's recent access patterns                       ║")
        print(f"  ║  → Consider litigation hold protocol                          ║")
        print(f"  ╚═══════════════════════════════════════════════════════════════╝")


def run_scenario_1_departure_theft():
    """Scenario: Departing partner stealing client data"""
    print("\n" + "=" * 70)
    print("  SCENARIO 1: DEPARTING PARTNER DATA THEFT")
    print("  " + "-" * 66)
    print("  A senior partner is planning to leave and take clients.")
    print("  Multiple gems will fire over the next few days.")
    print("=" * 70)
    
    correlator = AIONCorrelator()
    user = "sarah.chen@biglaw.com"
    
    # Sequence of gem alerts as the attack unfolds
    gem_alerts = [
        HRGem.detect_linkedin_update(user),
        EmailGem.detect_forward_rule(user),
        DMSGem.detect_bulk_download(user),
        CloudGem.detect_personal_cloud(user),
        PrintGem.detect_bulk_print(user),
    ]
    
    print("\n  Press ENTER to start receiving gem alerts...")
    input()
    
    for i, alert in enumerate(gem_alerts):
        print_gem_alert(alert, i + 1)
        result = correlator.ingest_gem_alert(alert)
        print_aion_correlation(result)
        
        if result["correlation_detected"]:
            print("\n  " + "=" * 66)
            print("  ATTACK CHAIN IDENTIFIED")
            print("  " + "-" * 66)
            print(f"  Gems saw {i + 1} isolated signals.")
            print(f"  AION connected them into: {result['temporal_alerts'][0].pattern_name}")
            print("  " + "=" * 66)
            break
        
        time.sleep(1)
    
    return correlator


def run_scenario_2_vpn_breach():
    """Scenario: VPN credential compromise"""
    print("\n" + "=" * 70)
    print("  SCENARIO 2: VPN CREDENTIAL COMPROMISE")
    print("  " + "-" * 66)
    print("  Attacker stole VPN credentials and is accessing firm data.")
    print("=" * 70)
    
    correlator = AIONCorrelator()
    user = "john.smith@biglaw.com"
    
    gem_alerts = [
        CloudflareGem.detect_unusual_login(user),
        CloudflareGem.detect_impossible_travel(user),
        DMSGem.detect_permission_check(user),
        DMSGem.detect_bulk_download(user),
    ]
    
    print("\n  Press ENTER to start receiving gem alerts...")
    input()
    
    for i, alert in enumerate(gem_alerts):
        print_gem_alert(alert, i + 1)
        result = correlator.ingest_gem_alert(alert)
        print_aion_correlation(result)
        
        if result["correlation_detected"]:
            print("\n  " + "=" * 66)
            print("  VPN BREACH DETECTED")
            print("  " + "-" * 66)
            print(f"  Pattern matched: {result['temporal_alerts'][0].pattern_name}")
            print("  This is NOT the real John Smith - credential was stolen.")
            print("  " + "=" * 66)
            break
        
        time.sleep(1)
    
    return correlator


def run_scenario_3_mixed_attack():
    """Scenario: Multiple users, mixed signals"""
    print("\n" + "=" * 70)
    print("  SCENARIO 3: REAL-TIME MONITORING (MULTIPLE USERS)")
    print("  " + "-" * 66)
    print("  Continuous stream of gem alerts from different users.")
    print("  AION correlates per-user to detect attack chains.")
    print("=" * 70)
    
    correlator = AIONCorrelator()
    
    # Mix of normal activity and attack sequence
    alerts = [
        ("Normal", EmailGem.detect_forward_rule("normal.user1@biglaw.com")),
        ("Normal", DMSGem.detect_bulk_download("normal.user2@biglaw.com")),
        ("ATTACK", HRGem.detect_linkedin_update("departing.partner@biglaw.com")),
        ("Normal", CloudflareGem.detect_unusual_login("traveling.lawyer@biglaw.com")),
        ("ATTACK", EmailGem.detect_forward_rule("departing.partner@biglaw.com")),
        ("Normal", PrintGem.detect_bulk_print("paralegal@biglaw.com")),
        ("ATTACK", DMSGem.detect_bulk_download("departing.partner@biglaw.com")),
    ]
    
    print("\n  Press ENTER to start real-time monitoring...")
    input()
    
    attack_detected = False
    for label, alert in alerts:
        prefix = "  [NORMAL]" if label == "Normal" else "  [??????]"
        print(f"\n{prefix} Incoming from {alert.gem_name}...")
        
        result = correlator.ingest_gem_alert(alert)
        
        if result["correlation_detected"]:
            print_aion_correlation(result)
            attack_detected = True
            print("\n  AION isolated the attack among normal activity!")
            break
        else:
            print(f"     User: {alert.user}")
            print(f"     Signal: {alert.raw_signal}")
            print(f"     Status: Logged ({result['process_time_us']:.0f}μs)")
        
        time.sleep(0.5)
    
    return correlator


def show_integration_architecture():
    """Show how the integration works"""
    print("\n" + "=" * 70)
    print("  INTEGRATION ARCHITECTURE")
    print("=" * 70)
    
    print("""
  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │   YOUR GEMS                          AION OS                        │
  │   ─────────                          ───────                        │
  │                                                                     │
  │   🌐 Cloudflare Gem ──┐                                             │
  │   📧 Email Gem ───────┼──→  ┌─────────────────────┐                 │
  │   📁 DMS Gem ─────────┼──→  │   WEBHOOK API       │                 │
  │   👤 HR Gem ──────────┼──→  │   POST /api/alert   │                 │
  │   ☁️ Cloud Gem ───────┼──→  └─────────┬───────────┘                 │
  │   🖨️ Print Gem ───────┘               │                             │
  │                                       ▼                             │
  │                           ┌─────────────────────┐                   │
  │                           │ TEMPORAL CORRELATION│                   │
  │                           │ 29 Attack Patterns  │                   │
  │                           │ 55K events/second   │                   │
  │                           └─────────┬───────────┘                   │
  │                                     │                               │
  │                                     ▼                               │
  │                           ┌─────────────────────┐                   │
  │                           │ BASELINE ANALYSIS   │                   │
  │                           │ Per-user behavior   │                   │
  │                           │ Deviation detection │                   │
  │                           └─────────┬───────────┘                   │
  │                                     │                               │
  │                                     ▼                               │
  │                           ┌─────────────────────┐                   │
  │                           │ ACTIONABLE ALERTS   │──→ Dashboard      │
  │                           │ Pattern + Severity  │──→ SIEM           │
  │                           │ Recommendations     │──→ Response Team  │
  │                           └─────────────────────┘                   │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘
    """)


def show_value_proposition():
    """Show the value add"""
    print("\n" + "=" * 70)
    print("  THE VALUE: GEMS + AION")
    print("=" * 70)
    
    print("""
  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │   WITHOUT AION                    WITH AION                         │
  │   ────────────                    ─────────                         │
  │                                                                     │
  │   • 6 separate gems               • Unified correlation             │
  │   • 6 separate alert streams      • Single attack narrative         │
  │   • Analyst connects dots         • AION connects dots              │
  │   • Detected in months            • Detected in seconds             │
  │   • Reactive forensics            • Proactive prevention            │
  │                                                                     │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                     │
  │   TYPHOON CASE STUDY:                                               │
  │                                                                     │
  │   • Real case: 36 months to detect departure theft                  │
  │   • With AION: Detected at event 2 of 5 (Day 2)                     │
  │   • Time saved: 35+ months                                          │
  │   • Damages prevented: $2M+ in client revenue                       │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘
    """)


def main():
    print_banner()
    
    print("  This demo shows how your gems integrate with AION.")
    print("  Each scenario demonstrates real-time correlation.\n")
    
    print("  Select a demo:")
    print("  1. Departing Partner Data Theft")
    print("  2. VPN Credential Compromise")
    print("  3. Real-Time Mixed Traffic Monitoring")
    print("  4. Integration Architecture")
    print("  5. Run All Scenarios")
    print()
    
    choice = input("  Enter choice (1-5): ").strip()
    
    if choice == "1":
        run_scenario_1_departure_theft()
    elif choice == "2":
        run_scenario_2_vpn_breach()
    elif choice == "3":
        run_scenario_3_mixed_attack()
    elif choice == "4":
        show_integration_architecture()
        show_value_proposition()
    elif choice == "5":
        run_scenario_1_departure_theft()
        print("\n  Press ENTER for next scenario...")
        input()
        run_scenario_2_vpn_breach()
        print("\n  Press ENTER for next scenario...")
        input()
        run_scenario_3_mixed_attack()
        print("\n  Press ENTER for architecture overview...")
        input()
        show_integration_architecture()
        show_value_proposition()
    else:
        print("  Invalid choice. Running all scenarios...")
        run_scenario_1_departure_theft()
    
    print("\n" + "=" * 70)
    print("  DEMO COMPLETE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
