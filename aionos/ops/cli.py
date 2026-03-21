"""
EchoWorks Ops Engine -- CLI
==============================
Command-line interface for the full operations system:
  - Memos:     create, list, show, update, activate, archive
  - Playbooks: create, list, show, step, reset
  - Metrics:   record, list, trend
  - Reviews:   generate, show, history
  - Daily:     run daily ops report

Usage:
    python -m aionos.ops.cli daily
    python -m aionos.ops.cli memo create "Title" --category sales --issue "..."
    python -m aionos.ops.cli memo list
    python -m aionos.ops.cli memo show 1
    python -m aionos.ops.cli playbook create "Client Onboarding" --steps 5
    python -m aionos.ops.cli playbook step 1 2 --notes "Done"
    python -m aionos.ops.cli metric record "emails_sent" 10 --target 20
    python -m aionos.ops.cli review generate
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from aionos.ops.store import OpsStore, _get_current_week
from aionos.ops.runner import OpsRunner
from aionos.ops.learner import EvolutionEngine
from aionos.ops.briefing import Briefing
from aionos.ops.notify import notify_brief_ready
from aionos.ops.triggers import TriggerEngine
from aionos.ops.templates import TemplateLibrary
from aionos.ops import scheduler as sched


# ================================================================
#  MEMO COMMANDS
# ================================================================

def _memo_create(args, ops: OpsStore) -> None:
    steps = []
    if args.next_steps:
        for i, s in enumerate(args.next_steps.split(";"), 1):
            steps.append({"step_num": i, "description": s.strip(), "done": False})

    review = ""
    if args.review_days:
        review = (date.today() + timedelta(days=int(args.review_days))).isoformat()

    mid = ops.create_memo(
        title=args.title,
        category=args.category,
        issue=args.issue or "",
        strategy=args.strategy or "",
        tradeoffs=args.tradeoffs or "",
        metrics=args.metrics or "",
        next_steps=steps,
        review_date=review,
    )
    print(f"  Created memo #{mid}: {args.title} [{args.category}]")
    if review:
        print(f"  Review scheduled: {review}")


def _memo_list(args, ops: OpsStore) -> None:
    memos = ops.list_memos(
        category=args.category if args.category != "all" else None,
        status=args.status if args.status != "all" else None,
    )
    if not memos:
        print("  No memos found.")
        return

    print(f"\n  {'ID':>4}  {'Title':<35} {'Category':<12} {'Status':<10} {'Review':<12}")
    print(f"  {'-'*4}  {'-'*35} {'-'*12} {'-'*10} {'-'*12}")
    for m in memos:
        review = m.get("review_date", "")[:10] or "-"
        print(
            f"  {m['id']:>4}  {m['title']:<35.35} "
            f"{m['category']:<12} {m['status']:<10} {review:<12}"
        )
    print(f"\n  Total: {len(memos)}")


def _memo_show(args, ops: OpsStore) -> None:
    m = ops.get_memo(args.memo_id)
    if not m:
        print(f"  Memo #{args.memo_id} not found.")
        return

    print(f"\n  {'=' * 60}")
    print(f"  MEMO #{m['id']}: {m['title']}")
    print(f"  Category: {m['category']}  |  Status: {m['status']}")
    if m.get("review_date"):
        print(f"  Review by: {m['review_date'][:10]}")
    print(f"  {'=' * 60}\n")

    sections = [
        ("ISSUE (what problem?)", m.get("issue", "")),
        ("STRATEGY (how?)", m.get("strategy", "")),
        ("TRADE-OFFS (what NOT doing?)", m.get("tradeoffs", "")),
        ("SUCCESS METRICS", m.get("metrics", "")),
    ]
    for label, content in sections:
        if content:
            print(f"  --- {label} ---")
            for line in content.split("\n"):
                print(f"  {line}")
            print()

    steps = m.get("next_steps", [])
    if steps:
        print(f"  --- NEXT STEPS ---")
        for s in steps:
            check = "[x]" if s.get("done") else "[ ]"
            desc = s.get("description", "")
            print(f"  {check} {desc}")
        print()

    print(f"  Created: {m['created'][:16]}  |  Updated: {m['updated'][:16]}")


def _memo_update(args, ops: OpsStore) -> None:
    fields = {}
    if args.title:
        fields["title"] = args.title
    if args.issue:
        fields["issue"] = args.issue
    if args.strategy:
        fields["strategy"] = args.strategy
    if args.tradeoffs:
        fields["tradeoffs"] = args.tradeoffs
    if args.metrics:
        fields["metrics"] = args.metrics
    if args.review_days:
        fields["review_date"] = (
            date.today() + timedelta(days=int(args.review_days))
        ).isoformat()
    if not fields:
        print("  No fields to update. Use --title, --issue, --strategy, etc.")
        return
    ops.update_memo(args.memo_id, **fields)
    print(f"  Updated memo #{args.memo_id}")


def _memo_activate(args, ops: OpsStore) -> None:
    ops.activate_memo(args.memo_id)
    print(f"  Memo #{args.memo_id} activated")


def _memo_archive(args, ops: OpsStore) -> None:
    ops.archive_memo(args.memo_id)
    print(f"  Memo #{args.memo_id} archived")


# ================================================================
#  PLAYBOOK COMMANDS
# ================================================================

def _playbook_create(args, ops: OpsStore) -> None:
    steps = []
    if args.steps_text:
        for i, s in enumerate(args.steps_text.split(";"), 1):
            steps.append({
                "step_num": i,
                "action": s.strip(),
                "status": "not_started",
                "completed_date": "",
                "notes": "",
            })
    elif args.num_steps:
        for i in range(1, int(args.num_steps) + 1):
            steps.append({
                "step_num": i,
                "action": f"Step {i}",
                "status": "not_started",
                "completed_date": "",
                "notes": "",
            })

    pid = ops.create_playbook(
        name=args.name,
        category=args.category,
        description=args.description or "",
        trigger=args.trigger or "",
        steps=steps,
        owner=args.owner or "",
    )
    print(f"  Created playbook #{pid}: {args.name} [{args.category}]")
    print(f"  {len(steps)} steps defined")


def _playbook_list(args, ops: OpsStore) -> None:
    playbooks = ops.list_playbooks(
        category=args.category if args.category != "all" else None,
        status=args.status if args.status != "all" else None,
    )
    if not playbooks:
        print("  No playbooks found.")
        return

    print(f"\n  {'ID':>4}  {'Name':<30} {'Category':<12} {'Status':<14} {'Steps':<8} {'Runs':<5}")
    print(f"  {'-'*4}  {'-'*30} {'-'*12} {'-'*14} {'-'*8} {'-'*5}")
    for pb in playbooks:
        steps = pb.get("steps", [])
        done = sum(1 for s in steps if s.get("status") == "completed")
        total = len(steps)
        print(
            f"  {pb['id']:>4}  {pb['name']:<30.30} "
            f"{pb['category']:<12} {pb['status']:<14} "
            f"{done}/{total:<5} {pb.get('run_count', 0):<5}"
        )
    print(f"\n  Total: {len(playbooks)}")


def _playbook_show(args, ops: OpsStore) -> None:
    pb = ops.get_playbook(args.playbook_id)
    if not pb:
        print(f"  Playbook #{args.playbook_id} not found.")
        return

    print(f"\n  {'=' * 60}")
    print(f"  PLAYBOOK #{pb['id']}: {pb['name']}")
    print(f"  Category: {pb['category']}  |  Status: {pb['status']}")
    if pb.get("trigger"):
        print(f"  Trigger: {pb['trigger']}")
    if pb.get("description"):
        print(f"  {pb['description']}")
    print(f"  Runs: {pb.get('run_count', 0)}  |  Last run: {pb.get('last_run', 'never')[:10] or 'never'}")
    print(f"  {'=' * 60}\n")

    steps = pb.get("steps", [])
    for s in steps:
        status = s.get("status", "not_started")
        if status == "completed":
            icon = "[x]"
        elif status == "in_progress":
            icon = "[>]"
        else:
            icon = "[ ]"
        action = s.get("action", "")
        notes = f"  ({s['notes']})" if s.get("notes") else ""
        print(f"  {icon} Step {s['step_num']}: {action}{notes}")
    print()


def _playbook_step(args, ops: OpsStore) -> None:
    ops.complete_step(args.playbook_id, args.step_num, notes=args.notes or "")
    print(f"  Playbook #{args.playbook_id}, Step {args.step_num}: completed")


def _playbook_reset(args, ops: OpsStore) -> None:
    ops.reset_playbook(args.playbook_id)
    print(f"  Playbook #{args.playbook_id} reset for re-execution")


# ================================================================
#  METRIC COMMANDS
# ================================================================

def _metric_record(args, ops: OpsStore) -> None:
    mid = ops.record_metric(
        name=args.name,
        value=float(args.value),
        metric_type=args.type,
        category=args.category,
        target=float(args.target) if args.target else 0.0,
        period=args.period or "",
        notes=args.notes or "",
    )
    print(f"  Recorded: {args.name} = {args.value} [{args.type}]")


def _metric_list(args, ops: OpsStore) -> None:
    metrics = ops.get_metrics(
        name=args.name if args.name != "all" else None,
        category=args.category if args.category != "all" else None,
        period=args.period,
    )
    if not metrics:
        print("  No metrics found.")
        return

    print(f"\n  {'Name':<28} {'Value':>10} {'Target':>10} {'Period':<10} {'Category':<10}")
    print(f"  {'-'*28} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for m in metrics[:20]:
        print(
            f"  {m['name']:<28.28} {m['value']:>10.1f} "
            f"{m['target']:>10.1f} {m['period']:<10} {m['category']:<10}"
        )
    print(f"\n  Showing {min(len(metrics), 20)} of {len(metrics)}")


def _metric_trend(args, ops: OpsStore) -> None:
    points = ops.metric_trend(args.name, last_n=args.last or 8)
    if not points:
        print(f"  No data for '{args.name}'.")
        return

    print(f"\n  Trend: {args.name}")
    print(f"  {'-'*40}")
    max_val = max(p["value"] for p in points) or 1
    for p in points:
        bar_len = int(p["value"] / max_val * 30)
        bar = "#" * bar_len
        print(f"  {p['period']:<12} {p['value']:>8.1f}  {bar}")
    print()


# ================================================================
#  REVIEW COMMANDS
# ================================================================

def _review_generate(args, ops: OpsStore) -> None:
    runner = OpsRunner(ops)
    review = runner.generate_weekly_review()
    print(review)


def _review_show(args, ops: OpsStore) -> None:
    review = ops.get_review(args.week)
    if not review:
        week = args.week or _get_current_week()
        print(f"  No review for {week}. Run: python -m aionos.ops.cli review generate")
        return

    print(f"\n  {'=' * 60}")
    print(f"  WEEKLY REVIEW -- {review['week']}")
    print(f"  {'=' * 60}\n")

    if review.get("pipeline_summary"):
        print(review["pipeline_summary"])
        print()
    if review.get("metrics_summary"):
        print(review["metrics_summary"])
        print()
    if review.get("wins"):
        print(f"  --- WINS ---")
        print(f"  {review['wins']}")
        print()
    if review.get("blockers"):
        print(f"  --- BLOCKERS ---")
        print(f"  {review['blockers']}")
        print()
    if review.get("next_week_priorities"):
        print(f"  --- NEXT WEEK ---")
        print(f"  {review['next_week_priorities']}")
        print()


def _review_history(args, ops: OpsStore) -> None:
    reviews = ops.list_reviews(last_n=args.last or 8)
    if not reviews:
        print("  No reviews yet.")
        return

    print(f"\n  {'Week':<12} {'Created':<20}")
    print(f"  {'-'*12} {'-'*20}")
    for r in reviews:
        print(f"  {r['week']:<12} {r['created'][:16]:<20}")
    print()


# ================================================================
#  LEARN / EVOLUTION COMMANDS
# ================================================================

def _learn_full(args, ops: OpsStore) -> None:
    engine = EvolutionEngine(ops)
    report = engine.run_full_cycle()
    print(report)


def _learn_deals(args, ops: OpsStore) -> None:
    engine = EvolutionEngine(ops)
    print(engine.analyze_deals())
    print()
    print(engine.format_insights())


def _learn_playbooks(args, ops: OpsStore) -> None:
    engine = EvolutionEngine(ops)
    print(engine.analyze_playbooks())
    print()
    print(engine.format_insights())


def _learn_velocity(args, ops: OpsStore) -> None:
    engine = EvolutionEngine(ops)
    print(engine.analyze_velocity())
    print()
    print(engine.format_insights())


def _learn_insights(args, ops: OpsStore) -> None:
    """Show the latest evolution memo."""
    memos = ops.list_memos(category="operations", status="active")
    evolution_memos = [m for m in memos if "Evolution" in m.get("title", "")]
    if not evolution_memos:
        print("  No evolution insights yet. Run: python -m aionos.ops.cli learn")
        return
    # Show the latest
    m = evolution_memos[0]
    print(f"\n  {'=' * 60}")
    print(f"  {m['title']}")
    print(f"  {'=' * 60}\n")
    if m.get("issue"):
        print("  --- INSIGHTS ---")
        for line in m["issue"].split("\n"):
            print(f"  {line}")
        print()
    if m.get("strategy"):
        print("  --- RECOMMENDATIONS ---")
        for line in m["strategy"].split("\n"):
            print(f"  {line}")
        print()


# ================================================================
#  BRIEF COMMAND
# ================================================================

def _brief(args, ops: OpsStore) -> None:
    brief = Briefing(ops)
    result = brief.generate()
    print(result["text"])

    if args.save:
        path = brief.save()
        print(f"\n  Saved: {path}")

    if args.notify:
        sent = notify_brief_ready(result["summary"], result["urgency"])
        if sent:
            print("  Notification sent.")


# ================================================================
#  SCHEDULE COMMAND
# ================================================================

def _schedule(args, ops: OpsStore) -> None:
    cmd = args.sched_cmd
    if cmd == "install":
        time = args.time if hasattr(args, "time") and args.time else "08:30"
        sched.install(time)
    elif cmd == "uninstall":
        sched.uninstall()
    elif cmd == "status":
        sched.print_status()
    else:
        print("  Usage: schedule install | uninstall | status")


# ================================================================
#  TRIGGER COMMANDS
# ================================================================

def _trigger_list(args, ops: OpsStore) -> None:
    triggers = TriggerEngine(ops)
    show_all = hasattr(args, "all") and args.all
    rules = triggers.list_rules(enabled_only=not show_all)
    if not rules:
        print("  No trigger rules configured.")
        print("  Run: python -m aionos.ops.seed  (to seed defaults)")
        return

    print(f"\n  {'ID':>4}  {'Name':<30} {'Type':<8} {'Event':<18} {'PB':>3}  {'Enabled':<8}")
    print(f"  {'-'*4}  {'-'*30} {'-'*8} {'-'*18} {'-'*3}  {'-'*8}")
    for r in rules:
        enabled = "yes" if r["enabled"] else "no"
        pb = str(r["playbook_id"]) if r["playbook_id"] else "-"
        print(
            f"  {r['id']:>4}  {r['name']:<30.30} {r['trigger_type']:<8} "
            f"{r['event_type']:<18.18} {pb:>3}  {enabled:<8}"
        )
    print(f"\n  Total: {len(rules)}")


def _trigger_add(args, ops: OpsStore) -> None:
    triggers = TriggerEngine(ops)
    rule_id = triggers.add_rule(
        name=args.name,
        trigger_type=args.type,
        event_type=args.event or "",
        condition=args.condition or "",
        playbook_id=int(args.playbook) if args.playbook else None,
        action=args.action or "",
    )
    print(f"  Created trigger rule #{rule_id}: {args.name}")


def _trigger_enable(args, ops: OpsStore) -> None:
    triggers = TriggerEngine(ops)
    triggers.enable_rule(args.rule_id)
    print(f"  Enabled trigger rule #{args.rule_id}")


def _trigger_disable(args, ops: OpsStore) -> None:
    triggers = TriggerEngine(ops)
    triggers.disable_rule(args.rule_id)
    print(f"  Disabled trigger rule #{args.rule_id}")


def _trigger_fire(args, ops: OpsStore) -> None:
    triggers = TriggerEngine(ops)
    actions = triggers.fire_event(args.event_type)
    if actions:
        print(f"  Fired event '{args.event_type}' -- {len(actions)} action(s):")
        for a in actions:
            print(f"    >> {a}")
    else:
        print(f"  Fired event '{args.event_type}' -- no matching rules.")


def _trigger_check(args, ops: OpsStore) -> None:
    triggers = TriggerEngine(ops)
    result = triggers.check_all()
    print(result)


def _trigger_log(args, ops: OpsStore) -> None:
    triggers = TriggerEngine(ops)
    limit = args.limit if hasattr(args, "limit") else 20
    log = triggers.recent_log(limit=limit)
    if not log:
        print("  No trigger activity logged yet.")
        return

    print(f"\n  {'Timestamp':<20} {'Rule':<25} {'Event':<18} {'Action':<30}")
    print(f"  {'-'*20} {'-'*25} {'-'*18} {'-'*30}")
    for entry in log:
        ts = entry["timestamp"][:19].replace("T", " ")
        print(
            f"  {ts:<20} {entry.get('rule_name', '?'):<25.25} "
            f"{entry['event_type']:<18.18} {entry['action_taken']:<30.30}"
        )


# ================================================================
#  FUNNEL COMMANDS
# ================================================================

def _funnel_report(args, ops: OpsStore) -> None:
    from aionos.sales.funnel import FunnelEngine
    engine = FunnelEngine()
    print(engine.funnel_report())


def _funnel_score(args, ops: OpsStore) -> None:
    from aionos.sales.funnel import FunnelEngine
    engine = FunnelEngine()
    scored = engine.score_all()
    if not scored:
        print("  No active prospects to score.")
        return

    print(f"\n  {'ID':>4}  {'Name':<22} {'Company':<22} {'Stage':<16} {'Score':>5}")
    print(f"  {'-'*4}  {'-'*22} {'-'*22} {'-'*16} {'-'*5}")
    for p in scored:
        print(
            f"  {p['id']:>4}  {p['name']:<22.22} {p['company']:<22.22} "
            f"{p['stage']:<16} {p['lead_score']:>5}"
        )
    print(f"\n  Scored: {len(scored)} prospects")


def _funnel_health(args, ops: OpsStore) -> None:
    from aionos.sales.funnel import FunnelEngine, DealHealth
    engine = FunnelEngine()
    results = engine.health_check()

    for status in [DealHealth.HEALTHY, DealHealth.AT_RISK, DealHealth.STUCK, DealHealth.DEAD]:
        icon = {"healthy": "[OK]", "at_risk": "[!!]", "stuck": "[XX]", "dead": "[--]"}[status]
        deals = results[status]
        if deals:
            print(f"\n  {icon} {status.upper()} ({len(deals)})")
            for p in deals:
                print(f"    #{p['id']:>3} {p['name']:<20} {p['company']:<20} {p['health_reason']}")

    total = sum(len(v) for v in results.values())
    if total == 0:
        print("  No active deals to assess.")


def _funnel_advance(args, ops: OpsStore) -> None:
    from aionos.sales.funnel import FunnelEngine
    engine = FunnelEngine()
    actions = engine.auto_advance()
    if actions:
        print(f"  Auto-advanced {len(actions)} deal(s):")
        for a in actions:
            print(f"    >> {a}")

        # Fire stage_change events for trigger integration
        triggers = TriggerEngine(ops)
        for a in actions:
            # Parse "Auto-advanced #X Name (Company): old -> new"
            if "->" in a:
                new_stage = a.split("->")[-1].strip()
                triggers.fire_event("stage_change", new_stage=new_stage)
                if new_stage == "closed_won":
                    triggers.fire_event("deal_closed_won")
    else:
        print("  No deals qualified for auto-advance.")


# ================================================================
#  TEMPLATE COMMANDS
# ================================================================

def _template_list(args, ops: OpsStore) -> None:
    lib = TemplateLibrary()
    category = args.category if hasattr(args, "category") and args.category != "all" else None
    templates = lib.list_templates(category=category)

    if not templates:
        print("  No templates found.")
        return

    print(f"\n  {'Key':<30} {'Name':<30} {'Cat':<12} {'Steps':>5}")
    print(f"  {'-'*30} {'-'*30} {'-'*12} {'-'*5}")
    for t in templates:
        print(f"  {t['key']:<30} {t['name']:<30.30} {t['category']:<12} {t['steps']:>5}")
    print(f"\n  Total: {len(templates)}")
    print("  Use: python -m aionos.ops.cli template create <key>")


def _template_show(args, ops: OpsStore) -> None:
    lib = TemplateLibrary()
    tmpl = lib.get_template(args.key)
    if not tmpl:
        print(f"  Template '{args.key}' not found.")
        print("  Run: python -m aionos.ops.cli template list")
        return

    print(f"\n  {'=' * 60}")
    print(f"  TEMPLATE: {tmpl['name']}")
    print(f"  Category: {tmpl['category']}")
    print(f"  Trigger: {tmpl['trigger']}")
    print(f"  {'=' * 60}")
    print(f"\n  {tmpl['description']}\n")
    for i, step in enumerate(tmpl["steps"], 1):
        print(f"  {i:>2}. {step}")
    print()


def _template_create(args, ops: OpsStore) -> None:
    lib = TemplateLibrary()
    name_override = args.name if hasattr(args, "name") and args.name else None
    pb_id = lib.create_from_template(args.key, ops, name_override=name_override)
    if pb_id:
        pb = ops.get_playbook(pb_id)
        print(f"  Created playbook #{pb_id}: {pb['name']} [{pb['category']}]")
        print(f"  Steps: {len(pb.get('steps', []))}")
    else:
        print(f"  Template '{args.key}' not found.")
        print("  Run: python -m aionos.ops.cli template list")


# ================================================================
#  DAILY COMMAND
# ================================================================

def _daily(args, ops: OpsStore) -> None:
    runner = OpsRunner(ops)
    report = runner.run_daily()
    print(report)


# ================================================================
#  MAIN
# ================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m aionos.ops.cli",
        description="EchoWorks Ops Engine -- Local Operations System",
    )
    sub = parser.add_subparsers(dest="command")

    # daily
    sub.add_parser("daily", help="Run daily ops report")

    # ── memo ──
    memo_parser = sub.add_parser("memo", help="Operational memos")
    memo_sub = memo_parser.add_subparsers(dest="memo_cmd")

    p = memo_sub.add_parser("create", help="Create a memo")
    p.add_argument("title")
    p.add_argument("--category", default="strategy",
                   choices=["sales", "product", "threat_engine", "legal",
                            "operations", "hiring", "finance", "strategy"])
    p.add_argument("--issue", default="")
    p.add_argument("--strategy", default="")
    p.add_argument("--tradeoffs", default="")
    p.add_argument("--metrics", default="")
    p.add_argument("--next-steps", dest="next_steps", default="",
                   help="Semicolon-separated steps")
    p.add_argument("--review-days", dest="review_days", default=None,
                   help="Days until review")

    p = memo_sub.add_parser("list", help="List memos")
    p.add_argument("--category", default="all")
    p.add_argument("--status", default="all")

    p = memo_sub.add_parser("show", help="Show memo details")
    p.add_argument("memo_id", type=int)

    p = memo_sub.add_parser("update", help="Update a memo")
    p.add_argument("memo_id", type=int)
    p.add_argument("--title", default=None)
    p.add_argument("--issue", default=None)
    p.add_argument("--strategy", default=None)
    p.add_argument("--tradeoffs", default=None)
    p.add_argument("--metrics", default=None)
    p.add_argument("--review-days", dest="review_days", default=None)

    p = memo_sub.add_parser("activate", help="Activate a memo")
    p.add_argument("memo_id", type=int)

    p = memo_sub.add_parser("archive", help="Archive a memo")
    p.add_argument("memo_id", type=int)

    # ── playbook ──
    pb_parser = sub.add_parser("playbook", help="Executable playbooks")
    pb_sub = pb_parser.add_subparsers(dest="pb_cmd")

    p = pb_sub.add_parser("create", help="Create a playbook")
    p.add_argument("name")
    p.add_argument("--category", default="operations")
    p.add_argument("--description", default="")
    p.add_argument("--trigger", default="")
    p.add_argument("--steps", dest="steps_text", default="",
                   help="Semicolon-separated step actions")
    p.add_argument("--num-steps", dest="num_steps", default=None)
    p.add_argument("--owner", default="")

    p = pb_sub.add_parser("list", help="List playbooks")
    p.add_argument("--category", default="all")
    p.add_argument("--status", default="all")

    p = pb_sub.add_parser("show", help="Show playbook details")
    p.add_argument("playbook_id", type=int)

    p = pb_sub.add_parser("step", help="Complete a playbook step")
    p.add_argument("playbook_id", type=int)
    p.add_argument("step_num", type=int)
    p.add_argument("--notes", default="")

    p = pb_sub.add_parser("reset", help="Reset playbook for re-run")
    p.add_argument("playbook_id", type=int)

    # ── metric ──
    met_parser = sub.add_parser("metric", help="KPI metrics")
    met_sub = met_parser.add_subparsers(dest="met_cmd")

    p = met_sub.add_parser("record", help="Record a metric")
    p.add_argument("name")
    p.add_argument("value")
    p.add_argument("--type", default="count",
                   choices=["count", "currency", "percent", "duration"])
    p.add_argument("--category", default="sales")
    p.add_argument("--target", default=None)
    p.add_argument("--period", default="")
    p.add_argument("--notes", default="")

    p = met_sub.add_parser("list", help="List metrics")
    p.add_argument("--name", default="all")
    p.add_argument("--category", default="all")
    p.add_argument("--period", default=None)

    p = met_sub.add_parser("trend", help="View metric trend")
    p.add_argument("name")
    p.add_argument("--last", type=int, default=8)

    # ── learn / evolution ──
    learn_parser = sub.add_parser("learn", help="AION OS evolution -- self-improvement engine")
    learn_sub = learn_parser.add_subparsers(dest="learn_cmd")

    learn_sub.add_parser("deals", help="Analyze closed deals for patterns")
    learn_sub.add_parser("playbooks", help="Analyze playbook efficiency")
    learn_sub.add_parser("velocity", help="Pipeline velocity analysis")
    learn_sub.add_parser("insights", help="View stored evolution insights")

    # ── brief ──
    brief_parser = sub.add_parser("brief", help="Daily executive briefing")
    brief_parser.add_argument("--save", action="store_true",
                              help="Save briefing to file")
    brief_parser.add_argument("--notify", action="store_true",
                              help="Send Windows notification")

    # ── schedule ──
    sched_parser = sub.add_parser("schedule", help="AION OS task scheduler")
    sched_sub = sched_parser.add_subparsers(dest="sched_cmd")

    p = sched_sub.add_parser("install", help="Install daily scheduled task")
    p.add_argument("--time", default="08:30",
                   help="Time to run (HH:MM), default 08:30")

    sched_sub.add_parser("uninstall", help="Remove scheduled task")
    sched_sub.add_parser("status", help="Check scheduler status")

    # ── review ──
    rev_parser = sub.add_parser("review", help="Weekly reviews")
    rev_sub = rev_parser.add_subparsers(dest="rev_cmd")

    rev_sub.add_parser("generate", help="Generate weekly review")

    p = rev_sub.add_parser("show", help="Show a weekly review")
    p.add_argument("week", nargs="?", default=None)

    p = rev_sub.add_parser("history", help="Review history")
    p.add_argument("--last", type=int, default=8)

    # ── trigger ──
    trig_parser = sub.add_parser("trigger", help="Event/time/metric triggers")
    trig_sub = trig_parser.add_subparsers(dest="trig_cmd")

    p = trig_sub.add_parser("list", help="List trigger rules")
    p.add_argument("--all", action="store_true", help="Show disabled rules too")

    p = trig_sub.add_parser("add", help="Add a trigger rule")
    p.add_argument("name")
    p.add_argument("--type", default="event", choices=["event", "time", "metric"])
    p.add_argument("--event", default="")
    p.add_argument("--condition", default="")
    p.add_argument("--playbook", default=None, help="Playbook ID to start")
    p.add_argument("--action", default="")

    p = trig_sub.add_parser("enable", help="Enable a trigger rule")
    p.add_argument("rule_id", type=int)

    p = trig_sub.add_parser("disable", help="Disable a trigger rule")
    p.add_argument("rule_id", type=int)

    p = trig_sub.add_parser("fire", help="Manually fire an event")
    p.add_argument("event_type")

    trig_sub.add_parser("check", help="Run all trigger checks now")

    p = trig_sub.add_parser("log", help="View trigger execution log")
    p.add_argument("--limit", type=int, default=20)

    # ── funnel ──
    fun_parser = sub.add_parser("funnel", help="Sales funnel intelligence")
    fun_sub = fun_parser.add_subparsers(dest="fun_cmd")

    fun_sub.add_parser("report", help="Full funnel analytics report")
    fun_sub.add_parser("score", help="Lead scoring for all prospects")
    fun_sub.add_parser("health", help="Deal health check")
    fun_sub.add_parser("advance", help="Auto-advance deals based on signals")

    # ── template ──
    tmpl_parser = sub.add_parser("template", help="Playbook template library")
    tmpl_sub = tmpl_parser.add_subparsers(dest="tmpl_cmd")

    p = tmpl_sub.add_parser("list", help="List available templates")
    p.add_argument("--category", default="all")

    p = tmpl_sub.add_parser("show", help="Show template details")
    p.add_argument("key")

    p = tmpl_sub.add_parser("create", help="Create playbook from template")
    p.add_argument("key")
    p.add_argument("--name", default=None, help="Override playbook name")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    ops = OpsStore()

    try:
        if args.command == "daily":
            _daily(args, ops)
        elif args.command == "memo":
            cmd = args.memo_cmd
            if cmd == "create":
                _memo_create(args, ops)
            elif cmd == "list":
                _memo_list(args, ops)
            elif cmd == "show":
                _memo_show(args, ops)
            elif cmd == "update":
                _memo_update(args, ops)
            elif cmd == "activate":
                _memo_activate(args, ops)
            elif cmd == "archive":
                _memo_archive(args, ops)
            else:
                memo_parser.print_help()
        elif args.command == "playbook":
            cmd = args.pb_cmd
            if cmd == "create":
                _playbook_create(args, ops)
            elif cmd == "list":
                _playbook_list(args, ops)
            elif cmd == "show":
                _playbook_show(args, ops)
            elif cmd == "step":
                _playbook_step(args, ops)
            elif cmd == "reset":
                _playbook_reset(args, ops)
            else:
                pb_parser.print_help()
        elif args.command == "metric":
            cmd = args.met_cmd
            if cmd == "record":
                _metric_record(args, ops)
            elif cmd == "list":
                _metric_list(args, ops)
            elif cmd == "trend":
                _metric_trend(args, ops)
            else:
                met_parser.print_help()
        elif args.command == "learn":
            cmd = args.learn_cmd
            if cmd == "deals":
                _learn_deals(args, ops)
            elif cmd == "playbooks":
                _learn_playbooks(args, ops)
            elif cmd == "velocity":
                _learn_velocity(args, ops)
            elif cmd == "insights":
                _learn_insights(args, ops)
            else:
                _learn_full(args, ops)
        elif args.command == "brief":
            _brief(args, ops)
        elif args.command == "schedule":
            _schedule(args, ops)
        elif args.command == "review":
            cmd = args.rev_cmd
            if cmd == "generate":
                _review_generate(args, ops)
            elif cmd == "show":
                _review_show(args, ops)
            elif cmd == "history":
                _review_history(args, ops)
            else:
                rev_parser.print_help()
        elif args.command == "trigger":
            cmd = args.trig_cmd
            if cmd == "list":
                _trigger_list(args, ops)
            elif cmd == "add":
                _trigger_add(args, ops)
            elif cmd == "enable":
                _trigger_enable(args, ops)
            elif cmd == "disable":
                _trigger_disable(args, ops)
            elif cmd == "fire":
                _trigger_fire(args, ops)
            elif cmd == "check":
                _trigger_check(args, ops)
            elif cmd == "log":
                _trigger_log(args, ops)
            else:
                trig_parser.print_help()
        elif args.command == "funnel":
            cmd = args.fun_cmd
            if cmd == "report":
                _funnel_report(args, ops)
            elif cmd == "score":
                _funnel_score(args, ops)
            elif cmd == "health":
                _funnel_health(args, ops)
            elif cmd == "advance":
                _funnel_advance(args, ops)
            else:
                fun_parser.print_help()
        elif args.command == "template":
            cmd = args.tmpl_cmd
            if cmd == "list":
                _template_list(args, ops)
            elif cmd == "show":
                _template_show(args, ops)
            elif cmd == "create":
                _template_create(args, ops)
            else:
                tmpl_parser.print_help()
    finally:
        ops.close()


if __name__ == "__main__":
    main()
