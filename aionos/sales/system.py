"""
EchoWorks — Daily Sales Operating System
==========================================
One command. Everything you need. Every morning.

    python sell.py

This is the machine. It shows:
  1. Pipeline snapshot (where every dollar is)
  2. Today's cadence actions (who to contact, what to say, which step)
  3. Ready-to-paste messages for each action
  4. Stale deals that need a touch
  5. Weekly scorecard

Designed for one person, one offer ($5K/mo), one vertical (law firms).
Scales to future products by adding verticals to the engine.

Architecture:
  system.py (this file) → orchestrates everything
  ├── CadenceEngine  → multi-step outreach sequences
  ├── Pipeline       → prospect data + stage tracking
  ├── MessageGenerator → ready-to-paste messages
  ├── SalesLearner   → outreach logging + win tracking
  └── FunnelEngine   → scoring + health checks
"""

from __future__ import annotations

import sys
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from aionos.sales.prospects import Pipeline
from aionos.sales.messages import MessageGenerator
from aionos.sales.learner import SalesLearner
from aionos.sales.funnel import FunnelEngine
from aionos.sales.cadence import (
    CadenceEngine, SEQUENCES, STAGE_SEQUENCE_MAP, get_step_message,
)


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

OFFER_PRICE = 5000          # Single offer: $5K/mo
OFFER_NAME = "AION OS"
GUARANTEE = "90-day"
VERTICAL = "legal"
VERTICAL_LABEL = "Law Firms"

# Priority order for daily actions (highest value first)
STAGE_PRIORITY = {
    "negotiation": 1,       # Closest to money
    "proposal_sent": 2,     # Waiting on decision
    "demo_completed": 3,    # Need to send proposal
    "demo_scheduled": 4,    # Need to confirm/prep
    "engaged": 5,           # Need to book demo
    "cold": 6,              # New outreach
}

# Max days before a deal is "stale" per stage
STALE_THRESHOLDS = {
    "cold": 10,
    "engaged": 7,
    "demo_scheduled": 5,
    "demo_completed": 5,
    "proposal_sent": 10,
    "negotiation": 14,
}

# Daily outreach targets
DAILY_TARGETS = {
    "new_connects": 5,      # LinkedIn connection requests
    "cold_emails": 5,       # New cold emails
    "follow_ups": 10,       # Follow-up touches (any channel)
}

# Stage-specific playbook: what to do + what to send
PLAYBOOK = {
    "cold": {
        "action": "Send LinkedIn connection + cold email",
        "assets": ["Cold email (personalized)", "LinkedIn request (300 char)"],
        "goal": "Get a reply or connection acceptance",
        "next_stage": "engaged",
        "cadence_days": [1, 3, 5, 8, 12],
        "channels": ["linkedin", "email"],
    },
    "engaged": {
        "action": "Book the demo call",
        "assets": ["Demo booking message", "3-min demo recording link"],
        "goal": "Get a 20-min call on the calendar",
        "next_stage": "demo_scheduled",
        "cadence_days": [1, 3, 7],
        "channels": ["linkedin", "email"],
    },
    "demo_scheduled": {
        "action": "Confirm call + prep",
        "assets": ["Confirmation email", "Call prep notes"],
        "goal": "Show up prepared, run the demo",
        "next_stage": "demo_completed",
        "cadence_days": [0],
        "channels": ["email"],
    },
    "demo_completed": {
        "action": "Send one-pager + demo recording + proposal",
        "assets": ["One-pager PDF", "Demo recording (MP4)", "Follow-up email"],
        "goal": "Get a yes or a meeting with the decision group",
        "next_stage": "proposal_sent",
        "cadence_days": [0, 3, 7],
        "channels": ["email"],
    },
    "proposal_sent": {
        "action": "Follow up on proposal — warm, no pressure",
        "assets": ["Check-in email", "Objection responses (if needed)"],
        "goal": "Get to a verbal yes or negotiation",
        "next_stage": "negotiation",
        "cadence_days": [3, 7, 14],
        "channels": ["email", "phone"],
    },
    "negotiation": {
        "action": "Handle objections, close the deal",
        "assets": ["Objection playbook", "Contract / SOW"],
        "goal": "Signed agreement + first payment",
        "next_stage": "closed_won",
        "cadence_days": [1, 3, 7],
        "channels": ["email", "phone"],
    },
}


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def _days_since_update(prospect: dict) -> int:
    updated = prospect.get("updated") or prospect.get("created") or ""
    if not updated:
        return 999
    try:
        dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except (ValueError, TypeError):
        return 999


def _tier(prospect: dict) -> str:
    notes = (prospect.get("notes") or "").lower()
    source = (prospect.get("source") or "").lower()
    if any(k in notes for k in ("tier a", "warm", "referral", "dan intro")):
        return "A"
    if any(k in source for k in ("referral", "warm")):
        return "A"
    return "B"


def _priority_sort_key(prospect: dict) -> tuple:
    """Sort by: stage priority → tier → days stale (most stale first)."""
    stage = prospect.get("stage", "cold")
    return (
        STAGE_PRIORITY.get(stage, 99),
        0 if _tier(prospect) == "A" else 1,
        -_days_since_update(prospect),
    )


def _bar(width: int = 50, filled: int = 0, total: int = 1) -> str:
    if total == 0:
        return " " * width
    pct = min(filled / total, 1.0)
    n = int(pct * width)
    return "#" * n + "." * (width - n)


# ═══════════════════════════════════════════════════════════════
#  PIPELINE SNAPSHOT
# ═══════════════════════════════════════════════════════════════

def pipeline_snapshot(pipe: Pipeline) -> dict:
    """Print pipeline snapshot. Returns stage counts."""
    counts = pipe.count_by_stage()
    total = sum(counts.values())
    active = total - counts.get("closed_won", 0) - counts.get("closed_lost", 0)
    won = counts.get("closed_won", 0)
    revenue = won * OFFER_PRICE

    print(f"\n{'=' * 66}")
    print(f"  ECHOWORKS SALES SYSTEM  |  {date.today().strftime('%A, %B %d, %Y')}")
    print(f"  Offer: {OFFER_NAME} @ ${OFFER_PRICE:,}/mo  |  {GUARANTEE} guarantee")
    print(f"  Vertical: {VERTICAL_LABEL}")
    print(f"{'=' * 66}")

    print(f"\n  PIPELINE SNAPSHOT")
    print(f"  {'-' * 50}")
    print(f"  Active Prospects: {active}  |  Closed Won: {won}  |  MRR: ${revenue:,}/mo")
    print()

    stage_order = [
        ("cold", "Cold"),
        ("engaged", "Engaged"),
        ("demo_scheduled", "Demo Scheduled"),
        ("demo_completed", "Demo Completed"),
        ("proposal_sent", "Proposal Sent"),
        ("negotiation", "Negotiation"),
        ("closed_won", "Closed Won"),
        ("closed_lost", "Closed Lost"),
    ]

    for stage_key, stage_label in stage_order:
        ct = counts.get(stage_key, 0)
        if ct > 0:
            bar = "#" * min(ct, 30)
            print(f"  {stage_label:<20} {ct:>4}  {bar}")

    print()
    return counts


# ═══════════════════════════════════════════════════════════════
#  TODAY'S CADENCE ACTIONS
# ═══════════════════════════════════════════════════════════════

def todays_actions(pipe: Pipeline, cadence: CadenceEngine) -> List[dict]:
    """
    Build today's action list from the cadence engine.
    Returns list of action dicts sorted by priority.
    """
    # 1. Cadence-enrolled prospects with steps due today
    due = cadence.due_today()
    actions = []

    for item in due:
        step_info = item.get("step_info")
        if not step_info:
            continue

        stage = item.get("stage", "cold")
        prospect = {
            "id": item["prospect_id"],
            "name": item["name"],
            "company": item["company"],
            "title": item.get("title", ""),
            "email": item.get("email", ""),
            "vertical": item.get("vertical", "legal"),
            "stage": stage,
            "notes": item.get("notes", ""),
            "source": item.get("source", ""),
        }

        # Determine urgency from stage
        if stage in ("negotiation", "proposal_sent", "demo_completed"):
            urgency = "CLOSE"
        elif stage == "demo_scheduled":
            urgency = "PREP"
        elif stage == "engaged":
            urgency = "BOOK"
        else:
            urgency = "SEND"

        # Build channel actions string
        channels_str = " + ".join(ch["channel"] for ch in step_info["channels"])
        action_str = " / ".join(ch["action"] for ch in step_info["channels"])

        actions.append({
            "prospect": prospect,
            "stage": stage,
            "urgency": urgency,
            "step_num": item["current_step"],
            "total_steps": item["total_steps"],
            "sequence_name": item["sequence_name"],
            "sequence_label": item["sequence_label"],
            "channels": channels_str,
            "action": action_str,
            "step_info": step_info,
            "tier": _tier(prospect),
            "enrollment_id": item["id"],
        })

    # 2. Active deals NOT in cadence (demo_scheduled, negotiation, etc.)
    #    These are manual-touch deals
    enrolled_ids = {a["prospect"]["id"] for a in actions}
    all_prospects = pipe.list_all()
    for p in all_prospects:
        prospect = dict(p)
        if prospect["id"] in enrolled_ids:
            continue
        stage = prospect.get("stage", "cold")
        if stage in ("closed_won", "closed_lost", "cold"):
            continue
        # Only show non-cold active deals that aren't in cadence
        if stage in ("negotiation", "proposal_sent", "demo_completed",
                      "demo_scheduled", "engaged"):
            urgency = "CLOSE" if stage in ("negotiation", "proposal_sent",
                                            "demo_completed") else "PREP"
            playbook_entry = PLAYBOOK.get(stage, PLAYBOOK.get("cold", {}))
            actions.append({
                "prospect": prospect,
                "stage": stage,
                "urgency": urgency,
                "step_num": 0,
                "total_steps": 0,
                "sequence_name": "",
                "sequence_label": "Manual",
                "channels": "email",
                "action": playbook_entry.get("action", "Follow up"),
                "step_info": None,
                "tier": _tier(prospect),
                "enrollment_id": 0,
            })

    # Sort: CLOSE > PREP > BOOK > SEND, then tier A first
    urgency_order = {"CLOSE": 0, "PREP": 1, "BOOK": 2, "SEND": 3}
    actions.sort(key=lambda a: (
        urgency_order.get(a["urgency"], 99),
        0 if a["tier"] == "A" else 1,
        a["prospect"]["id"],
    ))

    return actions


def print_actions(actions: List[dict]) -> None:
    """Print today's cadence action list."""
    if not actions:
        print("  No actions due today. Run 'enroll' to start cadences.\n")
        return

    close_actions = [a for a in actions if a["urgency"] in ("CLOSE", "PREP")]
    book_actions = [a for a in actions if a["urgency"] == "BOOK"]
    send_actions = [a for a in actions if a["urgency"] == "SEND"]

    print(f"  TODAY'S ACTIONS  ({len(actions)} total)")
    print(f"  {'-' * 62}")

    idx = 1

    if close_actions:
        print(f"\n  >> CLOSE / PREP (highest priority)")
        for a in close_actions:
            p = a["prospect"]
            step_label = f"Step {a['step_num']}/{a['total_steps']}" if a["step_num"] else "Manual"
            print(f"  {idx:>3}. #{p['id']:<4} {p['name']:<22} {p['company']:<24}")
            print(f"       {a['stage']} | {step_label} | {a['channels']}")
            print(f"       -> {a['action']}")
            idx += 1

    if book_actions:
        print(f"\n  >> BOOK DEMOS")
        for a in book_actions:
            p = a["prospect"]
            step_label = f"Step {a['step_num']}/{a['total_steps']}"
            print(f"  {idx:>3}. #{p['id']:<4} {p['name']:<22} {p['company']:<24}")
            print(f"       {a['stage']} | {step_label} | {a['channels']}")
            print(f"       -> {a['action']}")
            idx += 1

    if send_actions:
        print(f"\n  >> COLD OUTREACH ({len(send_actions)} due)")
        for a in send_actions[:DAILY_TARGETS["new_connects"]]:
            p = a["prospect"]
            step_label = f"Step {a['step_num']}/{a['total_steps']}"
            print(f"  {idx:>3}. #{p['id']:<4} {p['name']:<22} {p['company']:<24}")
            print(f"       {step_label} | {a['channels']}")
            print(f"       -> {a['action']}")
            idx += 1
        remaining = len(send_actions) - DAILY_TARGETS["new_connects"]
        if remaining > 0:
            print(f"\n       ... and {remaining} more cold prospects due")

    print()


# ═══════════════════════════════════════════════════════════════
#  MESSAGE GENERATOR (cadence-aware)
# ═══════════════════════════════════════════════════════════════

def generate_message(pipe: Pipeline, gen: MessageGenerator,
                     cadence: CadenceEngine,
                     prospect_id: int) -> Optional[str]:
    """Generate the right message for a prospect's current cadence step."""
    prospect = pipe.get(prospect_id)
    if not prospect:
        return None

    name = prospect["name"]
    company = prospect["company"]
    first = name.split()[0] if name else "there"
    stage = prospect["stage"]

    # Get generated messages as base templates
    msgs = gen.generate(
        name=name,
        company=company,
        title=prospect.get("title", ""),
        vertical=prospect.get("vertical", VERTICAL),
    )

    # Check cadence enrollment
    enrollment = cadence.get_enrollment(prospect_id)

    if enrollment:
        seq_name = enrollment["sequence_name"]
        step_num = enrollment["current_step"]
        total = enrollment["total_steps"]
        seq = SEQUENCES.get(seq_name, {})
        steps = seq.get("steps", [])

        # Find current step
        step_info = None
        for s in steps:
            if s["step"] == step_num:
                step_info = s
                break

        if step_info:
            output = f"=== {name} @ {company} ===\n"
            output += f"--- Cadence: {seq.get('name', seq_name)} | "
            output += f"Step {step_num}/{total} ---\n\n"

            for ch in step_info["channels"]:
                channel = ch["channel"]
                template_key = ch["template_key"]
                msg = get_step_message(
                    step_num, seq_name, channel, first, company,
                    template_key, msgs,
                )
                label = channel.upper()
                output += f"--- {label}: {ch['action']} ---\n"
                output += f"{msg}\n\n"

            return output

    # Fallback: stage-based message for non-cadence prospects
    if stage == "demo_scheduled":
        return (
            f"=== DEMO PREP for {name} @ {company} ===\n\n"
            f"--- CONFIRMATION EMAIL ---\n"
            f"Subject: Confirming our call\n\n"
            f"{first},\n\n"
            f"Looking forward to our conversation. I'll walk through:\n"
            f"  - What the system detects (the full departure chain)\n"
            f"  - How it deploys (on-premise, your hardware)\n"
            f"  - A live detection scenario\n\n"
            f"Takes about 15-20 minutes. If anything changes, just let me know.\n\n"
            f"Moe\n"
        )
    elif stage == "negotiation":
        return (
            f"=== CLOSE for {name} @ {company} ===\n\n"
            f"--- PRICE: ${OFFER_PRICE:,}/mo | {GUARANTEE} guarantee ---\n\n"
            f"Subject: AION OS — Engagement Summary\n\n"
            f"{first},\n\n"
            f"Here's the summary:\n\n"
            f"  - {OFFER_NAME}: ${OFFER_PRICE:,}/month\n"
            f"  - On-premise deployment, zero data egress\n"
            f"  - Attorney departure detection + privilege exfiltration\n"
            f"  - 117+ behavioral pattern library\n"
            f"  - {GUARANTEE} performance guarantee — cancel anytime if we "
            f"don't deliver\n\n"
            f"Happy to hop on a call to finalize.\n\n"
            f"Moe\n"
        )
    else:
        # Generic cold outreach
        return (
            f"=== {name} @ {company} ===\n\n"
            f"--- LINKEDIN ---\n{msgs.get('linkedin_request', '')}\n\n"
            f"--- EMAIL ---\n{msgs.get('cold_email', '')}\n"
        )


# ═══════════════════════════════════════════════════════════════
#  WEEKLY SCORECARD
# ═══════════════════════════════════════════════════════════════

def weekly_scorecard(pipe: Pipeline, learner: SalesLearner) -> None:
    """Print weekly performance metrics."""
    counts = pipe.count_by_stage()
    total = sum(counts.values())
    won = counts.get("closed_won", 0)
    lost = counts.get("closed_lost", 0)
    active = total - won - lost
    pipeline_value = active * OFFER_PRICE  # potential MRR if all close

    print(f"\n  WEEKLY SCORECARD")
    print(f"  {'-' * 50}")
    print(f"  Pipeline Value:   ${pipeline_value:,}/mo potential")
    print(f"  Closed Won:       {won} (${won * OFFER_PRICE:,}/mo MRR)")
    print(f"  Closed Lost:      {lost}")
    print(f"  Active Deals:     {active}")
    print(f"  Win Rate:         {won / max(won + lost, 1) * 100:.0f}%")

    # Stage velocity
    all_p = pipe.list_all()
    stage_counts = defaultdict(list)
    for p in all_p:
        p = dict(p)
        stage = p.get("stage", "cold")
        if stage not in ("closed_won", "closed_lost"):
            stage_counts[stage].append(_days_since_update(p))

    if stage_counts:
        print(f"\n  Avg Days in Stage:")
        for stage in ("cold", "engaged", "demo_scheduled", "demo_completed",
                      "proposal_sent", "negotiation"):
            if stage in stage_counts:
                days_list = stage_counts[stage]
                avg = sum(days_list) / len(days_list)
                threshold = STALE_THRESHOLDS.get(stage, 7)
                flag = " !! SLOW" if avg > threshold else ""
                print(f"    {stage:<20} {avg:>5.1f}d  (target: <{threshold}d){flag}")
    print()


# ═══════════════════════════════════════════════════════════════
#  OBJECTION QUICK-REFERENCE
# ═══════════════════════════════════════════════════════════════

def objection_lookup(keyword: str = "") -> None:
    """Print objection responses matching keyword, or all."""
    from aionos.sales.engine import SalesEngine
    engine = SalesEngine()
    objections = engine.all_objections(VERTICAL)

    print(f"\n  OBJECTION PLAYBOOK")
    print(f"  {'-' * 50}")

    for obj in objections:
        if keyword and keyword.lower() not in obj.objection.lower():
            continue
        print(f"\n  THEY SAY: \"{obj.objection}\"")
        print(f"  YOU SAY:  {obj.response}")
        if obj.proof_point:
            print(f"  PROOF:    {obj.proof_point}")
    print()


# ═══════════════════════════════════════════════════════════════
#  INTERACTIVE SYSTEM
# ═══════════════════════════════════════════════════════════════

def _interactive_menu(pipe: Pipeline, gen: MessageGenerator,
                      learner: SalesLearner, cadence: CadenceEngine,
                      actions: List[dict]) -> None:
    """Interactive command loop after the dashboard loads."""
    print(f"  COMMANDS:")
    print(f"  {'-' * 62}")
    print(f"  [number]       Show ready-to-paste message for action #")
    print(f"  done [number]  Mark action # complete (auto-schedules next step)")
    print(f"  sent [id]      Log outreach for prospect #id (non-cadence)")
    print(f"  replied [id]   Prospect replied (pauses cadence)")
    print(f"  advance [id]   Move prospect to next stage (+new cadence)")
    print(f"  enroll [n]     Enroll n cold prospects into cadence (default: 5)")
    print(f"  send           Send cadence emails due today (dry-run)")
    print(f"  send --live    Actually send emails via Gmail")
    print(f"  send [id]      Send email to one prospect (dry-run)")
    print(f"  linkedin       Open LinkedIn actions in browser")
    print(f"  linkedin [id]  Open one prospect's LinkedIn")
    print(f"  export         Export pipeline to CSV (Downloads)")
    print(f"  report         Open visual dashboard in browser")
    print(f"  cadence        Show cadence stats")
    print(f"  score          Weekly scorecard")
    print(f"  objections     Objection playbook")
    print(f"  obj [word]     Search objections by keyword")
    print(f"  refresh        Reload pipeline")
    print(f"  q              Quit")
    print()

    while True:
        try:
            raw = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        if raw.lower() in ("q", "quit", "exit"):
            break

        # Generate message for action number
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(actions):
                pid = actions[idx]["prospect"]["id"]
                msg = generate_message(pipe, gen, cadence, pid)
                if msg:
                    print(f"\n{msg}")
                else:
                    print(f"  Could not generate message for #{pid}")
            else:
                print(f"  Invalid action number. Range: 1-{len(actions)}")
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "done" and len(parts) >= 2:
            try:
                idx = int(parts[1]) - 1
                if 0 <= idx < len(actions):
                    a = actions[idx]
                    pid = a["prospect"]["id"]
                    if a["sequence_name"]:
                        result = cadence.complete_step(pid, channel=a["channels"])
                        name = a["prospect"]["name"]
                        if result["sequence_complete"]:
                            print(f"  Done: #{pid} {name} — sequence COMPLETE")
                        else:
                            print(f"  Done: #{pid} {name} — step {result['completed_step']} complete")
                            print(f"        Next: step {result['next_step']} on {result['next_date']}")
                    else:
                        learner.record_outreach(pid, channel="email")
                        print(f"  Logged outreach for #{pid} ({a['prospect']['name']})")
                else:
                    print(f"  Invalid action number. Range: 1-{len(actions)}")
            except (ValueError, Exception) as e:
                print(f"  Error: {e}")

        elif cmd == "sent" and len(parts) >= 2:
            try:
                pid = int(parts[1])
                channel = parts[2] if len(parts) > 2 else "email"
                # Try cadence first
                if cadence.is_enrolled(pid):
                    result = cadence.complete_step(pid, channel=channel)
                    prospect = pipe.get(pid)
                    name = prospect["name"] if prospect else f"#{pid}"
                    if result["sequence_complete"]:
                        print(f"  Done: {name} — sequence COMPLETE")
                    else:
                        print(f"  Done: {name} — step {result['completed_step']} -> next step {result['next_step']} on {result['next_date']}")
                else:
                    learner.record_outreach(pid, channel=channel)
                    prospect = pipe.get(pid)
                    name = prospect["name"] if prospect else f"#{pid}"
                    print(f"  Logged {channel} outreach for {name}")
            except (ValueError, Exception) as e:
                print(f"  Error: {e}")

        elif cmd == "replied" and len(parts) >= 2:
            try:
                pid = int(parts[1])
                cadence.prospect_replied(pid)
                pipe.advance(pid, "engaged")
                prospect = pipe.get(pid)
                name = prospect["name"] if prospect else f"#{pid}"
                print(f"  {name} replied! Cadence paused, stage -> engaged")
            except (ValueError, Exception) as e:
                print(f"  Error: {e}")

        elif cmd == "advance" and len(parts) >= 2:
            try:
                pid = int(parts[1])
                prospect = pipe.get(pid)
                if not prospect:
                    print(f"  Prospect #{pid} not found.")
                    continue

                current = prospect["stage"]
                if len(parts) >= 3:
                    new_stage = parts[2]
                else:
                    new_stage = PLAYBOOK.get(current, {}).get("next_stage", "")

                if new_stage:
                    pipe.advance(pid, new_stage)
                    cadence.prospect_advanced(pid, new_stage)
                    enrolled = "yes" if STAGE_SEQUENCE_MAP.get(new_stage) else "no"
                    print(f"  Advanced #{pid} -> {new_stage} (cadence: {enrolled})")
                else:
                    print(f"  No next stage. Use: advance {pid} [stage_name]")
            except (ValueError, Exception) as e:
                print(f"  Error: {e}")

        elif cmd == "enroll":
            n = int(parts[1]) if len(parts) > 1 else 5
            count = cadence.bulk_enroll_cold(limit=n)
            print(f"  Enrolled {count} cold legal prospects into cadence")

        elif cmd == "cadence":
            stats = cadence.cadence_stats()
            print(f"\n  CADENCE STATS")
            print(f"  {'-' * 50}")
            for seq_name, data in stats.items():
                seq = SEQUENCES.get(seq_name, {})
                label = seq.get("name", seq_name)
                print(f"  {label}")
                print(f"    Active: {data.get('active', 0)}  |  "
                      f"Completed: {data.get('completed', 0)}  |  "
                      f"Replied: {data.get('replied', 0)}  |  "
                      f"Reply Rate: {data.get('reply_rate', '0%')}")
            if not stats:
                print("  No cadences active. Use 'enroll' to start.")
            print()

        elif cmd == "score":
            weekly_scorecard(pipe, learner)

        elif cmd == "objections":
            objection_lookup()

        elif cmd == "obj" and len(parts) >= 2:
            objection_lookup(" ".join(parts[1:]))

        elif cmd == "send":
            from aionos.sales.email_sender import EmailSender
            live = "--live" in parts
            sender = EmailSender(dry_run=not live)
            if not live:
                print("  [DRY RUN] Add '--live' to actually send.")
            # Check if a prospect ID was given
            pid = None
            for p in parts[1:]:
                if p.isdigit():
                    pid = int(p)
                    break
            if pid:
                sender.send_one(pid)
            else:
                sender.send_due_today()

        elif cmd == "linkedin":
            from aionos.sales.linkedin_assist import LinkedInAssist
            assist = LinkedInAssist()
            if len(parts) >= 2 and parts[1].isdigit():
                assist.open_one(int(parts[1]))
            else:
                assist.open_due_today()

        elif cmd == "export":
            from aionos.sales.crm_export import CRMExport
            exp = CRMExport()
            fmt = "csv"
            if "--json" in parts:
                fmt = "json"
            elif "--sheets" in parts:
                fmt = "sheets"
            import os
            from datetime import date as _date
            today = _date.today().isoformat()
            dl = os.path.join(os.path.expanduser("~"), "Downloads")
            if fmt == "json":
                path = os.path.join(dl, f"pipeline_{today}.json")
                exp.to_json(file_path=path)
            elif fmt == "sheets":
                path = os.path.join(dl, f"pipeline_{today}.tsv")
                exp.to_sheets(file_path=path)
            else:
                path = os.path.join(dl, f"pipeline_{today}.csv")
                exp.to_csv(file_path=path)

        elif cmd == "report":
            from aionos.sales.dashboard import DashboardReport
            report = DashboardReport()
            if "--file" in parts:
                import os
                from datetime import date as _date
                today = _date.today().isoformat()
                path = os.path.join(os.path.expanduser("~"), "Downloads",
                                    f"sales_dashboard_{today}.html")
                report.save(path)
            else:
                path = report.open_in_browser()
                print(f"  Dashboard opened: {path}")

        elif cmd == "refresh":
            print("  Refreshing...")
            _run_system(interactive=True)
            return

        else:
            print(f"  Unknown: {raw}")
            print(f"  Try: [number], done [#], sent [id], replied [id], "
                  f"advance [id], enroll, send, linkedin, export, report, q")


# ═══════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def _run_system(interactive: bool = True) -> None:
    """Run the full daily sales system."""
    pipe = Pipeline()
    gen = MessageGenerator()
    learner = SalesLearner()
    cadence = CadenceEngine()

    # 1. Pipeline snapshot
    pipeline_snapshot(pipe)

    # 2. Today's cadence actions
    actions = todays_actions(pipe, cadence)
    print_actions(actions)

    # 3. Interactive mode
    if interactive:
        _interactive_menu(pipe, gen, learner, cadence, actions)


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    if not args:
        _run_system(interactive=True)
        return

    cmd = args[0].lower()

    if cmd == "snapshot":
        pipe = Pipeline()
        pipeline_snapshot(pipe)

    elif cmd == "actions":
        pipe = Pipeline()
        cadence = CadenceEngine()
        actions = todays_actions(pipe, cadence)
        print_actions(actions)

    elif cmd == "message" and len(args) >= 2:
        pipe = Pipeline()
        gen = MessageGenerator()
        cadence = CadenceEngine()
        msg = generate_message(pipe, gen, cadence, int(args[1]))
        if msg:
            print(msg)
        else:
            print(f"  Prospect #{args[1]} not found.")

    elif cmd == "enroll":
        cadence = CadenceEngine()
        n = int(args[1]) if len(args) > 1 else 10
        count = cadence.bulk_enroll_cold(limit=n)
        print(f"  Enrolled {count} cold legal prospects into cadence")

    elif cmd == "score":
        pipe = Pipeline()
        learner = SalesLearner()
        weekly_scorecard(pipe, learner)

    elif cmd == "objections":
        keyword = " ".join(args[1:]) if len(args) > 1 else ""
        objection_lookup(keyword)

    elif cmd == "send":
        from aionos.sales.email_sender import EmailSender
        live = "--live" in args
        sender = EmailSender(dry_run=not live)
        if not live:
            print("\n  === DRY RUN === (add --live to actually send)")
        pid = None
        for a in args[1:]:
            if a.isdigit():
                pid = int(a)
                break
        if pid:
            sender.send_one(pid)
        else:
            sender.send_due_today()

    elif cmd == "linkedin":
        from aionos.sales.linkedin_assist import LinkedInAssist
        assist = LinkedInAssist()
        if len(args) >= 2 and args[1].isdigit():
            assist.open_one(int(args[1]))
        else:
            assist.open_due_today()

    elif cmd == "export":
        from aionos.sales.crm_export import CRMExport
        exp = CRMExport()
        if "--json" in args:
            path = os.path.join(os.path.expanduser("~"), "Downloads",
                                f"pipeline_{date.today().isoformat()}.json")
            exp.to_json(file_path=path)
        elif "--sheets" in args:
            path = os.path.join(os.path.expanduser("~"), "Downloads",
                                f"pipeline_{date.today().isoformat()}.tsv")
            exp.to_sheets(file_path=path)
        elif "--summary" in args:
            import json
            print(json.dumps(exp.summary(), indent=2))
        else:
            path = os.path.join(os.path.expanduser("~"), "Downloads",
                                f"pipeline_{date.today().isoformat()}.csv")
            exp.to_csv(file_path=path)

    elif cmd == "report":
        from aionos.sales.dashboard import DashboardReport
        report = DashboardReport()
        if "--file" in args:
            path = os.path.join(os.path.expanduser("~"), "Downloads",
                                f"sales_dashboard_{date.today().isoformat()}.html")
            report.save(path)
        else:
            path = report.open_in_browser()
            print(f"  Dashboard opened: {path}")

    elif cmd == "help":
        print("""
  EchoWorks Sales System
  ========================
  python sell.py                Full interactive dashboard
  python sell.py snapshot       Pipeline snapshot only
  python sell.py actions        Today's cadence actions
  python sell.py message [id]   Message for prospect (cadence-aware)
  python sell.py enroll [n]     Enroll n cold prospects into cadence
  python sell.py send           Dry-run email send (all due today)
  python sell.py send --live    Actually send emails via Gmail
  python sell.py send [id]      Send email to one prospect
  python sell.py linkedin       Open LinkedIn actions in browser
  python sell.py linkedin [id]  Open one prospect's LinkedIn
  python sell.py export         Export pipeline to CSV (~/Downloads)
  python sell.py export --json  Export as JSON
  python sell.py export --sheets Tab-separated for Google Sheets
  python sell.py report         Open visual dashboard in browser
  python sell.py report --file  Save dashboard to ~/Downloads
  python sell.py score          Weekly scorecard
  python sell.py objections     Objection playbook
  python sell.py help           This help

  Interactive Commands (inside dashboard):
    [number]       Show message for action #
    done [number]  Complete action # (auto-schedules next step)
    sent [id]      Log outreach (cadence-aware)
    replied [id]   Prospect replied (pauses cadence)
    advance [id]   Move to next stage (+new cadence)
    enroll [n]     Enroll n cold prospects
    send           Send cadence emails (dry-run)
    send --live    Send for real
    linkedin       Open LinkedIn actions
    export         Export CSV to Downloads
    report         Open visual dashboard
    cadence        Show cadence stats
    score          Weekly scorecard
    objections     Show objection playbook
    q              Quit
        """)
    else:
        print(f"  Unknown command: {cmd}. Try: python sell.py help")


if __name__ == "__main__":
    main()
