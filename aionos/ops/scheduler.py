"""
AION OS -- Scheduler
======================
Registers / removes Windows Scheduled Tasks so AION OS
runs automatically every morning (daily brief + notifications).

Uses schtasks.exe -- no external dependencies, no cloud.

Commands (via CLI):
    python -m aionos.ops.cli schedule install   -- register daily 8:30 AM task
    python -m aionos.ops.cli schedule uninstall -- remove the task
    python -m aionos.ops.cli schedule status    -- check if task is registered
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

TASK_NAME = "AION_OS_DailyBrief"
DEFAULT_TIME = "08:30"


def _python_exe() -> str:
    """Return the current Python executable path."""
    return sys.executable


def _workspace_dir() -> str:
    """Return the workspace root (parent of aionos/)."""
    return str(Path(__file__).resolve().parent.parent.parent)


def install(time: str = DEFAULT_TIME) -> bool:
    """
    Register a Windows Scheduled Task that runs the daily brief
    every morning at the given time.
    """
    python = _python_exe()
    workspace = _workspace_dir()
    command = f'"{python}" -m aionos.ops.cli brief --save --notify'

    # Remove existing task first (idempotent)
    uninstall(quiet=True)

    try:
        result = subprocess.run(
            [
                "schtasks",
                "/Create",
                "/TN", TASK_NAME,
                "/TR", command,
                "/SC", "DAILY",
                "/ST", time,
                "/F",
            ],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=15,
        )
        if result.returncode == 0:
            print(f"  Scheduled Task '{TASK_NAME}' installed.")
            print(f"  Runs daily at {time}")
            print(f"  Command: {command}")
            print(f"  Working dir: {workspace}")
            return True
        else:
            print(f"  Failed to install scheduled task: {result.stderr.strip()}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print(f"  Scheduler error: {e}")
        return False


def uninstall(quiet: bool = False) -> bool:
    """Remove the AION OS scheduled task."""
    try:
        result = subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            if not quiet:
                print(f"  Scheduled Task '{TASK_NAME}' removed.")
            return True
        else:
            if not quiet:
                print(f"  Task not found or already removed.")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        if not quiet:
            print("  Could not access Task Scheduler.")
        return False


def status() -> dict:
    """Check if the AION OS scheduled task exists and return its info."""
    try:
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            info = _parse_task_output(result.stdout)
            info["installed"] = True
            return info
        else:
            return {"installed": False}
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return {"installed": False, "error": "Cannot access Task Scheduler"}


def _parse_task_output(output: str) -> dict:
    """Parse schtasks /Query output into a dict."""
    info = {}
    for line in output.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if "Task Name" in key:
                info["task_name"] = val
            elif "Status" in key:
                info["status"] = val
            elif "Next Run Time" in key:
                info["next_run"] = val
            elif "Last Run Time" in key:
                info["last_run"] = val
            elif "Task To Run" in key:
                info["command"] = val
            elif "Scheduled Type" in key:
                info["schedule_type"] = val
            elif "Start Time" in key:
                info["start_time"] = val
    return info


def print_status():
    """Print current scheduler status."""
    info = status()
    if info.get("installed"):
        print(f"\n  AION OS Scheduler: ACTIVE")
        print(f"  Task:     {info.get('task_name', TASK_NAME)}")
        print(f"  Status:   {info.get('status', 'unknown')}")
        print(f"  Schedule: {info.get('schedule_type', 'DAILY')}")
        print(f"  Time:     {info.get('start_time', DEFAULT_TIME)}")
        print(f"  Next Run: {info.get('next_run', 'unknown')}")
        print(f"  Last Run: {info.get('last_run', 'never')}")
        print(f"  Command:  {info.get('command', 'unknown')}")
        print()
    else:
        print(f"\n  AION OS Scheduler: NOT INSTALLED")
        print(f"  Run: python -m aionos.ops.cli schedule install")
        print()
