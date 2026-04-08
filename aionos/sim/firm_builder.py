"""
EchoWorks — Simulated Law Firm Environment
=============================================
Creates a realistic law firm file structure for AION OS demonstration.

Structure mirrors a real 50-attorney firm's network drive:
  \\FIRM-SERVER\
    Matters\          — Client case files organized by matter number
    Billing\          — Financial records, invoices, trust accounts
    HR\               — Employee records, compensation, reviews
    Templates\        — Form documents, standard agreements
    SharedDrive\      — General firm resources
"""

import os
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

FIRM_ROOT = Path(__file__).parent.parent.parent / "sim_firm"

# ── Firm Personnel ────────────────────────────────────────────────

ATTORNEYS = {
    "jmitchell": {"name": "James Mitchell", "title": "Managing Partner", "years": 22},
    "kpatel":    {"name": "Karen Patel",    "title": "Senior Partner",   "years": 18},
    "rgarcia":   {"name": "Robert Garcia",  "title": "Partner",          "years": 14},
    "lwilson":   {"name": "Lisa Wilson",    "title": "Partner",          "years": 11},
    "tcarter":   {"name": "Tom Carter",     "title": "Senior Associate", "years": 7},
    "akim":      {"name": "Amy Kim",        "title": "Associate",        "years": 4},
    "dthompson": {"name": "Derek Thompson", "title": "Associate",        "years": 3},
    "mchen":     {"name": "Michelle Chen",  "title": "Junior Associate", "years": 1},
}

# The departing attorney — this is who the demo catches
DEPARTING_ATTORNEY = "rgarcia"

# ── Client Matters ────────────────────────────────────────────────

MATTERS = [
    {"number": "2024-0142", "client": "Meridian Healthcare", "type": "Employment Litigation",
     "lead": "jmitchell", "team": ["tcarter", "mchen"], "value": "$2.4M",
     "files": ["complaint.docx", "answer.docx", "discovery_plan.docx",
               "deposition_smith.pdf", "deposition_jones.pdf", "expert_report.pdf",
               "settlement_memo.docx", "billing_summary.xlsx"]},

    {"number": "2024-0187", "client": "Atlas Manufacturing", "type": "Trade Secret",
     "lead": "rgarcia", "team": ["akim", "dthompson"], "value": "$5.1M",
     "files": ["complaint_trade_secret.docx", "tro_motion.docx", "tro_brief.pdf",
               "client_formula_docs.pdf", "competitor_analysis.xlsx",
               "forensic_report_usb.pdf", "damages_calculation.xlsx",
               "deposition_knowles.pdf", "trial_strategy.docx", "jury_instructions.docx"]},

    {"number": "2024-0203", "client": "Riverstone Capital", "type": "Securities Fraud",
     "lead": "rgarcia", "team": ["tcarter"], "value": "$8.7M",
     "files": ["sec_complaint.docx", "response_brief.pdf", "financial_records.xlsx",
               "trading_data_2023.csv", "trading_data_2024.csv", "wire_transfer_log.pdf",
               "expert_witness_cv.docx", "damages_model.xlsx", "mediation_brief.docx"]},

    {"number": "2024-0221", "client": "Greenfield Properties", "type": "Real Estate",
     "lead": "kpatel", "team": ["lwilson", "akim"], "value": "$1.8M",
     "files": ["purchase_agreement.docx", "title_report.pdf", "survey.pdf",
               "environmental_assessment.pdf", "closing_docs.docx", "escrow_instructions.docx"]},

    {"number": "2024-0256", "client": "TechNova Solutions", "type": "IP Licensing",
     "lead": "lwilson", "team": ["dthompson", "mchen"], "value": "$3.2M",
     "files": ["license_agreement.docx", "patent_portfolio.xlsx", "royalty_schedule.xlsx",
               "infringement_analysis.docx", "cease_desist_draft.docx", "client_source_code_review.pdf"]},

    {"number": "2025-0012", "client": "Pinnacle Insurance", "type": "Bad Faith",
     "lead": "rgarcia", "team": ["akim"], "value": "$4.5M",
     "files": ["complaint_bad_faith.docx", "policy_documents.pdf", "claim_file.pdf",
               "adjuster_notes.pdf", "medical_records_redacted.pdf",
               "damages_report.docx", "expert_designation.docx"]},

    {"number": "2025-0034", "client": "Summit Logistics", "type": "Contract Dispute",
     "lead": "jmitchell", "team": ["tcarter", "dthompson"], "value": "$1.1M",
     "files": ["master_services_agreement.docx", "invoice_dispute.xlsx",
               "correspondence_log.pdf", "mediation_summary.docx"]},

    {"number": "2025-0051", "client": "Heritage Bank", "type": "Regulatory",
     "lead": "kpatel", "team": ["lwilson"], "value": "$6.3M",
     "files": ["occ_consent_order.pdf", "compliance_plan.docx", "bsa_audit.pdf",
               "customer_data_sample.xlsx", "remediation_timeline.docx",
               "board_presentation.pptx"]},
]

# ── File Content Generator ────────────────────────────────────────

def _fake_content(filename: str, matter: dict) -> str:
    """Generate realistic-looking file content."""
    ext = Path(filename).suffix
    if ext in (".docx", ".doc"):
        return (
            f"CONFIDENTIAL — ATTORNEY WORK PRODUCT\n"
            f"{'=' * 50}\n"
            f"Matter: {matter['number']} — {matter['client']}\n"
            f"Type: {matter['type']}\n"
            f"Document: {filename}\n"
            f"Lead Attorney: {ATTORNEYS[matter['lead']]['name']}\n"
            f"Date: {datetime.now().strftime('%B %d, %Y')}\n"
            f"{'=' * 50}\n\n"
            f"{''.join(random.choices(string.ascii_letters + ' ', k=random.randint(500, 2000)))}\n"
        )
    elif ext in (".xlsx", ".csv"):
        rows = random.randint(50, 500)
        return f"[Spreadsheet data — {rows} rows, {random.randint(5,15)} columns]\n" + \
               "\n".join(f"Row {i}," + ",".join(str(random.randint(1,99999)) for _ in range(8))
                         for i in range(min(rows, 20)))
    elif ext == ".pdf":
        return (
            f"[PDF Document — {random.randint(5,80)} pages]\n"
            f"Matter: {matter['number']}\n"
            f"PRIVILEGED AND CONFIDENTIAL\n"
            f"{''.join(random.choices(string.ascii_letters + ' ', k=random.randint(1000, 3000)))}\n"
        )
    elif ext == ".pptx":
        return f"[Presentation — {random.randint(10,40)} slides]\nMatter: {matter['number']}\n"
    return f"[File content for {filename}]\n"


# ── Build Functions ───────────────────────────────────────────────

def build_matters():
    """Create the Matters directory with all case files."""
    for matter in MATTERS:
        matter_dir = FIRM_ROOT / "Matters" / f"{matter['number']}_{matter['client'].replace(' ', '_')}"
        for subfolder in ["Pleadings", "Discovery", "Correspondence", "Billing", "WorkProduct"]:
            (matter_dir / subfolder).mkdir(parents=True, exist_ok=True)

        for filename in matter["files"]:
            # Place files in appropriate subfolders
            if any(w in filename for w in ["complaint", "answer", "motion", "brief", "tro"]):
                dest = matter_dir / "Pleadings" / filename
            elif any(w in filename for w in ["deposition", "discovery", "forensic", "records"]):
                dest = matter_dir / "Discovery" / filename
            elif any(w in filename for w in ["billing", "invoice", "damages", "royalty"]):
                dest = matter_dir / "Billing" / filename
            else:
                dest = matter_dir / "WorkProduct" / filename

            dest.write_text(_fake_content(filename, matter))


def build_billing():
    """Create billing and financial records."""
    billing_dir = FIRM_ROOT / "Billing"
    for attorney_id, attorney in ATTORNEYS.items():
        atty_dir = billing_dir / attorney_id
        atty_dir.mkdir(parents=True, exist_ok=True)
        for month in range(1, 13):
            (atty_dir / f"timesheet_2025_{month:02d}.xlsx").write_text(
                f"Timesheet — {attorney['name']} — 2025-{month:02d}\n"
                f"Total Hours: {random.randint(140, 220)}\n"
                f"Billable: {random.randint(120, 200)}\n"
            )
    # Trust accounts
    trust_dir = billing_dir / "TrustAccounts"
    trust_dir.mkdir(parents=True, exist_ok=True)
    for matter in MATTERS:
        (trust_dir / f"trust_{matter['number']}.xlsx").write_text(
            f"IOLTA Trust Account — {matter['client']}\n"
            f"Balance: ${random.randint(10000, 500000):,}\n"
        )


def build_hr():
    """Create HR records."""
    hr_dir = FIRM_ROOT / "HR"
    for subfolder in ["Personnel", "Compensation", "Reviews", "Policies"]:
        (hr_dir / subfolder).mkdir(parents=True, exist_ok=True)

    for attorney_id, attorney in ATTORNEYS.items():
        (hr_dir / "Personnel" / f"{attorney_id}_personnel_file.pdf").write_text(
            f"CONFIDENTIAL PERSONNEL FILE\n"
            f"Name: {attorney['name']}\n"
            f"Title: {attorney['title']}\n"
            f"Years: {attorney['years']}\n"
            f"Start Date: {(datetime.now() - timedelta(days=attorney['years']*365)).strftime('%Y-%m-%d')}\n"
        )
        (hr_dir / "Compensation" / f"{attorney_id}_comp_2025.xlsx").write_text(
            f"Compensation — {attorney['name']}\n"
            f"Base: ${random.randint(150, 450) * 1000:,}\n"
            f"Bonus: ${random.randint(20, 150) * 1000:,}\n"
            f"Equity: {random.randint(0, 15)}%\n"
        )
        (hr_dir / "Reviews" / f"{attorney_id}_review_2025.docx").write_text(
            f"Performance Review — {attorney['name']} — 2025\n"
            f"Rating: {random.choice(['Exceeds Expectations', 'Meets Expectations', 'Outstanding'])}\n"
        )

    # Firm policies
    for policy in ["employee_handbook.pdf", "data_security_policy.pdf",
                    "acceptable_use_policy.pdf", "departure_procedures.pdf",
                    "non_compete_agreement_template.docx"]:
        (hr_dir / "Policies" / policy).write_text(f"[Firm Policy Document: {policy}]\n")


def build_templates():
    """Create firm template documents."""
    tmpl_dir = FIRM_ROOT / "Templates"
    tmpl_dir.mkdir(parents=True, exist_ok=True)
    for tmpl in ["engagement_letter.docx", "retainer_agreement.docx",
                  "nda_mutual.docx", "nda_unilateral.docx",
                  "litigation_hold_notice.docx", "conflict_check_form.docx",
                  "case_opening_checklist.docx", "case_closing_checklist.docx",
                  "deposition_outline_template.docx", "motion_template.docx"]:
        (tmpl_dir / tmpl).write_text(f"[Template: {tmpl}]\nFirm: Mitchell Patel & Garcia LLP\n")


def build_shared():
    """Create shared drive resources."""
    shared = FIRM_ROOT / "SharedDrive"
    for subfolder in ["Marketing", "IT", "Admin", "CLE"]:
        (shared / subfolder).mkdir(parents=True, exist_ok=True)

    (shared / "Marketing" / "firm_brochure_2025.pdf").write_text("Mitchell Patel & Garcia LLP\n")
    (shared / "Marketing" / "client_list_master.xlsx").write_text(
        "CONFIDENTIAL — Master Client List\n" +
        "\n".join(f"{m['client']},{m['type']},{m['lead']},{m['value']}"
                  for m in MATTERS)
    )
    (shared / "IT" / "network_diagram.pdf").write_text("[Network topology diagram]\n")
    (shared / "IT" / "password_policy.docx").write_text("[Password policy document]\n")
    (shared / "IT" / "vpn_setup_guide.pdf").write_text("[VPN configuration guide]\n")
    (shared / "Admin" / "office_directory.xlsx").write_text(
        "Name,Extension,Email,Office\n" +
        "\n".join(f"{a['name']},{random.randint(100,999)},{uid}@mpg-law.com,Atlanta"
                  for uid, a in ATTORNEYS.items())
    )


def build_firm(root: Path = None):
    """Build the complete simulated law firm. Returns stats dict."""
    global FIRM_ROOT
    if root:
        FIRM_ROOT = root

    print("=" * 60)
    print("  BUILDING SIMULATED LAW FIRM: Mitchell Patel & Garcia LLP")
    print("=" * 60)
    print()

    build_matters()
    print(f"  ✓ Matters/        — {len(MATTERS)} active matters, {sum(len(m['files']) for m in MATTERS)} files")

    build_billing()
    print(f"  ✓ Billing/        — {len(ATTORNEYS)} attorney timesheets + trust accounts")

    build_hr()
    print(f"  ✓ HR/             — Personnel files, compensation, reviews, policies")

    build_templates()
    print("  ✓ Templates/      — 10 standard firm templates")

    build_shared()
    print("  ✓ SharedDrive/    — Marketing, IT, Admin, CLE resources")

    # Count total
    total = sum(1 for _ in FIRM_ROOT.rglob("*") if _.is_file())
    print()
    print(f"  TOTAL: {total} files across {FIRM_ROOT}")
    print()

    # Summary of the departing attorney's access
    rgarcia_matters = [m for m in MATTERS if m["lead"] == DEPARTING_ATTORNEY
                       or DEPARTING_ATTORNEY in m.get("team", [])]
    print(f"  ⚠ DEPARTING ATTORNEY: {ATTORNEYS[DEPARTING_ATTORNEY]['name']}")
    print(f"    Matters with access: {len(rgarcia_matters)}")
    print(f"    Total matter value:  ${sum(float(m['value'].replace('$','').replace('M','')) for m in rgarcia_matters):.1f}M")
    print(f"    Files at risk:       {sum(len(m['files']) for m in rgarcia_matters)}")
    print()

    return {
        "firm_name": "Mitchell Patel & Garcia LLP",
        "num_attorneys": len(ATTORNEYS),
        "num_matters": len(MATTERS),
        "total_files": total,
        "firm_root": str(FIRM_ROOT),
    }


if __name__ == "__main__":
    build_firm()
