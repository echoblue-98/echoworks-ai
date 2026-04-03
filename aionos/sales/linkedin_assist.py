"""
EchoWorks — LinkedIn Workflow Assistant
=========================================
Opens prospect LinkedIn profiles in browser and copies
the cadence-step message to clipboard. No LinkedIn API
abuse — just streamlines the manual flow.

Usage:
    python sell.py linkedin          Open all due LinkedIn actions
    python sell.py linkedin [id]     Open one prospect's profile

Flow:
    1. Pulls cadence prospects due today with LinkedIn actions
    2. Opens each profile in your default browser
    3. Copies the connection request / message to clipboard
    4. You paste and send manually
    5. Marks the LinkedIn channel as done
"""

from __future__ import annotations

import subprocess
import sys
import webbrowser
from typing import List, Optional

from aionos.sales.prospects import Pipeline
from aionos.sales.messages import MessageGenerator
from aionos.sales.cadence import CadenceEngine, SEQUENCES, get_step_message


def _copy_to_clipboard(text: str) -> bool:
    """Copy text to Windows clipboard."""
    try:
        process = subprocess.Popen(
            ["clip"], stdin=subprocess.PIPE, shell=True,
        )
        process.communicate(text.encode("utf-16le"))
        return True
    except Exception:
        return False


class LinkedInAssist:
    """Opens LinkedIn profiles + copies cadence messages to clipboard."""

    def __init__(self) -> None:
        self._pipe = Pipeline()
        self._gen = MessageGenerator()
        self._cadence = CadenceEngine()

    def _get_linkedin_message(self, prospect_id: int) -> Optional[dict]:
        """
        Get LinkedIn message for prospect's current cadence step.
        Returns dict with 'message', 'action', 'step_num', 'profile_url'
        or None if no LinkedIn action.
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

        # Find LinkedIn channel
        li_channel = None
        for ch in step_info["channels"]:
            if ch["channel"] == "linkedin":
                li_channel = ch
                break
        if not li_channel:
            return None

        prospect = self._pipe.get(prospect_id)
        if not prospect:
            return None

        name = prospect["name"]
        company = prospect["company"]
        first = name.split()[0] if name else "there"
        linkedin_url = (prospect.get("linkedin") or "").strip()

        # Generate message
        msgs = self._gen.generate(
            name=name, company=company,
            title=prospect.get("title", ""),
            vertical=prospect.get("vertical", "legal"),
        )

        message = get_step_message(
            step_num, seq_name, "linkedin", first, company,
            li_channel["template_key"], msgs,
        )

        # Build search URL if no profile URL stored
        if not linkedin_url:
            search_query = f"{name} {company}".replace(" ", "%20")
            linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}"

        return {
            "message": message,
            "action": li_channel["action"],
            "step_num": step_num,
            "sequence_name": seq_name,
            "profile_url": linkedin_url,
            "name": name,
            "company": company,
        }

    def open_one(self, prospect_id: int) -> bool:
        """Open one prospect's LinkedIn + copy message."""
        data = self._get_linkedin_message(prospect_id)
        if not data:
            prospect = self._pipe.get(prospect_id)
            name = prospect["name"] if prospect else f"#{prospect_id}"
            print(f"  {name} — no LinkedIn action due.")
            return False

        print(f"\n  #{prospect_id} {data['name']} @ {data['company']}")
        print(f"  Step {data['step_num']} | {data['action']}")
        print(f"  URL: {data['profile_url']}")
        print(f"\n  Message (copied to clipboard):")
        print(f"  {'─' * 50}")
        for line in data["message"].split("\n"):
            print(f"  {line}")
        print(f"  {'─' * 50}")

        _copy_to_clipboard(data["message"])
        webbrowser.open(data["profile_url"])
        return True

    def open_due_today(self, limit: int = 10) -> int:
        """Open all LinkedIn actions due today, one by one."""
        due = self._cadence.due_today()
        targets = []

        for item in due:
            pid = item["prospect_id"]
            data = self._get_linkedin_message(pid)
            if data:
                targets.append((pid, data))

        if not targets:
            print("  No LinkedIn actions due today.")
            return 0

        batch = targets[:limit]
        print(f"\n  LinkedIn Actions Due: {len(batch)}")
        print(f"  Each profile opens in browser + message copied to clipboard.")
        print(f"  After pasting, come back and type 'done' or 'skip'.\n")

        processed = 0
        for i, (pid, data) in enumerate(batch, 1):
            print(f"  [{i}/{len(batch)}] #{pid} {data['name']} @ {data['company']}")
            print(f"  Step {data['step_num']} | {data['action']}")
            print(f"  {'─' * 40}")
            for line in data["message"].split("\n"):
                print(f"  {line}")
            print(f"  {'─' * 40}")

            _copy_to_clipboard(data["message"])
            webbrowser.open(data["profile_url"])
            processed += 1

            if i < len(batch):
                try:
                    action = input("\n  [done/skip/q] > ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    break
                if action == "q":
                    break
                print()

        print(f"\n  Opened {processed}/{len(batch)} LinkedIn profiles.")
        return processed


def main() -> None:
    """CLI entry point."""
    assist = LinkedInAssist()
    args = sys.argv[1:]

    if args and args[0].isdigit():
        assist.open_one(int(args[0]))
    else:
        limit = int(args[0]) if args and args[0].isdigit() else 10
        assist.open_due_today(limit=limit)


if __name__ == "__main__":
    main()
