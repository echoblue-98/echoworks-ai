"""
AION OS — Categorical Outreach Console
=========================================
Interactive batch outreach tool organized by category.
Designed for a sales liaison to run daily:

    python -m aionos.sales.outreach

Workflow:
  1. Shows today's follow-up queue
  2. Categorizes cold prospects by vertical + tier
  3. Generates ready-to-paste messages per category
  4. Logs sent outreach and schedules follow-ups
  5. Tracks conversion by category for self-improvement
"""

from __future__ import annotations

import sys
import os
from collections import defaultdict
from datetime import date, datetime, timezone

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from aionos.sales.prospects import Pipeline
from aionos.sales.messages import MessageGenerator
from aionos.sales.learner import SalesLearner
from aionos.sales.funnel import FunnelEngine

# ── Constants ─────────────────────────────────────────────

VERTICALS = {
    "legal": "Law Firms & Legal Services",
    "healthcare": "Healthcare & Compliance",
    "realestate": "Title, Brokerage & Real Estate",
    "creator": "Creator IP — Labels, Studios & Publishers",
}

STAGES_ACTIVE = ("cold", "engaged", "demo_scheduled", "demo_completed",
                 "proposal_sent", "negotiation")

BATCH_SIZE = 10  # Default outreach batch

# ── Category helpers ──────────────────────────────────────

def _tier_label(prospect: dict) -> str:
    """Assign a priority tier based on notes/source."""
    notes = (prospect.get("notes") or "").lower()
    source = (prospect.get("source") or "").lower()
    if any(k in notes for k in ("tier a", "warm", "referral", "dan intro")):
        return "A"
    if any(k in source for k in ("referral", "warm")):
        return "A"
    if any(k in notes for k in ("tier b", "channel partner", "vendor")):
        return "B"
    if any(k in notes for k in ("tier c", "tier d", "national")):
        return "C"
    return "B"  # default mid-tier


def _days_stale(prospect: dict) -> int:
    """Days since last update."""
    updated = prospect.get("updated") or prospect.get("created") or ""
    if not updated:
        return 999
    try:
        dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except (ValueError, TypeError):
        return 999


def _categorize(prospects: list) -> dict:
    """
    Group prospects into outreach categories.
    Returns: {category_key: {label, vertical, stage, prospects: [sorted by tier+stale]}}
    """
    categories = {}
    # Group by vertical + stage bucket
    for p in prospects:
        vert = p.get("vertical", "legal")
        stage = p.get("stage", "cold")
        if stage in ("closed_won", "closed_lost"):
            continue
        if stage == "cold":
            bucket = "new_outreach"
        elif stage == "engaged":
            bucket = "follow_up"
        else:
            bucket = "active_deals"

        key = f"{vert}_{bucket}"
        if key not in categories:
            categories[key] = {
                "label": f"{VERTICALS.get(vert, vert)} — {bucket.replace('_', ' ').title()}",
                "vertical": vert,
                "bucket": bucket,
                "prospects": [],
            }
        categories[key]["prospects"].append(p)

    # Sort each category: tier A first, then by staleness (most stale first for cold)
    tier_order = {"A": 0, "B": 1, "C": 2}
    for cat in categories.values():
        cat["prospects"].sort(
            key=lambda p: (tier_order.get(_tier_label(p), 1), -_days_stale(p))
        )

    return categories


# ── Display helpers ───────────────────────────────────────

def _header(text: str) -> None:
    width = max(len(text) + 4, 50)
    print(f"\n{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}")


def _subheader(text: str) -> None:
    print(f"\n  --- {text} ---")


def _prospect_line(p: dict, idx: int = 0) -> str:
    tier = _tier_label(p)
    stale = _days_stale(p)
    stale_flag = f" ({stale}d stale)" if stale > 3 else ""
    return (
        f"  [{idx:>2}] #{p['id']:<4} {p['name']:<24} "
        f"{p['company']:<26} Tier {tier}{stale_flag}"
    )


# ── Core workflows ────────────────────────────────────────

def show_dashboard(pipe: Pipeline) -> None:
    """Print the full pipeline dashboard."""
    counts = pipe.count_by_stage()
    _header("AION OS  —  Sales Pipeline Dashboard")
    print(f"  Date: {date.today().isoformat()}")
    print()
    total = sum(counts.values())
    print(f"  Total Prospects: {total}")
    print()
    print(f"  {'Stage':<20} {'Count':>6}")
    print(f"  {'-'*20} {'-'*6}")
    for stage in ("cold", "engaged", "demo_scheduled", "demo_completed",
                  "proposal_sent", "negotiation", "closed_won", "closed_lost"):
        ct = counts.get(stage, 0)
        if ct > 0:
            bar = "#" * min(ct, 40)
            print(f"  {stage:<20} {ct:>6}  {bar}")
    print()


def show_follow_ups(pipe: Pipeline) -> list:
    """Show today's follow-up queue. Returns the list."""
    queue = pipe.daily_queue()
    if not queue:
        print("  No follow-ups due today.\n")
        return []

    _subheader(f"FOLLOW-UP QUEUE — {len(queue)} due today")
    for i, p in enumerate(queue, 1):
        next_dt = p.get("next_action_date", "")
        print(
            f"  [{i:>2}] #{p['id']:<4} {p['name']:<24} "
            f"{p['company']:<26} {p['stage']:<16} due: {next_dt}"
        )
    print()
    return list(queue)


def show_categories(pipe: Pipeline) -> dict:
    """Show categorized prospect breakdown. Returns categories dict."""
    all_prospects = pipe.list_all()
    categories = _categorize([dict(p) for p in all_prospects])

    _header("OUTREACH CATEGORIES")
    cat_list = []
    for i, (key, cat) in enumerate(sorted(categories.items()), 1):
        count = len(cat["prospects"])
        print(f"  [{i}] {cat['label']:<45} ({count} prospects)")
        cat_list.append((key, cat))

    print()
    return dict(cat_list) if cat_list else {}


def run_batch(
    pipe: Pipeline,
    gen: MessageGenerator,
    learner: SalesLearner,
    prospects: list,
    vertical: str,
    batch_size: int = BATCH_SIZE,
) -> int:
    """
    Interactive batch outreach for a list of prospects.
    Returns count of messages sent.
    """
    batch = prospects[:batch_size]
    if not batch:
        print("  No prospects in this category.")
        return 0

    sent_count = 0
    _subheader(f"Batch: {len(batch)} prospects — {VERTICALS.get(vertical, vertical)}")
    print()

    for i, p in enumerate(batch, 1):
        pid = p["id"]
        name = p["name"]
        company = p["company"]
        title = p.get("title", "")
        stage = p.get("stage", "cold")

        # Generate message
        try:
            msgs = gen.generate(
                name=name,
                company=company,
                title=title or "Partner",
                vertical=vertical,
            )
            linkedin_msg = msgs.get("linkedin_request", "")
            cold_email = msgs.get("cold_email", "")
        except Exception:
            linkedin_msg = ""
            cold_email = ""

        print(f"  ╔{'═' * 60}")
        print(f"  ║ [{i}/{len(batch)}]  #{pid} — {name}")
        print(f"  ║ {company}  |  {title or 'No title'}  |  Stage: {stage}")
        print(f"  ║ Tier: {_tier_label(p)}  |  Stale: {_days_stale(p)} days")
        print(f"  ╠{'═' * 60}")

        if linkedin_msg:
            # Truncate display for readability
            display = linkedin_msg[:280] + "..." if len(linkedin_msg) > 280 else linkedin_msg
            print(f"  ║ LINKEDIN ({len(linkedin_msg)} chars):")
            for line in display.split("\n"):
                print(f"  ║   {line}")

        print(f"  ╚{'═' * 60}")

        # Prompt
        action = input("  Action — [s]ent  [k]skip  [e]mail  [c]ustom  [q]uit batch: ").strip().lower()

        if action == "q":
            print("  Batch stopped.")
            break
        elif action == "s":
            # Log LinkedIn send
            pipe.log_action(pid, "Sent LinkedIn connection request", channel="linkedin")
            learner.record_outreach(pid, template=f"{vertical}_linkedin", channel="linkedin")
            if stage == "cold":
                pipe.set_next_action(pid, 3)
            sent_count += 1
            print(f"  >> Logged: LinkedIn sent for #{pid} {name}")
        elif action == "e":
            # Log email send
            pipe.log_action(pid, "Sent cold email", channel="email")
            learner.record_outreach(pid, template=f"{vertical}_cold_email", channel="email")
            if stage == "cold":
                pipe.set_next_action(pid, 3)
            sent_count += 1
            print(f"  >> Logged: Email sent for #{pid} {name}")
        elif action == "c":
            channel = input("  Channel [linkedin/email/phone/other]: ").strip() or "linkedin"
            note = input("  Note (optional): ").strip()
            action_text = f"Custom outreach: {note}" if note else "Custom outreach sent"
            pipe.log_action(pid, action_text, channel=channel)
            learner.record_outreach(pid, template=f"{vertical}_custom", channel=channel)
            if stage == "cold":
                pipe.set_next_action(pid, 3)
            sent_count += 1
            print(f"  >> Logged: Custom ({channel}) for #{pid} {name}")
        else:
            print(f"  >> Skipped #{pid} {name}")

        print()

    return sent_count


def log_outcome_interactive(pipe: Pipeline, learner: SalesLearner) -> None:
    """Log outcomes for prospects (replied, no_reply, meeting_booked, etc.)."""
    _subheader("LOG OUTCOMES")
    print("  Enter prospect ID and outcome. Type 'done' to finish.")
    print("  Outcomes: replied | no_reply | meeting_booked | demo_completed | closed_won | closed_lost")
    print()

    while True:
        raw = input("  Prospect ID (or 'done'): ").strip()
        if raw.lower() == "done":
            break
        try:
            pid = int(raw)
        except ValueError:
            print("  Invalid ID.")
            continue

        p = pipe.get(pid)
        if not p:
            print(f"  Prospect #{pid} not found.")
            continue

        print(f"  #{pid} {p['name']} — {p['company']} ({p['stage']})")
        outcome = input("  Outcome: ").strip().lower()
        if not outcome:
            continue

        learner.record_outcome(pid, outcome)

        # Auto-advance based on outcome
        if outcome == "replied" and p["stage"] == "cold":
            pipe.advance(pid, "engaged")
            print(f"  >> Advanced #{pid} to engaged")
        elif outcome == "meeting_booked":
            pipe.advance(pid, "demo_scheduled")
            print(f"  >> Advanced #{pid} to demo_scheduled")
        elif outcome == "demo_completed":
            pipe.advance(pid, "demo_completed")
            print(f"  >> Advanced #{pid} to demo_completed")
        elif outcome == "closed_won":
            pipe.advance(pid, "closed_won")
            print(f"  >> Advanced #{pid} to closed_won")
        elif outcome == "closed_lost":
            pipe.advance(pid, "closed_lost")
            print(f"  >> Advanced #{pid} to closed_lost")
        else:
            print(f"  >> Recorded: {outcome} for #{pid}")
        print()


def show_performance(learner: SalesLearner) -> None:
    """Show conversion performance by category."""
    _header("OUTREACH PERFORMANCE")
    try:
        report = learner.performance_report()
        if isinstance(report, dict):
            for key, val in report.items():
                print(f"  {key}: {val}")
        elif isinstance(report, str):
            print(f"  {report}")
        else:
            print(f"  {report}")
    except Exception as e:
        print(f"  No performance data yet. ({e})")
    print()


# ── Main loop ─────────────────────────────────────────────

def main() -> None:
    pipe = Pipeline()
    gen = MessageGenerator()
    learner = SalesLearner()
    funnel = FunnelEngine()

    _header("AION OS  —  Categorical Outreach Console")
    print("  Sales liaison workflow: Review → Select Category → Execute → Log")
    print()

    while True:
        print("  ┌─────────────────────────────────────────┐")
        print("  │  MAIN MENU                              │")
        print("  │                                         │")
        print("  │  [1] Pipeline Dashboard                 │")
        print("  │  [2] Today's Follow-Up Queue            │")
        print("  │  [3] New Outreach by Category           │")
        print("  │  [4] Log Outcomes (replied, booked...)  │")
        print("  │  [5] Performance Report                 │")
        print("  │  [6] Quick Add Prospect                 │")
        print("  │  [7] Health Check (stuck/at-risk)       │")
        print("  │  [q] Quit                               │")
        print("  └─────────────────────────────────────────┘")

        choice = input("\n  Select [1-7/q]: ").strip().lower()

        if choice == "q":
            print("\n  Session closed. Go close deals.\n")
            break

        elif choice == "1":
            show_dashboard(pipe)

        elif choice == "2":
            queue = show_follow_ups(pipe)
            if queue:
                act = input("  Run follow-up batch? [y/n]: ").strip().lower()
                if act == "y":
                    # Group by vertical for message generation
                    by_vert = defaultdict(list)
                    for p in queue:
                        by_vert[p["vertical"]].append(dict(p))
                    for vert, prospects in by_vert.items():
                        run_batch(pipe, gen, learner, prospects, vert, len(prospects))

        elif choice == "3":
            # Show categories, let user pick one, run batch
            all_prospects = pipe.list_all()
            categories = _categorize([dict(p) for p in all_prospects])

            # Only show cold prospects for new outreach
            cold_cats = {
                k: v for k, v in categories.items()
                if v["bucket"] == "new_outreach" and v["prospects"]
            }

            if not cold_cats:
                print("  No cold prospects to outreach. Add more prospects first.")
                continue

            _subheader("SELECT OUTREACH CATEGORY")
            cat_keys = []
            for i, (key, cat) in enumerate(sorted(cold_cats.items()), 1):
                count = len(cat["prospects"])
                print(f"  [{i}] {cat['label']:<45} ({count} prospects)")
                cat_keys.append(key)

            print(f"  [a] All categories sequentially")
            sel = input("\n  Category [1-{}/a]: ".format(len(cat_keys))).strip().lower()

            if sel == "a":
                total_sent = 0
                for key in cat_keys:
                    cat = cold_cats[key]
                    _subheader(cat["label"])
                    total_sent += run_batch(
                        pipe, gen, learner,
                        cat["prospects"], cat["vertical"],
                    )
                print(f"\n  Total sent this session: {total_sent}")
            else:
                try:
                    idx = int(sel) - 1
                    if 0 <= idx < len(cat_keys):
                        cat = cold_cats[cat_keys[idx]]
                        batch_input = input(f"  Batch size [{BATCH_SIZE}]: ").strip()
                        bs = int(batch_input) if batch_input.isdigit() else BATCH_SIZE
                        sent = run_batch(
                            pipe, gen, learner,
                            cat["prospects"], cat["vertical"], bs,
                        )
                        print(f"\n  Sent this batch: {sent}")
                    else:
                        print("  Invalid selection.")
                except ValueError:
                    print("  Invalid selection.")

        elif choice == "4":
            log_outcome_interactive(pipe, learner)

        elif choice == "5":
            show_performance(learner)

        elif choice == "6":
            # Quick add
            print()
            name = input("  Name: ").strip()
            if not name:
                continue
            company = input("  Company: ").strip()
            title = input("  Title (optional): ").strip()
            print("  Vertical: [1] legal  [2] healthcare  [3] realestate")
            v_sel = input("  Vertical [1]: ").strip()
            vert_map = {"1": "legal", "2": "healthcare", "3": "realestate"}
            vertical = vert_map.get(v_sel, "legal")
            linkedin = input("  LinkedIn handle (optional): ").strip()
            source = input("  Source [linkedin]: ").strip() or "linkedin"
            notes = input("  Notes (optional): ").strip()

            pid = pipe.add(
                name, company, title, vertical,
                linkedin=linkedin, source=source, notes=notes,
            )
            pipe.set_next_action(pid, 1)
            print(f"\n  Added #{pid}: {name} @ {company} [{vertical}]")
            print(f"  Scheduled for outreach tomorrow.\n")

        elif choice == "7":
            _subheader("PIPELINE HEALTH CHECK")
            try:
                health = funnel.health_check()
                for status in ("healthy", "at_risk", "stuck", "dead"):
                    items = health.get(status, [])
                    if items:
                        emoji = {"healthy": "+", "at_risk": "!", "stuck": "X", "dead": "-"}.get(status, " ")
                        print(f"\n  [{emoji}] {status.upper()} ({len(items)})")
                        for item in items[:10]:
                            if isinstance(item, dict):
                                print(f"      #{item.get('id','')} {item.get('name','')} — {item.get('company','')}")
                            else:
                                print(f"      {item}")
            except Exception as e:
                print(f"  Health check error: {e}")
            print()

        else:
            print("  Invalid option. Try 1-7 or q.\n")


if __name__ == "__main__":
    main()
