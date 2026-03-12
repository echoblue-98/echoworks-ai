"""
AION OS — Pilot Outreach Email Generator
=========================================
Generates firm-specific pilot proposal emails ready to send.

Usage:
    python pilot_outreach_email.py [kirkland|latham|quinn|all]
    
Or import and use in the pitch deck:
    from pilot_outreach_email import generate_email, PILOT_TERMS
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from firm_demo_packets import FIRM_PACKETS


# ════════════════════════════════════════════════════════════════
#  PILOT TERMS
# ════════════════════════════════════════════════════════════════
PILOT_TERMS = {
    "duration": "30 days",
    "analyses_included": 3,
    "pilot_fee": "$0 (no cost, no obligation)",
    "full_engagement_range": "$20K–$60K/month",
    "deliverables": [
        "3 custom departure risk analyses on hypothetical scenarios matching your practice mix",
        "Live demonstration of real-time detection across all 66 attack patterns",
        "Behavioral baseline model built on anonymized sample data from your environment",
        "Written threat assessment report with quantified risk exposure",
        "ROI analysis specific to your firm's partner count, revenue, and departure history",
    ],
    "requirements_from_firm": [
        "30-minute kickoff call with CISO or CTO",
        "Optional: anonymized 30-day event log sample (improves accuracy, not required)",
        "Designate one point of contact for the pilot period",
    ],
    "what_happens_after": [
        "You keep all reports and analyses regardless of decision",
        "No auto-renewal, no hidden commitments",
        "If valuable → discuss full deployment ($20K–$60K/month flat, on-premise)",
        "If not valuable → you still got a free threat assessment worth $50K+",
    ],
}


# ════════════════════════════════════════════════════════════════
#  EMAIL GENERATOR
# ════════════════════════════════════════════════════════════════
def generate_email(
    firm_key: str,
    recipient_name: str = "[Name]",
    recipient_title: str = "[Title]",
    sender_name: str = "Corey",
    sender_title: str = "Founder, CodeTyphoons",
) -> dict:
    """
    Generate a firm-specific pilot outreach email.
    
    Returns dict with: subject, body, follow_up_note
    """
    packet = FIRM_PACKETS.get(firm_key)
    if not packet:
        raise ValueError(f"No packet for '{firm_key}'. Available: {list(FIRM_PACKETS.keys())}")

    # Pick the most compelling scenario for the subject line
    top_scenario = packet.scenarios[0]
    
    subject = f"{packet.short_name} — insider threat pattern we built specifically for your firm"
    
    body = f"""
{recipient_name},

{packet.email_hook}

I'm {sender_name}, {sender_title}. I built AION OS after watching a 39-month litigation unfold over a single employee departure. The system we've built is purpose-built for law firm insider threats — it's not a general-purpose SIEM repackaged with a legal label.

**What makes this different from Splunk, CrowdStrike, or DTEX:**

AION correlates multi-day event sequences into attack chains. It doesn't just flag "large download" — it connects the VPN login at 11 PM, the client database export at midnight, the personal cloud sync at 1 AM, and the resignation letter at 9 AM into a single pattern with a severity score and recommended response.

We've built {len(packet.scenarios)} attack scenarios specifically modeled on {packet.short_name}'s practice mix ({', '.join(packet.key_practices)}). Here's one:

**Scenario: {top_scenario.name}**
{top_scenario.description}
Financial exposure: {top_scenario.financial_impact}

AION detects this pattern starting at the first anomalous event — typically 3-6 weeks before resignation. Your current tools find it during post-departure forensics, if at all.

**The offer:**

A {PILOT_TERMS['duration']} pilot at {PILOT_TERMS['pilot_fee']}. We run {PILOT_TERMS['analyses_included']} custom analyses on hypothetical scenarios matching your firm's practice areas. You get:

""".strip()

    for d in PILOT_TERMS["deliverables"]:
        body += f"\n• {d}"

    body += f"""

**What we need from you:**

"""
    for r in PILOT_TERMS["requirements_from_firm"]:
        body += f"• {r}\n"

    body += f"""
**After the pilot:**

"""
    for w in PILOT_TERMS["what_happens_after"]:
        body += f"• {w}\n"

    body += f"""
I have a 15-minute live demo I can run on a call — every section runs live detection, not screenshots. If it's not immediately valuable, I'll know in the first 5 minutes and won't waste your time.

Would 20 minutes work sometime in the next two weeks?

Best,
{sender_name}
{sender_title}

P.S. — I built {len(top_scenario.events)} specific event sequences for {packet.short_name} scenarios. The attack patterns reference your practice areas, your typical partner profiles, and your competitive landscape. This isn't a generic pitch — it's a threat briefing.
""".strip()

    follow_up = f"""
FOLLOW-UP NOTE (send 5 days after initial email if no response):

Subject: Re: {subject}

{recipient_name},

Following up on my note last week about the insider threat patterns we built for {packet.short_name}.

Since then, we've completed a competitive analysis showing that none of the incumbent solutions (Splunk, Sentinel, CrowdStrike, DTEX) offer:
- Law-firm-specific attack patterns ({len(packet.scenarios)} built for {packet.short_name})
- Attorney departure detection
- Ethics wall breach monitoring  
- Per-user behavioral baselines
- Self-improving detection rules

The gap is significant and the window before these vendors catch up is 12-24 months.

Happy to show you the 15-minute demo at your convenience. No cost, no obligation.

—{sender_name}
""".strip()

    return {
        "subject": subject,
        "body": body,
        "follow_up_note": follow_up,
        "firm": packet.name,
        "contact_targets": packet.contact_targets,
    }


# ════════════════════════════════════════════════════════════════
#  DAN UPDATE EMAIL (the one you send NOW, not to a firm)
# ════════════════════════════════════════════════════════════════
DAN_DEMO_UPDATE = """
Subject: AION OS demo is live — walkthrough attached

Dan,

While we figure out hardware timing, I wanted to show you what we built this week.

The interactive demo is live and running. 11 sections, every one runs real detection — not screenshots, not mockups. Here's what's in it:

1. **Opening** — hero stats: 50/50 tests, 66 attack patterns, 13,439 events/sec
2. **Firm-Specific Demos** — custom attack scenarios for Kirkland, Latham, and Quinn Emanuel with real intelligence and talking points
3. **Live Attack Simulation** — 5 pre-built scenarios + custom attack builder, runs through the actual detection engine
4. **Pattern Explorer** — searchable/filterable browser for all 66 patterns and 92 event types
5. **Live Benchmark Suite** — 10K-event throughput test, latency measurement, baseline + improvement engine validation
6. **Self-Improvement Engine** — invariant viewer, active policy inspector, live adversarial poisoning test
7. **ROI Calculator** — interactive sliders tuned per firm
8. **Competitive Matrix** — side-by-side vs Splunk/Sentinel/CrowdStrike/DTEX
9. **Architecture** — 5-layer deep dive with all 21 API endpoints
10. **Market & Pricing** — TAM analysis, 3 pricing tiers, 20 target firms
11. **The Close** — what we need, what you get

Every section is interactive. The attack demos run the actual engine in real-time with sub-millisecond latency.

I also built 3 firm-specific demo packets (Kirkland, Latham, Quinn Emanuel) with:
- Hyper-personalized attack scenarios (9 total) based on public intelligence
- Pre-written outreach emails ready to customize and send
- Financial impact analysis per scenario
- Key talking points for each demo

The deck runs offline too — pre-cached results so it works without internet.

Next step: I want to run this for you on a call so you can see the flow. 20 minutes. Let me know when works.

—Corey
""".strip()


# ════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target == "dan":
        print("=" * 60)
        print("  EMAIL TO DAN — DEMO UPDATE")
        print("=" * 60)
        print()
        print(DAN_DEMO_UPDATE)
        print()
        sys.exit(0)

    firms_to_generate = list(FIRM_PACKETS.keys()) if target == "all" else [
        k for k in FIRM_PACKETS if target.lower() in k.lower()
    ]

    if not firms_to_generate:
        print(f"No firm matching '{target}'. Available: {list(FIRM_PACKETS.keys())}")
        sys.exit(1)

    for firm in firms_to_generate:
        email = generate_email(firm)
        print("=" * 60)
        print(f"  PILOT EMAIL: {email['firm']}")
        print(f"  Contact targets: {', '.join(email['contact_targets'])}")
        print("=" * 60)
        print(f"\nSubject: {email['subject']}\n")
        print(email["body"])
        print("\n" + "-" * 60)
        print(email["follow_up_note"])
        print()
