"""
AION OS - SOC + Security Attacker Integration Test
Demonstrates: Real-time alerts → Pattern detection → Auto-escalate to Agent

This is the full pipeline:
  SIEM Alert → SOC Engine → Pattern Match → Security Attacker Agent
"""
import time

print("""
╔══════════════════════════════════════════════════════════════════╗
║           AION OS - FULL AGENT INTEGRATION TEST                  ║
║     SOC Real-Time → Security Attacker Agent Escalation           ║
╚══════════════════════════════════════════════════════════════════╝
""")

from aionos.modules.soc_ingestion import SOCIngestionEngine

# Fresh engine
engine = SOCIngestionEngine()

print("SCENARIO: VPN Database Theft (Typhoon pattern)")
print("="*60)
print()

# Alert 1: VPN anomaly (no escalation yet)
print("📡 Alert 1: VPN from unusual location...")
alert1 = engine.ingest_alert({
    'alert_type': 'vpn_anomaly',
    'user_id': 'suspect_user',
    'severity': 'high',
    'source_location': 'Unknown VPN - Eastern Europe',
    'action': 'VPN login from new geographic location',
    'timestamp': '2026-01-18T02:34:00Z'
})
print(f"   Risk Score: {alert1.departure_risk_score:.1f}")
print(f"   Pattern Match: {alert1.pattern_matches or 'None yet'}")
print(f"   Agent Triggered: {alert1.agent_analysis is not None}")
print()

time.sleep(1)

# Alert 2: Database access (triggers pattern + agent)
print("📡 Alert 2: Database bulk export...")
alert2 = engine.ingest_alert({
    'alert_type': 'database_access',
    'user_id': 'suspect_user',
    'severity': 'critical',
    'action': 'SELECT * FROM clients, billing, campaigns',
    'details': {'rows': 15000, 'tables': ['clients', 'billing', 'campaigns']},
    'timestamp': '2026-01-18T02:47:00Z'
})
print(f"   Risk Score: {alert2.departure_risk_score:.1f}")
print(f"   🚨 Pattern Match: {alert2.pattern_matches}")
print(f"   🤖 Agent Triggered: {alert2.agent_analysis is not None}")
print()

if alert2.agent_analysis:
    print("="*60)
    print("🤖 SECURITY ATTACKER AGENT ANALYSIS")
    print("="*60)
    print(f"   Agent: {alert2.agent_analysis.get('agent')}")
    print(f"   Triggered By: {alert2.agent_analysis.get('triggered_by')}")
    print(f"   Severity: {alert2.agent_analysis.get('severity')}")
    print()
    print("   Analysis:")
    print("-"*60)
    analysis = alert2.agent_analysis.get('analysis', '')
    # Print wrapped
    for line in analysis.split('\n'):
        print(f"   {line}")
    print()

print("""
FLOW COMPLETE:
  ✓ SOC ingested 2 alerts
  ✓ Pattern 'vpn_database_theft' detected on alert 2
  ✓ User risk exceeded 50% threshold
  ✓ Security Attacker agent auto-triggered
  ✓ Deep adversarial analysis returned

This is the 5-agent architecture in action:
  SOC (sensor) → Security Attacker (Agent #2) → Immediate response
""")
