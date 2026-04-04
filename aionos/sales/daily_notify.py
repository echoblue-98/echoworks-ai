"""
EchoWorks — Daily Content Notification
========================================
Sends today's content post to your phone via your own Gmail.
Runs on your machine. No third-party platforms.

Setup:
    1. Set environment variable:  GMAIL_APP_PASSWORD=your-16-char-app-password
    2. Set environment variable:  GMAIL_ADDRESS=echoworksaillc@gmail.com  (optional)
    3. Set environment variable:  NOTIFY_EMAIL=your-personal@gmail.com
    4. Schedule via Windows Task Scheduler (see install_schedule() below)

Manual run:
    python aionos/sales/daily_notify.py
    python aionos/sales/daily_notify.py --install   (sets up Task Scheduler)
"""

from __future__ import annotations

import os
import smtplib
import subprocess
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aionos.sales.content_engine import ContentEngine, WEEKLY_SCHEDULE


SENDER_EMAIL = os.getenv("GMAIL_ADDRESS", "echoworksaillc@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", SENDER_EMAIL)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_email() -> tuple[str, str, str]:
    """Build today's content notification email. Returns (subject, text_body, html_body)."""
    engine = ContentEngine()
    today = date.today()
    day_name = DAY_NAMES[today.weekday()]
    topic = WEEKLY_SCHEDULE.get(today.weekday(), "stats")

    linkedin_post = engine.get_todays_post("linkedin")
    ig_post = engine.get_todays_post("instagram")

    subject = f"Today's Post — {linkedin_post['label']} ({day_name})"

    text_body = (
        f"ECHOWORKS DAILY CONTENT — {day_name.upper()}\n"
        f"{'=' * 50}\n\n"
        f"PILLAR: {linkedin_post['label']}\n\n"
        f"LINKEDIN:\n"
        f"{'-' * 40}\n"
        f"{linkedin_post['content']}\n\n"
        f"INSTAGRAM:\n"
        f"{'-' * 40}\n"
        f"{ig_post['content']}\n\n"
        f"{'=' * 50}\n"
        f"Copy → Paste → Post\n"
    )

    html_body = f"""
    <div style="font-family: -apple-system, Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #e2e8f0; padding: 32px; border-radius: 16px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <span style="font-size: 12px; letter-spacing: 2px; color: #60a5fa; text-transform: uppercase; font-weight: 600;">EchoWorks Daily Content</span>
            <h2 style="margin: 8px 0 4px; font-size: 22px; color: #f1f5f9;">{day_name} — {linkedin_post['label']}</h2>
        </div>

        <div style="background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2); border-radius: 12px; padding: 24px; margin-bottom: 20px;">
            <div style="font-size: 11px; letter-spacing: 1.5px; color: #60a5fa; text-transform: uppercase; font-weight: 600; margin-bottom: 12px;">LinkedIn</div>
            <div style="white-space: pre-wrap; font-size: 14px; line-height: 1.7; color: #cbd5e1;">{linkedin_post['content']}</div>
        </div>

        <div style="background: rgba(139,92,246,0.08); border: 1px solid rgba(139,92,246,0.2); border-radius: 12px; padding: 24px; margin-bottom: 20px;">
            <div style="font-size: 11px; letter-spacing: 1.5px; color: #a78bfa; text-transform: uppercase; font-weight: 600; margin-bottom: 12px;">Instagram</div>
            <div style="white-space: pre-wrap; font-size: 14px; line-height: 1.7; color: #cbd5e1;">{ig_post['content']}</div>
        </div>

        <div style="text-align: center; font-size: 12px; color: rgba(241,245,249,0.4); margin-top: 16px;">
            Copy &rarr; Paste &rarr; Post &nbsp;|&nbsp; Sovereignty intact
        </div>
    </div>
    """

    return subject, text_body, html_body


def send_notification() -> None:
    """Send today's content to your phone."""
    if not GMAIL_APP_PASSWORD:
        print("  GMAIL_APP_PASSWORD not set.")
        print("  Set it:  $env:GMAIL_APP_PASSWORD='xxxx-xxxx-xxxx-xxxx'")
        return

    subject, text_body, html_body = build_email()

    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = NOTIFY_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"  Sent to {NOTIFY_EMAIL}: {subject}")
    except Exception as e:
        print(f"  Failed: {e}")


def preview() -> None:
    """Preview today's email in the terminal."""
    _, text_body, _ = build_email()
    print(text_body)


def install_schedule() -> None:
    """Install a Windows Task Scheduler task to run daily at 8am."""
    python_path = sys.executable
    script_path = os.path.abspath(__file__)

    task_name = "EchoWorks_DailyContent"

    # Build the schtasks command
    cmd = (
        f'schtasks /Create /SC DAILY /TN "{task_name}" '
        f'/TR "\\\"{python_path}\\\" \\\"{script_path}\\\"" '
        f'/ST 08:00 /F'
    )

    print(f"  Installing scheduled task: {task_name}")
    print(f"  Time: 8:00 AM daily")
    print(f"  Script: {script_path}")
    print(f"  Python: {python_path}")
    print()

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Task '{task_name}' installed successfully.")
        print(f"  Verify: schtasks /Query /TN \"{task_name}\"")
    else:
        print(f"  Failed to install task:")
        print(f"  {result.stderr}")
        print(f"\n  You may need to run as Administrator.")
        print(f"  Or run manually: schtasks /Create /SC DAILY /TN \"{task_name}\" /TR \"\\\"{python_path}\\\" \\\"{script_path}\\\"\" /ST 08:00 /F")


def main() -> None:
    args = sys.argv[1:]
    if "--install" in args:
        install_schedule()
    elif "--preview" in args:
        preview()
    else:
        send_notification()


if __name__ == "__main__":
    main()
