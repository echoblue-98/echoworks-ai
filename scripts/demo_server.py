"""
AION OS Demo Server

Runs a local WebSocket server that streams simulated signals
to the aion_live.html demo interface.

This allows the visual demo to show REAL signal flow without
needing Azure/Splunk credentials.

Usage:
    python demo_server.py
    
Then open aion_live_connected.html in your browser.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set
import sys
from pathlib import Path

# WebSocket library
try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets

sys.path.insert(0, str(Path(__file__).parent))

from aionos.connectors.microsoft_graph import DemoMode, SignalType
from aionos.modules.soc_ingestion import SOCIngestionEngine
from aionos.core.local_security_attacker import LocalSecurityAttacker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AION.DemoServer')


class DemoServer:
    """WebSocket server for demo signal streaming"""
    
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set = set()
        self.soc_engine = SOCIngestionEngine()
        self.security_agent = LocalSecurityAttacker()
    
    async def register(self, websocket):
        """Register new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total: {len(self.clients)}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'connected',
            'message': 'AION Node connected',
            'timestamp': datetime.now().isoformat()
        }))
    
    async def unregister(self, websocket):
        """Unregister client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total: {len(self.clients)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message, default=str)) for client in self.clients]
            )
    
    async def handle_client(self, websocket, path):
        """Handle individual client connection"""
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data.get('action') == 'trigger_vpn':
                    await self.run_vpn_demo()
                elif data.get('action') == 'trigger_departure':
                    await self.run_departure_demo()
                elif data.get('action') == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def run_vpn_demo(self):
        """Run VPN breach demo sequence"""
        logger.info("Starting VPN breach demo...")
        
        await self.broadcast({
            'type': 'demo_start',
            'scenario': 'vpn_breach',
            'title': 'VPN Breach Detected'
        })
        
        sequence = DemoMode.generate_vpn_breach_sequence()
        
        for i, signal in enumerate(sequence):
            await asyncio.sleep(signal['delay'] if i > 0 else 1)
            
            # Broadcast signal
            await self.broadcast({
                'type': 'signal',
                'signal_type': signal['signal_type'].value,
                'user': signal['user'],
                'severity': signal['severity'],
                'details': signal['details'],
                'timestamp': datetime.now().isoformat(),
                'signal_number': i + 1,
                'total_signals': len(sequence)
            })
            
            logger.info(f"Signal {i+1}/{len(sequence)}: {signal['signal_type'].value}")
        
        # Run agent analysis
        await asyncio.sleep(1)
        await self.broadcast({'type': 'agents_start'})
        
        # Simulate each agent
        agents = [
            ('security_attacker', 'Security Attacker', 2.0),
            ('network_breacher', 'Network Breacher', 1.8),
            ('data_exfiltrator', 'Data Exfiltrator', 2.2),
            ('insider_tracker', 'Insider Tracker', 1.5),
            ('evidence_recon', 'Evidence Recon', 2.0)
        ]
        
        findings = [
            'Attack vector: VPN credentials not revoked. 72-hour deprovisioning gap exploited. Pattern match: Typhoon Advertising 2021.',
            'Network path: VPN → 10.0.1.x → Database (SQL 1433). Firewall rules too permissive for terminated segments.',
            'Data at risk: 15,000 client records, billing, campaigns. Estimated value: $2.3M. 17-minute exfil window.',
            'Behavioral anomaly: 3 systems never accessed during employment. Pre-planned extraction route detected.',
            'Evidence secured: VPN logs, DB query logs, session recordings. Chain of custody initiated.'
        ]
        
        for i, (agent_id, agent_name, duration) in enumerate(agents):
            await self.broadcast({
                'type': 'agent_start',
                'agent_id': agent_id,
                'agent_name': agent_name
            })
            
            await asyncio.sleep(duration)
            
            await self.broadcast({
                'type': 'agent_complete',
                'agent_id': agent_id,
                'agent_name': agent_name,
                'finding': findings[i]
            })
        
        # Final diagnosis
        await asyncio.sleep(1)
        
        analysis = self.security_agent.analyze('vpn_database_theft', {
            'user': 'former_employee',
            'data_accessed': '15,000 records'
        })
        
        await self.broadcast({
            'type': 'diagnosis',
            'threat_type': analysis.threat_type,
            'severity': analysis.severity,
            'confidence': analysis.confidence,
            'immediate_actions': analysis.immediate_actions,
            'forensic_preservation': analysis.forensic_preservation,
            'notifications': analysis.notifications
        })
        
        # Bypass blocking
        await asyncio.sleep(2)
        
        bypasses = [
            {
                'attempt': 'Use different VPN endpoint to avoid geo-detection',
                'blocked': 'AION fingerprints device + credential pair, not just IP',
                'source': 'Pattern: Typhoon Advertising 2021'
            },
            {
                'attempt': 'Export data in small chunks under DLP threshold',
                'blocked': 'Cumulative query tracking active. Aggregate flagged.',
                'source': 'Pattern: M&A Partner Lateral 2023'
            },
            {
                'attempt': 'Use admin account to mask activity',
                'blocked': 'Behavioral baseline detects role-inconsistent access',
                'source': 'Pattern: Insider Threat Profile DB'
            },
            {
                'attempt': 'Delete access logs after exfiltration',
                'blocked': 'Immutable log shipping. Deletion triggers instant alert.',
                'source': 'Pattern: Evidence Spoliation Cases'
            }
        ]
        
        for bypass in bypasses:
            await self.broadcast({
                'type': 'bypass_blocked',
                'attempt': bypass['attempt'],
                'blocked': bypass['blocked'],
                'source': bypass['source']
            })
            await asyncio.sleep(1.5)
        
        await self.broadcast({
            'type': 'demo_complete',
            'scenario': 'vpn_breach',
            'detection_time': '13 minutes',
            'status': 'ALL THREATS NEUTRALIZED'
        })
    
    async def run_departure_demo(self):
        """Run attorney departure demo sequence"""
        logger.info("Starting attorney departure demo...")
        
        await self.broadcast({
            'type': 'demo_start',
            'scenario': 'attorney_departure',
            'title': 'Attorney Departure Risk'
        })
        
        sequence = DemoMode.generate_departure_sequence()
        
        for i, signal in enumerate(sequence):
            await asyncio.sleep(signal['delay'] if i > 0 else 1)
            
            await self.broadcast({
                'type': 'signal',
                'signal_type': signal['signal_type'].value,
                'user': signal['user'],
                'severity': signal['severity'],
                'details': signal['details'],
                'timestamp': datetime.now().isoformat(),
                'signal_number': i + 1,
                'total_signals': len(sequence)
            })
            
            logger.info(f"Signal {i+1}/{len(sequence)}: {signal['signal_type'].value}")
        
        # Agent analysis
        await asyncio.sleep(1)
        await self.broadcast({'type': 'agents_start'})
        
        agents = [
            ('security_attacker', 'Security Attacker', 1.8),
            ('network_breacher', 'Network Breacher', 2.0),
            ('data_exfiltrator', 'Data Exfiltrator', 2.5),
            ('insider_tracker', 'Insider Tracker', 2.2),
            ('evidence_recon', 'Evidence Recon', 1.8)
        ]
        
        findings = [
            'Threat: Partner has access to 847 client files, 12 years of relationship equity. High exfiltration likelihood.',
            'Access audit: 234 docs downloaded in 7 days (baseline: 45). Email forward to personal Gmail active.',
            'Exfil targets: Client contacts, deal memos, pricing strategies, pending M&A targets. USB activity detected.',
            'Behavioral match: LinkedIn +400% in 30 days. After-hours client contact via personal phone. Pre-departure signature.',
            'Evidence: Email metadata preserved. Document access logs secured. Personal device subpoena may be required.'
        ]
        
        for i, (agent_id, agent_name, duration) in enumerate(agents):
            await self.broadcast({
                'type': 'agent_start',
                'agent_id': agent_id,
                'agent_name': agent_name
            })
            await asyncio.sleep(duration)
            await self.broadcast({
                'type': 'agent_complete',
                'agent_id': agent_id,
                'agent_name': agent_name,
                'finding': findings[i]
            })
        
        # Diagnosis
        await asyncio.sleep(1)
        
        analysis = self.security_agent.analyze('pre_departure_exfil', {
            'user': 'sarah.johnson@demolaw.com',
            'role': 'Senior Partner'
        })
        
        await self.broadcast({
            'type': 'diagnosis',
            'threat_type': analysis.threat_type,
            'severity': analysis.severity,
            'confidence': analysis.confidence,
            'immediate_actions': analysis.immediate_actions,
            'forensic_preservation': analysis.forensic_preservation,
            'notifications': analysis.notifications
        })
        
        # Bypasses
        await asyncio.sleep(2)
        
        bypasses = [
            {
                'attempt': "Forward emails to spouse's email instead",
                'blocked': 'All non-firm domain forwarding flagged',
                'source': 'Pattern: Lateral Partner Move 2022'
            },
            {
                'attempt': 'Print documents instead of downloading',
                'blocked': 'Print queue monitoring active. Bulk printing triggers review.',
                'source': 'Pattern: Physical Exfil Protocol'
            },
            {
                'attempt': 'Take photos of screen with personal phone',
                'blocked': 'Sensitive doc watermarking enables post-leak tracing',
                'source': 'Pattern: Visual Exfil Detection'
            },
            {
                'attempt': 'Wait until after departure to contact clients',
                'blocked': 'Client communication monitoring continues 90 days post-exit',
                'source': 'Pattern: Non-Solicitation Enforcement'
            }
        ]
        
        for bypass in bypasses:
            await self.broadcast({
                'type': 'bypass_blocked',
                'attempt': bypass['attempt'],
                'blocked': bypass['blocked'],
                'source': bypass['source']
            })
            await asyncio.sleep(1.5)
        
        await self.broadcast({
            'type': 'demo_complete',
            'scenario': 'attorney_departure',
            'detection_time': '< 24 hours',
            'status': 'ALL THREATS NEUTRALIZED'
        })
    
    async def run(self):
        """Start the WebSocket server"""
        logger.info(f"Starting AION Demo Server on ws://{self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info("Demo server running. Open aion_live_connected.html")
            logger.info("Press Ctrl+C to stop")
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                 🔴 AION OS DEMO SERVER                        ║
    ║                                                               ║
    ║        WebSocket server for live demo visualization           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    server = DemoServer()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nDemo server stopped.")
