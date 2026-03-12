"""Quick test of baseline volume spike detection with realistic timing."""
from aionos.core.baseline_engine import get_baseline_engine, BehavioralBaselineEngine
from datetime import datetime, timedelta

# Fresh engine instance
engine = BehavioralBaselineEngine()
user_id = 'spike_test@company.com'

# Build baseline: 1 file download per day for 30 days
print("=" * 60)
print("BASELINE ENGINE VOLUME SPIKE TEST")
print("=" * 60)

now = datetime.now()
print(f"\nBuilding 30-day baseline (1 download/day)...")
for day in range(30, 0, -1):  # 30 days ago to yesterday
    ts = now - timedelta(days=day, hours=10)
    engine.record_event(user_id, 'file_download', ts, {'size': 1})

profile = engine.get_user_profile(user_id)
print(f"  Daily average: {profile['behaviors']['file_download']['daily_avg']}")
print(f"  Max daily: {profile['behaviors']['file_download']['max_daily']}")
print(f"  Data points: {profile.get('data_points', 0)}")
print(f"  Confidence: {profile.get('confidence', 'N/A')}")

# Now simulate attack: 10 downloads TODAY
print(f"\nSimulating attack: 10 file downloads TODAY...")
for i in range(10):
    ts = now - timedelta(minutes=60-i*5)  # All within last hour
    alerts = engine.record_event(user_id, 'file_download', ts, {'size': 50, 'path': f'/sensitive/file_{i}.docx'})
    if alerts:
        print(f"\n🚨 ALERT after download {i+1}:")
        for a in alerts:
            print(f"   Type: {a.deviation_type.value}")
            print(f"   Severity: {a.severity}")  
            print(f"   Multiplier: {a.deviation_multiplier:.1f}x normal")
            print(f"   Desc: {a.description}")

# Final profile
print(f"\nFinal profile:")
profile = engine.get_user_profile(user_id)
print(f"  Today's count: {profile['behaviors']['file_download'].get('count_today', '?')}")
print(f"  Total events: {profile['total_events_30d']}")

print("\n" + "=" * 60)
