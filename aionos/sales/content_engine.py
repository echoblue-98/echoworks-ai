"""
EchoWorks — Content Engine
=============================
Generates ready-to-post content for LinkedIn and Instagram
tailored to the law firm insider threat vertical.

Usage:
    python sell.py content                  Generate today's posts
    python sell.py content --week           Generate a week of posts
    python sell.py content --platform ig    Instagram-specific
    python sell.py content --topic stats    Topic filter
"""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from typing import List, Optional


# ═══════════════════════════════════════════════════════════════
#  CONTENT LIBRARY
# ═══════════════════════════════════════════════════════════════
# Each entry: topic, platform suitability, post template, hashtags

CONTENT_PILLARS = [
    {
        "topic": "stats",
        "label": "Industry Stat",
        "posts": [
            {
                "linkedin": (
                    "The average law firm discovers insider data theft 77 days after it starts.\n\n"
                    "Departing attorneys begin staging files 2-4 weeks before the resignation letter.\n\n"
                    "That means by the time most firms find out, the damage is done — $2M-$50M in "
                    "client migration costs, malpractice exposure, and evidence that's gone cold.\n\n"
                    "We built a system that detects it in under 3 seconds.\n\n"
                    "100% on-premise. No client data leaves your network.\n\n"
                    "#InsiderThreat #LawFirm #CyberSecurity #DataProtection #AttorneyDeparture"
                ),
                "instagram": (
                    "77 DAYS.\n\n"
                    "That's how long it takes the average law firm to discover insider data theft.\n\n"
                    "By then? The client book is gone. The evidence is cold. And the legal bill is "
                    "just getting started.\n\n"
                    "We detect it in under 3 seconds.\n\n"
                    "#CyberSecurity #LawFirm #InsiderThreat #DataProtection #AIONOS #EchoWorksAI"
                ),
            },
            {
                "linkedin": (
                    "97% of DLP alerts are false positives (Gartner).\n\n"
                    "Your security team is drowning in noise while real exfiltration goes undetected.\n\n"
                    "Pattern correlation > individual alerts. When you connect the dots — after-hours "
                    "matter access + bulk DMS export + personal email forward — you get 3 actionable "
                    "alerts instead of 4,200 false ones.\n\n"
                    "That's the difference between monitoring and detection.\n\n"
                    "#DLP #FalsePositives #InsiderThreat #CyberSecurity #LawFirm"
                ),
                "instagram": (
                    "97% of security alerts are FALSE POSITIVES.\n\n"
                    "Your team is buried in noise while real threats slip through.\n\n"
                    "We built a pattern-correlation engine that cuts through it. 3 real alerts "
                    "instead of 4,200 fake ones.\n\n"
                    "#CyberSecurity #DLP #InsiderThreat #EchoWorksAI #Detection"
                ),
            },
        ],
    },
    {
        "topic": "pain",
        "label": "Pain Point",
        "posts": [
            {
                "linkedin": (
                    "A partner leaves your firm on Friday.\n\n"
                    "By Monday, they've already:\n"
                    "• Downloaded 218 client matters\n"
                    "• Forwarded billing data to their personal Gmail\n"
                    "• Uploaded 890MB to a personal cloud drive\n\n"
                    "You won't know for 77 days.\n\n"
                    "Unless you have a detection engine running on your network — pattern-matching "
                    "across DMS, email, and cloud in real time.\n\n"
                    "This is what we built. 100% on-premise. Compliance-first.\n\n"
                    "#AttorneyDeparture #InsiderThreat #LawFirm #ClientProtection #EchoWorksAI"
                ),
                "instagram": (
                    "A partner leaves your firm.\n\n"
                    "218 client matters downloaded.\n"
                    "Billing data forwarded to personal email.\n"
                    "890MB uploaded to cloud.\n\n"
                    "You won't know for 77 days.\n\n"
                    "Unless your network is watching.\n\n"
                    "#AttorneyDeparture #InsiderThreat #LawFirm #EchoWorksAI"
                ),
            },
            {
                "linkedin": (
                    "\"We'd know if someone was stealing data.\"\n\n"
                    "This is what every firm says — until they discover that 2,847 documents "
                    "were staged over 3 weeks by a departing attorney, and no one noticed.\n\n"
                    "After-hours access. Bulk exports. Personal email forwards. It happens in "
                    "plain sight because no one is connecting the pattern.\n\n"
                    "Detection isn't about watching harder. It's about pattern correlation.\n\n"
                    "#InsiderThreat #LawFirm #DataSecurity #Detection #CyberSecurity"
                ),
                "instagram": (
                    "\"We'd know if someone was stealing data.\"\n\n"
                    "2,847 documents. 3 weeks. No one noticed.\n\n"
                    "Until we detected it in under 3 seconds.\n\n"
                    "#InsiderThreat #Detection #LawFirm #CyberSecurity #EchoWorksAI"
                ),
            },
        ],
    },
    {
        "topic": "compliance",
        "label": "Compliance Angle",
        "posts": [
            {
                "linkedin": (
                    "Security innovation has to align with compliance from the outset — "
                    "not bolted on after the fact.\n\n"
                    "This is something most security vendors get wrong. They build the detection "
                    "engine first, then figure out the regulatory implications later.\n\n"
                    "For law firms, that's backwards.\n\n"
                    "ABA Model Rule 1.6 requires reasonable measures to protect client information. "
                    "CFAA and DTSA provide the litigation framework. Your detection system needs to "
                    "produce evidence that holds up in proceedings — not just dashboards.\n\n"
                    "Compliance-first architecture:\n"
                    "• On-premise data residency (zero egress)\n"
                    "• Privilege-aware detection patterns\n"
                    "• Litigation-ready audit trails (PDF + JSONL)\n"
                    "• NIST 800-61 automated incident response\n\n"
                    "No regulatory exposure created by the tool meant to reduce it.\n\n"
                    "#Compliance #LawFirm #CyberSecurity #ABA #InsiderThreat #EchoWorksAI"
                ),
                "instagram": (
                    "Security innovation must align with compliance FROM THE OUTSET.\n\n"
                    "Not bolted on after the fact.\n\n"
                    "Our system is built compliance-first:\n"
                    "→ 100% on-premise\n"
                    "→ Privilege-aware detection\n"
                    "→ Litigation-ready evidence\n"
                    "→ NIST 800-61 compliant\n\n"
                    "No regulatory exposure created by the tool meant to reduce it.\n\n"
                    "#Compliance #CyberSecurity #LawFirm #AIONOS #EchoWorksAI"
                ),
            },
            {
                "linkedin": (
                    "Most cloud-based security tools can't serve law firms.\n\n"
                    "Why? Because sending client data off-premise — even to a security vendor — "
                    "can violate:\n"
                    "• ABA Model Rule 1.6 (client confidentiality)\n"
                    "• Client engagement letters with data residency clauses\n"
                    "• Privilege protections (attorney work product doctrine)\n\n"
                    "The detection system that's supposed to protect you shouldn't be the thing "
                    "that creates your next regulatory headache.\n\n"
                    "On-premise or nothing.\n\n"
                    "#DataResidency #LawFirm #Privacy #CyberSecurity #Compliance"
                ),
                "instagram": (
                    "Cloud security tools can't serve law firms.\n\n"
                    "Sending client data off-premise violates ABA rules and privilege "
                    "protections.\n\n"
                    "Your detection system shouldn't create your next regulatory headache.\n\n"
                    "On-premise or nothing.\n\n"
                    "#DataResidency #LawFirm #Compliance #CyberSecurity #EchoWorksAI"
                ),
            },
        ],
    },
    {
        "topic": "differentiation",
        "label": "Product Differentiation",
        "posts": [
            {
                "linkedin": (
                    "DLP tools were not built for insider threat.\n\n"
                    "They watch individual events: \"someone downloaded a file,\" \"someone "
                    "sent an email with an attachment.\"\n\n"
                    "They don't connect the chain:\n"
                    "After-hours matter access → Bulk DMS export → Personal email forward → "
                    "Cloud upload.\n\n"
                    "That's the departure pattern. It's always the same. And it takes 2-4 weeks.\n\n"
                    "We built an engine that correlates this chain in under 3 seconds. On your "
                    "hardware. No cloud.\n\n"
                    "Detection is pattern correlation, not event monitoring.\n\n"
                    "#InsiderThreat #DLP #PatternDetection #LawFirm #CyberSecurity"
                ),
                "instagram": (
                    "DLP tools were NOT built for insider threat.\n\n"
                    "They see events. We see patterns.\n\n"
                    "After-hours access → Bulk export → Personal email → Cloud upload.\n\n"
                    "That's the departure chain. We catch it in under 3 seconds.\n\n"
                    "#InsiderThreat #Detection #CyberSecurity #LawFirm #EchoWorksAI"
                ),
            },
            {
                "linkedin": (
                    "What happens in the 3.2 seconds after AION OS detects a departure pattern:\n\n"
                    "1. Sessions revoked across all systems\n"
                    "2. VPN access suspended\n"
                    "3. Evidence quarantined with litigation hold\n"
                    "4. Ethics partner notified automatically\n"
                    "5. Full audit trail generated — PDF and JSONL\n\n"
                    "NIST 800-61 compliant. Litigation-ready from the moment of detection.\n\n"
                    "Manual forensics takes weeks and costs $500-800/hr. This fires before "
                    "anyone knows it's happening.\n\n"
                    "#IncidentResponse #NIST #InsiderThreat #LawFirm #CyberSecurity #AIONOS"
                ),
                "instagram": (
                    "3.2 SECONDS.\n\n"
                    "That's detection → containment → evidence preservation.\n\n"
                    "Sessions revoked.\n"
                    "VPN suspended.\n"
                    "Evidence quarantined.\n"
                    "Ethics partner notified.\n"
                    "Audit trail generated.\n\n"
                    "All automatic. All litigation-ready.\n\n"
                    "#AIONOS #IncidentResponse #CyberSecurity #LawFirm #EchoWorksAI"
                ),
            },
        ],
    },
    {
        "topic": "social_proof",
        "label": "Authority / Social Proof",
        "posts": [
            {
                "linkedin": (
                    "We didn't build AION OS because it was an interesting engineering problem.\n\n"
                    "We built it because the alternative is finding out 77 days later that your "
                    "top partner walked with an $8M client book — and you have no evidence.\n\n"
                    "117+ behavioral patterns. Sub-second detection. On-premise deployment in "
                    "48 hours. 90-day guarantee.\n\n"
                    "Built by practitioners for practitioners.\n\n"
                    "#EchoWorksAI #InsiderThreat #LawFirm #CyberSecurity #AIONOS"
                ),
                "instagram": (
                    "117+ behavioral detection patterns.\n"
                    "Sub-second detection.\n"
                    "Deployed in 48 hours.\n"
                    "90-day guarantee.\n\n"
                    "Built by practitioners for practitioners.\n\n"
                    "#EchoWorksAI #AIONOS #InsiderThreat #LawFirm #CyberSecurity"
                ),
            },
        ],
    },
]

# Weekly posting schedule
WEEKLY_SCHEDULE = {
    0: "stats",          # Monday: Industry stat
    1: "pain",           # Tuesday: Pain point
    2: "compliance",     # Wednesday: Compliance angle
    3: "differentiation", # Thursday: Product diff
    4: "social_proof",   # Friday: Authority
    5: "pain",           # Saturday: Pain (IG-heavy day)
    6: "stats",          # Sunday: Stat recap
}


# ═══════════════════════════════════════════════════════════════
#  CONTENT ENGINE
# ═══════════════════════════════════════════════════════════════

class ContentEngine:
    """Generate and schedule social media content."""

    def get_todays_post(self, platform: str = "linkedin") -> dict:
        """Get the recommended post for today."""
        today = date.today()
        weekday = today.weekday()
        topic = WEEKLY_SCHEDULE.get(weekday, "stats")
        return self._pick_post(topic, platform, today)

    def get_week(self, platform: str = "linkedin",
                 start: Optional[date] = None) -> List[dict]:
        """Generate a full week of posts."""
        if not start:
            start = date.today()
            # Roll back to Monday
            start = start - timedelta(days=start.weekday())

        week = []
        for i in range(7):
            day = start + timedelta(days=i)
            topic = WEEKLY_SCHEDULE.get(day.weekday(), "stats")
            post = self._pick_post(topic, platform, day)
            post["date"] = day.isoformat()
            post["day_name"] = day.strftime("%A")
            week.append(post)
        return week

    def get_by_topic(self, topic: str, platform: str = "linkedin") -> dict:
        """Get a post for a specific topic."""
        return self._pick_post(topic, platform, date.today())

    def _pick_post(self, topic: str, platform: str, d: date) -> dict:
        """Pick a post from the library by topic, using date as seed."""
        pillar = None
        for p in CONTENT_PILLARS:
            if p["topic"] == topic:
                pillar = p
                break
        if not pillar:
            pillar = CONTENT_PILLARS[0]

        # Use date ordinal as seed for consistent daily selection
        idx = d.toordinal() % len(pillar["posts"])
        post_variants = pillar["posts"][idx]
        content = post_variants.get(platform, post_variants.get("linkedin", ""))

        return {
            "topic": pillar["topic"],
            "label": pillar["label"],
            "platform": platform,
            "content": content,
        }

    def list_topics(self) -> List[str]:
        """List available content topics."""
        return [p["topic"] for p in CONTENT_PILLARS]


def _print_post(post: dict) -> None:
    """Pretty-print a post."""
    print(f"\n  [{post.get('day_name', 'Today')}] {post['label']} — {post['platform'].upper()}")
    print(f"  {'─' * 55}")
    for line in post["content"].split("\n"):
        print(f"  {line}")
    print(f"  {'─' * 55}")


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    engine = ContentEngine()

    platform = "linkedin"
    topic = None
    week_mode = False

    i = 0
    while i < len(args):
        if args[i] == "--platform" and i + 1 < len(args):
            platform = args[i + 1].lower()
            if platform == "ig":
                platform = "instagram"
            i += 2
        elif args[i] == "--topic" and i + 1 < len(args):
            topic = args[i + 1]
            i += 2
        elif args[i] == "--week":
            week_mode = True
            i += 1
        else:
            i += 1

    if week_mode:
        print(f"\n  CONTENT CALENDAR — {platform.upper()}")
        print(f"  {'═' * 55}")
        posts = engine.get_week(platform=platform)
        for p in posts:
            _print_post(p)
    elif topic:
        post = engine.get_by_topic(topic, platform=platform)
        _print_post(post)
    else:
        post = engine.get_todays_post(platform=platform)
        print(f"\n  TODAY'S POST — {platform.upper()}")
        _print_post(post)


if __name__ == "__main__":
    main()
