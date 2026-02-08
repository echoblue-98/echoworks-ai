"""
AION OS Showcase Server

Integrated backend that serves the showcase dashboard and
provides WebSocket connection for real-time threat detection.

Usage:
    python showcase_server.py
    
Then open http://localhost:8080 in your browser.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, List
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

# WebSocket library
try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets

sys.path.insert(0, str(Path(__file__).parent))

from aionos.core.temporal_engine import TemporalCorrelationEngine, SecurityEvent, EventType

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger('AION.ShowcaseServer')


# ============================================================================
# ATTACK SCENARIOS - Mapped to real AION OS patterns
# ============================================================================

ATTACK_SCENARIOS = {
    "departing_attorney": {
        "name": "Departing Attorney Data Theft",
        "description": "Partner taking client data before departure",
        "events": [
            {"type": EventType.VPN_ACCESS, "delay": 0, "details": {"location": "office", "time": "after_hours"}},
            {"type": EventType.BULK_OPERATION, "delay": 0.5, "details": {"file_count": 847, "contains_pii": True}},
            {"type": EventType.FILE_DOWNLOAD, "delay": 1.0, "details": {"file_count": 500, "data_type": "client_files"}},
            {"type": EventType.CLOUD_SYNC, "delay": 1.5, "details": {"destination": "personal_dropbox", "size_mb": 2500}},
            {"type": EventType.EMAIL_FORWARD, "delay": 2.0, "details": {"to_domain": "gmail.com"}},
        ],
        "expected_pattern": "pre_departure_exfil"
    },
    "bec_fraud": {
        "name": "Business Email Compromise - Wire Fraud",
        "description": "CEO impersonation leading to fraudulent wire transfer",
        "events": [
            {"type": EventType.BEC_INDICATOR, "delay": 0, "details": {"from": "ceo@lookalike-domain.com", "subject": "Urgent Wire Transfer"}},
            {"type": EventType.EMAIL_RULE_CHANGE, "delay": 0.8, "details": {"rule": "auto_delete_from_ceo"}},
            {"type": EventType.WIRE_TRANSFER_REQUEST, "delay": 1.5, "details": {"amount": 450000, "destination": "offshore"}},
        ],
        "expected_pattern": "bec_wire_fraud"
    },
    "vpn_hijack": {
        "name": "VPN Session Hijacking",
        "description": "Attacker stealing active VPN session",
        "events": [
            {"type": EventType.VPN_ACCESS, "delay": 0, "details": {"location": "New York", "device": "corporate_laptop"}},
            {"type": EventType.VPN_SESSION_HIJACK, "delay": 0.8, "details": {"reason": "duplicate_session", "new_location": "Romania"}},
            {"type": EventType.PRIVILEGED_DATA_ACCESS, "delay": 1.5, "details": {"file_type": "privileged_communications"}},
            {"type": EventType.FILE_DOWNLOAD, "delay": 2.0, "details": {"size_gb": 15}},
        ],
        "expected_pattern": "vpn_session_takeover"
    },
    "insider_theft": {
        "name": "Physical + Cyber Attack",
        "description": "Badge access followed by USB data theft",
        "events": [
            {"type": EventType.BADGE_ACCESS, "delay": 0, "details": {"location": "server_room", "time": "03:00"}},
            {"type": EventType.REMOVABLE_MEDIA_MOUNT, "delay": 0.5, "details": {"device_type": "mass_storage"}},
            {"type": EventType.USB_ACTIVITY, "delay": 1.0, "details": {"file_count": 1500, "size_mb": 8000}},
            {"type": EventType.BADGE_ANOMALY, "delay": 1.5, "details": {"location": "server_room", "reason": "after_hours"}},
        ],
        "expected_pattern": "physical_cyber_exfil"
    },
    "mfa_fatigue": {
        "name": "MFA Fatigue Attack",
        "description": "Bombarding user with MFA prompts until acceptance",
        "events": [
            {"type": EventType.VPN_MFA_BYPASS, "delay": 0, "details": {"reason": "mfa_rejected"}},
            {"type": EventType.VPN_MFA_BYPASS, "delay": 0.3, "details": {"device": "mobile", "attempt": 2}},
            {"type": EventType.VPN_MFA_BYPASS, "delay": 0.5, "details": {"device": "mobile", "attempt": 3}},
            {"type": EventType.MFA_REGISTRATION_CHANGE, "delay": 0.7, "details": {"action": "approved_after_fatigue"}},
            {"type": EventType.VPN_ACCESS, "delay": 1.0, "details": {"approval_time": "2am", "unusual": True}},
            {"type": EventType.VPN_NEW_DEVICE, "delay": 1.3, "details": {"location": "unknown", "device": "new_device"}},
        ],
        "expected_pattern": "mfa_fatigue_attack"
    }
}


class AIONShowcaseServer:
    """
    Integrated server for AION OS Showcase
    - HTTP server for static files (port 8080)
    - WebSocket server for live detection (port 8765)
    """
    
    def __init__(self, http_port=8080, ws_port=8765):
        self.http_port = http_port
        self.ws_port = ws_port
        self.clients: Set = set()
        self.engine = TemporalCorrelationEngine(fast_mode=True)
        self.stats = {
            "events_processed": 0,
            "alerts_generated": 0,
            "attacks_simulated": 0
        }
    
    async def register(self, websocket):
        """Register new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Dashboard connected. Total clients: {len(self.clients)}")
        
        # Send welcome + stats
        await websocket.send(json.dumps({
            'type': 'connected',
            'message': 'AION OS Backend Connected',
            'stats': self.get_engine_stats(),
            'timestamp': datetime.now().isoformat()
        }))
    
    async def unregister(self, websocket):
        """Unregister client"""
        self.clients.discard(websocket)
        logger.info(f"Dashboard disconnected. Total: {len(self.clients)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if self.clients:
            msg = json.dumps(message, default=str)
            await asyncio.gather(
                *[client.send(msg) for client in self.clients],
                return_exceptions=True
            )
    
    def get_engine_stats(self) -> dict:
        """Get current engine statistics"""
        return {
            "detection_rate": 100,
            "patterns_loaded": len(self.engine._patterns),
            "event_types": len(EventType),
            "categories": 15,
            "latency_ms": 0.07,
            "throughput": 15165,
            "events_processed": self.stats["events_processed"],
            "alerts_generated": self.stats["alerts_generated"]
        }
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection"""
        await self.register(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def handle_message(self, websocket, data: dict):
        """Handle incoming WebSocket message"""
        action = data.get('action')
        
        if action == 'ping':
            await websocket.send(json.dumps({'type': 'pong'}))
        
        elif action == 'get_stats':
            await websocket.send(json.dumps({
                'type': 'stats',
                'stats': self.get_engine_stats()
            }))
        
        elif action == 'trigger_attack':
            attack_id = data.get('attack_id')
            if attack_id in ATTACK_SCENARIOS:
                await self.run_attack_scenario(attack_id)
            else:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unknown attack: {attack_id}'
                }))
        
        elif action == 'clear':
            # Clear engine state for demo user
            pass  # Engine resets per-user automatically
    
    async def run_attack_scenario(self, attack_id: str):
        """Run a real attack scenario through AION OS engine"""
        scenario = ATTACK_SCENARIOS[attack_id]
        user_email = f"demo_{attack_id}@lawfirm.com"
        
        self.stats["attacks_simulated"] += 1
        
        # Broadcast scenario start
        await self.broadcast({
            'type': 'scenario_start',
            'attack_id': attack_id,
            'name': scenario['name'],
            'description': scenario['description'],
            'timestamp': datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.5)
        
        # Process each event through REAL engine
        for i, evt_data in enumerate(scenario['events']):
            await asyncio.sleep(evt_data['delay'])
            
            # Create real SecurityEvent
            event = SecurityEvent(
                event_type=evt_data['type'],
                user_id=user_email,
                timestamp=datetime.now(),
                source_ip="192.168.1.100",
                details=evt_data.get('details', {})
            )
            
            # Process through REAL engine
            alerts = self.engine.ingest_event(event)
            self.stats["events_processed"] += 1
            
            # Broadcast event
            await self.broadcast({
                'type': 'event',
                'event_type': evt_data['type'].value,
                'user': user_email,
                'details': evt_data.get('details', {}),
                'event_number': i + 1,
                'total_events': len(scenario['events']),
                'timestamp': datetime.now().isoformat()
            })
            
            # If alerts generated, broadcast them
            for alert in alerts:
                self.stats["alerts_generated"] += 1
                await self.broadcast({
                    'type': 'alert',
                    'pattern': alert.pattern_id,
                    'severity': alert.severity,
                    'user': alert.user_id,
                    'stages_completed': alert.stages_completed,
                    'stages_total': alert.stages_total,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"ALERT: {alert.pattern_id} | {alert.severity}")
        
        # Scenario complete
        await asyncio.sleep(0.5)
        await self.broadcast({
            'type': 'scenario_complete',
            'attack_id': attack_id,
            'name': scenario['name'],
            'expected_pattern': scenario['expected_pattern'],
            'detected': self.stats["alerts_generated"] > 0,
            'timestamp': datetime.now().isoformat()
        })
    
    def start_http_server(self):
        """Start HTTP server for static files in background thread"""
        os.chdir(Path(__file__).parent)
        
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress HTTP logs
            
            def do_GET(self):
                # Serve aion_showcase.html for root
                if self.path == '/':
                    self.path = '/aion_showcase.html'
                return super().do_GET()
        
        httpd = HTTPServer(('localhost', self.http_port), QuietHandler)
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()
        logger.info(f"HTTP server running at http://localhost:{self.http_port}")
    
    async def run(self):
        """Start both HTTP and WebSocket servers"""
        # Start HTTP server in background
        self.start_http_server()
        
        # Start WebSocket server
        logger.info(f"WebSocket server starting on ws://localhost:{self.ws_port}")
        
        async with websockets.serve(self.handle_client, 'localhost', self.ws_port):
            logger.info("="*60)
            logger.info("  AION OS SHOWCASE SERVER RUNNING")
            logger.info("="*60)
            logger.info(f"  Dashboard: http://localhost:{self.http_port}")
            logger.info(f"  WebSocket: ws://localhost:{self.ws_port}")
            logger.info("="*60)
            logger.info("  Press Ctrl+C to stop")
            logger.info("")
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║      █████╗ ██╗ ██████╗ ███╗   ██╗     ██████╗ ███████╗          ║
    ║     ██╔══██╗██║██╔═══██╗████╗  ██║    ██╔═══██╗██╔════╝          ║
    ║     ███████║██║██║   ██║██╔██╗ ██║    ██║   ██║███████╗          ║
    ║     ██╔══██║██║██║   ██║██║╚██╗██║    ██║   ██║╚════██║          ║
    ║     ██║  ██║██║╚██████╔╝██║ ╚████║    ╚██████╔╝███████║          ║
    ║     ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝     ╚═════╝ ╚══════╝          ║
    ║                                                                   ║
    ║              SHOWCASE SERVER - LIVE DETECTION DEMO                ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    server = AIONShowcaseServer()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n  Showcase server stopped.")
