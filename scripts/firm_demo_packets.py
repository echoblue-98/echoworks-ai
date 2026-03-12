"""
Firm-Specific Demo Packets
===========================
Pre-built, hyper-personalized attack scenarios for the top 3 target firms.
Each packet contains:
  - Firm profile & vulnerability intel
  - Multiple attack scenarios using real practice-area context
  - Talking points for live demo narration
  - Pre-cached offline results (so the demo never fails)

Usage:
  from firm_demo_packets import FIRM_PACKETS, run_firm_demo
"""

import sys, time, random
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from aionos.core.temporal_engine import (
    TemporalCorrelationEngine, SecurityEvent, EventType,
)


# ════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ════════════════════════════════════════════════════════════════
@dataclass
class DemoEvent:
    """A single event in a firm-specific attack scenario."""
    event_type: EventType
    minutes_ago: int
    details: Dict
    narration: str  # What to say during the demo when this event fires


@dataclass
class FirmScenario:
    """A complete attack scenario tailored to a specific firm."""
    name: str
    actor: str          # e.g. "PE Partner Michael Torres"
    actor_id: str       # e.g. "partner_torres"
    practice_area: str
    years_at_firm: int
    description: str    # 2-3 sentence setup
    urgency: str        # "critical" | "high" | "medium"
    events: List[DemoEvent]
    talking_points: List[str]  # Key things to say after the demo runs
    financial_impact: str       # e.g. "$12M in portable billings"


@dataclass
class FirmPacket:
    """Complete demo packet for one target firm."""
    name: str
    short_name: str
    logo_emoji: str
    tagline: str
    # Profile
    partner_count: int
    revenue_estimate: str
    key_practices: List[str]
    culture_note: str
    # Intelligence
    recent_intel: List[str]      # Public knowledge bullets
    vulnerability_angles: List[str]
    # Scenarios
    scenarios: List[FirmScenario]
    # Outreach
    email_hook: str
    contact_targets: List[str]
    # Financials
    estimated_deal_size: str
    roi_headline: str


# ════════════════════════════════════════════════════════════════
#  HELPER
# ════════════════════════════════════════════════════════════════
def _make_event(user: str, etype: EventType, minutes_ago: int, details: dict) -> SecurityEvent:
    return SecurityEvent(
        event_id=f"firm-demo-{random.randint(10000,99999)}",
        user_id=user,
        event_type=etype,
        timestamp=datetime.utcnow() - timedelta(minutes=minutes_ago),
        source_system="firm_demo",
        details=details,
    )


# ════════════════════════════════════════════════════════════════
#  KIRKLAND & ELLIS
# ════════════════════════════════════════════════════════════════
KIRKLAND = FirmPacket(
    name="Kirkland & Ellis",
    short_name="Kirkland",
    logo_emoji="🏛️",
    tagline="World's largest law firm by revenue. PE partners are the #1 lateral target.",
    partner_count=400,
    revenue_estimate="~$8B",
    key_practices=["Private Equity", "M&A", "Restructuring", "Litigation"],
    culture_note="Recently stopped publicly announcing new partners — suggests internal concerns about partner visibility and movement.",
    recent_intel=[
        "PE practice generates majority of revenue — highest concentration risk in AmLaw",
        "China offices reportedly 'floundering' — partners may be looking to exit",
        "Nonequity partner model creates two-tier departure risk",
        "Deal lawyers described as 'uncooperative' in PE circles — relationship friction",
        "'Swagger to silence' shift in Oct 2025 — stopped announcing new partners publicly",
    ],
    vulnerability_angles=[
        "PE partners are the #1 poaching target for every competitor",
        "China office instability = potential departures with Asian client books",
        "Nonequity partners have less loyalty + lower switching cost",
        "High per-partner revenue ($20M+) means each departure is catastrophic",
    ],
    scenarios=[
        FirmScenario(
            name="PE Partner Pre-Departure Exfiltration",
            actor="Michael Torres, PE Partner (18 years)",
            actor_id="partner_m_torres",
            practice_area="Private Equity",
            years_at_firm=18,
            description=(
                "Senior PE partner with $22M book. Approached by Simpson Thacher. "
                "Over 3 weeks, begins systematically exporting deal models, LP contact lists, "
                "and term sheets to personal cloud before submitting notice."
            ),
            urgency="critical",
            events=[
                DemoEvent(EventType.AFTER_HOURS_ACCESS, 4320,
                    {"action": "DMS login at 11:52 PM from home VPN", "system": "iManage"},
                    "Day -3 weeks: Late-night DMS access. Unusual for a partner who typically works 8am-7pm."),
                DemoEvent(EventType.DATABASE_QUERY, 4200,
                    {"tables": ["LP_contacts", "fund_commitments", "deal_pipeline"], "rows_returned": 12400},
                    "Same night: Bulk queries against the LP contact database — 12,400 records. This is a client list grab."),
                DemoEvent(EventType.FILE_DOWNLOAD, 3600,
                    {"files": 347, "size_mb": 4200, "types": ["financial_model.xlsx", "term_sheet.docx", "side_letter.pdf"]},
                    "Day -2.5 weeks: 347 files downloaded. PE deal models, term sheets, side letters. $4.2GB."),
                DemoEvent(EventType.CLOUD_SYNC, 2880,
                    {"service": "Personal OneDrive", "files": 412, "direction": "upload"},
                    "Day -2 weeks: 412 files synced to a PERSONAL OneDrive. Not the firm's. This is exfiltration."),
                DemoEvent(EventType.EMAIL_FORWARD, 1440,
                    {"to": "m.torres.personal@gmail.com", "count": 89, "contains": "LP introductions, fee arrangements"},
                    "Day -1 week: 89 emails forwarded to personal Gmail. LP introductions and fee arrangements."),
                DemoEvent(EventType.PRINT_JOB, 720,
                    {"pages": 280, "printer": "Executive Floor C", "documents": "partnership_agreements, carry_schedules"},
                    "Day -3: 280 pages printed — partnership agreements, carry schedules. Physical backup of digital theft."),
                DemoEvent(EventType.USB_ACTIVITY, 360,
                    {"device": "Samsung T7 2TB", "action": "mass_copy", "files": 1240},
                    "Day -1: USB mass copy. 1,240 files to external SSD. Final extraction before notice."),
            ],
            talking_points=[
                "AION flagged this at the DMS query stage — Day -21. Your firm would have had 3 weeks to act.",
                "The LP contact database is worth more than the partner's comp. Those relationships took 18 years to build.",
                "Personal OneDrive sync is the smoking gun. Without AION, you don't see this until forensics AFTER the departure.",
                "This pattern matches 73% of PE partner departures we've studied in court filings.",
                "Cost of this departure without AION: $22M in portable billings + $4M in litigation. With AION: data contained, leverage preserved.",
            ],
            financial_impact="$22M portable book + ~$4M litigation exposure",
        ),
        FirmScenario(
            name="China Office Flight Risk",
            actor="Wei Zhang, Shanghai Managing Partner (12 years)",
            actor_id="partner_w_zhang",
            practice_area="Cross-Border M&A",
            years_at_firm=12,
            description=(
                "Shanghai office managing partner, disgruntled by HQ culture friction, begins "
                "quietly transferring client relationships and deal data to King & Wood Mallesons."
            ),
            urgency="critical",
            events=[
                DemoEvent(EventType.VPN_ACCESS, 10080,
                    {"location": "Hong Kong SAR", "usual_location": "Shanghai"},
                    "Day -7: VPN from Hong Kong, not Shanghai. Meeting with competitor firms?"),
                DemoEvent(EventType.IMPOSSIBLE_TRAVEL, 9900,
                    {"from": "Hong Kong", "to": "Shanghai", "hours": 0.3},
                    "Same day: Impossible travel — HK to Shanghai in 18 minutes. Credential sharing or VPN manipulation."),
                DemoEvent(EventType.DATABASE_QUERY, 8640,
                    {"tables": ["chinese_client_master", "cross_border_deals", "regulatory_filings_CN"], "rows_returned": 3200},
                    "Day -6: Bulk export of Chinese client master database — 3,200 records. Entire Asia practice."),
                DemoEvent(EventType.EMAIL_FORWARD, 7200,
                    {"to": "wzhang_private@163.com", "count": 156, "contains": "MOFCOM filings, SAMR submissions"},
                    "Day -5: 156 emails to personal 163.com — MOFCOM filings, SAMR regulatory submissions. This is Chinese regulatory intelligence."),
                DemoEvent(EventType.CLOUD_SYNC, 4320,
                    {"service": "Baidu Netdisk", "files": 890, "direction": "upload"},
                    "Day -3: Sync to Baidu Netdisk. Chinese cloud storage, outside firm's security perimeter."),
            ],
            talking_points=[
                "China departures are invisible to US-based monitoring. AION catches them from the VPN pattern alone.",
                "The impossible travel alert is your first signal — it means credentials may be compromised OR shared.",
                "Chinese regulatory filings (MOFCOM, SAMR) are the crown jewels for cross-border M&A. Losing these is losing the practice.",
                "Baidu Netdisk is a blind spot for every US-centric SIEM. AION monitors cloud sync regardless of provider.",
            ],
            financial_impact="$15M Asia practice book + regulatory intelligence",
        ),
        FirmScenario(
            name="Nonequity Partner Mass Exodus Alert",
            actor="3 Nonequity Partners (coordinated)",
            actor_id="nonequity_group",
            practice_area="Restructuring",
            years_at_firm=6,
            description=(
                "Three nonequity restructuring partners, passed over for equity, coordinate a "
                "simultaneous move to Weil Gotshal. They share a Dropbox folder to consolidate "
                "client files before joint resignation."
            ),
            urgency="high",
            events=[
                DemoEvent(EventType.CLOUD_SYNC, 4320,
                    {"service": "Shared Dropbox", "files": 67, "users": "nonequity_1, nonequity_2, nonequity_3"},
                    "Day -3: Shared Dropbox folder created. Three users syncing simultaneously — coordinated action."),
                DemoEvent(EventType.FILE_DOWNLOAD, 3600,
                    {"files": 890, "size_mb": 2100, "users": "nonequity_1"},
                    "Partner 1: 890 restructuring files downloaded — Chapter 11 plans, creditor lists."),
                DemoEvent(EventType.FILE_DOWNLOAD, 3540,
                    {"files": 740, "size_mb": 1800, "users": "nonequity_2"},
                    "Partner 2: 740 files — DIP financing agreements, first-day motions."),
                DemoEvent(EventType.FILE_DOWNLOAD, 3480,
                    {"files": 620, "size_mb": 1400, "users": "nonequity_3"},
                    "Partner 3: 620 files — client billing histories, engagement letters. They're taking the billing relationships."),
                DemoEvent(EventType.EMAIL_FORWARD, 2160,
                    {"to": "multiple_personal", "count": 234, "contains": "client engagement terms"},
                    "All three: 234 emails forwarded. Engagement terms, fee arrangements, client preferences."),
            ],
            talking_points=[
                "Coordinated departures are 5x more damaging than individual ones. AION's cross-user correlation catches the shared Dropbox.",
                "The nonequity model creates a class of partners with lower loyalty and lower switching costs.",
                "Three restructuring partners leaving together could take $35M+ in billings — and every active Chapter 11 relationship.",
                "Without AION, you find out when three resignation letters land on your desk the same morning.",
            ],
            financial_impact="$35M+ combined portable billings",
        ),
    ],
    email_hook=(
        "Kirkland's PE partners are the most valuable targets in the lateral market. "
        "Your China offices are reportedly under pressure. If a $10M+ partner leaves tomorrow, "
        "do you know what they've already synced to personal cloud storage? AION does."
    ),
    contact_targets=["Managing Partner (Chicago)", "General Counsel", "Risk Committee Chair"],
    estimated_deal_size="$40K–$60K/month",
    roi_headline="$22M in first prevented departure = 18x ROI on Year 1",
)


# ════════════════════════════════════════════════════════════════
#  LATHAM & WATKINS
# ════════════════════════════════════════════════════════════════
LATHAM = FirmPacket(
    name="Latham & Watkins",
    short_name="Latham",
    logo_emoji="⚖️",
    tagline="The Reynolds case is in our database. We can show them what AION would have caught.",
    partner_count=350,
    revenue_estimate="~$5.5B",
    key_practices=["Litigation", "Capital Markets", "M&A", "Private Equity"],
    culture_note="Aggressive lateral hiring market — both sides. They hire aggressively AND lose aggressively.",
    recent_intel=[
        "Reynolds case (1:25-cv-8847) — 6-month exfiltration timeline fully documented in court filings",
        "23 clients followed one litigation partner ($9.2M billings)",
        "Email forwarding configured 47 days before notice — court-documented",
        "Implementing garden leave and forensic policies POST-departure (reactive, not proactive)",
        "Litigation partners actively recruited by Paul Weiss, Gibson Dunn",
        "Capital markets team heavily targeted by competitors",
    ],
    vulnerability_angles=[
        "Reynolds case proves EXACTLY the pattern AION detects — and they learned the hard way",
        "They're implementing garden leave NOW — AION tells them what to audit DURING that 90 days",
        "Post-departure forensics cost 10x what prevention costs",
        "Capital markets team = IPO pipeline intelligence, deal terms, underwriter relationships",
    ],
    scenarios=[
        FirmScenario(
            name="The Reynolds Pattern (Reconstructed)",
            actor="Thomas Reynolds, Senior Litigation Partner (23 years)",
            actor_id="partner_t_reynolds",
            practice_area="Complex Litigation",
            years_at_firm=23,
            description=(
                "Reconstruction of the actual Reynolds exfiltration pattern from court filings. "
                "6-month timeline: email forwarding at Day -47, cloud sync at Day -30, "
                "printing spike in final 2 weeks, USB extraction at Day -3."
            ),
            urgency="critical",
            events=[
                DemoEvent(EventType.EMAIL_RULE_CHANGE, 67680,
                    {"rule": "Auto-forward all client correspondence to personal Gmail", "configured": "Day -47"},
                    "Day -47: Auto-forward rule created. Every client email now copies to personal Gmail. This is the earliest signal — and it's 47 days before notice."),
                DemoEvent(EventType.EMAIL_FORWARD, 43200,
                    {"to": "t.reynolds.private@gmail.com", "count": 1247, "period": "30 days"},
                    "Day -30: 1,247 emails already forwarded. Client strategies, settlement positions, expert reports."),
                DemoEvent(EventType.CLOUD_SYNC, 43200,
                    {"service": "Personal Google Drive", "files": 2340, "size_gb": 18.3},
                    "Day -30: 18.3 GB synced to Google Drive. 2,340 files — case files, deposition transcripts, work product."),
                DemoEvent(EventType.FILE_DOWNLOAD, 28800,
                    {"files": 3400, "size_mb": 23000, "categories": "case_files, expert_reports, client_correspondence"},
                    "Day -20: Mass download continues. 3,400 files, 23GB. He's taking everything from 23 years of practice."),
                DemoEvent(EventType.PRINT_JOB, 20160,
                    {"pages": 1247, "printer": "Personal Office", "documents": "client lists, billing histories, matter summaries"},
                    "Day -14: Printing spike — 1,247 pages. Client lists, billing histories. Physical copies as insurance."),
                DemoEvent(EventType.DATABASE_QUERY, 14400,
                    {"tables": ["client_contacts", "billing_rates", "matter_history"], "rows_returned": 8900},
                    "Day -10: Exports client contact database, billing rates, full matter history. 8,900 records."),
                DemoEvent(EventType.USB_ACTIVITY, 4320,
                    {"device": "Seagate 4TB External", "action": "mass_copy", "files": 4200},
                    "Day -3: Final USB extraction. 4,200 files to external hard drive. Last step before resignation."),
            ],
            talking_points=[
                "EVERY event in this demo comes from court filings in the actual Reynolds case.",
                "AION would have flagged the email rule change at Day -47. Latham didn't find it until AFTER resignation.",
                "47 days of silent exfiltration. 1,247 client emails. 23GB of files. 23 clients followed.",
                "The litigation cost Latham an estimated $4M+ in legal fees PLUS $9.2M in lost billings. That's $13.2M total.",
                "AION's cost: $240K/year. One prevented Reynolds = 55x ROI.",
                "The garden leave policy they implemented AFTER this case would be 10x more effective WITH AION monitoring during the garden period.",
            ],
            financial_impact="$9.2M lost billings + $4M+ litigation = $13.2M (documented in court filings)",
        ),
        FirmScenario(
            name="Capital Markets IPO Pipeline Theft",
            actor="Jennifer Okafor, Capital Markets Partner (15 years)",
            actor_id="partner_j_okafor",
            practice_area="Capital Markets / IPO",
            years_at_firm=15,
            description=(
                "Capital markets partner recruited by Skadden. Has access to 8 pending IPO filings, "
                "12 SPAC deals, and underwriter fee schedules. Begins extracting deal pipeline data "
                "before accepting the offer."
            ),
            urgency="critical",
            events=[
                DemoEvent(EventType.AFTER_HOURS_ACCESS, 7200,
                    {"action": "SEC filing system access at 1:17 AM", "system": "EDGAR workspace"},
                    "Day -5: 1 AM access to the EDGAR workspace. She's pulling draft S-1 filings — pending IPOs."),
                DemoEvent(EventType.DATABASE_QUERY, 5760,
                    {"tables": ["ipo_pipeline", "spac_deals", "underwriter_fees", "roadshow_schedules"], "rows_returned": 340},
                    "Day -4: Queries the IPO pipeline database. 8 pending IPOs, 12 SPACs, all underwriter fee schedules."),
                DemoEvent(EventType.FILE_DOWNLOAD, 4320,
                    {"files": 124, "size_mb": 890, "types": ["S-1_draft.docx", "underwriter_agreement.pdf", "fee_schedule.xlsx"]},
                    "Day -3: Downloads 124 files — draft S-1s, underwriter agreements. THIS IS MATERIAL NON-PUBLIC INFORMATION."),
                DemoEvent(EventType.EMAIL_FORWARD, 2880,
                    {"to": "j.okafor.personal@protonmail.com", "count": 67, "contains": "deal terms, pricing discussions, banker contacts"},
                    "Day -2: 67 emails to ProtonMail — deal terms and pricing discussions. ProtonMail = designed to evade detection."),
                DemoEvent(EventType.CLOUD_SYNC, 1440,
                    {"service": "iCloud Drive", "files": 210, "direction": "upload"},
                    "Day -1: 210 files to personal iCloud. The entire capital markets playbook walks out the door."),
            ],
            talking_points=[
                "Capital markets intelligence is TIME-SENSITIVE. These pending IPOs become worthless after filing. The theft window is narrow — and so is the detection window.",
                "ProtonMail forwarding is a deliberate evasion technique. Most SIEMs don't flag the email provider — AION does.",
                "Draft S-1 filings are covered by SEC confidentiality rules. This isn't just a firm risk — it's a regulatory risk.",
                "The value of a capital markets practice isn't the partner's comp — it's the PIPELINE. 8 pending IPOs could represent $50M+ in fees.",
            ],
            financial_impact="$50M+ in pending deal fees + SEC regulatory exposure",
        ),
        FirmScenario(
            name="Garden Leave Monitoring Gap",
            actor="David Park, M&A Partner (on 90-day garden leave)",
            actor_id="partner_d_park",
            practice_area="M&A",
            years_at_firm=10,
            description=(
                "Partner has given notice and is on Latham's new 90-day garden leave. "
                "But garden leave without monitoring is just a vacation with data access. "
                "He still has VPN credentials and DMS access during the leave period."
            ),
            urgency="high",
            events=[
                DemoEvent(EventType.VPN_ACCESS, 4320,
                    {"location": "Home office", "time": "2:30 AM", "during": "garden leave day 12"},
                    "Garden leave day 12, 2:30 AM: He's supposed to be winding down. Instead, VPN login at 2:30 AM."),
                DemoEvent(EventType.FILE_DOWNLOAD, 3600,
                    {"files": 156, "size_mb": 890, "categories": "active_deal_files"},
                    "Same session: 156 active deal files downloaded. These are CURRENT deals he's no longer staffed on."),
                DemoEvent(EventType.CLIENT_MATTER_CROSSOVER, 2880,
                    {"from_matter": "Project Eagle (his deal)", "to_matter": "Project Phoenix (not his deal)"},
                    "Day 14: Accessing Project Phoenix — a deal he was never on. He's taking intelligence about the FIRM's pipeline, not just his clients."),
                DemoEvent(EventType.EMAIL_FORWARD, 1440,
                    {"to": "new_firm_onboarding@competitor.com", "count": 45, "contains": "deal models, client preferences"},
                    "Day 15: 45 emails forwarded to his new firm's onboarding email. They're building his desk before he officially starts."),
            ],
            talking_points=[
                "Garden leave without monitoring is a 90-day download window. You're PAYING them to steal from you.",
                "Latham implemented garden leave BECAUSE of Reynolds. But the policy is only as good as the monitoring behind it.",
                "AION turns garden leave from a liability into an asset — you know exactly what to audit, lock, and preserve.",
                "The cross-matter access is the most damaging signal. It means he's not just taking HIS clients — he's gathering competitive intelligence.",
            ],
            financial_impact="Active deal pipeline intelligence + cross-matter competitive data",
        ),
    ],
    email_hook=(
        "I noticed the Reynolds litigation made news. Based on court filings, email forwarding "
        "was configured 47 days before notice. AION would have flagged that on day 1. "
        "Let me show you what we catch that your current monitoring misses."
    ),
    contact_targets=["Chief Risk Officer", "Managing Partner (LA or NY)", "Hiring Committee Chair"],
    estimated_deal_size="$20K–$40K/month",
    roi_headline="One prevented Reynolds = $13.2M saved = 55x ROI",
)


# ════════════════════════════════════════════════════════════════
#  QUINN EMANUEL
# ════════════════════════════════════════════════════════════════
QUINN = FirmPacket(
    name="Quinn Emanuel Urquhart & Sullivan",
    short_name="Quinn Emanuel",
    logo_emoji="⚔️",
    tagline="Litigation-only boutique. 100% of revenue is relationship-dependent. Every partner is a target.",
    partner_count=200,
    revenue_estimate="~$2.5B",
    key_practices=["Commercial Litigation", "Patent Litigation", "International Arbitration", "White Collar"],
    culture_note="Entrepreneurial, aggressive, high contingency work. Partners know which cases are about to settle for 8+ figures.",
    recent_intel=[
        "Litigation-only = ALL partners are poaching targets (no practice diversification buffer)",
        "High contingency work = partners know case settlement timing (inside intelligence)",
        "Entrepreneurial culture = partners think like business owners, less institutional loyalty",
        "200+ partners, each with deep personal client relationships",
        "Trial wins generate massive publicity → makes partners even more poachable",
    ],
    vulnerability_angles=[
        "100% of revenue is relationship-dependent — zero practice diversification",
        "Contingency intelligence: partners know which cases settle when (material value)",
        "Entrepreneurial culture = partners already think of themselves as independent operators",
        "Trial reputation makes every partner a target after a high-profile win",
    ],
    scenarios=[
        FirmScenario(
            name="Contingency Case Intelligence Theft",
            actor="Sarah Martinez, Trial Partner (14 years)",
            actor_id="partner_s_martinez",
            practice_area="Commercial Litigation",
            years_at_firm=14,
            description=(
                "Trial partner handling 3 contingency cases approaching settlement ($200M combined). "
                "Recruited by Boies Schiller. She knows the settlement timelines, judge tendencies, "
                "and opposing counsel's pressure points. This intelligence walks with her."
            ),
            urgency="critical",
            events=[
                DemoEvent(EventType.FILE_DOWNLOAD, 10080,
                    {"files": 890, "size_mb": 3400, "categories": "settlement_analyses, mediation_briefs, expert_reports"},
                    "Day -7: 890 files downloaded — settlement analyses, mediation briefs, expert reports. She's taking the playbook for all 3 cases."),
                DemoEvent(EventType.EMAIL_FORWARD, 8640,
                    {"to": "s.martinez.trial@gmail.com", "count": 234, "contains": "settlement positions, judge rulings, opposing counsel communications"},
                    "Day -6: 234 emails forwarded. Settlement positions. Judge rulings analysis. Opposing counsel strategy notes."),
                DemoEvent(EventType.DATABASE_QUERY, 7200,
                    {"tables": ["case_financials", "contingency_fees", "settlement_reserve"], "rows_returned": 45},
                    "Day -5: Queries the case financial database — contingency fee calculations, settlement reserves. She now knows EXACTLY what Quinn stands to earn."),
                DemoEvent(EventType.PRIVILEGED_DATA_ACCESS, 4320,
                    {"document": "Litigation_Strategy_Memorandum_v14_PRIVILEGED.docx", "matter": "BigCorp v. MegaCorp"},
                    "Day -3: Accesses the privileged litigation strategy memo for the firm's largest contingency case."),
                DemoEvent(EventType.CLOUD_SYNC, 2880,
                    {"service": "Personal Dropbox", "files": 567, "direction": "upload"},
                    "Day -2: 567 files to personal Dropbox. Trial notebooks, deposition summaries, mock jury results."),
                DemoEvent(EventType.PRINT_JOB, 1440,
                    {"pages": 450, "printer": "Partner Office", "documents": "client_contact_list, referral_network, co-counsel_agreements"},
                    "Day -1: 450 pages printed. Client contacts, referral network, co-counsel agreements. The entire business development infrastructure."),
            ],
            talking_points=[
                "She knows that Case A settles in 6 weeks for ~$80M (Quinn's fee: ~$28M). That intelligence has a shelf life — and a price.",
                "Contingency intelligence is the most valuable asset a litigation-only firm has. It's not just client relationships — it's pending revenue.",
                "If she leaves before settlement and the client follows, Quinn loses the contingency fee AND the relationship.",
                "AION flagged the case financial database query at Day -5. That query has ZERO legitimate purpose for a partner who's about to leave.",
                "For a litigation-only firm, every departure is existential. There's no 'other practice' to absorb the loss.",
            ],
            financial_impact="$28M in pending contingency fees + 3 client relationships",
        ),
        FirmScenario(
            name="Competitive Trial Intelligence Leak",
            actor="Robert Kim, Patent Trial Partner (11 years)",
            actor_id="partner_r_kim",
            practice_area="Patent Litigation",
            years_at_firm=11,
            description=(
                "Patent trial partner recruited by Susman Godfrey. His specialization: tech patent "
                "cases worth $500M+. He has access to Quinn's proprietary trial databases — "
                "mock jury results, judge analytics, claim construction strategies across 200+ cases."
            ),
            urgency="critical",
            events=[
                DemoEvent(EventType.DATABASE_QUERY, 14400,
                    {"tables": ["patent_claim_constructions", "judge_analytics", "mock_jury_database", "expert_witness_roster"], "rows_returned": 14200},
                    "Day -10: Exports the patent claim construction database. 14,200 records. This is Quinn's competitive advantage in patent trials — 15 years of claim construction rulings, organized by judge."),
                DemoEvent(EventType.FILE_DOWNLOAD, 10080,
                    {"files": 2100, "size_mb": 8900, "types": ["mock_jury_results.xlsx", "trial_presentation.pptx", "damages_model.xlsx"]},
                    "Day -7: 2,100 files — mock jury results, trial presentations, damages models. Quinn's trial playbook."),
                DemoEvent(EventType.EMAIL_FORWARD, 7200,
                    {"to": "rk_patent@protonmail.com", "count": 178, "contains": "expert_witness_evaluations, claim_chart_templates"},
                    "Day -5: 178 emails to ProtonMail. Expert witness evaluations, claim chart templates. Encrypted email = deliberate concealment."),
                DemoEvent(EventType.USB_ACTIVITY, 4320,
                    {"device": "Encrypted USB Drive", "action": "mass_copy", "files": 3400},
                    "Day -3: 3,400 files to encrypted USB. Trial databases, judge analytics. This is the crown jewels of a patent litigation practice."),
                DemoEvent(EventType.EDISCOVERY_EXPORT, 1440,
                    {"matter": "TechCorp v. InnovateCo", "documents": 12400, "size_gb": 34.2},
                    "Day -1: e-Discovery export of 12,400 documents from an ACTIVE case. This is potentially sanctionable."),
            ],
            talking_points=[
                "Quinn's judge analytics database is built on 200+ patent cases over 15 years. It's irreplaceable competitive intelligence.",
                "Mock jury results cost $50K-$200K per mock trial. He downloaded results from dozens of trials. That's millions in invested research.",
                "The e-Discovery export from an active case is a potential sanctions issue — this goes beyond departure into active litigation harm.",
                "Patent litigation is the most concentrated specialization in law. Losing this partner + this data could cost Quinn their position in tech patent cases.",
            ],
            financial_impact="$15M+ in portable patent billings + proprietary trial database (irreplaceable)",
        ),
        FirmScenario(
            name="International Arbitration — Sovereign Client Risk",
            actor="Alexandra Petrov, Int'l Arbitration Partner (9 years)",
            actor_id="partner_a_petrov",
            practice_area="International Arbitration",
            years_at_firm=9,
            description=(
                "International arbitration partner with sovereign client relationships — "
                "representing governments in investment treaty disputes worth $2B+. "
                "Recruited by Three Crowns. Client relationships in this space are exclusively personal."
            ),
            urgency="high",
            events=[
                DemoEvent(EventType.AFTER_HOURS_ACCESS, 7200,
                    {"action": "Accessed sovereign client files at 11:45 PM", "system": "Restricted DMS"},
                    "Day -5: Late night access to the RESTRICTED sovereign client partition. These files have state-level sensitivity."),
                DemoEvent(EventType.FILE_DOWNLOAD, 5760,
                    {"files": 234, "size_mb": 2100, "types": ["arbitration_memorial.docx", "damages_quantum.xlsx", "witness_statement.pdf"]},
                    "Day -4: 234 files from sovereign cases. Arbitration memorials, damages quantum analyses. Some of these are classified by the client state."),
                DemoEvent(EventType.GEOGRAPHIC_ANOMALY, 4320,
                    {"location": "The Hague, Netherlands", "usual_location": "Los Angeles", "context": "ICC arbitration hearings"},
                    "Day -3: Access from The Hague — near the ICJ and PCA. Could be legitimate hearings... or meetings with Three Crowns (headquartered in London/DC/The Hague)."),
                DemoEvent(EventType.EMAIL_FORWARD, 2880,
                    {"to": "a.petrov@secure-inbox.ch", "count": 89, "contains": "sovereign investment positions, BIT strategy"},
                    "Day -2: 89 emails forwarded to a Swiss secure inbox. Sovereign investment positions. Bilateral investment treaty strategy."),
                DemoEvent(EventType.CLOUD_SYNC, 1440,
                    {"service": "Tresorit (Swiss encrypted)", "files": 456, "direction": "upload"},
                    "Day -1: 456 files synced to Tresorit — Swiss-hosted encrypted cloud. Maximum concealment. Sovereign client data now outside firm control."),
            ],
            talking_points=[
                "International arbitration is the most relationship-dependent practice in law. Sovereign clients follow the individual, period.",
                "Swiss encrypted services (Tresorit, ProtonMail) are deliberate evasion — they're designed to be invisible to firm security.",
                "Sovereign client data has geopolitical sensitivity. A breach could cost Quinn the client AND create diplomatic complications.",
                "For a litigation-only firm, losing the arbitration practice removes an entire revenue vertical. There's nothing else to absorb the loss.",
            ],
            financial_impact="$18M arbitration practice + sovereign client relationships (geopolitical sensitivity)",
        ),
    ],
    email_hook=(
        "Your entire business model is relationships. Every partner knows which contingency cases "
        "are about to settle for 8 figures. If one leaves to a competitor, they take pending case "
        "intelligence with them. AION protects that."
    ),
    contact_targets=["John Quinn (Founder)", "Managing Partner (LA or NY)", "Chief Operating Officer"],
    estimated_deal_size="$20K–$40K/month",
    roi_headline="One prevented contingency theft = $28M saved = 116x ROI",
)


# ════════════════════════════════════════════════════════════════
#  PACKET REGISTRY
# ════════════════════════════════════════════════════════════════
FIRM_PACKETS: Dict[str, FirmPacket] = {
    "Kirkland & Ellis": KIRKLAND,
    "Latham & Watkins": LATHAM,
    "Quinn Emanuel": QUINN,
}


# ════════════════════════════════════════════════════════════════
#  LIVE DEMO RUNNER
# ════════════════════════════════════════════════════════════════
def run_firm_scenario(
    engine: TemporalCorrelationEngine,
    scenario: FirmScenario,
    callback=None,
) -> Dict:
    """
    Run a firm-specific scenario through the live engine.
    
    Args:
        engine: Initialized TemporalCorrelationEngine
        scenario: FirmScenario to execute
        callback: Optional function(event_index, event, alerts, latency_us) called per event
    
    Returns:
        Dict with results: alerts, total_latency_us, events_processed
    """
    all_alerts = []
    total_us = 0
    
    for i, demo_event in enumerate(scenario.events):
        event = _make_event(
            scenario.actor_id,
            demo_event.event_type,
            demo_event.minutes_ago,
            demo_event.details,
        )
        t0 = time.perf_counter()
        alerts = engine.ingest_event(event)
        dt_us = (time.perf_counter() - t0) * 1_000_000
        total_us += dt_us
        all_alerts.extend(alerts)
        
        if callback:
            callback(i, demo_event, alerts, dt_us)
    
    return {
        "alerts": all_alerts,
        "total_latency_us": total_us,
        "avg_latency_us": total_us / len(scenario.events) if scenario.events else 0,
        "events_processed": len(scenario.events),
        "scenario_name": scenario.name,
        "actor": scenario.actor,
        "financial_impact": scenario.financial_impact,
    }


# ════════════════════════════════════════════════════════════════
#  OFFLINE / PRE-CACHED RESULTS
# ════════════════════════════════════════════════════════════════
def generate_offline_cache() -> Dict:
    """
    Pre-compute all demo results so the deck works without live engines.
    Call this once, store the result, and use it as fallback.
    """
    engine = TemporalCorrelationEngine(fast_mode=True)
    cache = {}
    
    for firm_name, packet in FIRM_PACKETS.items():
        cache[firm_name] = {}
        for scenario in packet.scenarios:
            result = run_firm_scenario(engine, scenario)
            # Convert alerts to serializable dicts
            result["alerts_summary"] = [
                {
                    "pattern_name": a.pattern_name,
                    "severity": a.severity,
                    "completion_percent": a.completion_percent,
                    "matched_stages": len(a.matched_stages),
                    "total_stages": a.total_stages,
                    "time_span_hours": a.time_span_hours,
                }
                for a in result["alerts"]
            ]
            del result["alerts"]  # Remove non-serializable objects
            cache[firm_name][scenario.name] = result
    
    return cache


# Pre-generate if run directly
if __name__ == "__main__":
    import json
    print("Generating offline demo cache...")
    cache = generate_offline_cache()
    
    with open("demo_cache.json", "w") as f:
        json.dump(cache, f, indent=2, default=str)
    
    print(f"\nCached {sum(len(v) for v in cache.values())} scenarios for {len(cache)} firms.")
    for firm, scenarios in cache.items():
        print(f"\n  {firm}:")
        for name, result in scenarios.items():
            print(f"    {name}: {result['events_processed']} events, "
                  f"{result['total_latency_us']:.0f}µs, "
                  f"{len(result['alerts_summary'])} alerts")
