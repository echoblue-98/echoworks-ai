"""
Creator IP Vertical — Sales Configuration
============================================
Master file exfiltration, unreleased track leaks,
session stem theft, catalog rights disputes,
producer/engineer departure data staging.

Target: Record labels (indie + major-distributed),
music publishers, production studios, artist management.
"""

from aionos.sales.models import (
    BuyerPersona, BuyerRole, Objection, OutboundSequence,
    PricingTier, RegulatoryHook, ThreatScenario, Vertical, VerticalID,
)

CREATOR_VERTICAL = Vertical(
    id=VerticalID.CREATOR,
    display_name="Creator IP — Labels, Studios & Publishers",
    tagline="Catch the leak before the drop date",

    # ── What we detect ────────────────────────────────────────────
    threat_scenarios=[
        ThreatScenario(
            name="Master File Exfiltration",
            description="Engineer or producer exports unreleased master files, "
                        "stems, or session data from studio systems before or "
                        "after departing. Tracks appear on leak sites days later.",
            event_chain=[
                "After-hours DAW session access (Pro Tools / Logic / Ableton)",
                "Bulk export of stems / bounced masters (10+ GB)",
                "Transfer to personal drive (USB, AirDrop, cloud upload)",
                "Track surfaces on leak forum or rival's reference playlist",
            ],
            detection_speed="< 3 seconds",
            financial_impact="$500K-$10M in lost first-week revenue per album leak",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Pre-Release Catalog Leak",
            description="Insider with access to release schedule and master "
                        "vault leaks tracks ahead of strategic drop date, "
                        "destroying marketing spend and chart positioning.",
            event_chain=[
                "Access to release calendar / metadata system",
                "Download of pre-release masters from vault / DAM",
                "Distribution to unauthorized third party",
                "Track appears on streaming rip site or social media snippet",
            ],
            detection_speed="< 3 seconds",
            financial_impact="$1M-$20M in marketing ROI + chart position loss",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Producer Departure — Session Staging",
            description="Producer or mixer builds a personal archive of session "
                        "files, stems, and reference mixes before leaving the label "
                        "or switching management. Sessions used as leverage or "
                        "shopped to competing labels.",
            event_chain=[
                "Systematic download of sessions across multiple projects",
                "Export of mix stems and alternate versions",
                "Cloud sync to personal Dropbox/Google Drive",
                "Session files referenced in competing label's release",
            ],
            detection_speed="< 5 seconds",
            financial_impact="$200K-$5M in rights disputes + litigation costs",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Rights & Royalty Data Theft",
            description="A&R or business affairs staff exports artist contracts, "
                        "royalty splits, and rights ownership data before "
                        "departing to a competitor.",
            event_chain=[
                "Bulk export of royalty accounting data",
                "Download of artist contracts from document system",
                "Email forward of deal memos to personal account",
                "Competitor makes unusually informed offers to your artists",
            ],
            detection_speed="< 3 seconds",
            financial_impact="$1M-$50M in artist roster poaching",
            pattern_engine_bypass=True,
        ),
    ],

    # ── Who we sell to ────────────────────────────────────────────
    buyer_personas=[
        BuyerPersona(
            title="General Manager / President",
            role=BuyerRole.DECISION_MAKER,
            pain_points=[
                "Unreleased album leaked 2 weeks before drop date",
                "No visibility into who accesses master vault after hours",
                "Reactive forensics after leak costs $100K+ and takes weeks",
            ],
            trigger_events=[
                "Recent pre-release leak from the label or peer label",
                "Engineer or producer departure within last 6 months",
                "Artist publicly complained about leaked unreleased material",
            ],
            linkedin_search='"General Manager" OR "President" AND ("record label" OR "records")',
            email_subject="An unreleased album leaked 2 weeks before drop — the exfiltration started 3 weeks earlier",
            opening_line="The engineer who exports session stems and the attorney "
                         "who walks with client files — same threat model.",
        ),
        BuyerPersona(
            title="Head of A&R / Creative Director",
            role=BuyerRole.INFLUENCER,
            pain_points=[
                "Reference tracks and demos shared too broadly across sessions",
                "No audit trail on who has accessed which session files",
                "Producers shopping beats that were made under work-for-hire",
            ],
            trigger_events=[
                "Producer left and released similar-sounding material elsewhere",
                "Demo leaked on social media before deal closed",
                "Work-for-hire dispute over session ownership",
            ],
            linkedin_search='"Head of A&R" OR "VP A&R" OR "Creative Director" AND ("label" OR "records")',
            email_subject="Your demo session from Tuesday is already on SoundCloud — here's how that happens",
            opening_line="Most labels find out about a session leak after it's on social media. "
                         "By then, the damage is done.",
        ),
        BuyerPersona(
            title="COO / VP Operations",
            role=BuyerRole.TECHNICAL,
            pain_points=[
                "No centralized access control across studio systems and cloud storage",
                "DMCA takedowns are reactive — content stays up for days",
                "Can't prove chain of custody for rights disputes",
            ],
            trigger_events=[
                "DMCA filing volume increasing quarter over quarter",
                "Rights dispute required forensic audit of file access",
                "Insurance or distributor requiring security documentation",
            ],
            linkedin_search='"COO" OR "VP Operations" AND ("music" OR "label" OR "entertainment")',
            email_subject="4 sessions exported, 2 personal drives, 1 leak site — would your systems catch it?",
            opening_line="When a producer walks with session files, you need "
                         "evidence within hours, not a 6-week forensic engagement.",
        ),
    ],

    # ── Regulatory / contractual pressure ─────────────────────────
    regulatory_hooks=[
        RegulatoryHook(
            name="Copyright Act — Work for Hire",
            citation="17 U.S.C. § 101 (work made for hire)",
            penalty_range="Statutory damages $750-$150,000 per work infringed",
            relevance="Masters created under work-for-hire belong to the label. "
                      "Unauthorized export = copyright infringement. AION provides "
                      "evidence of the exfiltration chain.",
        ),
        RegulatoryHook(
            name="DMCA — Anti-Circumvention",
            citation="17 U.S.C. § 1201",
            penalty_range="$200-$2,500 statutory + criminal up to $500K / 5 years",
            relevance="Circumventing access controls on master vaults or DAM "
                      "systems = DMCA violation. AION detects bypass attempts.",
        ),
        RegulatoryHook(
            name="Computer Fraud & Abuse Act (CFAA)",
            citation="18 U.S.C. § 1030",
            penalty_range="Civil damages + criminal penalties up to 10 years",
            relevance="Exceeding authorized access to studio/label systems to "
                      "export session files = CFAA violation. AION logs evidence.",
        ),
        RegulatoryHook(
            name="Defend Trade Secrets Act (DTSA)",
            citation="18 U.S.C. § 1836",
            penalty_range="Injunctive relief + compensatory + exemplary damages (2x)",
            relevance="Unreleased masters, release schedules, royalty data = "
                      "trade secrets. Misappropriation detected in real time.",
        ),
    ],

    # ── How we handle pushback ────────────────────────────────────
    objections=[
        Objection(
            objection="We use Dropbox / Google Drive with permissions.",
            response="Cloud storage permissions control who CAN access files. "
                     "They don't detect WHO IS accessing files at 2 AM and "
                     "exporting 15 GB of stems to a personal account. "
                     "AION correlates the full chain: access → export → transfer.",
            proof_point="One label had proper Drive permissions. An engineer "
                        "with legitimate access exported 47 sessions in one night. "
                        "Nobody knew until tracks surfaced on a leak site 3 weeks later.",
        ),
        Objection(
            objection="Leaks are just part of the music business.",
            response="Leaks cost $500K-$10M in first-week revenue per album. "
                     "Marketing campaigns built around surprise drops are destroyed. "
                     "Chart positioning is gone. It doesn't have to be the cost of "
                     "doing business — the detection technology exists now.",
        ),
        Objection(
            objection="We're a small label — this is for majors.",
            response="Small labels are hit harder. A major absorbs a leak. "
                     "For an indie label, one leaked album can be the difference "
                     "between a profitable quarter and layoffs. And the threat "
                     "is the same — an engineer with session access is an engineer "
                     "with session access, regardless of label size.",
        ),
        Objection(
            objection="Our producers are trusted people.",
            response="Insider threats aren't about trust — they're about access. "
                     "77% of data exfiltration is from authorized users doing "
                     "unauthorized things. These aren't hackers. They're people "
                     "who already have the keys.",
        ),
        Objection(
            objection="We'd need this to work with Pro Tools / Logic / our DAW.",
            response="AION monitors at the file system and network level — it "
                     "doesn't need to integrate with any specific DAW. If a file "
                     "moves, we see it. Export, transfer, upload — all detected "
                     "regardless of which application originated the action.",
        ),
    ],

    # ── Pricing ───────────────────────────────────────────────────
    pricing=[
        PricingTier(
            tier_name="Catalog Watch",
            monthly=3750,
            includes=[
                "Detection engine (master exfiltration + session staging)",
                "Studio system file monitoring",
                "Real-time alerts on bulk exports",
                "Monthly pattern updates",
                "DMCA evidence package generation",
            ],
        ),
        PricingTier(
            tier_name="Vault Guard",
            monthly=7500,
            includes=[
                "Everything in Catalog Watch",
                "Multi-studio coverage",
                "Release calendar integration",
                "Custom pattern development (label-specific workflows)",
                "Quarterly threat briefings",
            ],
        ),
        PricingTier(
            tier_name="Full Spectrum",
            monthly=12500,
            includes=[
                "Everything in Vault Guard",
                "Dedicated threat analyst",
                "24/7 monitoring across all label systems",
                "Rights dispute evidence automation",
                "Annual red team exercise (simulated insider leak)",
            ],
        ),
    ],

    # ── Outbound cadence ──────────────────────────────────────────
    sequence=[
        OutboundSequence(day=1, channel="linkedin", action="Send connection request", template_key="creator_connection"),
        OutboundSequence(day=1, channel="email", action="Send cold email", template_key="creator_cold_email"),
        OutboundSequence(day=4, channel="linkedin", action="Follow up if accepted", template_key="creator_followup_accept"),
        OutboundSequence(day=7, channel="email", action="Send demo recording link", template_key="creator_demo_link"),
        OutboundSequence(day=10, channel="linkedin", action="Share relevant insight (leak news)", template_key="creator_insight"),
        OutboundSequence(day=14, channel="email", action="Breakup email — last touch", template_key="creator_breakup"),
    ],

    # ── Competitive positioning ───────────────────────────────────
    competitors={
        "DistroKid / TuneCore": "Distribution platforms, not security. No insider threat detection.",
        "Audible Magic": "Content ID / fingerprinting for published content. Doesn't detect pre-release exfiltration.",
        "YouTube Content ID": "Post-publication matching only. Leak already happened.",
        "Manual forensics": "Reactive. $500-800/hr. Takes weeks. Evidence often stale by the time it's gathered.",
        "Cloud storage permissions": "Access control ≠ threat detection. Authorized users are the threat.",
    },

    # ── Key stats ─────────────────────────────────────────────────
    stats={
        "avg_detection_time_industry": "3-6 weeks post-leak (after track surfaces publicly)",
        "avg_detection_time_aion": "< 3 seconds (at point of exfiltration)",
        "avg_revenue_loss_per_leak": "$500K-$10M first-week revenue impact",
        "insider_threat_percentage": "77% of data exfiltration from authorized users",
        "avg_forensic_cost": "$100K-$500K per incident (reactive investigation)",
        "aion_false_positive_rate": "< 2%",
    },
)
