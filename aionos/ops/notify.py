"""
AION OS -- Windows Notification System
=========================================
Sends Windows 10/11 toast notifications from AION OS.
Uses PowerShell's BurntToast module (auto-installs if missing)
or falls back to basic Windows notification via .NET.

No external Python dependencies. Zero cloud.

Usage:
    from aionos.ops.notify import send_notification
    send_notification("AION OS", "3 urgent items in your pipeline")
"""

from __future__ import annotations

import subprocess
import sys


def send_notification(
    title: str = "AION OS",
    message: str = "Daily brief ready.",
    urgency: str = "green",
) -> bool:
    """
    Send a Windows toast notification.

    Falls back gracefully if notifications are unavailable.
    Returns True if notification was sent.
    """
    # Map urgency to a simple tag
    tag = {"red": "[URGENT]", "yellow": "[ACTION]", "green": "[OK]"}.get(
        urgency, ""
    )
    full_title = f"{tag} {title}".strip()

    # Try BurntToast first (richer notifications)
    if _try_burnttoast(full_title, message):
        return True

    # Fallback: basic .NET toast
    if _try_dotnet_toast(full_title, message):
        return True

    # Final fallback: print to console
    print(f"\n  ** NOTIFICATION: {full_title} **")
    print(f"  {message}\n")
    return False


def _try_burnttoast(title: str, message: str) -> bool:
    """Try sending via BurntToast PowerShell module."""
    # Sanitize inputs for PowerShell - escape single quotes
    safe_title = title.replace("'", "''")
    safe_message = message.replace("'", "''")

    ps_script = f"""
if (-not (Get-Module -ListAvailable -Name BurntToast)) {{
    try {{
        Install-Module -Name BurntToast -Force -Scope CurrentUser -ErrorAction Stop
    }} catch {{
        exit 1
    }}
}}
Import-Module BurntToast -ErrorAction Stop
New-BurntToastNotification -Text '{safe_title}', '{safe_message}' -AppLogo $null
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _try_dotnet_toast(title: str, message: str) -> bool:
    """Fallback: Windows .NET notification via PowerShell."""
    safe_title = title.replace("'", "''")
    safe_message = message.replace("'", "''")

    ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{safe_title}</text>
            <text>{safe_message}</text>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('AION OS')
$notifier.Show($toast)
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def notify_brief_ready(summary: str, urgency: str = "green") -> bool:
    """Convenience: notify that daily brief is ready."""
    return send_notification("AION OS Daily Brief", summary, urgency)


def notify_deal_closed(name: str, company: str, value: str = "") -> bool:
    """Notify on deal close."""
    msg = f"{name} @ {company} -- CLOSED WON"
    if value:
        msg += f" ({value})"
    return send_notification("AION OS -- Deal Closed", msg, "green")


def notify_insight(insight: str) -> bool:
    """Notify on a critical evolution insight."""
    return send_notification("AION OS Evolution", insight, "yellow")
