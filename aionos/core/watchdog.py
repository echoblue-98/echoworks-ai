"""
AION OS - Service Watchdog
RED-017: Detects if AION service is stopped/killed

Runs as a separate lightweight process that monitors AION services.
If a service goes down unexpectedly, sends alert via multiple channels.

Usage:
    python -m aionos.core.watchdog --services webhook,node
    python -m aionos.core.watchdog --slack-webhook https://hooks.slack.com/...
"""

import os
import sys
import json
import time
import socket
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import threading

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('AION.Watchdog')


class ServiceWatchdog:
    """
    Monitors AION services and alerts if they go down.
    
    RED-017 Mitigation: Prevents insiders from silently disabling AION.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path(__file__).parent.parent.parent / "config" / "watchdog.json"
        self.config = self._load_config()
        self.services = {}
        self.alert_channels = []
        self.running = True
        self.last_heartbeat = {}
        
    def _load_config(self) -> Dict:
        """Load watchdog configuration."""
        default_config = {
            "services": {
                "webhook": {
                    "type": "http",
                    "url": "http://localhost:8080/health",
                    "interval_seconds": 30,
                    "timeout_seconds": 5
                },
                "node": {
                    "type": "process",
                    "process_name": "python",
                    "script_pattern": "run_node.py",
                    "interval_seconds": 30
                }
            },
            "alerts": {
                "log_file": "aionos/logs/watchdog_alerts.jsonl",
                "slack_webhook": None,
                "email": None
            },
            "thresholds": {
                "consecutive_failures": 3,
                "alert_cooldown_minutes": 5
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            # Create default config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default config: {self.config_path}")
            return default_config
    
    def check_http_service(self, name: str, config: Dict) -> bool:
        """Check if HTTP service is responding."""
        if not REQUESTS_AVAILABLE:
            # Fallback to socket check
            return self._check_port(config.get('url', ''))
        
        try:
            url = config.get('url', 'http://localhost:8080/health')
            timeout = config.get('timeout_seconds', 5)
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"HTTP check failed for {name}: {e}")
            return False
    
    def _check_port(self, url: str) -> bool:
        """Check if port is open (fallback when requests not available)."""
        try:
            # Parse URL
            if '://' in url:
                url = url.split('://')[1]
            host = url.split('/')[0].split(':')[0]
            port = int(url.split(':')[1].split('/')[0]) if ':' in url else 80
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_process_service(self, name: str, config: Dict) -> bool:
        """Check if process is running."""
        try:
            process_name = config.get('process_name', 'python')
            script_pattern = config.get('script_pattern', '')
            
            # Use tasklist on Windows, ps on Unix
            if sys.platform == 'win32':
                output = subprocess.check_output(
                    ['tasklist', '/FI', f'IMAGENAME eq {process_name}.exe'],
                    text=True, stderr=subprocess.DEVNULL
                )
                if script_pattern:
                    # Check running Python scripts via wmic
                    try:
                        wmic_output = subprocess.check_output(
                            ['wmic', 'process', 'where', f"name='{process_name}.exe'", 'get', 'commandline'],
                            text=True, stderr=subprocess.DEVNULL
                        )
                        return script_pattern in wmic_output
                    except:
                        return process_name in output
                return process_name in output
            else:
                output = subprocess.check_output(['pgrep', '-f', script_pattern or process_name], text=True)
                return len(output.strip()) > 0
        except subprocess.CalledProcessError:
            return False
        except Exception as e:
            logger.debug(f"Process check failed for {name}: {e}")
            return False
    
    def send_alert(self, service_name: str, status: str, message: str):
        """Send alert via configured channels."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "service": service_name,
            "status": status,
            "message": message,
            "hostname": socket.gethostname()
        }
        
        # Always log locally
        log_file = Path(self.config.get('alerts', {}).get('log_file', 'aionos/logs/watchdog_alerts.jsonl'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
        
        # Console alert
        logger.critical(f"🚨 ALERT: {service_name} - {status} - {message}")
        
        # Slack webhook
        slack_url = self.config.get('alerts', {}).get('slack_webhook')
        if slack_url and REQUESTS_AVAILABLE:
            try:
                requests.post(slack_url, json={
                    "text": f"🚨 AION Watchdog Alert\n*Service:* {service_name}\n*Status:* {status}\n*Message:* {message}\n*Host:* {socket.gethostname()}"
                }, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
    
    def check_service(self, name: str, config: Dict) -> bool:
        """Check a single service based on its type."""
        service_type = config.get('type', 'http')
        
        if service_type == 'http':
            return self.check_http_service(name, config)
        elif service_type == 'process':
            return self.check_process_service(name, config)
        else:
            logger.warning(f"Unknown service type: {service_type}")
            return True  # Assume OK for unknown types
    
    def monitor(self):
        """Main monitoring loop."""
        services_config = self.config.get('services', {})
        thresholds = self.config.get('thresholds', {})
        consecutive_threshold = thresholds.get('consecutive_failures', 3)
        cooldown_minutes = thresholds.get('alert_cooldown_minutes', 5)
        
        failure_counts = {name: 0 for name in services_config}
        last_alert_time = {name: None for name in services_config}
        
        logger.info("=" * 50)
        logger.info("🐕 AION Watchdog Started")
        logger.info("=" * 50)
        logger.info(f"Monitoring {len(services_config)} services:")
        for name in services_config:
            logger.info(f"  • {name}")
        logger.info("")
        
        while self.running:
            for name, config in services_config.items():
                interval = config.get('interval_seconds', 30)
                
                # Check if it's time to check this service
                last_check = self.last_heartbeat.get(name, 0)
                if time.time() - last_check < interval:
                    continue
                
                self.last_heartbeat[name] = time.time()
                
                # Perform check
                is_healthy = self.check_service(name, config)
                
                if is_healthy:
                    if failure_counts[name] > 0:
                        logger.info(f"✅ {name} recovered after {failure_counts[name]} failures")
                        self.send_alert(name, "RECOVERED", f"Service recovered after {failure_counts[name]} consecutive failures")
                    failure_counts[name] = 0
                else:
                    failure_counts[name] += 1
                    logger.warning(f"❌ {name} check failed ({failure_counts[name]}/{consecutive_threshold})")
                    
                    # Check if we should alert
                    if failure_counts[name] >= consecutive_threshold:
                        last_alert = last_alert_time[name]
                        cooldown_expired = (
                            last_alert is None or 
                            (datetime.now() - last_alert).total_seconds() > cooldown_minutes * 60
                        )
                        
                        if cooldown_expired:
                            self.send_alert(
                                name, 
                                "DOWN",
                                f"Service failed {failure_counts[name]} consecutive health checks. Possible insider attack or system failure."
                            )
                            last_alert_time[name] = datetime.now()
            
            time.sleep(5)  # Check loop interval
    
    def stop(self):
        """Stop the watchdog."""
        self.running = False
        logger.info("Watchdog stopping...")


def main():
    parser = argparse.ArgumentParser(description="AION Service Watchdog")
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--services', type=str, help='Comma-separated list of services to monitor')
    parser.add_argument('--slack-webhook', type=str, help='Slack webhook URL for alerts')
    
    args = parser.parse_args()
    
    watchdog = ServiceWatchdog(config_path=args.config)
    
    # Override config from CLI
    if args.slack_webhook:
        watchdog.config.setdefault('alerts', {})['slack_webhook'] = args.slack_webhook
    
    try:
        watchdog.monitor()
    except KeyboardInterrupt:
        watchdog.stop()
        print("\nWatchdog stopped.")


if __name__ == "__main__":
    main()
