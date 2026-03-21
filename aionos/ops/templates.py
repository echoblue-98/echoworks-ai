"""
EchoWorks Ops Engine -- Playbook Template Library
====================================================
Pre-built playbook templates organized by category.
Instantiate with one command instead of manually creating steps.

Categories:
  - sales:       outbound, follow-up, objection handling
  - operations:  onboarding, incident response, compliance
  - product:     release, demo, QA
  - technical:   deployment, monitoring, backup

Usage:
    from aionos.ops.templates import TemplateLibrary
    lib = TemplateLibrary()
    lib.list_templates()
    lib.create_from_template("sales_objection_handling", ops_store)
"""

from __future__ import annotations

from typing import Dict, List, Optional

from aionos.ops.store import OpsStore


# ─── Template definitions ────────────────────────────────────

TEMPLATES: Dict[str, Dict] = {
    # ═══════════════════════════════════════════════════════════
    #  SALES TEMPLATES
    # ═══════════════════════════════════════════════════════════
    "sales_cold_outbound": {
        "name": "Cold Outbound Campaign",
        "category": "sales",
        "description": "Structured cold outreach: research, email, LinkedIn, follow-up",
        "trigger": "manual",
        "steps": [
            "Research prospect -- company size, vertical, decision maker",
            "Draft personalized cold email using vertical template",
            "Send cold email (track open/reply)",
            "LinkedIn connection request with personalized note",
            "Day 3: Follow-up email with different angle",
            "Day 5: LinkedIn message with case study or stat",
            "Day 7: Breakup email or demo offer",
            "Log all activity and update prospect stage",
        ],
    },
    "sales_objection_handling": {
        "name": "Objection Handling Playbook",
        "category": "sales",
        "description": "Common objections and response framework",
        "trigger": "Prospect raises objection during demo or call",
        "steps": [
            "Identify objection type: price / need / timing / competition / authority",
            "Acknowledge: repeat back what they said to show understanding",
            "Reframe: connect objection to their stated pain point",
            "Provide proof: share relevant case study or metric",
            "Ask for next step: schedule follow-up or send proposal",
            "Log objection type for pattern analysis",
        ],
    },
    "sales_demo_prep": {
        "name": "Demo Preparation Checklist",
        "category": "sales",
        "description": "Pre-demo prep: env check, personalization, talking points",
        "trigger": "Demo scheduled with prospect",
        "steps": [
            "Verify LM Studio is running (localhost:1234)",
            "Verify SOC Console is running (localhost:9000)",
            "Research prospect: recent news, pain points, competitors they use",
            "Customize demo scenario for their vertical",
            "Prep 3 talking points tied to their specific problems",
            "Test screen share and audio",
            "Send calendar reminder + agenda 1 hour before",
        ],
    },
    "sales_proposal_creation": {
        "name": "Proposal Creation",
        "category": "sales",
        "description": "Create and send pricing proposal after demo",
        "trigger": "Demo completed, prospect interested",
        "steps": [
            "Select pricing tier: Baseline ($3,750), Intelligence ($7,500), or Sentinel ($12,500)",
            "Draft SOW: scope, timeline, deliverables, payment terms",
            "Include implementation plan (72-hour baseline + config)",
            "Add case study / ROI estimate specific to their vertical",
            "Internal review: check margins, scope creep risk",
            "Send proposal with 48-hour soft deadline",
            "Schedule follow-up call for 48 hours after send",
        ],
    },

    # ═══════════════════════════════════════════════════════════
    #  OPERATIONS TEMPLATES
    # ═══════════════════════════════════════════════════════════
    "ops_incident_response": {
        "name": "Client Incident Response",
        "category": "operations",
        "description": "Respond to insider threat alert detected by AION OS",
        "trigger": "High-severity alert from AION OS",
        "steps": [
            "Verify alert: check behavioral pattern, false positive score",
            "Collect evidence: activity logs, file access patterns, timeline",
            "Notify client CISO within 15 minutes",
            "Generate PDF threat report",
            "Provide recommended containment actions",
            "Schedule debrief call within 24 hours",
            "Log incident for pattern database",
        ],
    },
    "ops_compliance_audit": {
        "name": "Compliance Audit Preparation",
        "category": "operations",
        "description": "Prepare for SOC 2 / HIPAA / regulatory compliance review",
        "trigger": "Annual compliance review or client request",
        "steps": [
            "Verify all data encryption at rest and in transit",
            "Confirm zero-cloud architecture documentation is current",
            "Review access control logs for last 90 days",
            "Generate data handling procedures document",
            "Test incident response time (target: <15 min notification)",
            "Prepare privacy impact assessment if required",
            "Package all documentation for auditor review",
        ],
    },
    "ops_weekly_ops_review": {
        "name": "Weekly Operations Review",
        "category": "operations",
        "description": "Weekly review of all operational metrics and pipeline",
        "trigger": "Every Monday morning",
        "steps": [
            "Run: python -m aionos.ops.cli daily (pull daily report)",
            "Review pipeline counts by stage",
            "Check all stale deals and decide: re-engage or close",
            "Review metric trends (emails, demos, revenue)",
            "Update active memos with progress notes",
            "Plan this week's outbound targets (min 10 touches/day)",
            "Generate weekly review: python -m aionos.ops.cli review generate",
        ],
    },

    # ═══════════════════════════════════════════════════════════
    #  PRODUCT TEMPLATES
    # ═══════════════════════════════════════════════════════════
    "product_feature_release": {
        "name": "Feature Release Checklist",
        "category": "product",
        "description": "Ship a new feature from dev to production",
        "trigger": "Feature ready for release",
        "steps": [
            "Run full test suite: python -m pytest tests/",
            "Update version in setup.py",
            "Write release notes (what changed, why it matters)",
            "Run demo to verify feature works end-to-end",
            "Git commit and push to main",
            "Update docs/ website if needed",
            "Notify existing clients if feature affects their deployment",
        ],
    },
    "product_competitive_intel": {
        "name": "Competitive Intelligence Scan",
        "category": "product",
        "description": "Monthly competitive landscape analysis",
        "trigger": "First of each month",
        "steps": [
            "Check competitor websites for new features / pricing changes",
            "Search LinkedIn for competitor hiring patterns",
            "Review industry analyst reports (Gartner, Forrester)",
            "Update competitive comparison matrix",
            "Identify gaps where AION OS can differentiate",
            "Create memo with findings and recommendations",
        ],
    },

    # ═══════════════════════════════════════════════════════════
    #  TECHNICAL TEMPLATES
    # ═══════════════════════════════════════════════════════════
    "tech_client_deployment": {
        "name": "Client Deployment",
        "category": "technical",
        "description": "Deploy AION OS to client environment",
        "trigger": "Client onboarding step 3",
        "steps": [
            "Verify client hardware meets minimum specs (16GB RAM, 4-core CPU)",
            "Prepare isolated data directory and config file",
            "Install Python environment and dependencies",
            "Deploy AION OS core engine",
            "Configure LM Studio model for client's threat profile",
            "Run smoke test: verify all modules load",
            "Start 72-hour baseline scan",
            "Deliver baseline report when scan completes",
        ],
    },
    "tech_backup_recovery": {
        "name": "Backup & Recovery Drill",
        "category": "technical",
        "description": "Verify backup procedures and recovery time",
        "trigger": "Quarterly",
        "steps": [
            "Verify all SQLite databases can be backed up while running",
            "Create backup of pipeline.db, ops.db, and pattern databases",
            "Test restore from backup to fresh directory",
            "Verify data integrity after restore",
            "Document recovery time (target: <30 minutes)",
            "Update disaster recovery plan if needed",
        ],
    },
}


class TemplateLibrary:
    """Browse and instantiate playbook templates."""

    def list_templates(self, category: Optional[str] = None) -> List[Dict]:
        """List available templates, optionally filtered by category."""
        results = []
        for key, tmpl in TEMPLATES.items():
            if category and tmpl["category"] != category:
                continue
            results.append({
                "key": key,
                "name": tmpl["name"],
                "category": tmpl["category"],
                "description": tmpl["description"],
                "steps": len(tmpl["steps"]),
            })
        return results

    def get_template(self, key: str) -> Optional[Dict]:
        """Get full template definition."""
        return TEMPLATES.get(key)

    def create_from_template(
        self,
        key: str,
        ops: OpsStore,
        owner: str = "EchoWorks",
        name_override: Optional[str] = None,
    ) -> Optional[int]:
        """Instantiate a template as a real playbook in the ops store."""
        tmpl = TEMPLATES.get(key)
        if not tmpl:
            return None

        steps = []
        for i, action in enumerate(tmpl["steps"], 1):
            steps.append({
                "step_num": i,
                "action": action,
                "status": "not_started",
                "completed_date": "",
                "notes": "",
            })

        return ops.create_playbook(
            name=name_override or tmpl["name"],
            category=tmpl["category"],
            description=tmpl["description"],
            trigger=tmpl["trigger"],
            owner=owner,
            steps=steps,
        )

    def categories(self) -> List[str]:
        """List unique categories."""
        return sorted(set(t["category"] for t in TEMPLATES.values()))
