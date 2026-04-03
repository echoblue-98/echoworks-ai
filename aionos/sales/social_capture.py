"""
EchoWorks — Social Capture
============================
Bridge between social media engagement and the pipeline.
When someone engages on LinkedIn or Instagram (comment, DM, like),
log them here and they auto-enter the pipeline + cadence.

Usage:
    python sell.py capture                          Interactive add
    python sell.py capture "Name" "Company" linkedin
    python sell.py capture "Name" "Company" instagram --notes "Liked post"
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from typing import Optional

from aionos.sales.prospects import Pipeline
from aionos.sales.cadence import CadenceEngine, STAGE_SEQUENCE_MAP


class SocialCapture:
    """Capture social media engagement into the pipeline."""

    def __init__(self) -> None:
        self._pipe = Pipeline()
        self._cadence = CadenceEngine()

    def capture(
        self,
        name: str,
        company: str,
        platform: str = "linkedin",
        engagement_type: str = "engaged",
        title: str = "",
        email: str = "",
        linkedin_url: str = "",
        phone: str = "",
        notes: str = "",
        auto_enroll: bool = True,
    ) -> dict:
        """
        Add a social media lead to the pipeline.

        Args:
            platform: linkedin, instagram, twitter, website
            engagement_type: comment, like, dm, follow, form
        Returns:
            dict with prospect_id, enrolled, sequence
        """
        today = date.today().isoformat()
        source_tag = f"{platform}_{engagement_type}"
        full_notes = f"Captured {today} via {platform} ({engagement_type})"
        if notes:
            full_notes += f". {notes}"

        # Check for duplicates by name + company
        existing = self._find_existing(name, company)
        if existing:
            # Update notes with new engagement
            old_notes = existing.get("notes", "") or ""
            updated_notes = f"{old_notes} | {full_notes}" if old_notes else full_notes
            self._pipe.update(existing["id"], notes=updated_notes)
            if email and not existing.get("email"):
                self._pipe.update(existing["id"], email=email)
            if linkedin_url and not existing.get("linkedin"):
                self._pipe.update(existing["id"], linkedin=linkedin_url)
            if phone and not existing.get("phone"):
                self._pipe.update(existing["id"], phone=phone)

            return {
                "prospect_id": existing["id"],
                "status": "updated",
                "name": name,
                "company": company,
                "enrolled": False,
                "sequence": "",
                "message": f"Updated existing prospect #{existing['id']}",
            }

        # New prospect
        pid = self._pipe.add(
            name=name,
            company=company,
            title=title,
            vertical="legal",
            email=email,
            linkedin=linkedin_url,
            phone=phone,
            notes=full_notes,
            source=source_tag,
        )

        # Auto-enroll in cold cadence
        enrolled = False
        sequence = ""
        if auto_enroll:
            seq_name = STAGE_SEQUENCE_MAP.get("cold", "")
            if seq_name:
                self._cadence.enroll(pid, seq_name)
                enrolled = True
                sequence = seq_name

        return {
            "prospect_id": pid,
            "status": "created",
            "name": name,
            "company": company,
            "enrolled": enrolled,
            "sequence": sequence,
            "message": f"Added #{pid} {name} @ {company} ({source_tag})"
                       + (f" → enrolled in {sequence}" if enrolled else ""),
        }

    def _find_existing(self, name: str, company: str) -> Optional[dict]:
        """Check if prospect already exists by name + company."""
        all_p = self._pipe.list_all()
        name_lower = name.lower().strip()
        company_lower = company.lower().strip()
        for p in all_p:
            p = dict(p)
            if (p["name"].lower().strip() == name_lower
                    and p["company"].lower().strip() == company_lower):
                return p
        return None

    def batch_capture(self, leads: list) -> list:
        """
        Capture multiple leads at once.
        Each lead is a dict: {name, company, platform, engagement_type, ...}
        """
        results = []
        for lead in leads:
            result = self.capture(
                name=lead["name"],
                company=lead["company"],
                platform=lead.get("platform", "linkedin"),
                engagement_type=lead.get("engagement_type", "engaged"),
                title=lead.get("title", ""),
                email=lead.get("email", ""),
                linkedin_url=lead.get("linkedin_url", ""),
                notes=lead.get("notes", ""),
            )
            results.append(result)
        return results

    def interactive_capture(self) -> Optional[dict]:
        """Interactive prompt to capture a social lead."""
        print("\n  CAPTURE SOCIAL LEAD")
        print("  " + "─" * 40)
        try:
            name = input("  Name: ").strip()
            if not name:
                print("  Cancelled.")
                return None
            company = input("  Company: ").strip()
            if not company:
                print("  Cancelled.")
                return None
            platform = input("  Platform [linkedin/instagram/twitter/website]: ").strip().lower()
            if not platform:
                platform = "linkedin"
            eng_type = input("  Engagement [comment/like/dm/follow/form]: ").strip().lower()
            if not eng_type:
                eng_type = "engaged"
            title = input("  Title (optional): ").strip()
            email = input("  Email (optional): ").strip()
            linkedin_url = input("  LinkedIn URL (optional): ").strip()
            notes = input("  Notes (optional): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.")
            return None

        result = self.capture(
            name=name,
            company=company,
            platform=platform,
            engagement_type=eng_type,
            title=title,
            email=email,
            linkedin_url=linkedin_url,
            notes=notes,
        )

        print(f"\n  {result['message']}")
        return result


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    cap = SocialCapture()

    if not args:
        cap.interactive_capture()
        return

    # python sell.py capture "Name" "Company" platform
    name = args[0] if len(args) > 0 else ""
    company = args[1] if len(args) > 1 else ""
    platform = args[2] if len(args) > 2 else "linkedin"

    # Parse optional flags
    notes = ""
    email = ""
    title = ""
    eng_type = "engaged"
    i = 3
    while i < len(args):
        if args[i] == "--notes" and i + 1 < len(args):
            notes = args[i + 1]
            i += 2
        elif args[i] == "--email" and i + 1 < len(args):
            email = args[i + 1]
            i += 2
        elif args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        elif args[i] == "--type" and i + 1 < len(args):
            eng_type = args[i + 1]
            i += 2
        else:
            i += 1

    if name and company:
        result = cap.capture(
            name=name, company=company, platform=platform,
            engagement_type=eng_type, title=title, email=email,
            notes=notes,
        )
        print(f"  {result['message']}")
    else:
        cap.interactive_capture()


if __name__ == "__main__":
    main()
