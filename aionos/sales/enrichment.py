"""
EchoWorks — Prospect Enrichment Tool
=======================================
Systematically fill in missing emails, LinkedIn URLs, and phone numbers
across the pipeline.

Usage:
    python sell.py enrich              Show enrichment gaps
    python sell.py enrich --lookup     Open search URLs for top prospects
    python sell.py enrich --update     Interactive update mode
    python sell.py enrich --csv FILE   Batch update from CSV
"""

from __future__ import annotations

import csv
import os
import sys
import webbrowser
from typing import List, Optional

from aionos.sales.prospects import Pipeline


# ═══════════════════════════════════════════════════════════════
#  ENRICHMENT ENGINE
# ═══════════════════════════════════════════════════════════════

# Priority stages (enrich these first — closest to money)
PRIORITY_STAGES = [
    "negotiation", "proposal_sent", "demo_completed",
    "demo_scheduled", "engaged", "cold",
]


class EnrichmentTool:
    """Fill in missing prospect data."""

    def __init__(self) -> None:
        self.pipe = Pipeline()

    def gap_report(self) -> dict:
        """Show what's missing across the pipeline."""
        all_p = self.pipe.list_all()
        total = len(all_p)
        missing_email = [p for p in all_p if not p.get("email")]
        missing_linkedin = [p for p in all_p if not p.get("linkedin")]
        missing_phone = [p for p in all_p if not p.get("phone")]
        missing_title = [p for p in all_p if not p.get("title")]

        report = {
            "total": total,
            "missing_email": len(missing_email),
            "missing_linkedin": len(missing_linkedin),
            "missing_phone": len(missing_phone),
            "missing_title": len(missing_title),
            "email_coverage": f"{((total - len(missing_email)) / total * 100):.0f}%" if total else "0%",
            "priority_missing": [],
        }

        # Top priority: missing email in advanced stages
        for stage in PRIORITY_STAGES[:4]:
            for p in missing_email:
                if p.get("stage") == stage:
                    report["priority_missing"].append({
                        "id": p["id"],
                        "name": p["name"],
                        "company": p["company"],
                        "stage": stage,
                        "field": "email",
                    })

        return report

    def print_gap_report(self) -> None:
        """Print the gap report."""
        report = self.gap_report()
        print(f"\n  ENRICHMENT GAPS")
        print(f"  {'═' * 50}")
        print(f"  Total Prospects:     {report['total']}")
        print(f"  Missing Email:       {report['missing_email']}  ({report['email_coverage']} coverage)")
        print(f"  Missing LinkedIn:    {report['missing_linkedin']}")
        print(f"  Missing Phone:       {report['missing_phone']}")
        print(f"  Missing Title:       {report['missing_title']}")

        if report["priority_missing"]:
            print(f"\n  PRIORITY — Advanced-stage prospects missing email:")
            print(f"  {'─' * 50}")
            for pm in report["priority_missing"][:15]:
                print(f"  #{pm['id']:>3}  {pm['name']:<25} {pm['company']:<25} [{pm['stage']}]")
        print()

    def lookup_prospect(self, pid: int) -> None:
        """Open search URLs to find prospect's email."""
        prospect = self.pipe.get(pid)
        if not prospect:
            print(f"  Prospect #{pid} not found.")
            return

        name = prospect["name"]
        company = prospect["company"]
        query = f"{name} {company} email"

        # Generate search URLs
        urls = {
            "Google": f"https://www.google.com/search?q={_url_encode(query)}",
            "LinkedIn": f"https://www.linkedin.com/search/results/people/?keywords={_url_encode(name + ' ' + company)}",
        }

        print(f"\n  Looking up: {name} @ {company}")
        print(f"  {'─' * 40}")
        for label, url in urls.items():
            print(f"  {label}: {url}")
            webbrowser.open(url)
        print(f"\n  After finding info, run: python sell.py enrich --update")

    def lookup_top(self, limit: int = 5) -> None:
        """Open search URLs for top priority prospects missing email."""
        report = self.gap_report()
        priority = report["priority_missing"][:limit]
        if not priority:
            # Fall back to any missing email
            all_p = self.pipe.list_all()
            missing = [p for p in all_p if not p.get("email")]
            priority = [{"id": p["id"], "name": p["name"], "company": p["company"]}
                        for p in missing[:limit]]

        if not priority:
            print("  All prospects have emails!")
            return

        for pm in priority:
            self.lookup_prospect(pm["id"])

    def interactive_update(self) -> None:
        """Prompt user to update missing fields for top prospects."""
        all_p = self.pipe.list_all()
        missing = [p for p in all_p if not p.get("email")]

        # Sort by stage priority
        stage_order = {s: i for i, s in enumerate(PRIORITY_STAGES)}
        missing.sort(key=lambda p: stage_order.get(p.get("stage", "cold"), 99))

        if not missing:
            print("  All prospects have emails!")
            return

        print(f"\n  ENRICH MODE — {len(missing)} prospects need emails")
        print(f"  {'═' * 50}")
        print(f"  Enter email (or 'skip' / 'q' to quit)\n")

        updated = 0
        for p in missing:
            name = p["name"]
            company = p["company"]
            stage = p.get("stage", "cold")
            print(f"  #{p['id']:>3}  {name:<25} {company:<25} [{stage}]")

            email = input(f"        Email: ").strip()
            if email.lower() == "q":
                break
            if email.lower() == "skip" or not email:
                continue

            # Basic validation
            if "@" not in email or "." not in email:
                print(f"        Invalid email, skipped.")
                continue

            self.pipe.update(p["id"], email=email)
            updated += 1
            print(f"        Updated!")

            # Also ask for LinkedIn if missing
            if not p.get("linkedin"):
                li = input(f"        LinkedIn URL (optional): ").strip()
                if li and li.lower() != "skip":
                    self.pipe.update(p["id"], linkedin=li)

        print(f"\n  Updated {updated} prospects.")

    def batch_update_from_csv(self, csv_path: str) -> None:
        """Update prospects from a CSV file.

        Expected CSV columns: id (or name+company), email, linkedin, phone, title
        """
        if not os.path.exists(csv_path):
            print(f"  File not found: {csv_path}")
            return

        updated = 0
        skipped = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = None
                if "id" in row and row["id"]:
                    pid = int(row["id"])
                elif "name" in row and "company" in row:
                    # Find by name+company
                    all_p = self.pipe.list_all()
                    for p in all_p:
                        if (p["name"].lower() == row["name"].lower() and
                                p["company"].lower() == row["company"].lower()):
                            pid = p["id"]
                            break

                if not pid:
                    skipped += 1
                    continue

                updates = {}
                for field in ["email", "linkedin", "phone", "title"]:
                    if field in row and row[field].strip():
                        updates[field] = row[field].strip()

                if updates:
                    self.pipe.update(pid, **updates)
                    updated += 1
                else:
                    skipped += 1

        print(f"  Batch update: {updated} updated, {skipped} skipped")

    def generate_template_csv(self) -> str:
        """Generate a CSV template with all prospects missing data."""
        all_p = self.pipe.list_all()
        missing = [p for p in all_p if not p.get("email")]

        dl = os.path.join(os.path.expanduser("~"), "Downloads")
        path = os.path.join(dl, "enrichment_template.csv")

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "company", "stage", "email", "linkedin", "phone", "title"])
            for p in missing:
                writer.writerow([
                    p["id"], p["name"], p["company"], p.get("stage", "cold"),
                    "", p.get("linkedin", ""), p.get("phone", ""), p.get("title", ""),
                ])

        print(f"  Template saved: {path}")
        print(f"  Fill in the blanks, then run: python sell.py enrich --csv \"{path}\"")
        return path


def _url_encode(text: str) -> str:
    """Basic URL encoding."""
    import urllib.parse
    return urllib.parse.quote_plus(text)


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    tool = EnrichmentTool()

    if "--update" in args:
        tool.interactive_update()
    elif "--csv" in args:
        idx = args.index("--csv")
        if idx + 1 < len(args):
            tool.batch_update_from_csv(args[idx + 1])
        else:
            print("  Usage: python sell.py enrich --csv PATH")
    elif "--lookup" in args:
        # Check if a specific ID was given
        pid = None
        for a in args:
            if a.isdigit():
                pid = int(a)
                break
        if pid:
            tool.lookup_prospect(pid)
        else:
            tool.lookup_top()
    elif "--template" in args:
        tool.generate_template_csv()
    else:
        tool.print_gap_report()


if __name__ == "__main__":
    main()
