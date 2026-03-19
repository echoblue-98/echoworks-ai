"""
Healthcare Vertical — Sales Configuration
============================================
Billing fraud, upcoding, credential compromise,
HIPAA violations, controlled substance diversion,
unauthorized EMR access.

Target: Health systems 200+ beds, urgent care chains,
multi-provider clinics, compliance consulting firms.
"""

from aionos.sales.models import (
    BuyerPersona, BuyerRole, Objection, OutboundSequence,
    PricingTier, RegulatoryHook, ThreatScenario, Vertical, VerticalID,
)

HEALTHCARE_VERTICAL = Vertical(
    id=VerticalID.HEALTHCARE,
    display_name="Healthcare",
    tagline="Catch the breach before the OCR audit",

    # ── What we detect ────────────────────────────────────────────
    threat_scenarios=[
        ThreatScenario(
            name="Billing Fraud — Upcoding Pattern",
            description="Provider consistently bills at highest E&M code "
                        "(99215) far exceeding peer averages. Statistical "
                        "anomaly detection without LLM.",
            event_chain=[
                "Baseline claim ingestion (CPT code, amount, provider NPI)",
                "Statistical upcoding detection (92% vs 31% peer average)",
                "48+ claims in analysis window flagged",
                "Claims pipeline freeze recommended",
            ],
            detection_speed="< 3 seconds",
            financial_impact="$500K-$10M in False Claims Act liability (treble damages)",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Credential Compromise — Impossible Travel",
            description="Same provider NPI logs in from two cities within "
                        "a physically impossible timeframe, indicating "
                        "stolen credentials or credentialing fraud ring.",
            event_chain=[
                "EHR login from Location A (e.g., Chicago)",
                "EHR login from Location B (e.g., Houston) within 45 min",
                "Cross-reference with upcoding or Rx access flags",
                "Provider access suspension recommended",
            ],
            detection_speed="< 2 seconds",
            financial_impact="$1M-$5M in breach notification + OCR fines",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Controlled Substance Diversion",
            description="After-hours access to controlled substance records "
                        "correlated with prescribing anomalies and session "
                        "hijacking indicators.",
            event_chain=[
                "After-hours login to controlled substance module",
                "Access to oncology/pain management Rx records",
                "Prescribing pattern deviates from provider baseline",
                "Session ownership mismatch (MA using provider session)",
            ],
            detection_speed="< 3 seconds",
            financial_impact="DEA Schedule II violations, criminal prosecution, "
                            "facility license revocation",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Unauthorized Patient Record Access",
            description="Staff accessing patient charts with no clinical "
                        "justification — snooping on VIPs, coworkers, "
                        "family members, celebrities.",
            event_chain=[
                "EMR access event without matching patient assignment",
                "No open orders or clinical workflow for the patient",
                "Workstation location inconsistent with care unit",
                "Repeated access pattern (3+ views, no documentation)",
            ],
            detection_speed="< 1 second",
            financial_impact="$100K-$1.9M per HIPAA violation category",
            pattern_engine_bypass=True,
        ),
    ],

    # ── Who we sell to ────────────────────────────────────────────
    buyer_personas=[
        BuyerPersona(
            title="Chief Compliance Officer",
            role=BuyerRole.DECISION_MAKER,
            pain_points=[
                "Quarterly EMR audits catch violations months after they happen",
                "OCR enforcement actions increasing YoY",
                "No real-time correlation between access and clinical context",
            ],
            trigger_events=[
                "OCR investigation or CAP (corrective action plan) in progress",
                "HIPAA breach notification in past 12 months",
                "New OCR enforcement rule published",
            ],
            linkedin_search='"Chief Compliance Officer" OR "Privacy Officer" AND "healthcare"',
            email_subject="A registration clerk accessed a VIP chart 4 times last night — would your EMR have caught it?",
            opening_line="Most healthcare organizations audit EMR access quarterly "
                         "on random samples. Unauthorized access goes undetected for months.",
        ),
        BuyerPersona(
            title="CISO / IT Security Director",
            role=BuyerRole.TECHNICAL,
            pain_points=[
                "SIEM floods with noise, no clinical context",
                "Cloud CASB tools transmit PHI to vendor infrastructure",
                "Impossible travel detection not integrated with EHR",
            ],
            trigger_events=[
                "Ransomware incident at peer institution",
                "SIEM contract renewal evaluation",
                "New NIST cybersecurity framework adoption",
            ],
            linkedin_search='"CISO" OR "IT Security Director" AND ("hospital" OR "health system")',
            email_subject="Your SIEM can't see clinical context — here's what it's missing",
            opening_line="SIEMs flag anomalous logins. They can't tell you whether "
                         "the person who accessed that patient chart had a clinical reason to.",
        ),
        BuyerPersona(
            title="VP of Revenue Cycle / CFO",
            role=BuyerRole.INFLUENCER,
            pain_points=[
                "False Claims Act exposure from provider upcoding",
                "RAC audits clawing back $500K+ in reimbursements",
                "No proactive detection of billing anomalies",
            ],
            trigger_events=[
                "OIG audit notification received",
                "Qui tam / whistleblower complaint filed",
                "Revenue cycle vendor contract renewal",
            ],
            linkedin_search='"VP Revenue Cycle" OR "CFO" AND ("hospital" OR "health system")',
            email_subject="92% of one provider's claims are at the highest E&M code — your peers average 31%",
            opening_line="You won't catch upcoding from billing reports. You catch it "
                         "by correlating CPT codes against peer benchmarks in real time.",
        ),
    ],

    # ── Regulatory pressure ───────────────────────────────────────
    regulatory_hooks=[
        RegulatoryHook(
            name="HIPAA Privacy Rule",
            citation="45 CFR § 164.530(c)",
            penalty_range="$100-$50,000 per violation, max $1.9M per category/year",
            relevance="Requires appropriate safeguards to prevent unauthorized "
                      "use or disclosure of PHI. AION detects access without "
                      "clinical justification in real time.",
        ),
        RegulatoryHook(
            name="HIPAA Security Rule",
            citation="45 CFR § 164.312(b) — Audit Controls",
            penalty_range="Same as Privacy Rule tiers",
            relevance="Requires mechanisms to record and examine activity in "
                      "systems containing ePHI. Quarterly sampling ≠ compliance.",
        ),
        RegulatoryHook(
            name="False Claims Act",
            citation="31 U.S.C. § 3729",
            penalty_range="Treble damages + $11,181-$23,607 per false claim",
            relevance="Upcoding is a false claim. AION detects statistical "
                      "anomalies before the qui tam relator does.",
        ),
        RegulatoryHook(
            name="DEA Controlled Substances Act",
            citation="21 U.S.C. § 841",
            penalty_range="Criminal prosecution, facility license revocation",
            relevance="After-hours controlled substance access + prescribing "
                      "anomalies = diversion risk. AION correlates in real time.",
        ),
        RegulatoryHook(
            name="HITECH Act Breach Notification",
            citation="42 U.S.C. § 17932",
            penalty_range="$10K-$1.5M + mandatory public notification for 500+ records",
            relevance="Detecting unauthorized access before 500+ records are "
                      "compromised avoids the 'wall of shame' posting.",
        ),
    ],

    # ── Objection handling ────────────────────────────────────────
    objections=[
        Objection(
            objection="We already audit EMR access.",
            response="Quarterly audits on random samples catch violations 3-6 months "
                     "after they happen. OCR doesn't give credit for audits that find "
                     "breaches late. AION catches them in real time — before 500 records "
                     "are compromised and breach notification triggers.",
            proof_point="One simulation caught unauthorized access to a VIP chart "
                        "within 1 second. The quarterly audit would have found it in Q3.",
        ),
        Objection(
            objection="Our EHR vendor handles security.",
            response="EHR vendors manage system security — patching, uptime, access controls. "
                     "They don't correlate access events against clinical context. Epic's audit "
                     "log tells you who accessed a chart, not whether they had a reason to.",
        ),
        Objection(
            objection="We can't send PHI to a third-party vendor.",
            response="You don't. AION runs 100% on-premise inside your network. "
                     "No PHI, no ePHI, no audit data ever leaves your infrastructure. "
                     "The AI model runs locally on your hardware.",
        ),
        Objection(
            objection="Our compliance team is only 2 people.",
            response="That's exactly the problem AION solves. A 2-person team can't "
                     "manually audit millions of EMR access events. AION does it "
                     "automatically — they only see actionable alerts with evidence "
                     "packages ready for OCR response.",
        ),
        Objection(
            objection="We just passed our last OCR audit.",
            response="OCR audits evaluate your safeguards at a point in time. They don't "
                     "detect the registration clerk who accessed a VIP chart last Tuesday. "
                     "The question isn't whether you passed — it's what's happening "
                     "between audits.",
        ),
    ],

    # ── Pricing ───────────────────────────────────────────────────
    pricing=[
        PricingTier(
            tier_name="Baseline",
            monthly=3750,
            includes=[
                "Detection engine (unauthorized access + billing anomaly)",
                "117+ behavioral pattern library",
                "NIST 800-61 incident response automation",
                "EHR audit log integration (Epic, Cerner, MEDITECH)",
                "Monthly pattern updates",
            ],
        ),
        PricingTier(
            tier_name="Intelligence",
            monthly=7500,
            includes=[
                "Everything in Baseline",
                "Multi-facility coverage",
                "Controlled substance diversion detection",
                "Claims pipeline integration",
                "Quarterly compliance briefings",
            ],
        ),
        PricingTier(
            tier_name="Sentinel",
            monthly=12500,
            includes=[
                "Everything in Intelligence",
                "Dedicated compliance analyst",
                "24/7 monitoring",
                "OCR breach assessment automation",
                "DEA reporting integration",
            ],
        ),
    ],

    # ── Outbound cadence ──────────────────────────────────────────
    sequence=[
        OutboundSequence(day=1, channel="linkedin", action="Send connection request", template_key="health_connection"),
        OutboundSequence(day=1, channel="email", action="Send cold email", template_key="health_cold_email"),
        OutboundSequence(day=3, channel="linkedin", action="Follow up if accepted", template_key="health_followup_accept"),
        OutboundSequence(day=5, channel="email", action="Send demo recording link", template_key="health_demo_link"),
        OutboundSequence(day=8, channel="linkedin", action="Share HIPAA enforcement news", template_key="health_insight"),
        OutboundSequence(day=12, channel="email", action="Breakup email — last touch", template_key="health_breakup"),
    ],

    # ── Competitive positioning ───────────────────────────────────
    competitors={
        "Protenus": "Cloud-based. PHI transmitted to vendor infrastructure for analysis.",
        "Imprivata FairWarning": "Access monitoring only. No billing fraud or Rx diversion correlation.",
        "Splunk (SIEM)": "Generic log aggregation. No clinical context. Massive false positive rate.",
        "IBM QRadar": "Cloud-dependent analytics. No HIPAA-specific pattern library.",
        "Manual compliance team": "2-person team auditing quarterly samples. Reactive by definition.",
    },

    # ── Key stats ─────────────────────────────────────────────────
    stats={
        "hipaa_avg_fine": "$1.2M per enforcement action (HHS OCR 2024)",
        "breach_notification_threshold": "500 records → public notification + OCR investigation",
        "upcoding_false_claims_multiplier": "3x damages under False Claims Act",
        "avg_days_to_detect_breach": "197 days (IBM Cost of a Data Breach 2024)",
        "aion_detection_speed": "< 3 seconds",
        "controlled_substance_diversion_rate": "10-15% of healthcare workers (SAMHSA)",
    },
)
