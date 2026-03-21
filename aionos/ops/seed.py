"""
Seed the ops engine with initial playbooks and memos.

Run once:  python -m aionos.ops.seed
"""

from __future__ import annotations

from datetime import date, timedelta

from aionos.ops.store import OpsStore


def seed(ops: OpsStore) -> None:
    """Populate the ops store with starter playbooks, memos, and trigger rules."""

    # ────────────────────────────────────────────────────────────
    #  PLAYBOOK 1 -- Daily Sales Outbound
    # ────────────────────────────────────────────────────────────
    ops.create_playbook(
        name="Daily Sales Outbound",
        category="sales",
        description="Morning outbound routine -- 10 LinkedIn touches + 5 cold emails",
        trigger="Every business day, 9:00 AM",
        owner="EchoWorks",
        steps=[
            {"step_num": 1, "action": "Run: python -m aionos.sales.cli queue  (check today's queue)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 2, "action": "Generate messages: python -m aionos.sales.cli batch --type cold_email",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 3, "action": "Send 5 cold emails (paste from generated output)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 4, "action": "Send 10 LinkedIn connection requests with personalized notes",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 5, "action": "Log all touches: python -m aionos.sales.cli log <id> contacted",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 6, "action": "Record metric: python -m aionos.ops.cli metric record emails_sent <N>",
             "status": "not_started", "completed_date": "", "notes": ""},
        ],
    )

    # ────────────────────────────────────────────────────────────
    #  PLAYBOOK 2 -- Client Onboarding
    # ────────────────────────────────────────────────────────────
    ops.create_playbook(
        name="Client Onboarding",
        category="operations",
        description="End-to-end onboarding for a new AION OS client",
        trigger="New signed contract",
        owner="EchoWorks",
        steps=[
            {"step_num": 1, "action": "Collect client NDA and signed SOW",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 2, "action": "Provision isolated tenant (data directory + config file)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 3, "action": "Deploy AION OS agent on client hardware or VM",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 4, "action": "Ingest client HR roster and org chart",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 5, "action": "Configure threat patterns for client vertical",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 6, "action": "Run 72-hour baseline scan -- all detections suppressed",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 7, "action": "Deliver baseline report to client CISO",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 8, "action": "Enable live alerting -- SOC console online",
             "status": "not_started", "completed_date": "", "notes": ""},
        ],
    )

    # ────────────────────────────────────────────────────────────
    #  PLAYBOOK 3 -- Demo Recording
    # ────────────────────────────────────────────────────────────
    ops.create_playbook(
        name="Demo Recording",
        category="product",
        description="Record polished AION OS demo for investors and prospects",
        trigger="Before each funding round or new vertical push",
        owner="EchoWorks",
        steps=[
            {"step_num": 1, "action": "Start LM Studio with GPU offload (qwen2.5-coder-1.5b-instruct or larger)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 2, "action": "Verify localhost:1234 responds: curl http://localhost:1234/v1/models",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 3, "action": "Open SOC Command Console on localhost:9000 (python run_node.py)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 4, "action": "Set OBS: 1920x1080, 30fps, system audio + mic",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 5, "action": "Record 3 scenarios from DEMO_VOICEOVER_SCRIPT.md",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 6, "action": "Review recording -- trim dead air, re-record if needed",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 7, "action": "Export MP4 and upload to private YouTube / Google Drive",
             "status": "not_started", "completed_date": "", "notes": ""},
        ],
    )

    # ────────────────────────────────────────────────────────────
    #  MEMO 1 -- Revenue Target
    # ────────────────────────────────────────────────────────────
    review_30 = (date.today() + timedelta(days=30)).isoformat()
    m1 = ops.create_memo(
        title="$100K Revenue by Dec 2026",
        category="finance",
        issue="EchoWorks needs $100K ARR by Dec 31, 2026 to validate "
              "the business and de-risk the first hire.",
        strategy="Three verticals (legal, healthcare, real estate). "
                 "Start with $3,750/mo Baseline tier. "
                 "Close Sean ($2K integration) as proof of revenue. "
                 "Target 3 paying clients by Q3 2026.",
        tradeoffs="Not building a freemium tier. Not pursuing enterprise "
                  "sales cycle (>6 months). Not hiring until $5K MRR.",
        metrics="MRR, pipeline count, conversion rate (demo -> close), "
                "average deal size",
        next_steps=[
            {"step_num": 1, "description": "Close Sean -- $2K integration", "done": False},
            {"step_num": 2, "description": "Send Dan warm intro message", "done": False},
            {"step_num": 3, "description": "Complete 30 cold outbound touches", "done": False},
            {"step_num": 4, "description": "Record polished demo video", "done": False},
        ],
        review_date=review_30,
    )
    ops.activate_memo(m1)

    # ────────────────────────────────────────────────────────────
    #  MEMO 2 -- Sales Strategy
    # ────────────────────────────────────────────────────────────
    review_14 = (date.today() + timedelta(days=14)).isoformat()
    m2 = ops.create_memo(
        title="Outbound Sales Playbook Strategy",
        category="sales",
        issue="Need repeatable outbound process that generates demos "
              "without a sales team.",
        strategy="Use aionos.sales.cli for pipeline management. "
                 "Daily: 10 LinkedIn + 5 emails. "
                 "Weekly: review stale prospects, advance warm leads. "
                 "Monthly: refine messaging based on response rates.",
        tradeoffs="Not buying lead lists. Not using Sales Navigator yet. "
                  "Manual LinkedIn (no automation -- ban risk too high).",
        metrics="Response rate, demo bookings per week, pipeline velocity",
        next_steps=[
            {"step_num": 1, "description": "Execute Daily Sales Outbound playbook for 5 consecutive days", "done": False},
            {"step_num": 2, "description": "Track response rates in metrics", "done": False},
            {"step_num": 3, "description": "Refine cold email subject lines based on open rates", "done": False},
        ],
        review_date=review_14,
    )
    ops.activate_memo(m2)

    # ────────────────────────────────────────────────────────────
    #  MEMO 3 -- Product Roadmap
    # ────────────────────────────────────────────────────────────
    review_21 = (date.today() + timedelta(days=21)).isoformat()
    m3 = ops.create_memo(
        title="AION OS Product Roadmap Q2-Q3 2026",
        category="product",
        issue="Need to prioritize features that drive sales, "
              "not engineering for engineering's sake.",
        strategy="Ship demo-ready features first: PDF reports, "
                 "real-time SOC console, per-client threat profiles. "
                 "Delay: multi-tenant cloud, API marketplace, mobile app.",
        tradeoffs="Not building cloud deployment until 5+ clients. "
                  "Not building mobile app. Not open-sourcing core engine.",
        metrics="Features shipped per sprint, demo conversion rate, "
                "time from feature request to deployment",
        next_steps=[
            {"step_num": 1, "description": "Finalize PDF report generation for client deliverables", "done": False},
            {"step_num": 2, "description": "Polish SOC console for demo recording", "done": False},
            {"step_num": 3, "description": "Build client-specific threat profile config", "done": False},
        ],
        review_date=review_21,
    )
    ops.activate_memo(m3)

    # ────────────────────────────────────────────────────────────
    #  PLAYBOOK 4 -- Legal Vertical Outbound Cadence
    # ────────────────────────────────────────────────────────────
    ops.create_playbook(
        name="Legal Vertical -- Outbound Cadence",
        category="sales",
        description="7-day outbound for law firms: attorney departure theft, IP exfiltration, privilege violations",
        trigger="New legal prospect added",
        owner="EchoWorks",
        steps=[
            {"step_num": 1, "action": "Research firm on AMLAW 200 list -- identify recent departures and lateral hires",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 2, "action": "Send cold email: Attorney Departure Theft angle (use legal vertical template)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 3, "action": "LinkedIn connect w/ Managing Partner or CIO -- mention specific lateral move",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 4, "action": "Day 3: Follow-up email -- Privilege violation detection angle",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 5, "action": "Day 5: LinkedIn message -- Share attorney departure case study link",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 6, "action": "Day 7: Final follow-up -- Offer 15-min demo of AION OS legal threat detection",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 7, "action": "Log outcome + update prospect stage (engaged / demo_scheduled / cold)",
             "status": "not_started", "completed_date": "", "notes": ""},
        ],
    )

    # ────────────────────────────────────────────────────────────
    #  PLAYBOOK 5 -- Healthcare Vertical Outbound Cadence
    # ────────────────────────────────────────────────────────────
    ops.create_playbook(
        name="Healthcare Vertical -- Outbound Cadence",
        category="sales",
        description="7-day outbound for healthcare: billing fraud, HIPAA violations, insider EHR access",
        trigger="New healthcare prospect added",
        owner="EchoWorks",
        steps=[
            {"step_num": 1, "action": "Research org on HHS breach portal -- check recent HIPAA fines and OCR actions",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 2, "action": "Send cold email: HIPAA insider threat angle (use healthcare vertical template)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 3, "action": "LinkedIn connect w/ CISO, Compliance Officer, or Privacy Officer",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 4, "action": "Day 3: Follow-up email -- Billing fraud detection + EHR snooping angle",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 5, "action": "Day 5: LinkedIn message -- Share healthcare insider threat stat ($6.45B annual fraud)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 6, "action": "Day 7: Final follow-up -- Offer compliance audit demo of AION OS",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 7, "action": "Log outcome + update prospect stage",
             "status": "not_started", "completed_date": "", "notes": ""},
        ],
    )

    # ────────────────────────────────────────────────────────────
    #  PLAYBOOK 6 -- Real Estate Vertical Outbound Cadence
    # ────────────────────────────────────────────────────────────
    ops.create_playbook(
        name="Real Estate Vertical -- Outbound Cadence",
        category="sales",
        description="7-day outbound for real estate: wire fraud BEC, title company impersonation, closing day theft",
        trigger="New real estate prospect added",
        owner="EchoWorks",
        steps=[
            {"step_num": 1, "action": "Research firm -- check NAR membership, recent closings volume, past wire fraud incidents",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 2, "action": "Send cold email: Wire Fraud BEC angle (use realestate vertical template)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 3, "action": "LinkedIn connect w/ Broker, Managing Director, or IT Director",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 4, "action": "Day 3: Follow-up email -- Title company impersonation + escrow diversion angle",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 5, "action": "Day 5: LinkedIn message -- Share FBI IC3 wire fraud stat ($2.4B annual losses)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 6, "action": "Day 7: Final follow-up -- Offer demo of real-time BEC detection",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 7, "action": "Log outcome + update prospect stage",
             "status": "not_started", "completed_date": "", "notes": ""},
        ],
    )

    # ────────────────────────────────────────────────────────────
    #  PLAYBOOK 7 -- Post-Demo Follow-Up
    # ────────────────────────────────────────────────────────────
    ops.create_playbook(
        name="Post-Demo Follow-Up Sequence",
        category="sales",
        description="5-step follow-up after a demo to drive proposal and close",
        trigger="Demo completed",
        owner="EchoWorks",
        steps=[
            {"step_num": 1, "action": "Send thank-you email within 2 hours -- recap 3 key pain points discussed",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 2, "action": "Day 1: Send PDF threat assessment report tailored to their vertical",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 3, "action": "Day 3: Follow up -- ask if they shared with decision maker; offer 2nd demo for exec team",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 4, "action": "Day 5: Send pricing proposal -- Baseline tier $3,750/mo + implementation",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 5, "action": "Day 7: Final follow-up -- offer pilot program (30 days, reduced scope)",
             "status": "not_started", "completed_date": "", "notes": ""},
        ],
    )

    # ────────────────────────────────────────────────────────────
    #  PLAYBOOK 8 -- Stale Deal Re-Engagement
    # ────────────────────────────────────────────────────────────
    ops.create_playbook(
        name="Stale Deal Re-Engagement",
        category="sales",
        description="Re-engage prospects stuck in pipeline for 14+ days",
        trigger="Prospect stale alert",
        owner="EchoWorks",
        steps=[
            {"step_num": 1, "action": "Review prospect history -- identify where they went cold",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 2, "action": "Send breakup email: 'Should I close your file?' angle (drives 30%+ response rate)",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 3, "action": "If no reply in 3 days: LinkedIn message with new angle or case study",
             "status": "not_started", "completed_date": "", "notes": ""},
            {"step_num": 4, "action": "If reply: schedule call, re-qualify, update stage. If no reply: mark closed_lost",
             "status": "not_started", "completed_date": "", "notes": ""},
        ],
    )

    # ════════════════════════════════════════════════════════════
    #  DEFAULT TRIGGER RULES
    # ════════════════════════════════════════════════════════════
    from aionos.ops.triggers import TriggerEngine
    triggers = TriggerEngine(ops)

    # Get playbook IDs (they're sequential: 1-8 in seed order)
    all_pbs = ops.list_playbooks()
    pb_ids = {pb["name"]: pb["id"] for pb in all_pbs}

    # Time trigger: run Daily Sales Outbound every weekday
    triggers.add_rule(
        name="Weekday Sales Outbound",
        trigger_type="time",
        event_type="time_trigger",
        condition="weekday",
        playbook_id=pb_ids.get("Daily Sales Outbound"),
        action="Reset and start daily sales outbound playbook",
    )

    # Event trigger: demo completed -> start Post-Demo Follow-Up
    triggers.add_rule(
        name="Post-Demo Auto Follow-Up",
        trigger_type="event",
        event_type="stage_change",
        condition="new_stage=demo_completed",
        playbook_id=pb_ids.get("Post-Demo Follow-Up Sequence"),
        action="Auto-start post-demo follow-up sequence",
    )

    # Event trigger: deal closed won -> start Client Onboarding
    triggers.add_rule(
        name="Auto-Start Onboarding",
        trigger_type="event",
        event_type="deal_closed_won",
        condition="",
        playbook_id=pb_ids.get("Client Onboarding"),
        action="New client -- start onboarding playbook",
    )

    # Event trigger: prospect stale -> start Stale Re-Engagement
    triggers.add_rule(
        name="Stale Deal Recovery",
        trigger_type="event",
        event_type="prospect_stale",
        condition="",
        playbook_id=pb_ids.get("Stale Deal Re-Engagement"),
        action="Re-engage stale prospect",
    )

    # Metric trigger: closed_won hits 3+ -> celebrate & review
    triggers.add_rule(
        name="Revenue Milestone Alert",
        trigger_type="metric",
        event_type="metric_trigger",
        condition="closed_won>2",
        action="Revenue milestone reached! Review pricing and capacity.",
    )

    print("  Seeded ops engine:")
    print("    8 playbooks (Daily Outbound, Onboarding, Demo Recording,")
    print("                  Legal Cadence, Healthcare Cadence, Real Estate Cadence,")
    print("                  Post-Demo Follow-Up, Stale Re-Engagement)")
    print("    3 memos ($100K Revenue, Sales Strategy, Product Roadmap)")
    print("    5 trigger rules (weekday outbound, post-demo, onboarding,")
    print("                     stale recovery, revenue milestone)")
    print("    All memos activated with review dates set")


def main() -> None:
    ops = OpsStore()
    try:
        # Check if already seeded
        existing = ops.list_playbooks()
        if existing:
            print(f"  Ops engine already has {len(existing)} playbooks. Skipping seed.")
            print("  To re-seed, delete ops.db first.")
            return
        seed(ops)
    finally:
        ops.close()


if __name__ == "__main__":
    main()
