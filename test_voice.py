"""Test voice synthesis pipeline directly"""
import asyncio
import json
import websockets

async def test_voice():
    uri = 'ws://localhost:8765'
    print('Connecting to', uri)
    async with websockets.connect(uri) as ws:
        # Enable voice
        await ws.send(json.dumps({'action': 'voice_toggle', 'enabled': True}))
        msg = await ws.recv()
        print('Voice toggle response:', msg)
        
        # Trigger attack
        await ws.send(json.dumps({'action': 'trigger_attack', 'attack_id': 'departing_attorney'}))
        
        # Listen for messages
        for _ in range(30):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(msg)
                msg_type = data.get('type')
                if msg_type == 'voice_audio':
                    audio_len = len(data.get('audio', ''))
                    print(f"🔊 VOICE_AUDIO received: {audio_len} chars")
                elif msg_type == 'voice_state':
                    print(f"🔊 Voice state: {data.get('enabled')}")
                elif msg_type == 'alert':
                    print(f"⚠️  ALERT: {data.get('pattern')} [{data.get('severity')}]")
                elif msg_type == 'scenario_start':
                    print(f"▶️  SCENARIO START: {data.get('name')}")
                elif msg_type == 'scenario_complete':
                    print(f"✓  SCENARIO COMPLETE: detected={data.get('detected')}")
                elif msg_type == 'analysis_start':
                    print(f"🧠 ANALYSIS START")
                elif msg_type == 'analysis_complete':
                    print(f"🧠 ANALYSIS COMPLETE: risk={data.get('analysis', {}).get('risk_score')}")
                else:
                    print(f"   {msg_type}")
            except asyncio.TimeoutError:
                print("Timeout - no more messages")
                break

if __name__ == '__main__':
    asyncio.run(test_voice())
