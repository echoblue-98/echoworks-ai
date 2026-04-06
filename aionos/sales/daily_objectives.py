"""
EchoWorks — Daily Objectives Generator
========================================
Generates fresh daily objectives based on pipeline state, cadence
due dates, content schedule, and follow-up timing.

Sends to your phone alongside the daily content notification.

Usage:
    python aionos/sales/daily_objectives.py              # Send objectives email
    python aionos/sales/daily_objectives.py --preview     # Preview in terminal
    python aionos/sales/daily_objectives.py --install     # Schedule at 7:30am daily
"""

from __future__ import annotations

import os
import smtplib
import subprocess
import sys
import sqlite3
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aionos.sales.content_engine import ContentEngine, WEEKLY_SCHEDULE

SENDER_EMAIL = os.getenv("GMAIL_ADDRESS", "echoworksaillc@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", SENDER_EMAIL)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline.db")
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_pipeline_objectives() -> list[dict]:
    """Generate objectives from pipeline state."""
    objectives = []
    today = date.today()
    today_str = today.isoformat()
    day_name = DAY_NAMES[today.weekday()]
    is_weekend = today.weekday() >= 5

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout = 5000")
    cur = conn.cursor()

    # 1. Proposals outstanding — always follow up
    cur.execute("""
        SELECT id, name, company FROM prospects 
        WHERE stage = 'proposal_sent'
    """)
    for pid, name, company in cur.fetchall():
        objectives.append({
            "priority": "HIGH",
            "category": "Close",
            "task": f"Follow up on proposal — {name} @ {company} (#{pid})",
        })

    # 2. Demos scheduled — prep or confirm
    cur.execute("""
        SELECT id, name, company FROM prospects 
        WHERE stage = 'demo_scheduled'
    """)
    for pid, name, company in cur.fetchall():
        objectives.append({
            "priority": "HIGH",
            "category": "Demo",
            "task": f"Confirm/prep demo — {name} @ {company} (#{pid})",
        })

    # 3. Engaged prospects — move forward
    cur.execute("""
        SELECT id, name, company, notes FROM prospects 
        WHERE stage = 'engaged'
        AND vertical = 'legal'
        ORDER BY updated DESC
        LIMIT 5
    """)
    for pid, name, company, notes in cur.fetchall():
        objectives.append({
            "priority": "MEDIUM",
            "category": "Advance",
            "task": f"Follow up with {name} @ {company} (#{pid})",
        })

    # 4. Recently contacted — check for responses
    cur.execute("""
        SELECT COUNT(*) FROM prospects 
        WHERE stage = 'contacted'
        AND updated > ?
    """, ((today - timedelta(days=7)).isoformat(),))
    recent_contacted = cur.fetchone()[0]
    if recent_contacted > 0:
        objectives.append({
            "priority": "MEDIUM",
            "category": "Pipeline",
            "task": f"Check LinkedIn for responses — {recent_contacted} prospects contacted this week",
        })

    # 5. New connections needed (weekday only)
    if not is_weekend:
        cur.execute("""
            SELECT COUNT(*) FROM prospects 
            WHERE stage = 'cold'
            AND (name = title OR name IN ('Managing Partner','IT Director','CIO','CTO'))
            AND vertical = 'legal'
        """)
        unnamed = cur.fetchone()[0]
        if unnamed > 0:
            objectives.append({
                "priority": "MEDIUM",
                "category": "Outreach",
                "task": f"Search LinkedIn for contacts at {min(unnamed, 10)} target firms — send connection requests",
            })
    
    # 6. Prospects with no email — enrich
    cur.execute("""
        SELECT COUNT(*) FROM prospects 
        WHERE (email IS NULL OR email = '')
        AND stage NOT IN ('closed_won','closed_lost')
    """)
    no_email = cur.fetchone()[0]
    if no_email > 10:
        objectives.append({
            "priority": "LOW",
            "category": "Enrich",
            "task": f"Enrich pipeline — {no_email} prospects missing email addresses",
        })

    # 7. Content posting reminder
    engine = ContentEngine()
    post = engine.get_todays_post("linkedin")
    objectives.append({
        "priority": "HIGH",
        "category": "Content",
        "task": f"Post today's content — {post['label']} ({day_name}) on LinkedIn + IG",
    })

    # 8. Pipeline health stats
    cur.execute("SELECT stage, COUNT(*) FROM prospects GROUP BY stage")
    stage_counts = dict(cur.fetchall())
    total = sum(stage_counts.values())
    hot = stage_counts.get('proposal_sent', 0) + stage_counts.get('demo_scheduled', 0)
    objectives.append({
        "priority": "INFO",
        "category": "Dashboard",
        "task": f"Pipeline: {total} total | {hot} hot | {stage_counts.get('engaged', 0)} engaged | {stage_counts.get('contacted', 0)} contacted | {stage_counts.get('cold', 0)} cold",
    })

    conn.close()
    return objectives


def build_objectives_email() -> tuple[str, str, str]:
    """Build the daily objectives email."""
    today = date.today()
    day_name = DAY_NAMES[today.weekday()]
    objectives = get_pipeline_objectives()

    subject = f"Daily Objectives — {day_name} {today.strftime('%b %d')}"

    # Sort by priority
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    objectives.sort(key=lambda x: priority_order.get(x["priority"], 99))

    # Text version
    lines = [
        f"ECHOWORKS DAILY OBJECTIVES — {day_name.upper()} {today.strftime('%b %d').upper()}",
        "=" * 55,
        "",
    ]
    for i, obj in enumerate(objectives, 1):
        marker = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}.get(obj["priority"], "⚪")
        lines.append(f"  {marker} [{obj['category'].upper()}] {obj['task']}")
    
    lines.extend(["", "=" * 55, "Pain opens. Sovereignty wins. Compliance closes."])
    text_body = "\n".join(lines)

    # HTML version
    obj_rows = ""
    priority_colors = {
        "HIGH": ("#ff4444", "rgba(255,68,68,0.08)", "rgba(255,68,68,0.2)"),
        "MEDIUM": ("#eab308", "rgba(234,179,8,0.08)", "rgba(234,179,8,0.2)"),
        "LOW": ("#3b82f6", "rgba(59,130,246,0.08)", "rgba(59,130,246,0.2)"),
        "INFO": ("#64748b", "rgba(100,116,139,0.08)", "rgba(100,116,139,0.2)"),
    }
    for obj in objectives:
        color, bg, border = priority_colors.get(obj["priority"], ("#64748b", "rgba(100,116,139,0.08)", "rgba(100,116,139,0.2)"))
        obj_rows += f"""
        <div style="background: {bg}; border: 1px solid {border}; border-left: 3px solid {color}; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px;">
            <div style="font-size: 10px; letter-spacing: 1.5px; color: {color}; text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">{obj['priority']} — {obj['category']}</div>
            <div style="font-size: 14px; color: #e2e8f0; line-height: 1.5;">{obj['task']}</div>
        </div>"""

    html_body = f"""
    <div style="font-family: -apple-system, Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0a0a; color: #e2e8f0; padding: 32px; border-radius: 16px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <span style="font-size: 11px; letter-spacing: 2px; color: #ff4444; text-transform: uppercase; font-weight: 600;">Daily Objectives</span>
            <h2 style="margin: 8px 0 4px; font-size: 22px; color: #f1f5f9;">{day_name} — {today.strftime('%B %d, %Y')}</h2>
        </div>
        {obj_rows}
        <div style="text-align: center; font-size: 12px; color: rgba(241,245,249,0.3); margin-top: 20px; font-style: italic;">
            Pain opens. Sovereignty wins. Compliance closes.
        </div>
    </div>
    """

    return subject, text_body, html_body


def send_objectives() -> None:
    """Send today's objectives to your phone."""
    if not GMAIL_APP_PASSWORD:
        print("  GMAIL_APP_PASSWORD not set.")
        return

    subject, text_body, html_body = build_objectives_email()

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
    """Preview today's objectives in the terminal."""
    _, text_body, _ = build_objectives_email()
    print(text_body)


def install_schedule() -> None:
    """Install a Windows Task Scheduler task to run daily at 7:30am (before content at 8am)."""
    python_path = sys.executable
    script_path = os.path.abspath(__file__)
    task_name = "EchoWorks_DailyObjectives"

    cmd = (
        f'schtasks /Create /SC DAILY /TN "{task_name}" '
        f'/TR "\\\"{python_path}\\\" \\\"{script_path}\\\"" '
        f'/ST 07:30 /F'
    )

    print(f"  Installing scheduled task: {task_name}")
    print(f"  Time: 7:30 AM daily")
    print(f"  Script: {script_path}")
    print(f"  Python: {python_path}")
    print()

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Task '{task_name}' installed successfully.")
    else:
        print(f"  Failed: {result.stderr}")
        print(f"\n  May need Administrator.")


def main() -> None:
    args = sys.argv[1:]
    if "--install" in args:
        install_schedule()
    elif "--preview" in args:
        preview()
    else:
        send_objectives()


if __name__ == "__main__":
    main()
