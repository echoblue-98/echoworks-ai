"""Quick test of showcase server and document analysis"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    print("Testing WebSocket connection...")
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            # Test get_stats
            await ws.send(json.dumps({'action': 'get_stats'}))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            print(f"  ✓ Connected — Type: {data.get('type')}")
            if data.get('stats'):
                print(f"  ✓ Patterns: {data['stats'].get('patterns_loaded')}")
                print(f"  ✓ Categories: {data['stats'].get('categories')}")
            return True
    except Exception as e:
        print(f"  ✗ WebSocket Error: {e}")
        return False


async def test_doc_analysis():
    print("\nTesting Document Analysis...")
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            # Skip the initial connected message
            _ = await asyncio.wait_for(ws.recv(), timeout=5)
            
            # Send analyze_document
            test_text = """
            This Agreement grants Company exclusive rights to all Artist's 
            intellectual property in perpetuity throughout the world. Artist 
            waives any right to compensation beyond minimum required by law.
            All recordings shall be work made for hire and Company's property.
            """
            
            await ws.send(json.dumps({
                'action': 'analyze_document',
                'text': test_text,
                'doc_type': 'recording_agreement',
                'title': 'Test Contract'
            }))
            
            # Wait for analysis_start
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            print(f"  ✓ Received: {data.get('type')}")
            
            # Wait for analysis_complete
            response = await asyncio.wait_for(ws.recv(), timeout=30)
            data = json.loads(response)
            print(f"  ✓ Received: {data.get('type')}")
            
            if data.get('type') == 'doc_analysis_complete':
                print(f"  ✓ Risk Score: {data.get('risk_score')}/100")
                print(f"  ✓ Overall Risk: {data.get('overall_risk')}")
                print(f"  ✓ Clauses Found: {len(data.get('clauses', []))}")
                print(f"  ✓ Red Flags: {len(data.get('red_flags', []))}")
                return True
            else:
                print(f"  ✗ Unexpected response: {data.get('type')}")
                return False
                
    except asyncio.TimeoutError:
        print("  ✗ Timeout waiting for response")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


async def main():
    print("=" * 50)
    print("AION OS Integration Test")
    print("=" * 50)
    
    ws_ok = await test_websocket()
    doc_ok = await test_doc_analysis()
    
    print("\n" + "=" * 50)
    if ws_ok and doc_ok:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("=" * 50)
    
    return 0 if (ws_ok and doc_ok) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
