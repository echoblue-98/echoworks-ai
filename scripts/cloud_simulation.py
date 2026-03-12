"""
AION OS - Cloud Simulation Test
================================

Simulates attack scenarios through a real cloud endpoint.
Options:
1. Local server (Flask) - for internal testing
2. Webhook.site - free cloud endpoint for demos
3. ngrok tunnel - expose local AION to internet

Run: python cloud_simulation.py
"""

import sys
import time
import json
import threading
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent))

from aionos.core.temporal_engine import (
    TemporalCorrelationEngine, SecurityEvent, EventType
)
from aionos.core.baseline_engine import BehavioralBaselineEngine

# Try importing Flask for local server
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


# =============================================================================
# ATTACK SCENARIOS
# =============================================================================

SCENARIOS = {
    "vpn_breach": {
        "name": "VPN Credential Compromise",
        "description": "Former employee using retained VPN access from Eastern Europe",
        "events": [
            {
                "source": "vpn_gateway",
                "type": "vpn_brute_force",
                "user": "jsmith.terminated@firm.com",
                "timestamp_offset": 0,
                "details": {
                    "attempts": 5000,
                    "source_ip": "185.234.xx.xx",
                    "geo": "Russia",
                    "target": "VPN Gateway"
                }
            },
            {
                "source": "vpn_gateway", 
                "type": "vpn_access",
                "user": "jsmith.terminated@firm.com",
                "timestamp_offset": 30,
                "details": {
                    "status": "success",
                    "source_ip": "185.234.xx.xx",
                    "geo": "Russia",
                    "method": "credentials"
                }
            },
            {
                "source": "identity_provider",
                "type": "impossible_travel",
                "user": "jsmith.terminated@firm.com", 
                "timestamp_offset": 35,
                "details": {
                    "from_location": "New York, NY",
                    "to_location": "Moscow, Russia",
                    "time_gap_minutes": 3,
                    "distance_miles": 4665
                }
            },
            {
                "source": "database_monitor",
                "type": "database_query",
                "user": "jsmith.terminated@firm.com",
                "timestamp_offset": 60,
                "details": {
                    "query": "SELECT * FROM clients, matters, billing",
                    "rows_returned": 15000,
                    "database": "ClientDB",
                    "table": "clients"
                }
            },
            {
                "source": "dlp_system",
                "type": "file_download",
                "user": "jsmith.terminated@firm.com",
                "timestamp_offset": 120,
                "details": {
                    "file_count": 15000,
                    "total_size_mb": 2500,
                    "paths": ["/clients/", "/billing/", "/matters/"],
                    "duration_minutes": 47
                }
            }
        ],
        "expected_detection": "VPN Brute Force to Data Theft",
        "expected_actions": [
            "VPN session terminated",
            "User credentials revoked", 
            "Database server isolated",
            "Logs preserved"
        ]
    },
    
    "attorney_departure": {
        "name": "Departing Attorney Data Theft",
        "description": "Senior partner staging data before leaving for competitor",
        "events": [
            {
                "source": "linkedin_monitor",
                "type": "permission_change",
                "user": "rchen.partner@firm.com",
                "timestamp_offset": 0,
                "details": {
                    "platform": "LinkedIn",
                    "change": "headline_updated",
                    "new_value": "Open to opportunities | M&A | Corporate Law"
                }
            },
            {
                "source": "email_gateway",
                "type": "email_forward",
                "user": "rchen.partner@firm.com",
                "timestamp_offset": 3600,  # 1 hour later
                "details": {
                    "rule_type": "forward_all",
                    "destination": "rchen.personal@gmail.com",
                    "scope": "all_incoming"
                }
            },
            {
                "source": "dms_monitor",
                "type": "file_download",
                "user": "rchen.partner@firm.com",
                "timestamp_offset": 7200,  # 2 hours later
                "details": {
                    "file_count": 847,
                    "total_size_mb": 12500,
                    "paths": ["/clients/fortune500/", "/deals/pending/"],
                    "vs_baseline": "520% above normal"
                }
            },
            {
                "source": "cloud_monitor",
                "type": "cloud_sync",
                "user": "rchen.partner@firm.com",
                "timestamp_offset": 7800,  # 2h 10m later
                "details": {
                    "service": "Dropbox Personal",
                    "files_synced": 847,
                    "destination": "personal_account"
                }
            },
            {
                "source": "endpoint_agent",
                "type": "usb_activity",
                "user": "rchen.partner@firm.com",
                "timestamp_offset": 8400,  # 2h 20m later
                "details": {
                    "device": "SanDisk Extreme 256GB",
                    "device_id": "USB\\VID_0781&PID_5583",
                    "action": "connected",
                    "first_seen": True
                }
            }
        ],
        "expected_detection": "Attorney Departure Data Theft",
        "expected_actions": [
            "Email forwarding rules deleted",
            "Cloud sync permissions revoked",
            "USB ports disabled",
            "Access downgraded to read-only"
        ]
    },
    
    "mfa_fatigue": {
        "name": "MFA Fatigue Attack",
        "description": "Attacker bombarding user with MFA prompts at 2 AM",
        "events": [
            {
                "source": "mfa_provider",
                "type": "mfa_spam",
                "user": "mwilson@firm.com",
                "timestamp_offset": 0,
                "details": {
                    "push_count": 50,
                    "time_window_minutes": 20,
                    "time_of_day": "02:47 AM",
                    "source_ip": "45.xx.xx.xx"
                }
            },
            {
                "source": "mfa_provider",
                "type": "mfa_accepted",
                "user": "mwilson@firm.com",
                "timestamp_offset": 1200,  # 20 min later
                "details": {
                    "time": "02:47 AM",
                    "source_ip": "45.xx.xx.xx (Brazil)",
                    "device": "Unknown"
                }
            },
            {
                "source": "identity_provider",
                "type": "impossible_travel",
                "user": "mwilson@firm.com",
                "timestamp_offset": 1380,  # 23 min later
                "details": {
                    "from_location": "New York, NY",
                    "to_location": "São Paulo, Brazil",
                    "time_gap_minutes": 3
                }
            },
            {
                "source": "network_monitor",
                "type": "lateral_movement",
                "user": "mwilson@firm.com",
                "timestamp_offset": 1500,  # 25 min later
                "details": {
                    "systems_accessed": 12,
                    "time_window_minutes": 5,
                    "systems": ["DC01", "FileServer", "SharePoint", "GitLab"]
                }
            },
            {
                "source": "code_repository",
                "type": "file_download",
                "user": "mwilson@firm.com",
                "timestamp_offset": 1800,  # 30 min later
                "details": {
                    "action": "git clone",
                    "repos": ["internal-tools", "client-portal", "billing-api"],
                    "total_size_mb": 500
                }
            }
        ],
        "expected_detection": "MFA Fatigue to Account Takeover",
        "expected_actions": [
            "Session terminated",
            "Account locked",
            "All active tokens revoked",
            "Security team notified"
        ]
    },
    
    "after_hours_theft": {
        "name": "After-Hours Data Theft",
        "description": "Unusual access patterns during non-business hours indicating insider threat",
        "events": [
            {
                "source": "badge_system",
                "type": "permission_change",
                "user": "associate.jones@firm.com",
                "timestamp_offset": 0,
                "details": {
                    "event": "badge_entry",
                    "time": "02:15 AM",
                    "location": "Main Office",
                    "normal_hours": "9 AM - 6 PM"
                }
            },
            {
                "source": "workstation_monitor",
                "type": "vpn_access",
                "user": "associate.jones@firm.com",
                "timestamp_offset": 300,
                "details": {
                    "action": "workstation_login",
                    "time": "02:20 AM",
                    "location": "Office Floor 12"
                }
            },
            {
                "source": "dms_monitor",
                "type": "file_download",
                "user": "associate.jones@firm.com",
                "timestamp_offset": 600,
                "details": {
                    "file_count": 342,
                    "file_types": ["docx", "xlsx", "pdf"],
                    "matter_types": ["M&A", "Acquisition"],
                    "time": "02:30 AM"
                }
            },
            {
                "source": "endpoint_agent",
                "type": "usb_activity",
                "user": "associate.jones@firm.com",
                "timestamp_offset": 900,
                "details": {
                    "device_type": "USB Drive",
                    "action": "mass_copy",
                    "files_copied": 342,
                    "size_mb": 890
                }
            },
            {
                "source": "badge_system",
                "type": "permission_change",
                "user": "associate.jones@firm.com",
                "timestamp_offset": 1200,
                "details": {
                    "event": "badge_exit",
                    "time": "02:45 AM",
                    "total_time_minutes": 30
                }
            }
        ],
        "expected_detection": "After-Hours Insider Theft",
        "expected_actions": [
            "USB ports disabled",
            "Badge access suspended",
            "Security dispatch initiated",
            "All files flagged for review"
        ]
    },
    
    "lateral_movement": {
        "name": "Lateral Movement Attack",
        "description": "Compromised account moving through network to high-value targets",
        "events": [
            {
                "source": "identity_provider",
                "type": "vpn_access",
                "user": "intern.temp@firm.com",
                "timestamp_offset": 0,
                "details": {
                    "action": "login",
                    "source_ip": "198.51.xx.xx",
                    "geo": "Unknown VPN Provider"
                }
            },
            {
                "source": "network_monitor",
                "type": "lateral_movement",
                "user": "intern.temp@firm.com",
                "timestamp_offset": 120,
                "details": {
                    "systems_accessed": 8,
                    "systems": ["FileServer01", "PrintServer", "HR-DB", "Accounting"],
                    "time_window_minutes": 2,
                    "normal_access": ["FileServer01"]
                }
            },
            {
                "source": "ad_monitor",
                "type": "permission_change",
                "user": "intern.temp@firm.com",
                "timestamp_offset": 300,
                "details": {
                    "change": "group_membership",
                    "added_to": ["Domain Admins", "Backup Operators"],
                    "method": "PowerShell script"
                }
            },
            {
                "source": "database_monitor",
                "type": "database_query",
                "user": "intern.temp@firm.com",
                "timestamp_offset": 420,
                "details": {
                    "query": "SELECT * FROM hr_salaries, ssn_data",
                    "rows_returned": 2500,
                    "database": "HR_Confidential"
                }
            },
            {
                "source": "exfil_monitor",
                "type": "file_download",
                "user": "intern.temp@firm.com",
                "timestamp_offset": 600,
                "details": {
                    "method": "HTTPS to external IP",
                    "destination": "45.xx.xx.xx",
                    "size_mb": 150,
                    "encrypted": True
                }
            }
        ],
        "expected_detection": "Lateral Movement to Privilege Escalation",
        "expected_actions": [
            "Account disabled",
            "All sessions terminated",
            "Network segment isolated",
            "Incident response initiated"
        ]
    }
}


# =============================================================================
# EVENT TYPE MAPPING
# =============================================================================

EVENT_TYPE_MAP = {
    "vpn_brute_force": EventType.VPN_BRUTE_FORCE,
    "vpn_access": EventType.VPN_ACCESS,
    "impossible_travel": EventType.GEOGRAPHIC_ANOMALY,
    "database_query": EventType.DATABASE_QUERY,
    "file_download": EventType.FILE_DOWNLOAD,
    "permission_change": EventType.PERMISSION_CHANGE,
    "email_forward": EventType.EMAIL_FORWARD,
    "cloud_sync": EventType.CLOUD_SYNC,
    "usb_activity": EventType.USB_ACTIVITY,
    "mfa_spam": EventType.VPN_MFA_BYPASS,
    "mfa_accepted": EventType.VPN_ACCESS,
    "lateral_movement": EventType.LATERAL_MOVEMENT,
}

# Default event type for unmapped events
DEFAULT_EVENT_TYPE = EventType.VPN_ACCESS


# =============================================================================
# AION CLOUD SIMULATOR
# =============================================================================

class AIONCloudSimulator:
    """
    Simulates cloud-based attack scenarios through AION.
    Can run locally or connect to remote endpoints.
    """
    
    def __init__(self):
        self.temporal_engine = TemporalCorrelationEngine(fast_mode=True)
        self.baseline_engine = BehavioralBaselineEngine(fast_mode=True)
        self.detections = []
        self.auto_actions = []
        
    def process_event(self, event_data: Dict) -> Dict:
        """Process a single event through AION engines."""
        
        # Convert to SecurityEvent
        event_type = EVENT_TYPE_MAP.get(
            event_data.get("type", ""), 
            DEFAULT_EVENT_TYPE
        )
        
        event = SecurityEvent(
            event_id=f"cloud_{int(time.time()*1000)}",
            user_id=event_data.get("user", "unknown"),
            event_type=event_type,
            timestamp=datetime.now(),
            source_system=event_data.get("source", "cloud"),
            details=event_data.get("details", {})
        )
        
        # Process through temporal engine
        start = time.perf_counter()
        alerts = self.temporal_engine.ingest_event(event)
        latency_us = (time.perf_counter() - start) * 1_000_000
        
        result = {
            "event_id": event.event_id,
            "event_type": event_type.value,
            "user": event.user_id,
            "source": event.source_system,
            "processed_at": datetime.now().isoformat(),
            "latency_us": round(latency_us, 2),
            "pattern_detected": None,
            "severity": "INFO",
            "auto_actions": []
        }
        
        if alerts:
            alert = alerts[0]
            result["pattern_detected"] = alert.pattern_name
            result["severity"] = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
            result["confidence"] = alert.completion_percent  # Use completion_percent as confidence
            result["matched_stages"] = len(alert.matched_stages)
            result["total_stages"] = alert.total_stages
            
            # Determine auto-actions based on pattern
            result["auto_actions"] = self._get_auto_actions(alert.pattern_name, event_data)
            self.detections.append(result)
            self.auto_actions.extend(result["auto_actions"])
            
        return result
    
    def _get_auto_actions(self, pattern: str, event: Dict) -> List[str]:
        """Determine autonomous actions based on detected pattern."""
        
        actions = []
        user = event.get("user", "unknown")
        pattern_lower = pattern.lower()
        
        if "vpn" in pattern_lower or "brute" in pattern_lower:
            actions = [
                f"EXECUTED: VPN session terminated for {user}",
                f"EXECUTED: Credentials revoked for {user}",
                "EXECUTED: Database server isolated from network",
                "EXECUTED: All access logs preserved to immutable storage"
            ]
        elif "departure" in pattern_lower or "attorney" in pattern_lower or "exfil" in pattern_lower:
            actions = [
                f"EXECUTED: Email forwarding rules deleted for {user}",
                f"EXECUTED: Cloud sync permissions revoked for {user}",
                f"EXECUTED: USB ports disabled on {user}'s workstation",
                f"EXECUTED: Access downgraded to read-only for {user}"
            ]
        elif "mfa" in pattern_lower or "fatigue" in pattern_lower:
            actions = [
                f"EXECUTED: All sessions terminated for {user}",
                f"EXECUTED: Account locked for {user}",
                "EXECUTED: All OAuth tokens revoked",
                "EXECUTED: Security team notified via PagerDuty"
            ]
        elif "lateral" in pattern_lower:
            actions = [
                f"EXECUTED: Network access restricted for {user}",
                "EXECUTED: Accessed systems isolated",
                "EXECUTED: Forensic capture initiated"
            ]
        
        return actions
    
    def run_scenario(self, scenario_key: str, endpoint: Optional[str] = None):
        """
        Run a complete attack scenario.
        
        Args:
            scenario_key: Key from SCENARIOS dict
            endpoint: Optional cloud endpoint URL to POST events to
        """
        
        if scenario_key not in SCENARIOS:
            print(f"❌ Unknown scenario: {scenario_key}")
            return
        
        scenario = SCENARIOS[scenario_key]
        
        print()
        print("=" * 70)
        print(f"🎯 SCENARIO: {scenario['name']}")
        print(f"📋 {scenario['description']}")
        print("=" * 70)
        print()
        
        if endpoint:
            print(f"📡 Cloud Endpoint: {endpoint}")
            print()
        
        base_time = datetime.now()
        detection_count = 0
        
        for i, event_data in enumerate(scenario['events']):
            # Add timestamp
            event_data["timestamp"] = (
                base_time + timedelta(seconds=event_data["timestamp_offset"])
            ).isoformat()
            
            # Display event
            print(f"📥 EVENT {i+1}/{len(scenario['events'])}: {event_data['type']}")
            print(f"   User: {event_data['user']}")
            print(f"   Source: {event_data['source']}")
            
            # If endpoint provided, POST to it
            if endpoint:
                try:
                    resp = requests.post(
                        endpoint,
                        json=event_data,
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    print(f"   ☁️  Posted to cloud: {resp.status_code}")
                except Exception as e:
                    print(f"   ⚠️  Cloud POST failed: {e}")
            
            # Process through AION locally
            result = self.process_event(event_data)
            print(f"   ⚡ AION Latency: {result['latency_us']:.0f}μs")
            
            if result["pattern_detected"]:
                detection_count += 1
                print(f"   🚨 PATTERN DETECTED: {result['pattern_detected']}")
                print(f"   🔥 Severity: {result['severity']}")
                print()
                print("   ⚡ AUTO-RESPONSE EXECUTED:")
                for action in result["auto_actions"]:
                    print(f"      ✓ {action}")
                print()
            else:
                print(f"   ✅ Processed - No pattern match yet")
            
            print()
            time.sleep(0.5)  # Simulate real-time processing
        
        # Summary
        print("=" * 70)
        print("📊 SCENARIO SUMMARY")
        print("=" * 70)
        print(f"   Events processed: {len(scenario['events'])}")
        print(f"   Patterns detected: {detection_count}")
        print(f"   Auto-actions executed: {len(self.auto_actions)}")
        print()
        
        if detection_count > 0:
            print("   ✅ THREAT NEUTRALIZED BY AION")
            print()
            print("   ⚖️  LEGAL ACTIONS REQUIRED:")
            print("      • Review for criminal referral (24 hrs)")
            print("      • Assess notification requirements (48 hrs)")
            print("      • Prepare litigation documentation (72 hrs)")
        else:
            print("   ⚠️  No patterns detected - check scenario configuration")
        
        print()
        

def run_local_server():
    """Run a local Flask server to receive cloud events."""
    
    if not FLASK_AVAILABLE:
        print("❌ Flask not installed. Run: pip install flask")
        return
    
    app = Flask(__name__)
    simulator = AIONCloudSimulator()
    events_received = []
    
    @app.route('/api/v1/event', methods=['POST'])
    def receive_event():
        event_data = request.get_json()
        events_received.append(event_data)
        
        result = simulator.process_event(event_data)
        
        return jsonify({
            "status": "processed",
            "aion_analysis": result
        })
    
    @app.route('/api/v1/events', methods=['GET'])
    def list_events():
        return jsonify({
            "events_received": len(events_received),
            "detections": len(simulator.detections),
            "auto_actions": simulator.auto_actions
        })
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy", "engine": "AION OS"})
    
    print()
    print("=" * 60)
    print("🚀 AION OS Cloud Receiver")
    print("=" * 60)
    print()
    print("Endpoints:")
    print("  POST /api/v1/event  - Submit security event")
    print("  GET  /api/v1/events - List processed events")
    print("  GET  /health        - Health check")
    print()
    print("Starting server on http://localhost:8080")
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=False)


def interactive_menu():
    """Interactive menu for running simulations."""
    
    print()
    print("=" * 60)
    print("☁️  AION OS - Cloud Simulation Test")
    print("=" * 60)
    print()
    print("Options:")
    print("  1. Run VPN Breach scenario (local)")
    print("  2. Run Attorney Departure scenario (local)")
    print("  3. Run MFA Fatigue scenario (local)")
    print("  4. Run After-Hours Theft scenario (local)")
    print("  5. Run Lateral Movement scenario (local)")
    print("  6. Run ALL scenarios (local)")
    print("  7. Start local cloud receiver server")
    print("  8. Run scenario with webhook.site")
    print("  9. Run scenario with custom endpoint")
    print("  0. Exit")
    print()
    
    choice = input("Select option: ").strip()
    
    simulator = AIONCloudSimulator()
    
    if choice == "1":
        simulator.run_scenario("vpn_breach")
    elif choice == "2":
        simulator.run_scenario("attorney_departure")
    elif choice == "3":
        simulator.run_scenario("mfa_fatigue")
    elif choice == "4":
        simulator.run_scenario("after_hours_theft")
    elif choice == "5":
        simulator.run_scenario("lateral_movement")
    elif choice == "6":
        for key in SCENARIOS:
            simulator = AIONCloudSimulator()  # Fresh engine
            simulator.run_scenario(key)
            print("\n" + "="*70 + "\n")
    elif choice == "7":
        run_local_server()
    elif choice == "8":
        print()
        print("🌐 WEBHOOK.SITE INTEGRATION")
        print("=" * 40)
        print()
        print("1. Go to https://webhook.site in your browser")
        print("2. Copy the unique URL (looks like https://webhook.site/xxxxxxxx)")
        print("3. Paste it below")
        print()
        endpoint = input("Webhook.site URL: ").strip()
        
        if not endpoint:
            print("❌ No URL provided")
        elif not endpoint.startswith("https://webhook.site"):
            print("⚠️  Warning: URL doesn't look like webhook.site, proceeding anyway...")
        
        print()
        print("Select scenario:")
        print("  1. VPN Breach")
        print("  2. Attorney Departure")
        print("  3. MFA Fatigue")
        print("  4. After-Hours Theft")
        print("  5. Lateral Movement")
        print("  6. ALL scenarios")
        scenario_choice = input("Scenario: ").strip()
        
        scenario_map = {
            "1": "vpn_breach", 
            "2": "attorney_departure", 
            "3": "mfa_fatigue",
            "4": "after_hours_theft",
            "5": "lateral_movement"
        }
        
        if scenario_choice == "6":
            for key in SCENARIOS:
                simulator = AIONCloudSimulator()
                simulator.run_scenario(key, endpoint)
                print("\n" + "="*70 + "\n")
        elif scenario_choice in scenario_map:
            simulator.run_scenario(scenario_map[scenario_choice], endpoint)
        else:
            print("Invalid scenario")
            
    elif choice == "9":
        print()
        print("Enter cloud endpoint URL:")
        endpoint = input("URL: ").strip()
        print()
        print("Select scenario:")
        print("  1. VPN Breach")
        print("  2. Attorney Departure")
        print("  3. MFA Fatigue")
        print("  4. After-Hours Theft")
        print("  5. Lateral Movement")
        scenario_choice = input("Scenario: ").strip()
        
        scenario_map = {
            "1": "vpn_breach", 
            "2": "attorney_departure", 
            "3": "mfa_fatigue",
            "4": "after_hours_theft",
            "5": "lateral_movement"
        }
        if scenario_choice in scenario_map:
            simulator.run_scenario(scenario_map[scenario_choice], endpoint)
    elif choice == "0":
        print("Goodbye!")
        return
    else:
        print("Invalid option")
    
    print()
    input("Press Enter to continue...")
    interactive_menu()


if __name__ == "__main__":
    interactive_menu()
