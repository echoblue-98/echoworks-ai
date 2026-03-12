import warnings
warnings.filterwarnings('ignore')
from red_team_full_spectrum import ExpandedRedTeamSimulator

# Fresh simulator
sim = ExpandedRedTeamSimulator()

# Run specific scenarios
test_indices = [0, 2, 4, 5, 14]  # VPN Brute Force, Session Hijack, MFA Fatigue, Concurrent, Service Account
for i in test_indices:
    s = sim.scenarios[i]
    events = [e['type'].value for e in s.events]
    result = sim.simulate_attack(s)
    print(f'{i}. {s.name}')
    print(f'   Events: {events}')
    print(f'   Detected: {result["detected"]}')
    if result['detected']:
        print(f'   Pattern: {result["detections"][0]["pattern"]}')
    print()
