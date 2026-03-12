"""Test the temporal correlation engine integration."""

from aionos.core.temporal_engine import TemporalCorrelationEngine, SecurityEvent, EventType
from datetime import datetime, timedelta
from pathlib import Path
import uuid

print('Testing Temporal Correlation Engine...')
print('=' * 60)

# Create engine
engine = TemporalCorrelationEngine(Path('aionos/knowledge/test_events.json'))

# Simulate alerts coming in from Dan's gems over time
now = datetime.utcnow()

# Day 1: VPN access (normal looking)
e1 = SecurityEvent(
    event_id=str(uuid.uuid4()),
    user_id='strevino@typhoon.com',
    event_type=EventType.VPN_ACCESS,
    timestamp=now - timedelta(days=5),
    source_system='cloudflare_gem',
    details={'ip': '192.168.1.100', 'location': 'Austin, TX'}
)
alerts1 = engine.ingest_event(e1)
print(f'Day 1 - VPN Access: {len(alerts1)} alerts')

# Day 3: Database query (normal looking)
e2 = SecurityEvent(
    event_id=str(uuid.uuid4()),
    user_id='strevino@typhoon.com',
    event_type=EventType.DATABASE_QUERY,
    timestamp=now - timedelta(days=3),
    source_system='sql_gem',
    details={'query': 'SELECT * FROM clients', 'rows': 25000}
)
alerts2 = engine.ingest_event(e2)
print(f'Day 3 - DB Query: {len(alerts2)} alerts')
if alerts2:
    print(f'  -> PATTERN DETECTED: {alerts2[0].pattern_name} ({alerts2[0].completion_percent:.0f}%)')

# Day 4: Bulk operation (suspicious in context)
e3 = SecurityEvent(
    event_id=str(uuid.uuid4()),
    user_id='strevino@typhoon.com',
    event_type=EventType.BULK_OPERATION,
    timestamp=now - timedelta(days=2),
    source_system='file_gem',
    details={'operation': 'copy', 'files': 8000}
)
alerts3 = engine.ingest_event(e3)
print(f'Day 4 - Bulk Op: {len(alerts3)} alerts')
if alerts3:
    for a in alerts3:
        print(f'  -> PATTERN DETECTED: {a.pattern_name} ({a.completion_percent:.0f}%)')
        print(f'     SEVERITY: {a.severity}')
        print(f'     ACTIONS: {a.recommended_actions[0]}')

print()
print('=' * 60)
print('Timeline for strevino@typhoon.com:')
for event in engine.get_user_timeline('strevino@typhoon.com'):
    print(f"  [{event['timestamp'][:10]}] {event['event_type']}")
