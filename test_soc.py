"""Test SOC pattern detection - simulates Typhoon VPN database theft"""
from aionos.modules.soc_ingestion import get_soc_engine, ingest_alert

engine = get_soc_engine()

print("=== SIMULATING VPN DATABASE THEFT PATTERN ===")
print("(This is what happened in Dan's case)")
print()

# Alert 1: VPN from unusual location
a1 = ingest_alert({
    'alert_type': 'vpn_anomaly',
    'user_id': 'former_employee',
    'severity': 'high',
    'source_location': 'Unknown VPN endpoint',
    'action': 'VPN connection from new location'
})
print(f"1. VPN Anomaly: Risk={a1.departure_risk_score:.1f}")

# Alert 2: Database bulk access
a2 = ingest_alert({
    'alert_type': 'database_access',
    'user_id': 'former_employee',
    'severity': 'critical',
    'action': 'SELECT * FROM clients - bulk export',
    'details': {'rows': 15000, 'tables': ['clients', 'billing', 'contacts']}
})
print(f"2. Database Access: Risk={a2.departure_risk_score:.1f}")
print(f"   🚨 PATTERN MATCH: {a2.pattern_matches}")

# Show cumulative risk
status = engine.get_status()
print()
print("=== HIGH RISK USERS ===")
for user in status['high_risk_users']:
    print(f"  🔴 {user['user_id']}: {user['risk_score']:.1f}")

print()
print("=== RECOMMENDATION ===")
risk_profile = engine.get_user_risk('former_employee')
print(f"  {risk_profile['recommendation']}")
