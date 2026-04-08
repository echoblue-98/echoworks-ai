"""
EchoWorks — Attorney Departure Scenario Runner
=================================================
Simulates a realistic 14-day attorney departure against the simulated
law firm. Uses REAL file operations on the REAL file system.

The scenario:
  Robert Garcia, Partner (14 years), is secretly planning to leave
  for a competitor. He's the lead attorney on $18.3M in active matters.
  Over 14 days, he gradually exfiltrates client data.

  AION OS should detect and alert on this behavior in real time.
"""

import os
import json
import shutil
import time
import random
import requests
from datetime import datetime
from pathlib import Path

FIRM_ROOT = Path(__file__).parent.parent.parent / "sim_firm"
EXFIL_DIR = FIRM_ROOT.parent / "sim_exfil"  # Simulated personal USB/cloud folder
API_URL = "http://127.0.0.1:8080/api/v1/alert"
API_KEY = ""  # Set by demo runner

# Detection tracking — collected by demo runner for summary
detected_temporal = []
detected_deviation = []
events_sent = 0


def configure(api_key: str = "", api_url: str = ""):
    """Configure API settings from the demo runner."""
    global API_KEY, API_URL, detected_temporal, detected_deviation, events_sent
    if api_key:
        API_KEY = api_key
    if api_url:
        API_URL = api_url
    detected_temporal = []
    detected_deviation = []
    events_sent = 0


def _set_user(username: str):
    """Set the current simulated user for the file watcher."""
    os.environ["AION_SIM_USER"] = username


def _current_user() -> str:
    return os.environ.get("AION_SIM_USER", "unknown")


def _pause(seconds: float, label: str = ""):
    """Visible pause between actions."""
    if label:
        print(f"    ⏳ {label}")
    time.sleep(seconds)


def _send_event(event_type: str, filepath: Path, sensitivity: str = "MEDIUM",
                matter: str = ""):
    """Send an event directly to the AION OS API (guaranteed delivery)."""
    if not API_KEY:
        return  # File watcher will handle it
    user = _current_user()
    try:
        rel = str(filepath.relative_to(FIRM_ROOT)) if FIRM_ROOT in filepath.parents else str(filepath)
    except ValueError:
        rel = str(filepath)
    alert = {
        "type": event_type,
        "user": f"{user}@mpg-law.com",
        "timestamp": datetime.now().isoformat(),
        "source": "aion_file_watcher",
        "details": {
            "path": rel,
            "matter_number": matter,
            "sensitivity": sensitivity,
            "file_extension": filepath.suffix,
            "file_size_bytes": filepath.stat().st_size if filepath.exists() else 0,
            "hostname": "FIRM-SERVER-01",
        }
    }
    try:
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        resp = requests.post(API_URL, json=alert, headers=headers, timeout=10)
        if resp.status_code == 200:
            global events_sent
            events_sent += 1
            data = resp.json()
            if "temporal_correlation" in data:
                for ta in data["temporal_correlation"].get("alerts", []):
                    detected_temporal.append(ta)
                    sev = ta.get('severity', '?')
                    print(f"    🚨 TEMPORAL: {ta['pattern']} ({sev}) — {ta['completion_percent']}% complete")
            if "behavioral_deviation" in data:
                for da in data["behavioral_deviation"].get("alerts", []):
                    detected_deviation.append(da)
                    print(f"    ⚡ BASELINE: {da['type']} ({da['severity']}) — {da.get('message', '')[:60]}")
    except Exception:
        pass


def _classify(filepath: Path) -> str:
    """Quick sensitivity classification."""
    p = str(filepath).lower()
    if "hr" in p and ("compensation" in p or "personnel" in p):
        return "CRITICAL"
    if "client_list" in p or "master" in p:
        return "CRITICAL"
    if "trust" in p or "billing" in p:
        return "HIGH"
    if "strategy" in p or "work_product" in p:
        return "HIGH"
    return "MEDIUM"


def _extract_matter(filepath: Path) -> str:
    for part in filepath.parts:
        if len(part) >= 8 and part[:4].isdigit() and "-" in part[:9]:
            return part.split("_")[0]
    return ""


def _open_file(filepath: Path):
    """Simulate opening/reading a file."""
    if filepath.exists():
        _ = filepath.read_text()
        # Touch to trigger watchdog modified event
        filepath.write_text(filepath.read_text())
        _send_event("file_modified", filepath, _classify(filepath), _extract_matter(filepath))


def _copy_file(src: Path, dest_dir: Path):
    """Copy a file to the exfiltration target."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest


# ── Normal Activity (Baseline Building) ──────────────────────────

def run_normal_activity(days: int = 5, speed: float = 0.3):
    """
    Simulate normal attorney activity to build baseline.
    Each 'day' takes ~10 seconds at default speed.
    """
    print("=" * 60)
    print("  PHASE 0: NORMAL BASELINE ACTIVITY")
    print("  Building 'normal' patterns for all attorneys...")
    print("=" * 60)
    print()

    attorneys = {
        "jmitchell": ["2024-0142", "2025-0034"],
        "kpatel":    ["2024-0221", "2025-0051"],
        "rgarcia":   ["2024-0187", "2024-0203", "2025-0012"],
        "lwilson":   ["2024-0221", "2024-0256"],
        "tcarter":   ["2024-0142", "2024-0203", "2025-0034"],
        "akim":      ["2024-0187", "2024-0256", "2025-0012"],
        "dthompson": ["2024-0187", "2024-0256", "2025-0034"],
        "mchen":     ["2024-0142", "2024-0256"],
    }

    for day in range(1, days + 1):
        print(f"  📅 Day {day}/{days} — Normal operations")

        for attorney, matters in attorneys.items():
            _set_user(attorney)
            # Each attorney opens 2-4 files per day from their matters
            matter_num = random.choice(matters)
            matter_dir = _find_matter_dir(matter_num)
            if not matter_dir:
                continue

            files = list(matter_dir.rglob("*"))
            files = [f for f in files if f.is_file()]
            if not files:
                continue

            num_access = random.randint(2, 4)
            for f in random.sample(files, min(num_access, len(files))):
                _open_file(f)
                time.sleep(speed * 0.5)

        _pause(speed * 0.5, f"End of day {day}")
        print()

    print("  ✓ Baseline established.\n")


# ── Departure Scenario ───────────────────────────────────────────

def run_departure_scenario(speed: float = 0.5):
    """
    Robert Garcia's 14-day departure exfiltration.
    Compressed to ~3 minutes for demo recording.
    """
    _set_user("rgarcia")
    EXFIL_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  🚨 PHASE 1: RECONNAISSANCE (Days 1-3)")
    print("  Robert Garcia begins unusual access patterns...")
    print("=" * 60)
    print()

    # Day 1: Access matters he's not assigned to (unusual)
    print("  📅 Day 1 — Accessing unfamiliar matters")
    unrelated = ["2024-0221", "2025-0051", "2024-0256"]  # Not his matters
    for matter_num in unrelated:
        matter_dir = _find_matter_dir(matter_num)
        if matter_dir:
            for f in list(matter_dir.rglob("*"))[:3]:
                if f.is_file():
                    _open_file(f)
                    _pause(speed * 0.5)
    print("    → Accessed 3 matters outside his normal caseload\n")

    # Day 2: Looks at client master list and HR compensation
    print("  📅 Day 2 — Accessing sensitive firm data")
    sensitive_files = [
        FIRM_ROOT / "SharedDrive" / "Marketing" / "client_list_master.xlsx",
        FIRM_ROOT / "SharedDrive" / "Admin" / "office_directory.xlsx",
        FIRM_ROOT / "SharedDrive" / "IT" / "network_diagram.pdf",
    ]
    for f in sensitive_files:
        if f.exists():
            _open_file(f)
            _pause(speed * 0.5)
    print("    → Accessed master client list, office directory, network diagram\n")

    # Day 3: Accesses HR files (employee records, compensation)
    print("  📅 Day 3 — Accessing HR records")
    hr_files = list((FIRM_ROOT / "HR").rglob("*"))
    hr_files = [f for f in hr_files if f.is_file()]
    for f in hr_files[:6]:
        _open_file(f)
        _pause(speed * 0.3)
    print("    → Browsed 6 HR files including compensation data\n")

    _pause(speed)

    print("=" * 60)
    print("  🚨 PHASE 2: STAGING (Days 4-8)")
    print("  Robert begins copying files to personal storage...")
    print("=" * 60)
    print()

    # Day 4-5: Copy his own matter files
    print("  📅 Days 4-5 — Copying own matter files")
    garcia_matters = ["2024-0187", "2024-0203", "2025-0012"]
    copy_count = 0
    for matter_num in garcia_matters:
        matter_dir = _find_matter_dir(matter_num)
        if not matter_dir:
            continue
        dest = EXFIL_DIR / matter_num
        for f in matter_dir.rglob("*"):
            if f.is_file():
                _copy_file(f, dest)
                # Report the file access to AION (the copy source was read)
                _send_event("file_download", f, _classify(f), _extract_matter(f))
                copy_count += 1
                _pause(speed * 0.15)
    print(f"    → Copied {copy_count} files from 3 matters (${18.3}M value)\n")

    # Day 6: Syncing to personal cloud and copying client list
    print("  📅 Day 6 — Syncing to personal cloud storage")
    client_list = FIRM_ROOT / "SharedDrive" / "Marketing" / "client_list_master.xlsx"
    if client_list.exists():
        _copy_file(client_list, EXFIL_DIR / "firm_intel")
        _send_event("file_download", client_list, "CRITICAL")
        _pause(speed * 0.3)
        # Cloud sync detected — uploading matter files to OneDrive
        _send_event("cloud_sync", client_list, "CRITICAL")
        _pause(speed * 0.3)
    print("    → Master client list synced to personal cloud\n")

    # Day 7-8: Copy billing records + email forwarding
    print("  📅 Days 7-8 — Copying billing data + forwarding emails")
    billing_copy = 0
    for f in (FIRM_ROOT / "Billing").rglob("*"):
        if f.is_file() and ("rgarcia" in str(f) or "trust" in str(f).lower()):
            _copy_file(f, EXFIL_DIR / "billing")
            _send_event("file_download", f, "HIGH")
            billing_copy += 1
            _pause(speed * 0.15)
    # Email forwarding — setting up auto-forward to personal email
    _send_event("email_forward", FIRM_ROOT / "SharedDrive" / "Admin" / "office_directory.xlsx", "HIGH")
    _pause(speed * 0.3)
    print(f"    → Copied {billing_copy} billing/trust files")
    print(f"    → Email auto-forward rule created to personal account\n")

    _pause(speed)

    print("=" * 60)
    print("  🚨 PHASE 3: ACCELERATION (Days 9-12)")
    print("  Robert's activity spikes — bulk operations...")
    print("=" * 60)
    print()

    # Day 9-10: Massive file access spike
    print("  📅 Days 9-10 — Bulk file access across ALL matters")
    bulk_count = 0
    for matter_dir in (FIRM_ROOT / "Matters").iterdir():
        if matter_dir.is_dir():
            for f in matter_dir.rglob("*"):
                if f.is_file():
                    _open_file(f)
                    bulk_count += 1
                    _pause(speed * 0.08)
    print(f"    → Accessed {bulk_count} files across ALL matters (10x normal volume)\n")

    # Day 11: Copy everything to USB drive + exfil
    print("  📅 Day 11 — Bulk copy to USB drive")
    bulk_copy = 0
    for matter_dir in (FIRM_ROOT / "Matters").iterdir():
        if matter_dir.is_dir():
            dest = EXFIL_DIR / "all_matters" / matter_dir.name
            for f in matter_dir.rglob("*"):
                if f.is_file():
                    _copy_file(f, dest)
                    _send_event("bulk_download", f, "HIGH", _extract_matter(f))
                    bulk_copy += 1
                    _pause(speed * 0.05)
    # USB activity detected
    _send_event("usb_activity", FIRM_ROOT / "Matters", "CRITICAL")
    _pause(speed * 0.3)
    print(f"    → Bulk copied {bulk_copy} files to USB drive\n")

    # Day 12: Print confidential documents + copy templates
    print("  📅 Day 12 — Printing confidential docs + copying templates")
    for f in (FIRM_ROOT / "Templates").rglob("*"):
        if f.is_file():
            _copy_file(f, EXFIL_DIR / "templates")
            _send_event("file_download", f, "MEDIUM")
            _pause(speed * 0.2)
    # Large print job — printing client list and strategy docs
    _send_event("print_job", FIRM_ROOT / "SharedDrive" / "Marketing" / "client_list_master.xlsx", "CRITICAL")
    _pause(speed * 0.3)
    print("    → All firm templates copied")
    print("    → Large print job sent: 247 pages\n")

    _pause(speed)

    print("=" * 60)
    print("  🚨 PHASE 4: COVER-UP (Days 13-14)")
    print("  Robert attempts to hide his tracks...")
    print("=" * 60)
    print()

    # Day 13: Delete recent files from his matter folders
    print("  📅 Day 13 — Deleting recent access evidence")
    delete_count = 0
    for matter_num in garcia_matters:
        matter_dir = _find_matter_dir(matter_num)
        if not matter_dir:
            continue
        # Delete some work product files
        wp_dir = matter_dir / "WorkProduct"
        if wp_dir.exists():
            for f in list(wp_dir.iterdir()):
                if f.is_file() and random.random() > 0.5:
                    _send_event("file_deleted", f, "HIGH", _extract_matter(f))
                    f.unlink()
                    delete_count += 1
                    _pause(speed * 0.2)
    print(f"    → Deleted {delete_count} work product files from his matters\n")

    # Day 14: Final resignation day
    print("  📅 Day 14 — Resignation day")
    print("    → Robert Garcia submits resignation letter")
    print("    → Requests immediate departure")
    print()

    # Count what was exfiltrated
    exfil_total = sum(1 for _ in EXFIL_DIR.rglob("*") if _.is_file())
    print("=" * 60)
    print("  📊 EXFILTRATION SUMMARY")
    print("=" * 60)
    print(f"    Files copied to personal storage: {exfil_total}")
    print(f"    Matters compromised: ALL ({len(list((FIRM_ROOT / 'Matters').iterdir()))} matters)")
    print(f"    Files deleted (cover-up): {delete_count}")
    print(f"    Client list stolen: YES")
    print(f"    Billing/trust data stolen: YES")
    print(f"    Firm templates stolen: YES")
    print()


# ── Helpers ───────────────────────────────────────────────────────

def _find_matter_dir(matter_num: str) -> Path | None:
    """Find matter directory by number."""
    matters_root = FIRM_ROOT / "Matters"
    if not matters_root.exists():
        return None
    for d in matters_root.iterdir():
        if d.is_dir() and d.name.startswith(matter_num):
            return d
    return None


# ── Main ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not FIRM_ROOT.exists():
        print("Run firm_builder.py first to create the simulated firm.")
        raise SystemExit(1)

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   AION OS — ATTORNEY DEPARTURE DETECTION DEMO          ║")
    print("║   Scenario: Robert Garcia, Partner, 14-year tenure     ║")
    print("║   Action: Exfiltrating $18.3M in client data           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print("  This runs REAL file operations on your file system.")
    print("  The AION OS file watcher detects every action.")
    print()

    run_normal_activity(days=3, speed=0.2)
    run_departure_scenario(speed=0.3)
