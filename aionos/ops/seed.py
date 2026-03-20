"""
Seed the ops engine with initial playbooks and memos.

Run once:  python -m aionos.ops.seed
"""

from __future__ import annotations

from datetime import date, timedelta

from aionos.ops.store import OpsStore


def seed(ops: OpsStore) -> None:
    """Populate the ops store with starter playbooks and memos."""

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

    print("  Seeded ops engine:")
    print("    3 playbooks (Daily Sales Outbound, Client Onboarding, Demo Recording)")
    print("    3 memos ($100K Revenue, Sales Strategy, Product Roadmap)")
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
