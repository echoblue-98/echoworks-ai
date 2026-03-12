"""
AION OS - Demo for Dan
======================
This script runs attack scenarios and sends alerts to webhook.site
so you can show Dan real-time detection.

INSTRUCTIONS:
1. Go to https://webhook.site in your browser
2. Copy the unique URL it gives you
3. Run this script and paste the URL when prompted
4. Watch alerts appear in real-time on webhook.site
5. Screenshot or screen-share with Dan
"""

import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from aionos.core.temporal_engine import TemporalCorrelationEngine, SecurityEvent, EventType


def send_alert_to_webhook(webhook_url: str, alert_data: dict):
    """Send alert to webhook.site"""
    try:
        resp = requests.post(webhook_url, json=alert_data, timeout=5)
        return resp.status_code == 200
    except:
        return False


def run_vpn_breach_scenario(engine, webhook_url):
    """Simulate VPN breach attack"""
    print("\n" + "="*60)
    print("🔓 SCENARIO 1: VPN Credential Compromise")
    print("="*60)
    
    user = "jsmith@typhoon-lawfirm.com"
    base = datetime.now() - timedelta(hours=1)
    
    events = [
        ("Brute force attack detected", EventType.VPN_BRUTE_FORCE, 0),
        ("Successful VPN login after attack", EventType.VPN_ACCESS, 30),
        ("Login from unusual location (Moscow)", EventType.GEOGRAPHIC_ANOMALY, 35),
    ]
    
    for desc, etype, mins in events:
        ts = base + timedelta(minutes=mins)
        event = SecurityEvent(
            event_id=f"vpn_{mins}",
            user_id=user,
            event_type=etype,
            timestamp=ts,
            source_system="vpn_gateway",
            details={"description": desc}
        )
        
        print(f"  📥 Event: {desc}")
        alerts = engine.ingest_event(event)
        
        if alerts:
            alert = alerts[0]
            print(f"  🚨 ALERT TRIGGERED: {alert.pattern_name}")
            
            # Send to webhook
            alert_payload = {
                "alert_type": "VPN_BREACH",
                "pattern": alert.pattern_name,
                "user": user,
                "severity": alert.severity,
                "stages_matched": f"{len(alert.matched_stages)}/{alert.total_stages}",
                "timestamp": datetime.now().isoformat(),
                "recommended_actions": [
                    "1. Disable VPN access for this user immediately",
                    "2. Reset all credentials",
                    "3. Check for data exfiltration",
                    "4. Notify security team"
                ]
            }
            
            if send_alert_to_webhook(webhook_url, alert_payload):
                print(f"  ✅ Alert sent to webhook!")
            else:
                print(f"  ⚠️ Failed to send to webhook")
        
        time.sleep(0.5)


def run_attorney_departure_scenario(engine, webhook_url):
    """Simulate attorney departure data theft"""
    print("\n" + "="*60)
    print("👔 SCENARIO 2: Departing Attorney Data Theft")
    print("="*60)
    
    user = "partner.leaving@typhoon-lawfirm.com"
    base = datetime.now() - timedelta(days=5)
    
    events = [
        ("Mass file downloads detected", EventType.FILE_DOWNLOAD, 0),
        ("Files synced to personal cloud", EventType.CLOUD_SYNC, 24),
        ("Email forwarding rule created", EventType.EMAIL_FORWARD, 48),
        ("Large print job submitted", EventType.PRINT_JOB, 72),
    ]
    
    for desc, etype, hours in events:
        ts = base + timedelta(hours=hours)
        event = SecurityEvent(
            event_id=f"atty_{hours}",
            user_id=user,
            event_type=etype,
            timestamp=ts,
            source_system="m365",
            details={"description": desc}
        )
        
        print(f"  📥 Event: {desc}")
        alerts = engine.ingest_event(event)
        
        if alerts:
            alert = alerts[0]
            print(f"  🚨 ALERT TRIGGERED: {alert.pattern_name}")
            
            alert_payload = {
                "alert_type": "INSIDER_THREAT",
                "pattern": alert.pattern_name,
                "user": user,
                "severity": alert.severity,
                "stages_matched": f"{len(alert.matched_stages)}/{alert.total_stages}",
                "timestamp": datetime.now().isoformat(),
                "risk_indicators": [
                    "Partner announced departure last week",
                    "Accessing client files outside normal pattern",
                    "Personal cloud sync detected",
                    "Possible trade secret theft"
                ],
                "recommended_actions": [
                    "1. Preserve all access logs",
                    "2. Interview IT about recent activity",
                    "3. Review departing attorney checklist",
                    "4. Consider legal hold on devices"
                ]
            }
            
            if send_alert_to_webhook(webhook_url, alert_payload):
                print(f"  ✅ Alert sent to webhook!")
        
        time.sleep(0.5)


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          AION OS - LIVE DEMO FOR DAN                      ║
    ║          Real-Time Security Alert System                  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    print("SETUP:")
    print("  1. Open https://webhook.site in your browser")
    print("  2. Copy the unique URL it generates")
    print("  3. Paste it below\n")
    
    webhook_url = input("Webhook.site URL: ").strip()
    
    if not webhook_url:
        print("❌ No URL provided. Exiting.")
        return
    
    if not webhook_url.startswith("https://"):
        print("❌ Invalid URL. Must start with https://")
        return
    
    print("\n🚀 Starting AION OS...")
    engine = TemporalCorrelationEngine(fast_mode=True)
    print(f"   Loaded {len(engine.attack_sequences)} attack patterns")
    
    # Run scenarios
    run_vpn_breach_scenario(engine, webhook_url)
    run_attorney_departure_scenario(engine, webhook_url)
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE!")
    print("="*60)
    print(f"\nCheck webhook.site for the alerts.")
    print("Screenshot the results for Dan's email.")
    
    stats = engine.get_stats()
    print(f"\nStats: {stats['events_processed']} events, {stats['alerts_generated']} alerts")


if __name__ == "__main__":
    main()
