import warnings
warnings.filterwarnings('ignore')
from aionos.core.temporal_engine import TemporalCorrelationEngine, SecurityEvent, EventType
from datetime import datetime, timedelta

# Fresh engine for EACH scenario
def test_fresh(name, events):
    engine = TemporalCorrelationEngine()  # FRESH ENGINE
    user = name.lower().replace(' ', '_') + '@test.com'
    base = datetime.now() - timedelta(hours=2)
    
    print(f'\n{name}')
    print(f'  User: {user}')
    for i, (etype, delay) in enumerate(events):
        ts = base + timedelta(hours=delay)
        event = SecurityEvent(
            event_id=f'evt_{i}',
            user_id=user,
            event_type=etype,
            timestamp=ts,
            source_system='test'
        )
        alerts = engine.ingest_event(event)
        if alerts:
            print(f'  DETECTED at event {i+1}: {alerts[0].pattern_name}')
            return True
    print(f'  NOT DETECTED')
    return False

# Test each scenario with fresh engine
test_fresh('VPN Session Hijacking', [
    (EventType.VPN_SESSION_HIJACK, 0),
    (EventType.IMPOSSIBLE_TRAVEL, 0.05),
    (EventType.DATABASE_QUERY, 0.1),
])

test_fresh('MFA Fatigue Attack', [
    (EventType.VPN_MFA_BYPASS, 0),
    (EventType.VPN_ACCESS, 0.1),
    (EventType.GEOGRAPHIC_ANOMALY, 0.2),
])

test_fresh('Concurrent Session', [
    (EventType.VPN_CONCURRENT_SESSION, 0),
    (EventType.DATABASE_QUERY, 0.05),
    (EventType.FILE_DOWNLOAD, 0.1),
])

test_fresh('Service Account', [
    (EventType.SERVICE_ACCOUNT_USE, 0),
    (EventType.DATABASE_QUERY, 0.1),
    (EventType.BULK_OPERATION, 0.5),
])
