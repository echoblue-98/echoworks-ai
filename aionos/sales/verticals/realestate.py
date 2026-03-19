"""
Real Estate Vertical — Sales Configuration
=============================================
Wire fraud BEC, money laundering, rapid-flip schemes,
shell entity obfuscation, closing fraud.

Target: Title companies, large brokerages (100+ agents),
escrow/settlement companies, commercial RE firms.
"""

from aionos.sales.models import (
    BuyerPersona, BuyerRole, Objection, OutboundSequence,
    PricingTier, RegulatoryHook, ThreatScenario, Vertical, VerticalID,
)

REALESTATE_VERTICAL = Vertical(
    id=VerticalID.REALESTATE,
    display_name="Real Estate",
    tagline="Stop the wire before the funds move",

    # ── What we detect ────────────────────────────────────────────
    threat_scenarios=[
        ThreatScenario(
            name="Wire Fraud BEC — Closing Redirect",
            description="Threat actor compromises email thread, sends modified "
                        "wire instructions with spoofed domain and new routing "
                        "number. Buyer wires closing funds to offshore account.",
            event_chain=[
                "Email thread compromise (domain homoglyph detected)",
                "Modified wire instructions with new routing number",
                "Urgency language scoring exceeds threshold",
                "Sender IP geolocation anomaly (foreign origin)",
                "Wire freeze at bank + buyer alert via secure channel",
            ],
            detection_speed="< 3 seconds",
            financial_impact="$200K-$2M per transaction (avg RE wire: $400K)",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Money Laundering — Rapid Flip",
            description="Property purchased and resold within days at inflated "
                        "price through layered LLC entities with offshore funding.",
            event_chain=[
                "Deed transfer between LLC entities",
                "Property relisted within 30 days at 30%+ markup",
                "Beneficial ownership moved to multi-layer Delaware entity",
                "All-cash purchase with offshore wire origin",
            ],
            detection_speed="< 3 seconds",
            financial_impact="$1M-$50M laundered per transaction chain",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Invoice Manipulation — Vendor Fraud",
            description="Fraudulent vendor invoices inserted into closing "
                        "documents with inflated amounts or fictitious services.",
            event_chain=[
                "New vendor added to closing file within 48 hours of settlement",
                "Invoice amount exceeds historical average for service type",
                "Vendor entity created within 90 days (shell indicator)",
                "Routing number on invoice doesn't match vendor's known bank",
            ],
            detection_speed="< 5 seconds",
            financial_impact="$50K-$500K per closing",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Straw Buyer Detection",
            description="Purchaser is a nominee acting on behalf of a sanctioned "
                        "or undisclosed beneficial owner to circumvent CTR/SAR "
                        "reporting thresholds.",
            event_chain=[
                "Purchaser profile inconsistent with property value (income/employment)",
                "Multiple properties purchased under same entity structure",
                "Cash purchases structured below CTR threshold ($10K increments)",
                "Beneficial owner matches OFAC/SDN watchlist patterns",
            ],
            detection_speed="< 5 seconds",
            financial_impact="FinCEN penalties + criminal prosecution",
            pattern_engine_bypass=False,  # needs LLM for entity resolution
        ),
    ],

    # ── Who we sell to ────────────────────────────────────────────
    buyer_personas=[
        BuyerPersona(
            title="Title Company President / Owner",
            role=BuyerRole.DECISION_MAKER,
            pain_points=[
                "Title insurance claims from wire fraud increasing",
                "'Call to verify' policies break under closing pressure",
                "No automated detection of BEC in email threads",
            ],
            trigger_events=[
                "Wire fraud incident at company or peer firm",
                "Title insurance premium increase due to fraud claims",
                "FinCEN Geographic Targeting Order issued for their market",
            ],
            linkedin_search='"President" OR "Owner" AND "title company"',
            email_subject="An $847K wire redirect was caught 18 hours before closing — here's how",
            opening_line="Wire fraud BEC is costing real estate over $400M a year. "
                         "The attack is always the same.",
        ),
        BuyerPersona(
            title="Brokerage Ops Manager / COO",
            role=BuyerRole.INFLUENCER,
            pain_points=[
                "Agents forwarding wire instructions via unsecured email",
                "No visibility into closing document chain of custody",
                "E&O insurance claims from fraud incidents",
            ],
            trigger_events=[
                "Agent fell for BEC — funds lost",
                "E&O insurance audit or renewal",
                "New state real estate commission security requirements",
            ],
            linkedin_search='"Operations Manager" OR "COO" AND ("brokerage" OR "real estate")',
            email_subject="Your agents are one spoofed email away from a $400K wire loss",
            opening_line="The buyer's agent forwards 'updated wire instructions' from "
                         "what looks like the title company. The domain is off by one letter.",
        ),
        BuyerPersona(
            title="BSA/AML Compliance Officer",
            role=BuyerRole.TECHNICAL,
            pain_points=[
                "Manual SAR filing process takes 2-3 days",
                "FinCEN beneficial ownership rules expanding",
                "Can't correlate property transactions with entity structures",
            ],
            trigger_events=[
                "FinCEN issued new beneficial ownership rule",
                "Geographic Targeting Order for local market",
                "Peer institution received FinCEN enforcement action",
            ],
            linkedin_search='"BSA Officer" OR "AML Compliance" AND "real estate"',
            email_subject="4 transactions, 3 shell entities, 1 offshore wire — would your BSA program catch it?",
            opening_line="FinCEN's Corporate Transparency Act is expanding beneficial "
                         "ownership requirements. Manual review can't keep up.",
        ),
    ],

    # ── Regulatory pressure ───────────────────────────────────────
    regulatory_hooks=[
        RegulatoryHook(
            name="FinCEN — Bank Secrecy Act",
            citation="31 U.S.C. § 5311",
            penalty_range="$25K-$1M per violation + criminal penalties",
            relevance="Title companies and settlement agents have SAR filing "
                      "obligations. AION automates detection and pre-fills SARs.",
        ),
        RegulatoryHook(
            name="Corporate Transparency Act (CTA)",
            citation="31 U.S.C. § 5336 (effective 2024)",
            penalty_range="$500/day civil + $10K criminal + 2 years imprisonment",
            relevance="Requires beneficial ownership disclosure. AION detects "
                      "multi-layer shell entity structures automatically.",
        ),
        RegulatoryHook(
            name="FinCEN Geographic Targeting Orders",
            citation="FinCEN GTO (periodically renewed)",
            penalty_range="$25K per violation",
            relevance="Requires reporting of all-cash purchases above threshold "
                      "in targeted markets. AION flags qualifying transactions.",
        ),
        RegulatoryHook(
            name="FBI IC3 Wire Fraud Reporting",
            citation="18 U.S.C. § 1343 (Wire Fraud)",
            penalty_range="Up to 20 years imprisonment per count",
            relevance="AION generates IC3 complaint data automatically when "
                      "BEC wire fraud is detected.",
        ),
    ],

    # ── Objection handling ────────────────────────────────────────
    objections=[
        Objection(
            objection="We tell buyers to call and verify wire instructions.",
            response="'Call to verify' policies have a 60%+ non-compliance rate under "
                     "closing pressure. Buyers call the number on the spoofed email. "
                     "AION catches the domain homoglyph and routing number anomaly "
                     "before the buyer even sees the email.",
            proof_point="$847K wire redirect caught 18 hours before closing — "
                        "the buyer had already prepared the wire.",
        ),
        Objection(
            objection="Our title insurance covers wire fraud losses.",
            response="Title insurance covers title defects, not BEC wire fraud. "
                     "Most policies explicitly exclude social engineering losses. "
                     "When the buyer wires $400K to a threat actor, that money is gone.",
        ),
        Objection(
            objection="Wire fraud is the bank's problem.",
            response="Once funds clear the receiving bank (usually 24-48 hours), "
                     "recovery rate drops below 10%. The bank isn't liable for "
                     "authorized transfers — the buyer authorized the wire based "
                     "on spoofed instructions. Prevention is the only defense.",
        ),
        Objection(
            objection="We're a small title company — this seems like enterprise software.",
            response="Wire fraud doesn't discriminate by company size. BEC attacks "
                     "specifically target smaller firms because they have weaker "
                     "email security. Baseline tier at $3,750/month is less than "
                     "the deductible on one fraud claim.",
        ),
        Objection(
            objection="We already use email security / spam filtering.",
            response="Email security catches spam and known malware. BEC wire fraud "
                     "uses clean emails from compromised accounts — no malware, "
                     "no attachments, no links. The threat is in the content: "
                     "modified routing numbers and urgency language.",
        ),
    ],

    # ── Pricing ───────────────────────────────────────────────────
    pricing=[
        PricingTier(
            tier_name="Baseline",
            monthly=3750,
            includes=[
                "Detection engine (wire fraud BEC + domain spoofing)",
                "117+ behavioral pattern library",
                "NIST 800-61 incident response automation",
                "Email thread analysis integration",
                "Monthly pattern updates",
            ],
        ),
        PricingTier(
            tier_name="Intelligence",
            monthly=7500,
            includes=[
                "Everything in Baseline",
                "Multi-branch coverage",
                "Money laundering detection (rapid flips + shell entities)",
                "FinCEN SAR auto-generation",
                "Quarterly threat briefings",
            ],
        ),
        PricingTier(
            tier_name="Sentinel",
            monthly=12500,
            includes=[
                "Everything in Intelligence",
                "Dedicated fraud analyst",
                "24/7 monitoring",
                "FBI IC3 reporting automation",
                "OFAC/SDN watchlist screening",
            ],
        ),
    ],

    # ── Outbound cadence ──────────────────────────────────────────
    sequence=[
        OutboundSequence(day=1, channel="linkedin", action="Send connection request", template_key="re_connection"),
        OutboundSequence(day=1, channel="email", action="Send cold email", template_key="re_cold_email"),
        OutboundSequence(day=3, channel="linkedin", action="Follow up if accepted", template_key="re_followup_accept"),
        OutboundSequence(day=5, channel="email", action="Send demo recording link", template_key="re_demo_link"),
        OutboundSequence(day=8, channel="linkedin", action="Share wire fraud news article", template_key="re_insight"),
        OutboundSequence(day=12, channel="email", action="Breakup email — last touch", template_key="re_breakup"),
    ],

    # ── Competitive positioning ───────────────────────────────────
    competitors={
        "CertifID": "Wire verification only. Doesn't detect BEC email compromise or money laundering.",
        "Closinglock": "Wire verification tool. No pattern correlation across email + transaction layers.",
        "Email security (Proofpoint/Mimecast)": "Catches malware and spam. BEC uses clean emails — no malware to detect.",
        "Manual 'call to verify'": "60%+ non-compliance rate under closing pressure. Buyers call the spoofed number.",
        "Title insurance": "Doesn't cover BEC/social engineering losses. Exclusion in most policies.",
    },

    # ── Key stats ─────────────────────────────────────────────────
    stats={
        "annual_re_wire_fraud_losses": "$446M (FBI IC3 2024)",
        "avg_wire_fraud_loss": "$400K per transaction",
        "call_to_verify_compliance": "< 40% under closing pressure",
        "fund_recovery_rate_after_48h": "< 10%",
        "bec_attack_growth_yoy": "65% increase (FBI IC3)",
        "aion_detection_speed": "< 3 seconds",
    },
)
