"""
Sales Engine — CLI
====================
Command-line interface to run the full sales automation:
  - Add/list/update prospects
  - Generate personalized messages
  - View daily action queue
  - Export CSV for bulk email tools
  - View pipeline stats

Usage:
    python -m aionos.sales.cli add "Sarah Chen" "Baker McKenzie" legal --title "Managing Partner" --email sche@bm.com
    python -m aionos.sales.cli generate 1
    python -m aionos.sales.cli batch legal
    python -m aionos.sales.cli queue
    python -m aionos.sales.cli stats
    python -m aionos.sales.cli export prospects.csv
    python -m aionos.sales.cli advance 1 demo_scheduled
    python -m aionos.sales.cli history 1
    python -m aionos.sales.cli stale
    python -m aionos.sales.cli import prospects.csv
"""

from __future__ import annotations

import argparse
import sys
import os
from datetime import date, datetime

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from aionos.sales.engine import SalesEngine
from aionos.sales.prospects import Pipeline
from aionos.sales.messages import MessageGenerator
from aionos.sales.learner import SalesLearner


def _cli_add(args, pipe: Pipeline) -> None:
    pid = pipe.add(
        name=args.name,
        company=args.company,
        vertical=args.vertical,
        title=args.title or "",
        email=args.email or "",
        linkedin=args.linkedin or "",
        phone=args.phone or "",
        notes=args.notes or "",
        source=args.source or "manual",
    )
    # Schedule first action for tomorrow
    pipe.set_next_action(pid, days_from_now=1)
    print(f"  Added prospect #{pid}: {args.name} @ {args.company} [{args.vertical}]")
    print(f"  First action scheduled for tomorrow")


def _cli_list(args, pipe: Pipeline) -> None:
    prospects = pipe.list_all(
        vertical=args.vertical if hasattr(args, "vertical") and args.vertical != "all" else None,
        stage=args.stage if hasattr(args, "stage") and args.stage != "all" else None,
    )
    if not prospects:
        print("  No prospects found.")
        return

    print(f"\n  {'ID':>4}  {'Name':<22} {'Company':<22} {'Vertical':<12} {'Stage':<16} {'Email':<30}")
    print(f"  {'-'*4}  {'-'*22} {'-'*22} {'-'*12} {'-'*16} {'-'*30}")
    for p in prospects:
        print(
            f"  {p['id']:>4}  {p['name']:<22.22} {p['company']:<22.22} "
            f"{p['vertical']:<12} {p['stage']:<16} {p['email']:<30.30}"
        )
    print(f"\n  Total: {len(prospects)}")


def _cli_generate(args, pipe: Pipeline, gen: MessageGenerator) -> None:
    prospect = pipe.get(args.prospect_id)
    if not prospect:
        print(f"  Prospect #{args.prospect_id} not found.")
        return

    msgs = gen.generate(
        name=prospect["name"],
        company=prospect["company"],
        title=prospect.get("title", ""),
        vertical=prospect["vertical"],
    )

    print(f"\n{'='*70}")
    print(f"  MESSAGES FOR: {prospect['name']} @ {prospect['company']}")
    print(f"  Vertical: {prospect['vertical']}  |  Stage: {prospect['stage']}")
    print(f"{'='*70}\n")

    for key in ["cold_email", "linkedin_request", "follow_up_1", "follow_up_2", "follow_up_3"]:
        if key in msgs:
            label = key.replace("_", " ").upper()
            print(f"  +--- {label} {'-' * (55 - len(label))}+")
            for line in msgs[key].split("\n"):
                print(f"  | {line}")
            print(f"  +{'-'*60}+\n")

    # Show objection handlers
    obj_keys = [k for k in msgs if k.startswith("objection_")]
    if obj_keys:
        print(f"  +--- OBJECTION HANDLERS {'-'*35}+")
        for k in obj_keys[:3]:
            for line in msgs[k].split("\n"):
                print(f"  | {line}")
            print(f"  |")
        print(f"  +{'-'*60}+\n")


def _cli_batch(args, pipe: Pipeline, gen: MessageGenerator) -> None:
    vertical = args.vertical if args.vertical != "all" else None
    prospects = pipe.list_all(vertical=vertical, stage="cold")
    if not prospects:
        print("  No cold prospects found for batch generation.")
        return

    limit = args.limit or 10
    batch = prospects[:limit]

    print(f"\n  Generating messages for {len(batch)} prospects...\n")
    for p in batch:
        msgs = gen.generate(
            name=p["name"],
            company=p["company"],
            title=p.get("title", ""),
            vertical=p["vertical"],
        )
        print(f"  -- #{p['id']} {p['name']} @ {p['company']} ({p['vertical']}) --")
        print(f"  LINKEDIN (paste this):")
        print(f"  {msgs['linkedin_request']}")
        print()
        print(f"  EMAIL SUBJECT: {msgs['cold_email'].split(chr(10))[0].replace('Subject: ', '')}")
        print(f"  {'-'*50}")
        print()


def _cli_queue(args, pipe: Pipeline, gen: MessageGenerator, engine: SalesEngine) -> None:
    date_str = args.date or date.today().isoformat()
    queue = pipe.daily_queue(date_str)
    if not queue:
        print(f"  No actions due for {date}.")
        print("  Tip: Add prospects and they'll auto-schedule.")
        return

    print(f"\n  === DAILY ACTION QUEUE -- {date_str} ===")
    print(f"  {len(queue)} prospect(s) need action today")
    print()

    for p in queue:
        seq_day = p.get("sequence_day", 0)
        next_action = engine.get_next_action(p["vertical"], seq_day)
        channel = next_action.channel.upper() if next_action else "EMAIL"
        action = next_action.action if next_action else "Follow up"

        msgs = gen.generate(
            name=p["name"],
            company=p["company"],
            title=p.get("title", ""),
            vertical=p["vertical"],
        )

        print(f"  +--- #{p['id']} {p['name']} @ {p['company']} ---")
        print(f"  |  Stage: {p['stage']}  |  Day: {seq_day}")
        print(f"  |  Channel: {channel}  |  Action: {action}")

        if channel == "LINKEDIN":
            print(f"  |")
            print(f"  |  PASTE THIS:")
            print(f"  |  {msgs['linkedin_request']}")
        elif channel == "EMAIL":
            email_key = "cold_email" if seq_day == 0 else f"follow_up_{min(seq_day, 3)}"
            if email_key in msgs:
                subject_line = msgs[email_key].split("\n")[0]
                print(f"  |")
                print(f"  |  {subject_line}")
                if p.get("email"):
                    print(f"  |  To: {p['email']}")

        print(f"  +{'-'*50}")
        print()


def _cli_stats(args, pipe: Pipeline) -> None:
    counts = pipe.count_by_stage()
    if not counts:
        print("  Pipeline is empty. Run 'add' to start.")
        return

    total = sum(counts.values())
    print(f"\n  === PIPELINE STATS ===")
    for stage, count in sorted(counts.items()):
        bar = "#" * count
        print(f"  {stage:<16} {count:>3}  {bar}")
    print(f"  {'-'*28}")
    print(f"  {'TOTAL':<16} {total:>3}")
    print()


def _cli_advance(args, pipe: Pipeline) -> None:
    prospect = pipe.get(args.prospect_id)
    if not prospect:
        print(f"  Prospect #{args.prospect_id} not found.")
        return
    old_stage = prospect["stage"]
    pipe.advance(args.prospect_id, args.stage)
    print(f"  {prospect['name']}: {old_stage} -> {args.stage}")

    # Fire trigger events for automation
    try:
        from aionos.ops.store import OpsStore
        from aionos.ops.triggers import TriggerEngine
        ops = OpsStore()
        triggers = TriggerEngine(ops)
        actions = triggers.fire_event(
            "stage_change",
            prospect_id=args.prospect_id,
            old_stage=old_stage,
            new_stage=args.stage,
        )
        if args.stage == "closed_won":
            actions += triggers.fire_event("deal_closed_won", prospect_id=args.prospect_id)
        elif args.stage == "closed_lost":
            actions += triggers.fire_event("deal_closed_lost", prospect_id=args.prospect_id)
        elif args.stage == "demo_scheduled":
            actions += triggers.fire_event("demo_scheduled", prospect_id=args.prospect_id)
        elif args.stage == "proposal_sent":
            actions += triggers.fire_event("proposal_sent", prospect_id=args.prospect_id)
        for a in actions:
            print(f"    >> Trigger: {a}")
        ops.close()
    except Exception:
        pass


def _cli_history(args, pipe: Pipeline) -> None:
    prospect = pipe.get(args.prospect_id)
    if not prospect:
        print(f"  Prospect #{args.prospect_id} not found.")
        return

    print(f"\n  History for {prospect['name']} @ {prospect['company']}:")
    history = pipe.get_history(args.prospect_id)
    if not history:
        print("  No actions logged yet.")
        return
    for h in history:
        ts = h["timestamp"][:16]
        print(f"  {ts}  [{h.get('channel', ''):>8}]  {h['action']}")


def _cli_stale(args, pipe: Pipeline) -> None:
    days = args.days or 7
    stale = pipe.stale_prospects(days)
    if not stale:
        print(f"  No stale prospects (>{days} days without action).")
        return

    print(f"\n  ⚠ {len(stale)} prospect(s) stale (>{days} days):")
    for p in stale:
        last = p.get("last_action_date", "never")[:10] or "never"
        print(f"  #{p['id']:>3}  {p['name']:<22} {p['company']:<22} last: {last}")


def _cli_export(args, pipe: Pipeline) -> None:
    path = args.filepath or "prospects_export.csv"
    result = pipe.export_csv(path)
    print(f"  Exported to {result}")
    print(f"  Use this CSV with Brevo, Mailchimp, or Google Apps Script for bulk sending.")


def _cli_import(args, pipe: Pipeline) -> None:
    if not os.path.exists(args.filepath):
        print(f"  File not found: {args.filepath}")
        return
    count = pipe.import_csv(args.filepath)
    print(f"  Imported {count} prospects from {args.filepath}")


def _cli_log(args, pipe: Pipeline) -> None:
    prospect = pipe.get(args.prospect_id)
    if not prospect:
        print(f"  Prospect #{args.prospect_id} not found.")
        return
    pipe.log_action(
        args.prospect_id,
        action=args.action,
        channel=args.channel or "",
        message=args.message or "",
    )
    if args.follow_up_days:
        pipe.set_next_action(args.prospect_id, int(args.follow_up_days))
        print(f"  Logged + next follow-up in {args.follow_up_days} days")
    else:
        print(f"  Logged: {args.action}")


def _cli_outreach(args, pipe: Pipeline) -> None:
    """Log an outreach send with tracking tags."""
    learner = SalesLearner()
    oid = learner.record_outreach(
        prospect_id=args.prospect_id,
        template=args.template or "",
        channel=args.channel or "email",
        persona=args.persona or "",
        tier=args.tier or "",
    )
    prospect = pipe.get(args.prospect_id)
    name = prospect["name"] if prospect else f"#{args.prospect_id}"
    print(f"  Outreach #{oid} logged for {name} [{args.channel or 'email'}]")

    # Also log in activity log for funnel tracking
    pipe.log_action(
        args.prospect_id,
        action=f"Sent {args.template or 'outreach'} via {args.channel or 'email'}",
        channel=args.channel or "email",
    )
    learner.close()


def _cli_outcome(args, pipe: Pipeline) -> None:
    """Record outcome of outreach."""
    learner = SalesLearner()
    learner.record_outcome(args.prospect_id, args.outcome)
    prospect = pipe.get(args.prospect_id)
    name = prospect["name"] if prospect else f"#{args.prospect_id}"
    print(f"  Outcome recorded: {name} -> {args.outcome}")

    # Show updated segment weights
    segments = learner.top_segments()
    if segments:
        print(f"\n  Updated segment weights:")
        for s in segments[:5]:
            print(f"    {s['segment']:<30} weight: {s['weight']}  "
                  f"({s['sent']} sent, {s['reply_rate']} reply)")
    learner.close()


def _cli_learn(args, pipe: Pipeline) -> None:
    """Show self-improvement report."""
    learner = SalesLearner()
    print(learner.performance_report())
    learner.close()


def _cli_priority(args, pipe: Pipeline) -> None:
    """Show prioritized prospect list based on learned weights."""
    learner = SalesLearner()
    vertical = args.vertical if args.vertical != "all" else "legal"
    limit = args.limit or 15
    priority = learner.prioritize_prospects(vertical=vertical, limit=limit)

    if not priority:
        print("  No prospects to prioritize.")
        learner.close()
        return

    print(f"\n  === PRIORITIZED OUTREACH LIST ({vertical}) ===")
    print(f"  {'#':>3}  {'ID':>4}  {'Name':<20} {'Company':<25} "
          f"{'Score':>5} {'Priority':>8} {'Persona W':>9} {'Tier W':>6}")
    print(f"  {'-'*3}  {'-'*4}  {'-'*20} {'-'*25} "
          f"{'-'*5} {'-'*8} {'-'*9} {'-'*6}")
    for i, p in enumerate(priority, 1):
        print(
            f"  {i:>3}  {p['id']:>4}  {p['name']:<20.20} {p['company']:<25.25} "
            f"{p.get('lead_score', 0):>5} {p['priority']:>8} "
            f"{p.get('persona_weight', 1.0):>9.2f} {p.get('tier_weight', 1.0):>6.2f}"
        )
    print(f"\n  Showing top {len(priority)} of {vertical} prospects")
    print(f"  Weights adjust after 5+ outreaches per segment")
    learner.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m aionos.sales.cli",
        description="AION OS Sales Automation Engine",
    )
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="Add a prospect")
    p_add.add_argument("name")
    p_add.add_argument("company")
    p_add.add_argument("vertical", choices=["legal", "healthcare", "realestate"])
    p_add.add_argument("--title", default="")
    p_add.add_argument("--email", default="")
    p_add.add_argument("--linkedin", default="")
    p_add.add_argument("--phone", default="")
    p_add.add_argument("--notes", default="")
    p_add.add_argument("--source", default="manual")

    # list
    p_list = sub.add_parser("list", help="List prospects")
    p_list.add_argument("--vertical", default="all")
    p_list.add_argument("--stage", default="all")

    # generate
    p_gen = sub.add_parser("generate", help="Generate messages for a prospect")
    p_gen.add_argument("prospect_id", type=int)

    # batch
    p_batch = sub.add_parser("batch", help="Batch generate for cold prospects")
    p_batch.add_argument("vertical", nargs="?", default="all")
    p_batch.add_argument("--limit", type=int, default=10)

    # queue
    p_queue = sub.add_parser("queue", help="View daily action queue")
    p_queue.add_argument("--date", default=None)

    # stats
    sub.add_parser("stats", help="Pipeline statistics")

    # advance
    p_adv = sub.add_parser("advance", help="Move prospect to new stage")
    p_adv.add_argument("prospect_id", type=int)
    p_adv.add_argument("stage", choices=[
        "cold", "engaged", "demo_scheduled", "demo_completed",
        "proposal_sent", "negotiation", "closed_won", "closed_lost",
    ])

    # history
    p_hist = sub.add_parser("history", help="View prospect action history")
    p_hist.add_argument("prospect_id", type=int)

    # stale
    p_stale = sub.add_parser("stale", help="Find prospects with no recent action")
    p_stale.add_argument("--days", type=int, default=7)

    # export
    p_export = sub.add_parser("export", help="Export prospects to CSV")
    p_export.add_argument("filepath", nargs="?", default="prospects_export.csv")

    # import
    p_import = sub.add_parser("import", help="Import prospects from CSV")
    p_import.add_argument("filepath")

    # log
    p_log = sub.add_parser("log", help="Log an action against a prospect")
    p_log.add_argument("prospect_id", type=int)
    p_log.add_argument("action")
    p_log.add_argument("--channel", default="")
    p_log.add_argument("--message", default="")
    p_log.add_argument("--follow-up-days", dest="follow_up_days", default=None)

    # funnel
    p_funnel = sub.add_parser("funnel", help="Funnel report (scoring + health)")

    # outreach — log a tracked outreach send
    p_outreach = sub.add_parser("outreach", help="Log tracked outreach (for self-improvement)")
    p_outreach.add_argument("prospect_id", type=int)
    p_outreach.add_argument("--template", default="")
    p_outreach.add_argument("--channel", default="email")
    p_outreach.add_argument("--persona", default="")
    p_outreach.add_argument("--tier", default="")

    # outcome — record what happened
    p_outcome = sub.add_parser("outcome", help="Record outreach outcome")
    p_outcome.add_argument("prospect_id", type=int)
    p_outcome.add_argument("outcome", choices=[
        "replied", "no_reply", "bounced", "unsubscribed", "objection",
        "meeting_booked", "demo_completed", "proposal_sent",
        "closed_won", "closed_lost",
    ])

    # learn — self-improvement report
    sub.add_parser("learn", help="Self-improvement report (what's working)")

    # priority — weighted prospect ranking
    p_priority = sub.add_parser("priority", help="Prioritized outreach list")
    p_priority.add_argument("--vertical", default="legal")
    p_priority.add_argument("--limit", type=int, default=15)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    engine = SalesEngine()
    pipe = Pipeline()
    gen = MessageGenerator(engine)

    try:
        if args.command == "add":
            _cli_add(args, pipe)
        elif args.command == "list":
            _cli_list(args, pipe)
        elif args.command == "generate":
            _cli_generate(args, pipe, gen)
        elif args.command == "batch":
            _cli_batch(args, pipe, gen)
        elif args.command == "queue":
            _cli_queue(args, pipe, gen, engine)
        elif args.command == "stats":
            _cli_stats(args, pipe)
        elif args.command == "advance":
            _cli_advance(args, pipe)
        elif args.command == "history":
            _cli_history(args, pipe)
        elif args.command == "stale":
            _cli_stale(args, pipe)
        elif args.command == "export":
            _cli_export(args, pipe)
        elif args.command == "import":
            _cli_import(args, pipe)
        elif args.command == "log":
            _cli_log(args, pipe)
        elif args.command == "funnel":
            from aionos.sales.funnel import FunnelEngine
            engine_f = FunnelEngine(pipe)
            print(engine_f.funnel_report())
        elif args.command == "outreach":
            _cli_outreach(args, pipe)
        elif args.command == "outcome":
            _cli_outcome(args, pipe)
        elif args.command == "learn":
            _cli_learn(args, pipe)
        elif args.command == "priority":
            _cli_priority(args, pipe)
    finally:
        pipe.close()


if __name__ == "__main__":
    main()
