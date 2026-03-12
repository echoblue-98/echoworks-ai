"""
AION OS - Improvement Engine Demo
===================================

Demonstrates the full recursive self-improvement cycle:
  1. Initialize engine with default policy
  2. Record analyst feedback (simulated)
  3. Run improvement cycle (generates candidates)
  4. Review proposals
  5. Approve/reject with policy versioning
  6. Show before/after diff
"""

from aionos.improvement import (
    ImprovementEngine,
    PolicyStore,
    EvaluationEngine,
    FeedbackCollector,
    AnalystFeedback,
    AlertOutcome,
)
from aionos.improvement.feedback_collector import FeedbackType
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
import json

console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]AION OS Improvement Engine Demo[/]\n"
        "Recursive Self-Improvement — Safe, Versioned, Human-Approved",
        border_style="cyan"
    ))

    # =========================================================================
    # Step 1: Initialize
    # =========================================================================
    console.print("\n[bold green]1. Initializing Improvement Engine...[/]")
    engine = ImprovementEngine(llm_provider="mock")
    engine.initialize()

    status = engine.get_status()
    console.print(f"   Active policy: v{status['active_policy']['version']}")
    console.print(f"   Policy fingerprint: {status['active_policy']['fingerprint']}")
    console.print(f"   Test suite: loaded")

    # =========================================================================
    # Step 2: Simulate analyst feedback
    # =========================================================================
    console.print("\n[bold green]2. Recording analyst feedback...[/]")

    feedback_items = [
        AnalystFeedback(
            feedback_type=FeedbackType.ALERT_CORRECT.value,
            analyst_id="alice",
            alert_id="alert_001",
            notes="Confirmed insider data theft — Knowles pattern",
            triage_seconds=120.0,
        ),
        AnalystFeedback(
            feedback_type=FeedbackType.ALERT_NOISY.value,
            analyst_id="alice",
            alert_id="alert_002",
            notes="VPN login from home office is normal for this user",
            corrected_severity="P4",
            triage_seconds=15.0,
        ),
        AnalystFeedback(
            feedback_type=FeedbackType.ALERT_NOISY.value,
            analyst_id="bob",
            alert_id="alert_003",
            notes="MFA prompt count was 2, below threshold — false alarm",
            corrected_category="non_issue",
            triage_seconds=10.0,
        ),
        AnalystFeedback(
            feedback_type=FeedbackType.ALERT_CORRECT.value,
            analyst_id="bob",
            alert_id="alert_004",
            notes="BEC wire fraud attempt confirmed",
            triage_seconds=300.0,
        ),
        AnalystFeedback(
            feedback_type=FeedbackType.ALERT_MISSED.value,
            analyst_id="alice",
            alert_id="alert_005",
            notes="Attorney departure exfil was not caught — badge + USB + after-hours VPN",
            corrected_severity="P1",
            corrected_category="attorney_departure_exfil",
            triage_seconds=600.0,
        ),
    ]

    for fb in feedback_items:
        engine.record_feedback(fb)
        emoji = {"alert_correct": "✅", "alert_noisy": "🔇", "alert_missed": "⚠️"}
        console.print(
            f"   {emoji.get(fb.feedback_type, '📝')} "
            f"{fb.feedback_type} — {fb.notes[:60]}..."
        )

    # =========================================================================
    # Step 3: Compute metrics
    # =========================================================================
    console.print("\n[bold green]3. Computing detection metrics...[/]")

    metrics = engine.evaluation.compute_metrics()
    table = Table(title="Detection Quality Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Precision", f"{metrics.precision:.0%}")
    table.add_row("Recall (approx)", f"{metrics.recall_approx:.0%}")
    table.add_row("F1 Score", f"{metrics.f1_score:.0%}")
    table.add_row("Noise Ratio", f"{metrics.noise_ratio:.0%}")
    table.add_row("Composite Score", f"{metrics.score():.1f} / 100")
    table.add_row("Total Alerts", str(metrics.total_alerts))
    table.add_row("True Positives", str(metrics.true_positives))
    table.add_row("False Positives", str(metrics.false_positives))
    table.add_row("Missed Threats", str(metrics.missed_threats))
    console.print(table)

    # =========================================================================
    # Step 4: Run improvement cycle
    # =========================================================================
    console.print("\n[bold green]4. Running improvement cycle...[/]")

    result = engine.run_improvement_cycle()
    console.print(f"   Status: {result['status']}")

    if result.get("proposal"):
        proposal = result["proposal"]
        console.print(f"   Proposal: {proposal.get('description', 'N/A')}")
        console.print(f"   Candidate policy: v{result.get('candidate_version', '?')}")
        console.print(f"   Changes: {len(proposal.get('changes', []))}")

        for change in proposal.get("changes", []):
            console.print(
                f"      → {change.get('description', '')}: "
                f"{change.get('old_value')} → {change.get('new_value')}"
            )

    # =========================================================================
    # Step 5: Show policy versions & diff
    # =========================================================================
    console.print("\n[bold green]5. Policy version history...[/]")

    versions = engine.policy_store.list_versions()
    ver_table = Table(title="Policy Versions")
    ver_table.add_column("Version", style="cyan")
    ver_table.add_column("Status", style="white")
    ver_table.add_column("Created By", style="white")
    ver_table.add_column("Description", style="dim")
    for v in versions:
        ver_table.add_row(
            f"v{v['version']}",
            v["status"],
            v["created_by"],
            v["description"][:50],
        )
    console.print(ver_table)

    # Diff if we have candidate
    if len(versions) >= 2:
        diff = engine.policy_store.diff(
            versions[0]["version"], versions[-1]["version"]
        )
        console.print(f"\n   [bold]Diff v{diff.from_version} → v{diff.to_version}:[/]")
        console.print(f"   {diff.summary}")

    # =========================================================================
    # Step 6: Show proposals for review
    # =========================================================================
    console.print("\n[bold green]6. Pending proposals for human review...[/]")

    proposals = engine.get_pending_proposals()
    if proposals:
        for p in proposals:
            console.print(Panel(
                f"Version: v{p['version']}\n"
                f"Created by: {p['created_by']}\n"
                f"Description: {p['description']}\n"
                f"Score: {p.get('evaluation_score', 'pending')}\n\n"
                f"[dim]{p.get('prompt', '')}[/]",
                title="📋 Proposal for Review",
                border_style="yellow",
            ))
    else:
        console.print("   No pending proposals")

    # =========================================================================
    # Step 7: Show nudges
    # =========================================================================
    console.print("\n[bold green]7. Improvement nudges for analysts...[/]")

    nudges = engine.feedback.get_active_nudges()
    if nudges:
        for n in nudges:
            console.print(Panel(
                f"[bold]{n.title}[/]\n\n"
                f"{n.description}\n\n"
                f"Before: score={n.before_stats.get('score', '?')}, "
                f"FPs={n.before_stats.get('false_positives', '?')}\n"
                f"After:  score={n.after_stats.get('score', '?')}, "
                f"FPs={n.after_stats.get('false_positives', '?')}",
                title="💡 Improvement Nudge",
                border_style="green",
            ))
    else:
        console.print("   No active nudges (need shadow mode evaluation)")

    # =========================================================================
    # Step 8: Simulate approval
    # =========================================================================
    if proposals:
        version_to_approve = proposals[0]["version"]
        console.print(f"\n[bold green]8. Simulating approval of v{version_to_approve}...[/]")
        approval = engine.approve_proposal(
            version_to_approve,
            analyst_id="alice",
            notes="Reviewed changes — looks good, reducing MFA noise",
        )
        console.print(f"   ✅ {approval['status']} — v{approval['version']} is now active")

        # Show final state
        final_status = engine.get_status()
        console.print(f"   Active policy: v{final_status['active_policy']['version']}")

    # =========================================================================
    # Summary
    # =========================================================================
    console.print(Panel.fit(
        "[bold green]Improvement Engine Demo Complete[/]\n\n"
        "What happened:\n"
        "  1. Default policy initialized (v1)\n"
        "  2. Analyst feedback recorded (5 corrections)\n"
        "  3. Metrics computed (precision, recall, F1)\n"
        "  4. LLM proposed threshold adjustments\n"
        "  5. Policy versioned and diffed\n"
        "  6. Proposal surfaced for human review\n"
        "  7. Analyst approved → new version activated\n\n"
        "[dim]This is recursive self-improvement at the system level,\n"
        "grounded in human feedback and replay, not a model\n"
        "rewriting its own code in the dark.[/]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
