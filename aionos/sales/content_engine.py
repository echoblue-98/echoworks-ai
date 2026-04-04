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
    {
        "topic": "strategy",
        "label": "Strategic Insight",
        "posts": [
            {
                "linkedin": (
                    "Most cybersecurity vendors compete on product features.\n\n"
                    "But features get copied. Every time something works, 20 competitors "
                    "show up doing the exact same thing within 6 months.\n\n"
                    "What doesn't get copied:\n"
                    "• Distribution — the engine that gets you to every law firm in America\n"
                    "• Domain depth — 117 behavioral patterns built from studying how attorneys "
                    "actually exfiltrate data\n"
                    "• Compliance architecture — built for ABA rules from day one, not bolted on\n\n"
                    "Product moats are temporary. Distribution moats compound.\n\n"
                    "We're not building a feature. We're building the category.\n\n"
                    "#Strategy #CyberSecurity #LawFirm #InsiderThreat #EchoWorksAI"
                ),
                "instagram": (
                    "Features get copied.\n"
                    "Distribution doesn't.\n\n"
                    "We're not building a product.\n"
                    "We're building the category.\n\n"
                    "117 detection patterns. Compliance-first. On-premise.\n\n"
                    "#Strategy #CyberSecurity #LawFirm #EchoWorksAI"
                ),
            },
            {
                "linkedin": (
                    "\"Just price it cheap and the market will come.\"\n\n"
                    "This is the most dangerous startup advice in Silicon Valley.\n\n"
                    "Marc Andreessen: \"Higher prices equals faster growth. If you price high, "
                    "you can fund a much more expensive sales and marketing effort, which means "
                    "you're much more likely to win the market.\"\n\n"
                    "We charge $5,000/month. Not because we want to be expensive. Because:\n\n"
                    "1. It funds the R&D that keeps us 2 years ahead\n"
                    "2. It funds the support your firm actually needs during incidents\n"
                    "3. It proves the moat — if your detection system is irreplaceable, "
                    "the price reflects it\n\n"
                    "The definition of a moat is the ability to charge more.\n\n"
                    "#Pricing #Strategy #CyberSecurity #LawFirm #EchoWorksAI"
                ),
                "instagram": (
                    "\"Price it cheap and the market will come.\"\n\n"
                    "The most dangerous advice in tech.\n\n"
                    "Higher price = faster growth.\n"
                    "Higher price = better R&D.\n"
                    "Higher price = better support.\n\n"
                    "The definition of a moat is the ability to charge more.\n\n"
                    "#Strategy #Pricing #CyberSecurity #LawFirm #EchoWorksAI"
                ),
            },
            {
                "linkedin": (
                    "Early adopters will find you.\n\n"
                    "The other 95% of the market won't.\n\n"
                    "This is the gap that kills most cybersecurity startups. They get a "
                    "handful of enthusiastic firms who sought them out — then wonder why "
                    "growth stalls.\n\n"
                    "The firms that need insider threat detection the most aren't on "
                    "product hunt sites. They're running 50-attorney practices, dealing "
                    "with partner departures in real time, and they've never heard of you.\n\n"
                    "You have to go to them. With the right message. At the right time. "
                    "Through the right channel.\n\n"
                    "Product gets you in the door. Distribution gets you the market.\n\n"
                    "#Distribution #Sales #CyberSecurity #LawFirm #InsiderThreat #EchoWorksAI"
                ),
                "instagram": (
                    "Early adopters find you.\n"
                    "The other 95% won't.\n\n"
                    "Product gets you in the door.\n"
                    "Distribution gets you the market.\n\n"
                    "#Distribution #Strategy #CyberSecurity #LawFirm #EchoWorksAI"
                ),
            },
        ],
    },
    {
        "topic": "sovereignty",
        "label": "Data Sovereignty",
        "posts": [
            {
                "linkedin": (
                    "Cloud AI is a community kitchen.\n\n"
                    "Everyone's grandma dumps recipes into the same pot. Your sauce becomes "
                    "their sauce.\n\n"
                    "Data sovereignty is your kitchen. Only your cooks touch your recipes.\n\n"
                    "Law firms upload case files to cloud AI tools every day. Instant drafting "
                    "magic. No one asks \"where'd my patterns go?\"\n\n"
                    "Here's where they go:\n"
                    "• Into model weights that serve other tenants\n"
                    "• Into telemetry pipelines feeding vendor data lakes\n"
                    "• Into training sets that make competitors' tools smarter\n\n"
                    "SOC2 badges don't address model inversion — where your behavioral patterns "
                    "leak through outputs to other tenants. Encryption doesn't help when the "
                    "decrypted data trains the model.\n\n"
                    "The tool that's supposed to protect your firm shouldn't be the extraction "
                    "machine underneath.\n\n"
                    "On-premise or nothing.\n\n"
                    "#DataSovereignty #AI #LawFirm #Privacy #CyberSecurity #EchoWorksAI"
                ),
                "instagram": (
                    "Cloud AI = community kitchen.\n"
                    "Your sauce becomes their sauce.\n\n"
                    "Sovereignty = your kitchen.\n"
                    "Only your cooks touch your recipes.\n\n"
                    "On-premise or nothing.\n\n"
                    "#DataSovereignty #AI #LawFirm #Privacy #EchoWorksAI"
                ),
            },
            {
                "linkedin": (
                    "Nobody sees a sovereignty breach.\n\n"
                    "A ransomware attack makes headlines. A departing attorney makes the "
                    "trade press. But when your cloud AI vendor feeds your patterns into "
                    "a model that serves your competitor — that's invisible.\n\n"
                    "It shows up as margin erosion. As a competitor who suddenly knows your "
                    "pricing signals. As a rival firm that drafts motions that sound eerily "
                    "familiar.\n\n"
                    "There's no breach notification for this. No incident report. No headline.\n\n"
                    "Just a slow bleed you can't trace.\n\n"
                    "This is why \"it just works\" isn't good enough. Speed isn't the question. "
                    "Ownership is.\n\n"
                    "Your detection system should learn from YOUR history, not a shared model "
                    "trained on everyone's data.\n\n"
                    "#DataSovereignty #InsiderThreat #AI #LawFirm #CyberSecurity #EchoWorksAI"
                ),
                "instagram": (
                    "Ransomware makes headlines.\n"
                    "Sovereignty breaches don't.\n\n"
                    "They show up as margin erosion.\n"
                    "As competitors who suddenly know your pricing.\n"
                    "As rival firms drafting motions that sound familiar.\n\n"
                    "No breach notification. No headline.\n"
                    "Just a slow bleed you can't trace.\n\n"
                    "#DataSovereignty #AI #LawFirm #CyberSecurity #EchoWorksAI"
                ),
            },
            {
                "linkedin": (
                    "5 reasons the majority misses data sovereignty:\n\n"
                    "1. \"It just works\" illusion — Cloud AI demos flawlessly. Upload case "
                    "files, get instant magic. No one asks where their patterns went.\n\n"
                    "2. Complexity hides extraction — Understanding the pipeline from LoRA "
                    "fine-tuning to model weights to vendor data lakes requires depth most "
                    "buyers don't have.\n\n"
                    "3. Hype cycle drowns warnings — \"AI = future\" drowns out \"your IP = "
                    "their training data.\" CISOs raising flags sound like dinosaurs.\n\n"
                    "4. No immediate pain trigger — Data mixing is invisible. You don't see "
                    "the competitor undercutting you because the model learned your signals.\n\n"
                    "5. Security theater — SOC2 badges, encryption claims, \"enterprise-grade.\" "
                    "None address model inversion where your patterns leak through outputs to "
                    "other tenants.\n\n"
                    "The people who see it are talking to operators, not marketers.\n\n"
                    "What's your take — is cloud convenience worth the extraction tradeoff?\n\n"
                    "#DataSovereignty #AI #CyberSecurity #LawFirm #Privacy #EchoWorksAI"
                ),
                "instagram": (
                    "Why nobody sees the sovereignty problem:\n\n"
                    "1. \"It just works\" — no one asks where patterns go\n"
                    "2. Complexity hides extraction\n"
                    "3. Hype drowns warnings\n"
                    "4. No immediate pain trigger\n"
                    "5. Security theater (SOC2 ≠ sovereignty)\n\n"
                    "The people who see it talk to operators, not marketers.\n\n"
                    "#DataSovereignty #AI #LawFirm #CyberSecurity #EchoWorksAI"
                ),
            },
        ],
    },
    {
        "topic": "buyer_education",
        "label": "Buyer Education",
        "posts": [
            {
                "linkedin": (
                    "3 questions every managing partner should ask before buying cybersecurity\n\n"
                    "Most law firms buy based on features. That's the wrong filter.\n\n"
                    "Ask these instead:\n\n"
                    "1. \"Where does our client data go when your system analyzes it?\"\n"
                    "If the answer is \"our cloud\" — you just gave a third party access to "
                    "privileged communications.\n\n"
                    "2. \"What happens when an attorney gives two weeks notice?\"\n"
                    "If they can't answer in specifics — they're selling generic IT security, "
                    "not insider threat detection.\n\n"
                    "3. \"Does this satisfy ABA Model Rule 1.6 and Formal Opinion 477R?\"\n"
                    "If they pause — they didn't build for law firms. They bolted on a "
                    "compliance checkbox.\n\n"
                    "The right vendor answers all three without hesitating.\n\n"
                    "#CyberSecurity #LawFirm #InsiderThreat #ABA #DataProtection"
                ),
                "instagram": (
                    "3 questions before you buy cybersecurity:\n\n"
                    "1. Where does our client data go?\n"
                    "2. What happens when an attorney gives notice?\n"
                    "3. Does this satisfy ABA Model Rule 1.6?\n\n"
                    "If your vendor pauses on any of these — they didn't build for law firms.\n\n"
                    "#CyberSecurity #LawFirm #InsiderThreat #EchoWorksAI"
                ),
            },
        ],
    },
]

# Weekly posting schedule
WEEKLY_SCHEDULE = {
    0: "stats",           # Monday: Industry stat
    1: "pain",            # Tuesday: Pain point
    2: "compliance",      # Wednesday: Compliance angle
    3: "differentiation", # Thursday: Product diff
    4: "social_proof",    # Friday: Authority
    5: "strategy",        # Saturday: Strategic insight
    6: "sovereignty",     # Sunday: Data sovereignty
}

# Bonus rotation — buyer education posts cycle in on Wednesdays (alternates with compliance)
BONUS_PILLARS = ["buyer_education"]


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
