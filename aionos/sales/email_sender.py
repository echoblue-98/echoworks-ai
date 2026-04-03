"""
EchoWorks — Cadence-Aware Email Sender
========================================
Sends the right email for each prospect's current cadence step.
Integrates with CadenceEngine so 'send' = complete the email
channel for that step and auto-schedule the next one.

Setup:
    1. Enable 2-Step Verification on your Google account
    2. Create an App Password: Google Account > Security > App Passwords
    3. Set environment variable:  GMAIL_APP_PASSWORD=your-16-char-app-password
       (or put it in a .env file in the project root)
    4. Run:  python sell.py send         (dry-run preview)
             python sell.py send --live  (actually send)

Features:
    - Cadence-step-aware: sends the right message for the right step
    - Single-prospect send:  send_one(prospect_id)
    - Batch send all due today:  send_due_today()
    - 30-75 second random delay between sends (avoids spam filters)
    - CAN-SPAM compliant unsubscribe footer
    - Dry-run mode by default
    - Rate limited to 50/day (Gmail best practice)
    - Auto-completes cadence step after successful send
"""

from __future__ import annotations

import os
import random
import smtplib
import ssl
import sys
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from aionos.sales.prospects import Pipeline
from aionos.sales.messages import MessageGenerator
from aionos.sales.learner import SalesLearner
from aionos.sales.cadence import CadenceEngine, SEQUENCES, get_step_message

# ── Configuration ─────────────────────────────────────────

SENDER_EMAIL = os.getenv("GMAIL_ADDRESS", "echoworksaillc@gmail.com")
SENDER_NAME = "EchoBlue Holdings"
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

MAX_PER_DAY = 50           # Gmail safe limit
MIN_DELAY_SEC = 30         # Min seconds between sends
MAX_DELAY_SEC = 75         # Max seconds between sends

UNSUBSCRIBE_FOOTER = """

---
EchoBlue Holdings LLC | Atlanta, GA
Reply STOP to unsubscribe from future emails.
"""


# ── Email sender ──────────────────────────────────────────

class EmailSender:
    """Cadence-aware email sender. Sends the right message per step."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._pipe = Pipeline()
        self._gen = MessageGenerator()
        self._learner = SalesLearner()
        self._cadence = CadenceEngine()
        self._sent_count = 0

    def _connect_smtp(self) -> smtplib.SMTP:
        if not GMAIL_APP_PASSWORD:
            raise RuntimeError(
                "GMAIL_APP_PASSWORD not set.\n"
                "  1. Go to Google Account > Security > App Passwords\n"
                "  2. Create an app password for 'Mail'\n"
                "  3. Set:  GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx"
            )
        context = ssl.create_default_context()
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        return server

    def _build_email(self, to_email: str, subject: str, body: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        full_body = body + UNSUBSCRIBE_FOOTER
        msg.attach(MIMEText(full_body, "plain", "utf-8"))
        return msg

    def _extract_subject_body(self, email_text: str, company: str) -> tuple:
        """Split 'Subject: ...\n\nbody' format into (subject, body)."""
        lines = email_text.strip().split("\n")
        subject = f"Insider Threat Detection — {company}"
        body = email_text
        if lines and lines[0].lower().startswith("subject:"):
            subject = lines[0].split(":", 1)[1].strip()
            body = "\n".join(lines[1:]).strip()
        return subject, body

    def _get_cadence_email(self, prospect_id: int) -> Optional[dict]:
        """
        Get the email content for a prospect's current cadence step.
        Returns dict with 'subject', 'body', 'step_num', 'sequence_name'
        or None if no email action on current step.
        """
        enrollment = self._cadence.get_enrollment(prospect_id)
        if not enrollment:
            return None

        seq_name = enrollment["sequence_name"]
        step_num = enrollment["current_step"]
        seq = SEQUENCES.get(seq_name, {})
        steps = seq.get("steps", [])

        step_info = None
        for s in steps:
            if s["step"] == step_num:
                step_info = s
                break
        if not step_info:
            return None

        # Find email channel in this step
        email_channel = None
        for ch in step_info["channels"]:
            if ch["channel"] == "email":
                email_channel = ch
                break
        if not email_channel:
            return None  # No email action on this step

        prospect = self._pipe.get(prospect_id)
        if not prospect:
            return None

        name = prospect["name"]
        company = prospect["company"]
        first = name.split()[0] if name else "there"

        # Generate base messages
        msgs = self._gen.generate(
            name=name, company=company,
            title=prospect.get("title", ""),
            vertical=prospect.get("vertical", "legal"),
        )

        # Get step-specific message
        email_text = get_step_message(
            step_num, seq_name, "email", first, company,
            email_channel["template_key"], msgs,
        )

        subject, body = self._extract_subject_body(email_text, company)

        return {
            "subject": subject,
            "body": body,
            "step_num": step_num,
            "sequence_name": seq_name,
            "action": email_channel["action"],
            "template_key": email_channel["template_key"],
        }

    def send_one(self, prospect_id: int) -> bool:
        """
        Send the cadence email for a single prospect.
        Returns True if sent (or previewed in dry-run).
        """
        prospect = self._pipe.get(prospect_id)
        if not prospect:
            print(f"  Prospect #{prospect_id} not found.")
            return False

        email_addr = prospect.get("email", "").strip()
        if not email_addr or "@" not in email_addr:
            print(f"  #{prospect_id} {prospect['name']} — no email address on file.")
            return False

        email_data = self._get_cadence_email(prospect_id)
        if not email_data:
            print(f"  #{prospect_id} {prospect['name']} — no email step due.")
            return False

        name = prospect["name"]
        company = prospect["company"]
        step = email_data["step_num"]
        seq = email_data["sequence_name"]

        print(f"\n  #{prospect_id} {name} <{email_addr}>")
        print(f"  Cadence: {seq} | Step {step}")
        print(f"  Subject: {email_data['subject']}")

        if self.dry_run:
            print(f"  [DRY RUN] Preview:")
            for line in email_data["body"].split("\n")[:8]:
                print(f"    {line}")
            print(f"    ...")
            return True

        server = None
        try:
            server = self._connect_smtp()
            msg = self._build_email(email_addr, email_data["subject"], email_data["body"])
            server.send_message(msg)
            self._sent_count += 1

            # Complete the cadence step (email channel only)
            self._cadence.complete_step(prospect_id, channel="email")
            print(f"  SENT + step {step} completed")
            return True
        except Exception as e:
            print(f"  FAILED: {e}")
            return False
        finally:
            if server:
                server.quit()

    def send_due_today(self, limit: int = MAX_PER_DAY) -> int:
        """
        Send emails for all cadence prospects due today that have
        an email action on their current step.
        Returns count sent.
        """
        due = self._cadence.due_today()
        targets = []

        for item in due:
            pid = item["prospect_id"]
            prospect = self._pipe.get(pid)
            if not prospect:
                continue
            email_addr = (prospect.get("email") or "").strip()
            if not email_addr or "@" not in email_addr:
                continue

            email_data = self._get_cadence_email(pid)
            if email_data:
                targets.append((pid, prospect, email_data))

        if not targets:
            print("  No email actions due today (missing email addresses or non-email steps).")
            return 0

        batch = targets[:limit]
        print(f"\n  Cadence Email Send: {len(batch)} prospects")
        print(f"  Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"  Delay: {MIN_DELAY_SEC}-{MAX_DELAY_SEC}s between sends\n")

        server = None
        if not self.dry_run:
            try:
                server = self._connect_smtp()
                print("  SMTP connected.\n")
            except Exception as e:
                print(f"  SMTP connection failed: {e}")
                return 0

        sent = 0
        for i, (pid, prospect, email_data) in enumerate(batch, 1):
            name = prospect["name"]
            email_addr = prospect["email"]
            step = email_data["step_num"]

            print(f"  [{i}/{len(batch)}] #{pid} {name} <{email_addr}> | Step {step}")
            print(f"    Subject: {email_data['subject']}")

            if self.dry_run:
                print(f"    [DRY RUN] Would send.")
            else:
                try:
                    msg = self._build_email(email_addr, email_data["subject"], email_data["body"])
                    server.send_message(msg)
                    sent += 1
                    # Complete cadence step
                    self._cadence.complete_step(pid, channel="email")
                    print(f"    SENT + step {step} completed")
                except Exception as e:
                    print(f"    FAILED: {e}")

            if i < len(batch) and not self.dry_run:
                delay = random.randint(MIN_DELAY_SEC, MAX_DELAY_SEC)
                print(f"    Waiting {delay}s...")
                time.sleep(delay)

            print()

        if server:
            server.quit()

        print(f"  Complete. Sent: {sent}/{len(batch)}")
        return sent


# ── CLI ───────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="EchoWorks Cadence Email Sender")
    parser.add_argument("--live", action="store_true",
                        help="Actually send emails (default is dry-run)")
    parser.add_argument("--prospect", type=int, default=None,
                        help="Send to a specific prospect ID")
    parser.add_argument("--limit", type=int, default=MAX_PER_DAY,
                        help="Max emails to send in batch")
    args = parser.parse_args()

    dry_run = not args.live
    sender = EmailSender(dry_run=dry_run)

    if dry_run:
        print("\n  === DRY RUN MODE === (add --live to actually send)")

    if args.prospect:
        sender.send_one(args.prospect)
    else:
        sender.send_due_today(limit=args.limit)


if __name__ == "__main__":
    main()
