"""
AION OS — Automated Email Campaign Sender
============================================
Sends personalized cold emails through Gmail SMTP with
proper pacing, tracking, and CAN-SPAM compliance.

Setup:
    1. Enable 2-Step Verification on your Google account
    2. Create an App Password: Google Account > Security > App Passwords
    3. Set in .env:  GMAIL_APP_PASSWORD=your-16-char-app-password
    4. Run:  python -m aionos.sales.email_sender

Features:
    - Personalized emails per vertical playbook
    - 30-60 second random delay between sends (avoids spam filters)
    - Automatic logging to pipeline + learner
    - CAN-SPAM compliant unsubscribe footer
    - Dry-run mode to preview before sending
    - Rate limited to 50/day (Gmail best practice)
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

class EmailCampaign:

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._pipe = Pipeline()
        self._gen = MessageGenerator()
        self._learner = SalesLearner()
        self._sent_count = 0

    def _connect_smtp(self) -> smtplib.SMTP:
        if not GMAIL_APP_PASSWORD:
            raise RuntimeError(
                "GMAIL_APP_PASSWORD not set. "
                "Create one at: Google Account > Security > App Passwords. "
                "Then add to .env: GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx"
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

        # Plain text version
        full_body = body + UNSUBSCRIBE_FOOTER
        msg.attach(MIMEText(full_body, "plain", "utf-8"))

        return msg

    def send_campaign(
        self,
        vertical: Optional[str] = None,
        stage: str = "cold",
        limit: int = MAX_PER_DAY,
    ) -> int:
        """
        Send personalized emails to prospects with email addresses.
        Returns count of emails sent.
        """
        prospects = self._pipe.list_all(vertical=vertical, stage=stage)
        targets = [
            dict(p) for p in prospects
            if p["email"] and p["email"].strip()
            and "@" in p["email"]
        ]

        if not targets:
            print("  No prospects with email addresses in this segment.")
            print("  Add emails: python -m aionos.sales.cli advance <id> --email user@firm.com")
            return 0

        batch = targets[:limit]
        print(f"\n  Email campaign: {len(batch)} recipients")
        print(f"  Mode: {'DRY RUN (no emails sent)' if self.dry_run else 'LIVE'}")
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
        for i, p in enumerate(batch, 1):
            pid = p["id"]
            name = p["name"]
            company = p["company"]
            email = p["email"]
            title = p.get("title", "")
            vert = p.get("vertical", "legal")

            # Generate email
            try:
                msgs = self._gen.generate(
                    name=name, company=company,
                    title=title or "Partner", vertical=vert,
                )
                cold_email = msgs.get("cold_email", "")
            except Exception:
                cold_email = ""

            if not cold_email:
                print(f"  [{i}/{len(batch)}] #{pid} {name} — skipped (no template)")
                continue

            # Parse subject from cold_email (first line usually "Subject: ...")
            lines = cold_email.strip().split("\n")
            subject = "Insider Threat Detection for " + company
            body = cold_email
            if lines[0].lower().startswith("subject:"):
                subject = lines[0].split(":", 1)[1].strip()
                body = "\n".join(lines[1:]).strip()

            print(f"  [{i}/{len(batch)}] #{pid} {name} <{email}>")
            print(f"    Subject: {subject}")
            if self.dry_run:
                print(f"    [DRY RUN] Would send. Body preview: {body[:100]}...")
            else:
                try:
                    msg = self._build_email(email, subject, body)
                    server.send_message(msg)
                    sent += 1
                    # Log to pipeline
                    self._pipe.log_action(pid, "Sent cold email via campaign", channel="email")
                    self._learner.record_outreach(pid, template=f"{vert}_cold_email", channel="email")
                    self._pipe.set_next_action(pid, 3)
                    print(f"    SENT")
                except Exception as e:
                    print(f"    FAILED: {e}")

            # Pace sends
            if i < len(batch):
                delay = random.randint(MIN_DELAY_SEC, MAX_DELAY_SEC)
                if not self.dry_run:
                    print(f"    Waiting {delay}s...")
                    time.sleep(delay)

            print()

        if server:
            server.quit()

        print(f"  Campaign complete. Sent: {sent}/{len(batch)}")
        return sent


# ── CLI ───────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="AION OS Email Campaign Sender")
    parser.add_argument("--live", action="store_true", help="Actually send emails (default is dry-run)")
    parser.add_argument("--vertical", type=str, default=None, help="Filter by vertical")
    parser.add_argument("--limit", type=int, default=MAX_PER_DAY, help="Max emails to send")
    args = parser.parse_args()

    dry_run = not args.live
    campaign = EmailCampaign(dry_run=dry_run)

    if dry_run:
        print("\n  === DRY RUN MODE === (add --live to actually send)")

    campaign.send_campaign(vertical=args.vertical, limit=args.limit)


if __name__ == "__main__":
    main()
