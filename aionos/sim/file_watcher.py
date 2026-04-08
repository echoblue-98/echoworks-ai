"""
EchoWorks — Real-Time File System Watcher
============================================
Monitors the simulated law firm directory and sends REAL file access
events to the AION OS detection engine via the REST API.

This is the MISSING CONNECTOR — it bridges actual file system activity
to the detection pipeline.
"""

import json
import time
import hashlib
import requests
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

API_URL = "http://127.0.0.1:8000/api/v1/alert"
FIRM_ROOT = Path(__file__).parent.parent.parent / "sim_firm"


def _classify_sensitivity(path: str) -> str:
    """Classify file sensitivity based on path."""
    p = path.lower()
    if "/hr/" in p or "\\hr\\" in p:
        if "compensation" in p or "personnel" in p:
            return "CRITICAL"
        return "HIGH"
    if "trust" in p or "billing" in p:
        return "HIGH"
    if "client_list" in p or "master" in p:
        return "CRITICAL"
    if "/matters/" in p or "\\matters\\" in p:
        if "strategy" in p or "work_product" in p or "workproduct" in p:
            return "HIGH"
        return "MEDIUM"
    if "/templates/" in p or "\\templates\\" in p:
        return "LOW"
    return "MEDIUM"


def _extract_matter(path: str) -> str:
    """Extract matter number from file path."""
    parts = Path(path).parts
    for part in parts:
        if part[:4].isdigit() and "-" in part[:9]:
            return part.split("_")[0]
    return ""


def _extract_user_from_context(path: str, default: str = "unknown") -> str:
    """In simulation mode, extract user from the access context."""
    # The demo runner sets an env var or we infer from path
    import os
    return os.environ.get("AION_SIM_USER", default)


class FirmFileWatcher(FileSystemEventHandler):
    """Watches firm directory and POSTs events to AION OS API."""

    def __init__(self, api_url: str = API_URL, api_key: str = "", verbose: bool = True):
        self.api_url = api_url
        self.api_key = api_key
        self.verbose = verbose
        self.event_count = 0
        self.alert_count = 0  # count of API alerts received back
        self.temporal_alerts = []
        self.deviation_alerts = []
        self.alert_buffer = []
        self._last_flush = time.time()
        self._dedup = set()  # prevent duplicate events within 2s window

    def _dedup_key(self, event_type: str, path: str) -> str:
        return f"{event_type}:{path}:{int(time.time() / 2)}"

    def _send_alert(self, event_type: str, src_path: str, dest_path: str = ""):
        """Send a file event to AION OS."""
        key = self._dedup_key(event_type, src_path)
        if key in self._dedup:
            return
        self._dedup.add(key)

        # Clean up old dedup keys
        if len(self._dedup) > 10000:
            self._dedup.clear()

        user = _extract_user_from_context(src_path)
        rel_path = str(Path(src_path).relative_to(FIRM_ROOT)) if FIRM_ROOT in Path(src_path).parents or Path(src_path) == FIRM_ROOT else src_path
        matter = _extract_matter(src_path)
        sensitivity = _classify_sensitivity(src_path)

        alert = {
            "type": f"file_{event_type}",
            "user": f"{user}@mpg-law.com",
            "timestamp": datetime.now().isoformat(),
            "source": "aion_file_watcher",
            "details": {
                "path": rel_path,
                "dest_path": dest_path if dest_path else None,
                "matter_number": matter,
                "sensitivity": sensitivity,
                "file_extension": Path(src_path).suffix,
                "file_size_bytes": Path(src_path).stat().st_size if Path(src_path).exists() else 0,
                "hostname": "FIRM-SERVER-01",
            }
        }

        self.event_count += 1

        if self.verbose:
            icon = {"access": "👁", "created": "📄", "modified": "✏️",
                    "moved": "📦", "deleted": "🗑️"}.get(event_type, "📌")
            sens_color = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(sensitivity, "⚪")
            print(f"  {icon} [{self.event_count:04d}] {event_type.upper():10s} {sens_color} {rel_path[:70]}")

        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            resp = requests.post(self.api_url, json=alert, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Track detection alerts from the engine
                if "temporal_correlation" in data:
                    for ta in data["temporal_correlation"].get("alerts", []):
                        self.temporal_alerts.append(ta)
                        self.alert_count += 1
                        if self.verbose:
                            print(f"    🚨 TEMPORAL: {ta['pattern']} ({ta['severity']}) — {ta['completion_percent']}% complete")
                if "behavioral_deviation" in data:
                    for da in data["behavioral_deviation"].get("alerts", []):
                        self.deviation_alerts.append(da)
                        self.alert_count += 1
                        if self.verbose:
                            print(f"    ⚡ BASELINE: {da['type']} ({da['severity']}) — {da['message'][:60]}")
            elif self.verbose:
                print(f"    ⚠ API returned {resp.status_code}")
        except (requests.ConnectionError, requests.Timeout, requests.ReadTimeout):
            # API not running or slow — buffer for later
            self.alert_buffer.append(alert)
            if len(self.alert_buffer) == 1 and self.verbose:
                print("    ⚠ API not reachable — buffering events")
        except Exception:
            pass  # Don't crash the watcher thread

    # ── Watchdog event handlers ───────────────────────────────────

    def on_created(self, event):
        if not event.is_directory:
            self._send_alert("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._send_alert("modified", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._send_alert("moved", event.src_path, event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._send_alert("deleted", event.src_path)


def start_watcher(firm_root: Path = FIRM_ROOT, api_url: str = API_URL,
                  api_key: str = "", verbose: bool = True) -> Observer:
    """Start watching the firm directory. Returns the observer."""
    handler = FirmFileWatcher(api_url=api_url, api_key=api_key, verbose=verbose)
    observer = Observer()
    observer.schedule(handler, str(firm_root), recursive=True)
    observer.start()

    if verbose:
        print(f"  👁 File watcher active on: {firm_root}")
        print(f"  📡 Sending events to: {api_url}")
        print()

    return observer, handler


if __name__ == "__main__":
    if not FIRM_ROOT.exists():
        print("Firm directory not found. Run firm_builder.py first.")
        raise SystemExit(1)

    print("=" * 60)
    print("  AION OS — Real-Time File System Monitor")
    print("=" * 60)
    print()

    observer, handler = start_watcher()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print(f"\n  Stopped. Total events captured: {handler.event_count}")
    observer.join()
