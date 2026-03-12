"""
AION OS - SOC Integration Demo for Dan
Real-time departure risk detection from SIEM alerts

This is what would have caught the VPN database theft.
"""
import time

print("""
╔══════════════════════════════════════════════════════════════════╗
║                    AION OS - SOC INTEGRATION                     ║
║              Real-Time Departure Risk Detection                  ║
╠══════════════════════════════════════════════════════════════════╣
║  Ingests security alerts from Splunk/Sentinel/any SIEM          ║
║  Correlates with departure risk patterns                         ║
║  Detects VPN database theft pattern (your exact scenario)        ║
╚══════════════════════════════════════════════════════════════════╝
""")

from aionos.modules.soc_ingestion import SOCIngestionEngine

# Fresh engine for demo
engine = SOCIngestionEngine()

print("5 DETECTION PATTERNS LOADED:")
print("-" * 50)
for i, p in enumerate(engine.high_risk_patterns, 1):
    print(f"  {i}. {p['name']}: {p['description']}")
print()

input("Press Enter to simulate attack sequence...\n")

# ============================================================================
# SIMULATE THE TYPHOON ATTACK
# ============================================================================

print("=" * 60)
print("SIMULATING: VPN Database Theft (Your Exact Scenario)")
print("=" * 60)
print()

# Alert 1: VPN anomaly
print("📡 INCOMING ALERT FROM SIEM...")
time.sleep(1)
alert1 = engine.ingest_alert({
    'alert_type': 'vpn_anomaly',
    'user_id': 'former_employee',
    'severity': 'high',
    'source_ip': '185.42.33.100',
    'source_location': 'Unknown - VPN Endpoint',
    'action': 'VPN connection from new location',
    'timestamp': '2026-01-18T02:34:00Z'
}, source='generic')

print(f"""
┌─────────────────────────────────────────────────────────────┐
│ ALERT 1: VPN ANOMALY                                        │
├─────────────────────────────────────────────────────────────┤
│ User:      former_employee                                  │
│ Action:    VPN connection from new location                 │
│ Location:  Unknown - VPN Endpoint                           │
│ Time:      02:34 AM (after hours)                           │
├─────────────────────────────────────────────────────────────┤
│ 🎯 Departure Risk Score: {alert1.departure_risk_score:.1f}                              │
│ 📊 Pattern Matches: {alert1.pattern_matches if alert1.pattern_matches else 'None yet'}                                │
└─────────────────────────────────────────────────────────────┘
""")

time.sleep(2)

# Alert 2: Database access
print("📡 INCOMING ALERT FROM SIEM...")
time.sleep(1)
alert2 = engine.ingest_alert({
    'alert_type': 'database_access',
    'user_id': 'former_employee',
    'severity': 'critical',
    'action': 'SELECT * FROM clients, billing, contacts',
    'details': {
        'rows_returned': 15000,
        'tables_accessed': ['clients', 'billing', 'contacts', 'campaigns'],
        'query_type': 'bulk_export'
    },
    'timestamp': '2026-01-18T02:47:00Z'
}, source='generic')

print(f"""
┌─────────────────────────────────────────────────────────────┐
│ ALERT 2: DATABASE ACCESS                                    │
├─────────────────────────────────────────────────────────────┤
│ User:      former_employee                                  │
│ Action:    Bulk export from client database                 │
│ Rows:      15,000                                           │
│ Tables:    clients, billing, contacts, campaigns            │
├─────────────────────────────────────────────────────────────┤
│ 🚨 Departure Risk Score: {alert2.departure_risk_score:.1f}                            │
│ 🔴 PATTERN MATCH: {alert2.pattern_matches}               │
└─────────────────────────────────────────────────────────────┘
""")

time.sleep(1)

# Show final analysis
print()
print("=" * 60)
print("🚨 AION REAL-TIME ANALYSIS")
print("=" * 60)

status = engine.get_status()
user_profile = engine.get_user_risk('former_employee')

print(f"""
┌─────────────────────────────────────────────────────────────┐
│ USER RISK PROFILE: former_employee                          │
├─────────────────────────────────────────────────────────────┤
│ Cumulative Risk Score: {user_profile['cumulative_risk_score']:.0f}/100                           │
│ Alert Count:           {user_profile['alert_count']}                                     │
│ Pattern Matches:       {user_profile['pattern_matches']}               │
├─────────────────────────────────────────────────────────────┤
│ 🔴 RECOMMENDATION:                                          │
│ {user_profile['recommendation'][:57]}│
│ {user_profile['recommendation'][57:] if len(user_profile['recommendation']) > 57 else ''}
└─────────────────────────────────────────────────────────────┘
""")

print("""
THIS IS WHAT WOULD HAVE CAUGHT YOUR ATTACK.

The VPN login at 2:34 AM followed by database bulk export at 2:47 AM
triggers the 'vpn_database_theft' pattern - modeled after your case.

AION would have:
  ✓ Detected the VPN anomaly in real-time
  ✓ Correlated with database access 13 minutes later
  ✓ Triggered CRITICAL alert with recommendation to revoke access
  ✓ Given you 13 minutes to act instead of discovering months later

Endpoints ready for SIEM integration:
  POST /api/soc/ingest    - Receive alerts from Splunk/Sentinel
  GET  /api/soc/status    - Dashboard view
  GET  /api/soc/user/{id} - User risk profile
""")
