"""Quick test of baseline engine detection."""
from aionos.core.baseline_engine import get_baseline_engine
from datetime import datetime, timedelta

engine = get_baseline_engine()
user_id = 'test_baseline@company.com'

# Build baseline with file_download only
base = datetime(2026, 1, 1)
print("Building 30-day baseline...")
for day in range(30):
    ts = base + timedelta(days=day, hours=10)
    engine.record_event(user_id, 'file_download', ts, {'size': 1})

print('Baseline built. Profile:')
profile = engine.get_user_profile(user_id)
print(f"  Behaviors: {list(profile.get('behaviors', {}).keys())}")
print(f"  file_download daily_avg: {profile['behaviors'].get('file_download', {}).get('daily_avg', 0)}")

# Now test a NEW behavior (USB activity - never seen before)
print()
print('Testing NEW behavior (usb_activity)...')
alerts = engine.record_event(user_id, 'usb_activity', datetime.now(), {'files': 100})
print(f'Alerts generated: {len(alerts)}')
for a in alerts:
    print(f'  - {a.deviation_type.value}: {a.description[:70]}...')

# Now test a VOLUME spike (10 downloads in one hour)
print()
print('Testing VOLUME spike (10 downloads in one hour)...')
for i in range(10):
    alerts = engine.record_event(user_id, 'file_download', datetime.now(), {'size': 50})
    if alerts:
        print(f'Alerts after {i+1} downloads: {len(alerts)}')
        for a in alerts:
            print(f'  - {a.deviation_type.value}: {a.severity} - {a.deviation_multiplier:.1f}x normal')
        break

print()
print("Done!")
