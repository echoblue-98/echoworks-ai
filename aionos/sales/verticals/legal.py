"""
Legal Vertical — Law Firm Sales Configuration
================================================
Attorney departure theft, client file exfiltration,
lateral move data staging, ethics violation detection.

Target: AmLaw 200, mid-size firms 50-500 attorneys,
boutique litigation/IP firms.
"""

from aionos.sales.models import (
    BuyerPersona, BuyerRole, Objection, OutboundSequence,
    PricingTier, RegulatoryHook, ThreatScenario, Vertical, VerticalID,
)

LEGAL_VERTICAL = Vertical(
    id=VerticalID.LEGAL,
    display_name="Law Firms",
    tagline="Catch the departure before the resignation letter",

    # ── What we detect ────────────────────────────────────────────
    threat_scenarios=[
        ThreatScenario(
            name="Attorney Departure Theft",
            description="Multi-stage data exfiltration by departing attorney: "
                        "matter access → bulk DMS export → personal email forward → cloud upload",
            event_chain=[
                "After-hours matter access (iManage/NetDocuments)",
                "Bulk DMS export (218+ files, 890MB+)",
                "Email forward to personal Gmail/Yahoo",
                "Cloud upload to Dropbox/OneDrive via split-tunnel VPN",
            ],
            detection_speed="< 3 seconds",
            financial_impact="$2M-$50M in client migration + litigation costs",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Client List Staging",
            description="Attorney builds exportable client contact list "
                        "before announcing lateral move",
            event_chain=[
                "CRM/contact export (Salesforce, InterAction)",
                "Billing report downloads filtered by origination credit",
                "Calendar export of client meetings",
                "LinkedIn connection surge with client contacts",
            ],
            detection_speed="< 5 seconds",
            financial_impact="$5M-$100M in portable client revenue at risk",
            pattern_engine_bypass=True,
        ),
        ThreatScenario(
            name="Privileged Document Exfiltration",
            description="Bulk download of attorney-client privileged documents "
                        "across matters, often preceding litigation or regulatory action",
            event_chain=[
                "Cross-matter document search (privilege-tagged)",
                "Bulk download exceeding normal work patterns",
                "USB device insertion or print spike",
                "Email to outside counsel or personal account",
            ],
            detection_speed="< 3 seconds",
            financial_impact="Waiver of privilege, malpractice exposure",
            pattern_engine_bypass=True,
        ),
    ],

    # ── Who we sell to ────────────────────────────────────────────
    buyer_personas=[
        BuyerPersona(
            title="Managing Partner",
            role=BuyerRole.DECISION_MAKER,
            pain_points=[
                "Lost $8M client book when partner left to competitor",
                "No visibility into what attorneys access before resignation",
                "Outside counsel bills for reactive forensics after the fact",
            ],
            trigger_events=[
                "Recent lateral partner departure",
                "Law firm merger or dissolution rumors",
                "Client poaching incident in past 12 months",
            ],
            linkedin_search='"Managing Partner" AND ("law firm" OR "legal")',
            email_subject="Your attorneys are staging data right now — you just can't see it",
            opening_line="When an attorney decides to leave for a competing firm, "
                         "the data exfiltration starts 2-4 weeks before they tell you.",
        ),
        BuyerPersona(
            title="IT Director / CIO",
            role=BuyerRole.TECHNICAL,
            pain_points=[
                "DLP tools generate thousands of false positives",
                "No correlation between DMS access and HR departure signals",
                "Cloud-based security tools violate client confidentiality agreements",
            ],
            trigger_events=[
                "DLP renewal coming up — evaluating alternatives",
                "Post-breach forensics engagement just completed",
                "New client requiring on-premise data handling",
            ],
            linkedin_search='"IT Director" OR "CIO" AND "law firm"',
            email_subject="Your DLP is missing the departure pattern — here's why",
            opening_line="DLP tools flag file downloads. They don't correlate "
                         "matter access, email forwards, and cloud uploads into "
                         "a single departure-theft chain.",
        ),
        BuyerPersona(
            title="General Counsel / Ethics Partner",
            role=BuyerRole.INFLUENCER,
            pain_points=[
                "ABA Model Rule 1.6 obligations when staff accesses client files",
                "State bar disciplinary risk from data breach",
                "Need litigation-ready evidence, not just alerts",
            ],
            trigger_events=[
                "Ethics complaint filed against the firm",
                "State bar issued new data security guidance",
                "Client demanding security audit documentation",
            ],
            linkedin_search='"General Counsel" OR "Ethics Partner" AND "law firm"',
            email_subject="If an attorney exports 2,847 files before resigning — do you have evidence?",
            opening_line="When a departing attorney takes client files, your firm "
                         "needs litigation-ready evidence within hours, not weeks.",
        ),
    ],

    # ── Why they must buy (regulatory pressure) ───────────────────
    regulatory_hooks=[
        RegulatoryHook(
            name="ABA Model Rule 1.6",
            citation="ABA Model Rules of Professional Conduct, Rule 1.6(c)",
            penalty_range="Disciplinary action, malpractice liability",
            relevance="Requires reasonable measures to prevent unauthorized "
                      "disclosure of client information. Departure theft = breach.",
        ),
        RegulatoryHook(
            name="Computer Fraud & Abuse Act (CFAA)",
            citation="18 U.S.C. § 1030",
            penalty_range="Civil damages + criminal penalties up to 10 years",
            relevance="Departing attorney exceeding authorized access to firm "
                      "systems to stage files = CFAA violation. AION provides evidence.",
        ),
        RegulatoryHook(
            name="Defend Trade Secrets Act (DTSA)",
            citation="18 U.S.C. § 1836",
            penalty_range="Injunctive relief + compensatory + exemplary damages (2x)",
            relevance="Client lists, work product, billing data = trade secrets. "
                      "AION detects misappropriation in real time.",
        ),
        RegulatoryHook(
            name="State Bar Ethics Opinions",
            citation="Varies by jurisdiction (e.g., ABA Formal Opinion 477R)",
            penalty_range="Bar discipline, suspension, disbarment",
            relevance="Firms have duty to supervise technology use. "
                      "Failure to detect departure theft = supervisory failure.",
        ),
        RegulatoryHook(
            name="Compliance-First Innovation",
            citation="Best practice — align security innovations with compliance from the outset",
            penalty_range="Reputational damage, audit failures, regulatory sanctions",
            relevance="Any detection or monitoring system deployed without compliance "
                      "alignment risks creating more liability than it prevents. "
                      "AION OS is built compliance-first: on-premise data residency, "
                      "privilege-aware detection, litigation-ready audit trails.",
        ),
    ],

    # ── How we handle pushback ────────────────────────────────────
    objections=[
        Objection(
            objection="We already have DLP.",
            response="DLP flags individual file downloads. It doesn't correlate "
                     "matter access + bulk exports + personal email + cloud uploads "
                     "into a departure-theft chain. That's what AION does — pattern "
                     "correlation across systems in real time.",
            proof_point="One firm had 4,200 DLP alerts/month. AION generated 3 "
                        "actionable alerts in the same period — all confirmed threats.",
        ),
        Objection(
            objection="Our data can't go to the cloud for analysis.",
            response="It doesn't. AION runs 100% on-premise. No event data, no PII, "
                     "no client files ever leave your network. The AI model runs "
                     "locally on your hardware.",
        ),
        Objection(
            objection="We'd know if someone was stealing data.",
            response="The average time to detect insider data theft is 77 days "
                     "(Ponemon Institute). Departing attorneys start staging 2-4 weeks "
                     "before resignation. By the time you find out, the files are gone.",
            proof_point="2,847 documents staged over 3 weeks — detected in under "
                        "3 seconds once AION was running.",
        ),
        Objection(
            objection="This seems expensive for a mid-size firm.",
            response="One lateral partner departure can cost $2M-$50M in client "
                     "revenue. One privilege waiver from undetected exfiltration "
                     "can exceed $10M in malpractice exposure. $5,000/month is "
                     "insurance against a 7-figure loss.",
        ),
        Objection(
            objection="We need to run this by our IT committee.",
            response="Understood. I can put together a one-page technical spec "
                     "for your IT team — deployment requirements, data flow, "
                     "integration points with iManage/NetDocuments. And I can "
                     "do a 20-minute technical demo for them separately.",
        ),
    ],

    # ── Pricing ───────────────────────────────────────────────────
    # Single offer. One price. No tiers. Per advisor strategy.
    pricing=[
        PricingTier(
            tier_name="AION OS",
            monthly=5000,
            includes=[
                "Full detection engine (attorney departure + privilege exfiltration)",
                "117+ behavioral pattern library",
                "NIST 800-61 incident response automation",
                "Compliance-first architecture — innovation aligned with regulatory requirements from the outset",
                "iManage/NetDocuments integration",
                "Monthly pattern updates",
                "On-premise deployment — zero data egress",
                "90-day performance guarantee",
            ],
        ),
    ],

    # ── Outbound cadence ──────────────────────────────────────────
    sequence=[
        OutboundSequence(day=1, channel="linkedin", action="Send connection request", template_key="legal_connection"),
        OutboundSequence(day=1, channel="email", action="Send cold email", template_key="legal_cold_email"),
        OutboundSequence(day=3, channel="linkedin", action="Follow up if accepted", template_key="legal_followup_accept"),
        OutboundSequence(day=5, channel="email", action="Send demo recording link", template_key="legal_demo_link"),
        OutboundSequence(day=8, channel="linkedin", action="Share relevant article/insight", template_key="legal_insight"),
        OutboundSequence(day=12, channel="email", action="Breakup email — last touch", template_key="legal_breakup"),
    ],

    # ── Competitive positioning ───────────────────────────────────
    competitors={
        "Relativity Trace": "Cloud-based. Client data leaves the firm's network.",
        "Microsoft Purview DLP": "No pattern correlation. Individual file alerts only. Thousands of false positives.",
        "Teramind": "Employee monitoring tool, not insider threat. No legal-specific patterns.",
        "DTEX": "Cloud analytics platform. Requires sending endpoint data off-premise.",
        "Manual forensics": "Reactive. $500-800/hr. Takes weeks. Evidence often stale.",
    },

    # ── Key stats ─────────────────────────────────────────────────
    stats={
        "avg_detection_time_industry": "77 days (Ponemon Institute)",
        "avg_detection_time_aion": "< 3 seconds",
        "avg_departure_staging_window": "2-4 weeks before resignation",
        "avg_client_revenue_at_risk": "$2M-$50M per lateral partner",
        "dlp_false_positive_rate": "97% (Gartner)",
        "aion_false_positive_rate": "< 2%",
    },
)
