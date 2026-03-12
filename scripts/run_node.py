"""
AION OS - Node Runner

This script starts the Living Node with all connectors attached.
Deploy this in the client's environment.

Usage:
    python run_node.py --config ./config/
    python run_node.py --watch user@company.com
    python run_node.py --investigate user@company.com
"""

import asyncio
import argparse
import json
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('aion_node.log')
    ]
)
logger = logging.getLogger('AION.Node')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from aionos.modules.soc_ingestion import SOCIngestionEngine
from aionos.core.local_security_attacker import LocalSecurityAttacker


class AIONNode:
    """
    The Living Node - AION's persistent runtime.
    
    Connects to:
    - Microsoft Graph (Azure AD, O365, SharePoint)
    - More connectors coming...
    
    All processing happens locally. Zero data leaves the environment.
    """

    def __init__(self, config_dir: str = './config'):
        self.config_dir = Path(config_dir)
        self.connectors = {}
        self.soc_engine = SOCIngestionEngine()
        self.security_agent = LocalSecurityAttacker()
        self.running = False

        logger.info("=" * 60)
        logger.info("AION OS - The Living Node")
        logger.info("=" * 60)
        logger.info(f"Config directory: {self.config_dir}")

    async def initialize(self):
        """Initialize all configured connectors"""
        
        # Microsoft Graph
        graph_config = self.config_dir / 'microsoft_graph.json'
        if graph_config.exists():
            try:
                from aionos.connectors.microsoft_graph import MicrosoftGraphConnector
                
                self.connectors['microsoft_graph'] = MicrosoftGraphConnector(
                    config_path=str(graph_config)
                )
                
                connected = await self.connectors['microsoft_graph'].connect()
                if connected:
                    # Attach SOC engine for auto-escalation
                    self.connectors['microsoft_graph'].attach_soc_engine(self.soc_engine)
                    logger.info("✅ Microsoft Graph connector: ACTIVE")
                else:
                    logger.error("❌ Microsoft Graph connector: FAILED")
                    
            except ImportError as e:
                logger.warning(f"Microsoft Graph dependencies not installed: {e}")
                logger.info("Run: pip install msal aiohttp")
            except Exception as e:
                logger.error(f"Microsoft Graph initialization failed: {e}")
        else:
            logger.info(f"No Microsoft Graph config found at {graph_config}")
            logger.info("Copy microsoft_graph.example.json and configure credentials")

        # Add more connectors here as they're built
        # - Splunk
        # - Okta
        # - CrowdStrike
        # - etc.

        logger.info(f"Active connectors: {len(self.connectors)}")

    async def watch_user(self, user_email: str):
        """Add a user to departure risk monitoring"""
        if 'microsoft_graph' in self.connectors:
            result = await self.connectors['microsoft_graph'].watch_user(user_email)
            if 'error' not in result:
                logger.info(f"Now watching: {user_email}")
                print(json.dumps(result, indent=2, default=str))
            else:
                logger.error(f"Failed to watch user: {result['error']}")
        else:
            logger.error("Microsoft Graph connector not configured")

    async def investigate_user(self, user_email: str):
        """Full investigation of a user"""
        if 'microsoft_graph' not in self.connectors:
            logger.error("Microsoft Graph connector not configured")
            return

        logger.info(f"Starting investigation: {user_email}")
        result = await self.connectors['microsoft_graph'].investigate_user(user_email)

        # Run through local security agent
        if result.get('findings'):
            analysis = self.security_agent.analyze(
                threat_type=result['findings'][0]['type'] if result['findings'] else 'unknown',
                context={
                    'user': user_email,
                    'findings': result['findings'],
                    'risk_score': result['risk_score']
                }
            )
            result['agent_analysis'] = {
                'threat_type': analysis.threat_type,
                'severity': analysis.severity,
                'immediate_actions': analysis.immediate_actions,
                'forensic_preservation': analysis.forensic_preservation
            }

        print("\n" + "=" * 60)
        print("INVESTIGATION REPORT")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))

        return result

    async def run(self, scan_interval: int = 300):
        """Start continuous monitoring"""
        self.running = True
        logger.info(f"Starting continuous monitoring (interval: {scan_interval}s)")
        logger.info("Press Ctrl+C to stop")

        while self.running:
            try:
                # Scan all connectors
                for name, connector in self.connectors.items():
                    if hasattr(connector, 'scan_all_signals'):
                        signals = await connector.scan_all_signals()
                        if signals:
                            logger.warning(f"[{name}] Detected {len(signals)} signals")
                            for s in signals:
                                logger.warning(f"  [{s.severity.upper()}] {s.signal_type.value}: {s.user_email}")

                await asyncio.sleep(scan_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scan error: {e}")
                await asyncio.sleep(60)

        logger.info("Node stopped")

    def stop(self):
        """Stop the node"""
        self.running = False


async def main():
    parser = argparse.ArgumentParser(
        description="AION OS - The Living Node",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_node.py                          # Start continuous monitoring
  python run_node.py --watch user@firm.com    # Add user to watch list
  python run_node.py --investigate user@firm.com  # Full user investigation
  python run_node.py --config ./custom/config/    # Use custom config dir
        """
    )
    parser.add_argument('--config', type=str, default='./config', 
                       help='Configuration directory path')
    parser.add_argument('--watch', type=str, 
                       help='Add user email to departure risk monitoring')
    parser.add_argument('--investigate', type=str,
                       help='Full investigation of user')
    parser.add_argument('--interval', type=int, default=300,
                       help='Scan interval in seconds (default: 300)')

    args = parser.parse_args()

    node = AIONNode(config_dir=args.config)

    # Handle Ctrl+C gracefully
    def handle_signal(sig, frame):
        logger.info("Shutdown signal received...")
        node.stop()

    signal.signal(signal.SIGINT, handle_signal)

    await node.initialize()

    if args.watch:
        await node.watch_user(args.watch)
    elif args.investigate:
        await node.investigate_user(args.investigate)
    else:
        await node.run(scan_interval=args.interval)


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                     🔴 AION OS                                ║
    ║                   THE LIVING NODE                             ║
    ║                                                               ║
    ║          Adversarial Intelligence Operating System            ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    asyncio.run(main())
