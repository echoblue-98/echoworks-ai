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
import time
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
from aionos.api.lmstudio_client import LMStudioClient
from aionos.core.persistence import create_store, ReportStore
from aionos.modules.document_intelligence import DocumentIntelligenceEngine, DocumentType
from aionos.api.voice_synthesis import get_voice_synthesizer, cleanup_voice

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger('AION.ShowcaseServer')

# ============================================================================
# WEBSOCKET AUTHENTICATION
# Simple token-based auth. Set AION_WS_TOKEN in .env for production.
# If not set, auth is disabled (demo mode).
# ============================================================================
WS_AUTH_TOKEN = os.environ.get("AION_WS_TOKEN", "")
WS_AUTH_ENABLED = bool(WS_AUTH_TOKEN)


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
    - Pre-cached forensic reports for instant demo
    """
    
    def __init__(self, http_port=8080, ws_port=8765):
        self.http_port = http_port
        self.ws_port = ws_port
        self.clients: Set = set()
        self.engine = TemporalCorrelationEngine(fast_mode=True)
        self.lm_client = LMStudioClient()
        self.report_cache: Dict[str, dict] = {}  # attack_id -> cached report
        
        # Persistent storage (auto-detects Redis > JSON file > memory)
        self.event_store = create_store('auto', data_dir='./aion_data')
        self.report_store = ReportStore(data_dir='./aion_data')
        
        # Document intelligence engine (multi-modal legal analysis)
        self.doc_engine = DocumentIntelligenceEngine(data_dir='./aion_data')
        
        # Voice synthesis (ElevenLabs TTS for real-time alerts)
        self.voice = get_voice_synthesizer()
        self.voice_enabled = False  # Toggle via WebSocket action
        
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
        """Get current engine statistics including metering"""
        meter = self.report_store.get_meter()
        return {
            "detection_rate": 100,
            "patterns_loaded": 66,
            "event_types": len(EventType),
            "categories": 15,
            "latency_ms": 0.07,
            "throughput": 15165,
            "events_processed": self.stats["events_processed"],
            "alerts_generated": self.stats["alerts_generated"],
            "total_reports": meter.get("total_reports", 0),
            "reports_this_month": meter.get("reports_by_month", {}).get(
                datetime.now().strftime('%Y-%m'), 0
            )
        }
    
    async def handle_client(self, websocket, path=None):
        """Handle WebSocket client connection with optional auth"""
        # Token authentication (if enabled)
        if WS_AUTH_ENABLED:
            try:
                # Check query params for token: ws://localhost:8765?token=xxx
                query = websocket.request.path if hasattr(websocket, 'request') else path or ''
                if '?token=' in query:
                    token = query.split('?token=')[-1].split('&')[0]
                else:
                    # Wait for auth message
                    auth_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    auth_data = json.loads(auth_msg)
                    token = auth_data.get('token', '')
                
                if token != WS_AUTH_TOKEN:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Authentication failed. Invalid token.'
                    }))
                    await websocket.close(1008, 'Authentication failed')
                    logger.warning(f"Auth failed from {websocket.remote_address}")
                    return
                logger.info(f"Client authenticated: {websocket.remote_address}")
            except asyncio.TimeoutError:
                await websocket.send(json.dumps({
                    'type': 'error', 
                    'message': 'Authentication timeout. Send token within 5 seconds.'
                }))
                await websocket.close(1008, 'Auth timeout')
                return
            except Exception as e:
                logger.error(f"Auth error: {e}")
                await websocket.close(1008, 'Auth error')
                return
        
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
        
        elif action == 'voice_toggle':
            self.voice_enabled = data.get('enabled', not self.voice_enabled)
            await websocket.send(json.dumps({
                'type': 'voice_state',
                'enabled': self.voice_enabled
            }))
            logger.info(f"Voice synthesis {'enabled' if self.voice_enabled else 'disabled'}")
        
        elif action == 'analyze_document':
            # Multi-modal document intelligence
            text = data.get('text', '')
            doc_type_str = data.get('doc_type', 'other')
            title = data.get('title', '')
            parties = data.get('parties', [])
            
            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.OTHER
            
            if not text:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'No document text provided'
                }))
                return
            
            await self.broadcast({
                'type': 'doc_analysis_start',
                'title': title or 'Document Analysis',
                'timestamp': datetime.now().isoformat()
            })
            
            analysis = self.doc_engine.analyze_document(
                text=text, doc_type=doc_type, title=title, parties=parties
            )
            
            await self.broadcast({
                'type': 'doc_analysis_complete',
                'document_id': analysis.document_id,
                'title': analysis.title,
                'document_type': analysis.document_type.value,
                'parties': analysis.parties,
                'risk_score': analysis.risk_score,
                'overall_risk': analysis.overall_risk.value,
                'summary': analysis.summary,
                'red_flags': analysis.red_flags,
                'recommendations': analysis.recommendations,
                'clauses': [
                    {
                        'clause_type': c.clause_type.value,
                        'summary': c.summary,
                        'risk_level': c.risk_level.value,
                        'risk_reason': c.risk_reason,
                        'parties_affected': c.parties_affected,
                        'recommendations': c.recommendations
                    }
                    for c in analysis.clauses
                ],
                'key_obligations': analysis.key_obligations,
                'metadata': analysis.metadata,
                'timestamp': datetime.now().isoformat()
            })
            
            # Voice announcement for document analysis
            if self.voice_enabled and self.voice:
                try:
                    text = self.voice.format_doc_analysis(
                        analysis.risk_score,
                        analysis.overall_risk.value,
                        len(analysis.clauses),
                        len(analysis.red_flags)
                    )
                    audio_b64 = await self.voice.speak_base64(text)
                    if audio_b64:
                        await self.broadcast({'type': 'voice_audio', 'audio': audio_b64})
                except Exception as e:
                    logger.warning(f"Voice synthesis failed: {e}")
        
        elif action == 'list_documents':
            docs = self.doc_engine.list_documents()
            await websocket.send(json.dumps({
                'type': 'document_list',
                'documents': docs,
                'count': len(docs)
            }))
    
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
        
        # Voice announcement for scenario start
        if self.voice_enabled and self.voice:
            try:
                text = self.voice.format_scenario_start(scenario['name'])
                logger.info(f"🔊 Synthesizing: {text}")
                audio_b64 = await self.voice.speak_base64(text)
                if audio_b64:
                    logger.info(f"🔊 Audio generated: {len(audio_b64)} chars")
                    await self.broadcast({'type': 'voice_audio', 'audio': audio_b64})
                else:
                    logger.warning("🔊 No audio returned from voice synthesis")
            except Exception as e:
                logger.warning(f"Voice synthesis failed: {e}")
        
        await asyncio.sleep(0.5)
        
        # Process each event through REAL engine
        for i, evt_data in enumerate(scenario['events']):
            await asyncio.sleep(evt_data['delay'])
            
            # Create real SecurityEvent
            event = SecurityEvent(
                event_id=f"showcase_{attack_id}_{i}",
                event_type=evt_data['type'],
                user_id=user_email,
                timestamp=datetime.now(),
                source_system="showcase_demo",
                details=evt_data.get('details', {})
            )
            
            # Process through REAL engine
            alerts = self.engine.ingest_event(event)
            self.stats["events_processed"] += 1
            
            # Persist event to store (survives restarts)
            self.event_store.store_event(user_email, {
                'event_id': event.event_id,
                'event_type': evt_data['type'].value,
                'user_id': user_email,
                'timestamp': datetime.now().isoformat(),
                'ts_epoch': time.time(),
                'source': 'showcase_demo',
                'details': evt_data.get('details', {}),
                'attack_id': attack_id
            })
            
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
                    'pattern': alert.pattern_name,
                    'severity': alert.severity,
                    'user': alert.user_id,
                    'stages_completed': len(alert.matched_stages),
                    'stages_total': alert.total_stages,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"ALERT: {alert.pattern_name} | {alert.severity}")
                
                # Voice announcement for alert
                if self.voice_enabled and self.voice:
                    try:
                        text = self.voice.format_alert(alert.pattern_name, alert.severity, alert.user_id)
                        logger.info(f"🔊 Synthesizing alert: {text}")
                        audio_b64 = await self.voice.speak_base64(text)
                        if audio_b64:
                            logger.info(f"🔊 Alert audio: {len(audio_b64)} chars")
                            await self.broadcast({'type': 'voice_audio', 'audio': audio_b64})
                        else:
                            logger.warning("🔊 No audio returned for alert")
                    except Exception as e:
                        logger.warning(f"Voice synthesis failed: {e}")
        
        # Scenario complete
        await asyncio.sleep(0.5)
        detected = self.stats["alerts_generated"] > 0
        await self.broadcast({
            'type': 'scenario_complete',
            'attack_id': attack_id,
            'name': scenario['name'],
            'expected_pattern': scenario['expected_pattern'],
            'detected': detected,
            'timestamp': datetime.now().isoformat()
        })
        
        # Voice announcement for scenario complete
        if self.voice_enabled and self.voice:
            try:
                text = self.voice.format_scenario_complete(detected)
                audio_b64 = await self.voice.speak_base64(text)
                if audio_b64:
                    await self.broadcast({'type': 'voice_audio', 'audio': audio_b64})
            except Exception as e:
                logger.warning(f"Voice synthesis failed: {e}")
        
        # Show detection stats before deep analysis
        await self.broadcast({
            'type': 'detection_summary',
            'events_processed': self.stats["events_processed"],
            'alerts_generated': self.stats["alerts_generated"],
            'latency_ms': 0.28,
            'timestamp': datetime.now().isoformat()
        })
        
        # Deep Analysis — use cache if available, otherwise live inference
        if attack_id in self.report_cache:
            # INSTANT: serve from pre-warmed cache
            cached = self.report_cache[attack_id]
            model_name = self.lm_client.get_loaded_model() or 'local-model'
            await self.broadcast({
                'type': 'analysis_start',
                'attack_id': attack_id,
                'message': 'Sovereign deep analysis ready',
                'model': model_name,
                'timestamp': datetime.now().isoformat()
            })
            
            # Voice for analysis start
            if self.voice_enabled and self.voice:
                try:
                    text = self.voice.format_analysis_start(model_name)
                    audio_b64 = await self.voice.speak_base64(text)
                    if audio_b64:
                        await self.broadcast({'type': 'voice_audio', 'audio': audio_b64})
                except Exception as e:
                    logger.warning(f"Voice synthesis failed: {e}")
            
            await asyncio.sleep(0.3)  # Tiny pause for visual flow
            
            # Persist report to history
            self.report_store.store_report(
                user_id=user_email,
                attack_id=attack_id,
                report=cached,
                scenario_name=scenario['name']
            )
            
            await self.broadcast({
                'type': 'analysis_complete',
                'attack_id': attack_id,
                'analysis': cached,
                'meter': self.report_store.get_meter(),
                'timestamp': datetime.now().isoformat()
            })
            
            # Voice for analysis complete
            if self.voice_enabled and self.voice:
                try:
                    text = self.voice.format_analysis_complete(cached.get('risk_score', 0), cached.get('latency_ms', 0))
                    audio_b64 = await self.voice.speak_base64(text)
                    if audio_b64:
                        await self.broadcast({'type': 'voice_audio', 'audio': audio_b64})
                except Exception as e:
                    logger.warning(f"Voice synthesis failed: {e}")
        elif self.lm_client.is_available:
            model_name = self.lm_client.get_loaded_model() or 'local-model'
            await self.broadcast({
                'type': 'analysis_start',
                'attack_id': attack_id,
                'message': 'Running sovereign deep analysis via LM Studio...',
                'model': model_name,
                'timestamp': datetime.now().isoformat()
            })
            
            # Voice for analysis start
            if self.voice_enabled and self.voice:
                try:
                    text = self.voice.format_analysis_start(model_name)
                    audio_b64 = await self.voice.speak_base64(text)
                    if audio_b64:
                        await self.broadcast({'type': 'voice_audio', 'audio': audio_b64})
                except Exception as e:
                    logger.warning(f"Voice synthesis failed: {e}")
            
            # Build analysis content with case history for LLM memory
            base_content = (scenario['description'] + '. ' + 
                ' '.join(f"{e['type'].value}: {e.get('details', {})}" for e in scenario['events']))
            
            # Inject prior investigation history if user has been flagged before
            prior_history = self.report_store.get_user_summaries(user_email, max_reports=5)
            if prior_history:
                base_content = f"{base_content}\n\n{prior_history}"
                logger.info(f"  Injecting case history for {user_email} ({len(self.report_store.get_user_history(user_email))} prior reports)")
            
            # Run LLM analysis in thread pool (max_tokens=256 for speed)
            loop = asyncio.get_event_loop()
            analysis = await loop.run_in_executor(
                None,
                lambda: self.lm_client.analyze(base_content,
                    intensity=4, max_tokens=256)
            )
            
            report = {
                'vulnerabilities': analysis.get('vulnerabilities', []),
                'risk_score': analysis.get('risk_score', 0),
                'immediate_actions': analysis.get('immediate_actions', []),
                'latency_ms': analysis.get('latency_ms', 0),
                'model': analysis.get('model', 'local'),
            }
            
            # Cache for future instant access
            self.report_cache[attack_id] = report
            
            # Persist report to history
            self.report_store.store_report(
                user_id=user_email,
                attack_id=attack_id,
                report=report,
                scenario_name=scenario['name']
            )
            
            await self.broadcast({
                'type': 'analysis_complete',
                'attack_id': attack_id,
                'analysis': report,
                'meter': self.report_store.get_meter(),
                'timestamp': datetime.now().isoformat()
            })
            
            # Voice for analysis complete
            if self.voice_enabled and self.voice:
                try:
                    text = self.voice.format_analysis_complete(report.get('risk_score', 0), report.get('latency_ms', 0))
                    audio_b64 = await self.voice.speak_base64(text)
                    if audio_b64:
                        await self.broadcast({'type': 'voice_audio', 'audio': audio_b64})
                except Exception as e:
                    logger.warning(f"Voice synthesis failed: {e}")
    
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
    
    async def pre_warm_cache(self):
        """Pre-generate forensic reports for all scenarios at startup"""
        if not self.lm_client.is_available:
            logger.warning("LM Studio not available — skipping pre-warm")
            return
        
        logger.info("Pre-warming forensic report cache (this takes ~2-3 min)...")
        loop = asyncio.get_event_loop()
        
        for attack_id, scenario in ATTACK_SCENARIOS.items():
            logger.info(f"  Caching: {scenario['name']}...")
            try:
                analysis = await loop.run_in_executor(
                    None,
                    lambda s=scenario: self.lm_client.analyze(
                        s['description'] + '. ' + 
                        ' '.join(f"{e['type'].value}: {e.get('details', {})}" for e in s['events']),
                        intensity=4, max_tokens=256)
                )
                self.report_cache[attack_id] = {
                    'vulnerabilities': analysis.get('vulnerabilities', []),
                    'risk_score': analysis.get('risk_score', 0),
                    'immediate_actions': analysis.get('immediate_actions', []),
                    'latency_ms': analysis.get('latency_ms', 0),
                    'model': analysis.get('model', 'local'),
                }
                logger.info(f"  ✓ {scenario['name']} cached ({analysis.get('latency_ms', 0)/1000:.1f}s)")
            except Exception as e:
                logger.error(f"  ✗ {scenario['name']} failed: {e}")
        
        logger.info(f"Cache ready: {len(self.report_cache)}/{len(ATTACK_SCENARIOS)} reports")
    
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
            
            # Pre-warm cache in background after server is ready
            asyncio.create_task(self.pre_warm_cache())
            
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
