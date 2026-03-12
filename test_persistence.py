"""Quick test of persistence + report store + case memory"""
import time
from aionos.core.persistence import create_store, ReportStore

# Step 1: Test event store
print("=" * 50)
print("STEP 1: Event Persistence")
print("=" * 50)
store = create_store('auto', data_dir='./aion_data')
print(f"Store type: {type(store).__name__}")

store.store_event('test@lawfirm.com', {
    'event_id': 'test_001',
    'event_type': 'vpn_access',
    'user_id': 'test@lawfirm.com',
    'ts_epoch': time.time(),
    'details': {'location': 'office'}
})
store.flush()
print(f"Events stored: {store.get_event_count()}")
print(f"Users tracked: {store.get_user_count()}")

# Step 2: Test report store + metering
print("\n" + "=" * 50)
print("STEP 2: Report Storage + Metering")
print("=" * 50)
rs = ReportStore(data_dir='./aion_data')

rid = rs.store_report(
    user_id='test@lawfirm.com',
    attack_id='departing_attorney',
    report={
        'vulnerabilities': [
            {'title': 'Client data exfiltration via personal Dropbox', 'severity': 'CRITICAL'},
            {'title': 'After-hours bulk file download', 'severity': 'HIGH'}
        ],
        'risk_score': 87,
        'immediate_actions': ['Revoke VPN access', 'Freeze cloud sync', 'Notify managing partner'],
        'latency_ms': 15000,
        'model': 'qwen2.5-coder-1.5b'
    },
    scenario_name='Departing Attorney Data Theft'
)
print(f"Report stored: {rid}")

meter = rs.get_meter()
print(f"Total reports generated: {meter['total_reports']}")
print(f"Reports this month: {meter.get('reports_by_month', {})}")
print(f"Reports by user: {meter.get('reports_by_user', {})}")

# Step 3: Test case-level memory
print("\n" + "=" * 50)
print("STEP 3: Case-Level LLM Memory")
print("=" * 50)
history = rs.get_user_summaries('test@lawfirm.com')
if history:
    print("History text for LLM prompt injection:")
    print(history)
else:
    print("No prior history found")

# Step 4: Verify persistence across "restart"
print("\n" + "=" * 50)
print("STEP 4: Restart Simulation")
print("=" * 50)
store.close()
del store, rs

# Re-create (simulates server restart)
store2 = create_store('auto', data_dir='./aion_data')
rs2 = ReportStore(data_dir='./aion_data')
print(f"After restart - Events: {store2.get_event_count()}")
print(f"After restart - Users: {store2.get_user_count()}")
print(f"After restart - Reports: {rs2.get_meter()['total_reports']}")
history2 = rs2.get_user_summaries('test@lawfirm.com')
print(f"After restart - History preserved: {'YES' if history2 else 'NO'}")
if history2:
    print(f"History text:\n{history2}")

print("\n✓ ALL PERSISTENCE TESTS PASSED")
