"""
AION OS - 100% LOCAL Security Attacker Agent Test
Zero LLM dependency - No API calls

This is the AION way.
"""
import time

print("""
╔══════════════════════════════════════════════════════════════════╗
║           AION OS - 100% LOCAL AGENT TEST                        ║
║          Security Attacker - Zero LLM Dependency                 ║
╚══════════════════════════════════════════════════════════════════╝
""")

from aionos.modules.soc_ingestion import SOCIngestionEngine
from aionos.core.local_security_attacker import get_local_attacker

# Fresh engine
engine = SOCIngestionEngine()

print("SCENARIO: VPN Database Theft (Typhoon pattern)")
print("ANALYSIS MODE: 100% LOCAL - Zero API calls")
print("="*60)
print()

# Alert 1: VPN anomaly
print("📡 Alert 1: VPN from unusual location...")
alert1 = engine.ingest_alert({
    'alert_type': 'vpn_anomaly',
    'user_id': 'suspect_user',
    'severity': 'high',
    'source_location': 'Unknown VPN - Eastern Europe',
    'action': 'VPN login from new geographic location',
    'timestamp': '2026-01-18T02:34:00Z'
}, auto_escalate=False)  # Don't auto-escalate yet
print(f"   Risk Score: {alert1.departure_risk_score:.1f}")
print(f"   Pattern Match: {alert1.pattern_matches or 'None yet'}")
print()

time.sleep(1)

# Alert 2: Database access (triggers pattern)
print("📡 Alert 2: Database bulk export...")
alert2 = engine.ingest_alert({
    'alert_type': 'database_access',
    'user_id': 'suspect_user',
    'severity': 'critical',
    'action': 'SELECT * FROM clients, billing, campaigns',
    'details': {'rows': 15000, 'tables': ['clients', 'billing', 'campaigns']},
    'timestamp': '2026-01-18T02:47:00Z'
}, auto_escalate=False)  # Manual trigger for demo
print(f"   Risk Score: {alert2.departure_risk_score:.1f}")
print(f"   🚨 Pattern Match: {alert2.pattern_matches}")
print()

# Now trigger LOCAL Security Attacker
print("="*60)
print("🤖 TRIGGERING LOCAL SECURITY ATTACKER AGENT...")
print("   Mode: 100% LOCAL - Zero LLM calls")
print("="*60)
print()

time.sleep(1)

# Get the analysis
analysis = engine.trigger_security_attacker('suspect_user', use_local=True)

print(f"Agent: {analysis['agent']}")
print(f"Mode: {analysis['mode']}")
print(f"Triggered By: {analysis['triggered_by']}")
print(f"Risk Score: {analysis['risk_score']}")
print(f"Confidence: {analysis['confidence']}")
print()
print(f"THREAT TYPE: {analysis['threat_type']}")
print(f"SEVERITY: {analysis['severity']}")
print(f"OBJECTIVE: {analysis['attack_objective']}")
print()

print("IMMEDIATE ACTIONS:")
print("-"*50)
for action in analysis['immediate_actions']:
    print(f"  □ {action}")
print()

print("FORENSIC PRESERVATION:")
print("-"*50)
for item in analysis['forensic_preservation']:
    print(f"  □ {item}")
print()

print("NOTIFICATIONS:")
print("-"*50)
for notify in analysis['notifications']:
    print(f"  □ {notify}")
print()

print("PREVENTION RECOMMENDATIONS:")
print("-"*50)
for rec in analysis['prevention_recommendations']:
    print(f"  • {rec}")
print()

print("""
════════════════════════════════════════════════════════════════════
✅ ANALYSIS COMPLETE - 100% LOCAL
   No data sent to Claude, Gemini, or any external LLM.
   This is the AION way: proprietary, private, self-contained.
════════════════════════════════════════════════════════════════════
""")
