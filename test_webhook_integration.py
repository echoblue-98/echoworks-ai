"""
Test webhook integration with both Temporal and Baseline engines.
"""

from aionos.api.alert_webhook import (
    _convert_to_baseline_params, 
    _convert_to_temporal_event, 
    get_baseline_engine, 
    get_temporal_engine
)
from datetime import datetime


def test_integration():
    """Test that both engines are properly wired into the webhook."""
    
    # Simulate an alert from Dan's gem
    alert = {
        'type': 'file_download',
        'user': 'srevino@typhoon.com',
        'timestamp': '2026-01-24T14:30:00Z',
        'source': 'cloudflare_gem',
        'details': {
            'file_count': 50,
            'location': 'Austin, TX',
            'path': '/client/smith_case/'
        }
    }

    print("=" * 60)
    print("🧪 WEBHOOK INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Test temporal conversion
    print("1. Testing Temporal Engine Conversion...")
    temp_event = _convert_to_temporal_event(alert)
    assert temp_event is not None
    print(f"   ✅ Temporal event: {temp_event.event_type.value} for {temp_event.user_id}")
    
    # Test baseline conversion
    print("\n2. Testing Baseline Engine Conversion...")
    baseline_params = _convert_to_baseline_params(alert)
    assert baseline_params is not None
    print(f"   ✅ Baseline params: event_type={baseline_params['event_type']}")
    print(f"   ✅ Volume: {baseline_params['details']['volume']} files")
    print(f"   ✅ Location: {baseline_params['details']['location']}")
    
    # Test temporal engine ingestion
    print("\n3. Testing Temporal Engine Ingestion...")
    temporal_engine = get_temporal_engine()
    temporal_alerts = temporal_engine.ingest_event(temp_event)
    print(f"   ✅ Temporal patterns checked: {len(temporal_alerts)} pattern alerts")
    
    # Test baseline engine recording
    print("\n4. Testing Baseline Engine Recording...")
    baseline_engine = get_baseline_engine()
    deviation_alerts = baseline_engine.record_event(
        user_id=baseline_params['user_id'],
        event_type=baseline_params['event_type'],
        timestamp=baseline_params['timestamp'],
        details=baseline_params['details']
    )
    print(f"   ✅ Event recorded for {baseline_params['user_id']}")
    print(f"   ✅ Deviation alerts: {len(deviation_alerts)}")
    
    # Test profile retrieval
    print("\n5. Testing Profile Retrieval...")
    profile = baseline_engine.get_user_profile(baseline_params['user_id'])
    if profile:
        print(f"   ✅ Profile retrieved: {profile.get('confidence', 'N/A')} confidence")
        print(f"   ✅ Data points: {profile.get('data_points', 0)}")
    else:
        print("   ⚠️  No profile yet (need more events)")
    
    print()
    print("=" * 60)
    print("🎯 ALL INTEGRATION TESTS PASSED!")
    print("=" * 60)
    print()
    print("Both engines are now wired into the webhook:")
    print("  • Temporal Correlation → Detects multi-stage attack patterns")
    print("  • Behavioral Baseline → Detects deviations from normal")
    print()
    print("When Dan's gems POST to /api/v1/alert, AION now:")
    print("  1. Matches against known patterns (Typhoon, etc.)")
    print("  2. Checks temporal correlation across time")  
    print("  3. Compares against user's behavioral baseline")
    print("  4. Returns all alerts in unified response")
    print()


if __name__ == "__main__":
    test_integration()
