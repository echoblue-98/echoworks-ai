"""
AION OS - Human Capacity CLI
Command-line interface for the Human Capacity Gem

Usage:
    python -m aionos.api.capacity_cli analyze-gap --current "..." --desired "..."
    python -m aionos.api.capacity_cli eq-challenge --situation "..." --response "..."
    python -m aionos.api.capacity_cli challenge-belief --belief "..." 
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.markdown import Markdown
from typing import Optional, List
import json

from aionos.modules.human_capacity_gem import (
    create_capacity_session,
    GrowthIntensity
)

app = typer.Typer(
    name="AION Capacity",
    help="Adversarial intelligence for human growth",
    add_completion=False
)

console = Console()


def _render_header():
    """Show the AION Capacity header"""
    header = """
╔═══════════════════════════════════════════════════════════╗
║                    AION CAPACITY GEM                      ║
║           Adversarial Intelligence for Growth             ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(header, style="bold cyan")
    console.print("⚠️  Warning: This AI doesn't coddle. It challenges.\n", style="yellow")


@app.command(name="analyze-gap")
def analyze_capacity_gap(
    current: str = typer.Option(..., help="Where you are now (be honest)"),
    desired: str = typer.Option(..., help="Where you want to be (be ambitious)"),
    intensity: str = typer.Option(
        "challenging",
        help="gentle/challenging/confrontational/adversarial/transformational"
    ),
    fears: Optional[str] = typer.Option(None, help="What are you afraid of?"),
    obstacles: Optional[str] = typer.Option(None, help="What's in your way?"),
    past_failures: Optional[str] = typer.Option(None, help="What have you tried before?")
):
    """
    Analyze the gap between where you are and where you want to be.
    Then challenge every excuse keeping you there.
    """
    
    _render_header()
    
    console.print(Panel(
        f"[bold]CURRENT STATE:[/bold] {current}\n"
        f"[bold]DESIRED STATE:[/bold] {desired}\n"
        f"[bold]INTENSITY:[/bold] {intensity.upper()}",
        title="🎯 Capacity Gap Analysis",
        border_style="cyan"
    ))
    
    # Create context
    context = {}
    if fears:
        context["fears"] = fears
    if obstacles:
        context["obstacles"] = obstacles
    if past_failures:
        context["past_failures"] = past_failures
    
    # Run analysis
    gem = create_capacity_session(intensity)
    
    with console.status("[bold yellow]Running adversarial analysis..."):
        analysis = gem.analyze_capacity_gap(current, desired, context)
    
    # Display results
    _render_gap_analysis(analysis)
    _render_blind_spots(analysis["blind_spots"])
    _render_hard_questions(analysis["confrontational_questions"])
    _render_growth_prescription(analysis["growth_prescription"])
    _render_accountability(analysis["accountability_metrics"])
    
    console.print("\n")
    console.print(Panel(
        "[bold red]⏰ 24-HOUR CHALLENGE:[/bold red]\n"
        "Do ONE uncomfortable thing from this analysis in the next 24 hours.\n"
        "If you don't, you're not serious about change.",
        border_style="red"
    ))


@app.command(name="eq-challenge")
def emotional_intelligence_challenge(
    situation: str = typer.Option(..., help="Describe the situation"),
    response: str = typer.Option(..., help="Your response to the situation"),
    intensity: str = typer.Option("challenging", help="Intensity level")
):
    """
    Analyze your emotional patterns and get adversarial feedback.
    This isn't therapy. This is pattern recognition.
    """
    
    _render_header()
    
    console.print(Panel(
        f"[bold]SITUATION:[/bold] {situation}\n"
        f"[bold]YOUR RESPONSE:[/bold] {response}",
        title="🧠 Emotional Intelligence Challenge",
        border_style="cyan"
    ))
    
    gem = create_capacity_session(intensity)
    
    with console.status("[bold yellow]Analyzing emotional patterns..."):
        analysis = gem.emotional_intelligence_challenge(situation, response)
    
    # Display EQ analysis
    _render_emotional_pattern(analysis["your_pattern"])
    _render_eq_blind_spots(analysis["what_you_missed"])
    _render_growth_edge(analysis["growth_edge"])
    _render_better_response(analysis["alternative_response"])
    _render_eq_exercises(analysis["practice_exercises"])


@app.command(name="challenge-belief")
def challenge_belief(
    belief: str = typer.Option(..., help="The belief you want to examine"),
    evidence_for: Optional[str] = typer.Option(None, help="Evidence supporting the belief"),
    evidence_against: Optional[str] = typer.Option(None, help="Evidence contradicting the belief"),
    intensity: str = typer.Option("challenging", help="Intensity level")
):
    """
    Challenge your beliefs adversarially.
    Most beliefs are inherited, not examined.
    """
    
    _render_header()
    
    console.print(Panel(
        f"[bold]BELIEF TO EXAMINE:[/bold] {belief}",
        title="🔍 Belief Challenge",
        border_style="cyan"
    ))
    
    evidence_for_list = evidence_for.split(",") if evidence_for else []
    evidence_against_list = evidence_against.split(",") if evidence_against else []
    
    gem = create_capacity_session(intensity)
    
    with console.status("[bold yellow]Challenging belief system..."):
        analysis = gem.confrontational_feedback(belief, evidence_for_list, evidence_against_list)
    
    # Display belief challenge
    _render_belief_audit(analysis["belief_audit"])
    _render_cui_bono(analysis["who_benefits"])
    _render_belief_cost(analysis["cost_of_belief"])
    _render_alternatives(analysis["alternative_beliefs"])
    _render_experiment(analysis["experiment"])


def _render_gap_analysis(analysis: dict):
    """Display gap analysis results"""
    
    gap = analysis["gap_analysis"]
    
    console.print("\n")
    console.print(Panel(
        f"[bold]REALITY CHECK:[/bold] {gap['current_reality_check']}\n\n"
        f"[bold]GAP SEVERITY:[/bold] {gap['gap_severity']}\n\n"
        f"[bold]TIME COST:[/bold] {gap['time_cost']}\n\n"
        f"[bold]HIDDEN COSTS:[/bold]\n" +
        "\n".join([f"  • {cost}" for cost in gap['hidden_costs']]),
        title="📊 Gap Analysis",
        border_style="yellow"
    ))


def _render_blind_spots(blind_spots: list):
    """Display blind spots"""
    
    console.print("\n")
    console.print("[bold red]🚨 BLIND SPOTS DETECTED[/bold red]", style="bold")
    console.print("(The things you're not seeing about yourself)\n")
    
    for spot in blind_spots[:3]:  # Show first 3
        console.print(Panel(
            f"[bold cyan]{spot['category']}[/bold cyan]\n\n"
            f"[bold]Pattern:[/bold] {spot['pattern']}\n"
            f"[bold]Evidence:[/bold] {spot['evidence']}\n\n"
            f"[bold red]CONFRONTATION:[/bold red]\n{spot['confrontation']}",
            border_style="red"
        ))


def _render_hard_questions(questions: list):
    """Display confrontational questions"""
    
    console.print("\n")
    console.print("[bold yellow]❓ HARD QUESTIONS[/bold yellow]", style="bold")
    console.print("(Answer these or admit you're not ready)\n")
    
    for i, q in enumerate(questions[:5], 1):
        console.print(f"[bold cyan]{i}.[/bold cyan] {q['question']}")
        console.print(f"   [dim]{q['warning']}[/dim]\n")


def _render_growth_prescription(prescription: dict):
    """Display growth prescription"""
    
    console.print("\n")
    console.print(Panel(
        "[bold]IMMEDIATE ACTION (24 HOURS):[/bold]\n"
        f"{prescription['immediate_action']['what']}\n"
        f"[dim]{prescription['immediate_action']['why']}[/dim]\n\n"
        
        "[bold]7-DAY SPRINT:[/bold]\n"
        f"{prescription['7_day_sprint']['what']}\n"
        f"[dim]{prescription['7_day_sprint']['warning']}[/dim]\n\n"
        
        "[bold]30-DAY TRANSFORMATION:[/bold]\n"
        f"{prescription['30_day_transformation']['what']}\n"
        f"[bold yellow]{prescription['30_day_transformation']['milestone']}[/bold yellow]\n\n"
        
        "[bold]90-DAY BREAKTHROUGH:[/bold]\n"
        f"{prescription['90_day_breakthrough']['what']}\n"
        f"[bold green]{prescription['90_day_breakthrough']['success_criteria']}[/bold green]",
        title="💊 Growth Prescription",
        border_style="green"
    ))
    
    console.print("\n[bold]NON-NEGOTIABLES:[/bold]")
    for item in prescription['non_negotiables']:
        console.print(f"  ✓ {item}")


def _render_accountability(metrics: dict):
    """Display accountability metrics"""
    
    console.print("\n")
    console.print(Panel(
        f"[bold]MEASUREMENT:[/bold] {metrics['what_gets_measured']}\n\n"
        f"[bold]PUBLIC COMMITMENT:[/bold] {metrics['public_commitment']}\n\n"
        f"[bold]CONSEQUENCE DESIGN:[/bold] {metrics['consequence_design']}\n\n"
        f"[bold]WEEKLY REVIEW:[/bold] {metrics['weekly_review']}\n\n"
        f"[bold red]RED FLAGS:[/bold red]\n" +
        "\n".join([f"  🚩 {flag}" for flag in metrics['red_flags']]) +
        f"\n\n[bold yellow]TRUTH SERUM:[/bold yellow]\n{metrics['truth_serum']}",
        title="📏 Accountability System",
        border_style="magenta"
    ))


def _render_emotional_pattern(pattern: dict):
    """Display emotional pattern analysis"""
    
    p = pattern['likely_pattern']
    
    console.print("\n")
    console.print(Panel(
        f"[bold red]PATTERN DETECTED:[/bold red] {p['pattern']}\n\n"
        f"[bold]Signal:[/bold] {p['signal']}\n"
        f"[bold]Cost:[/bold] {p['cost']}\n"
        f"[bold green]Upgrade:[/bold green] {p['upgrade']}\n\n"
        f"[bold yellow]WHY THIS MATTERS:[/bold yellow]\n{pattern['why_this_matters']}\n\n"
        f"[bold red]CONFRONTATION:[/bold red]\n{pattern['confrontation']}",
        title="🎭 Your Emotional Pattern",
        border_style="red"
    ))


def _render_eq_blind_spots(blind_spots: list):
    """Display EQ blind spots"""
    
    console.print("\n")
    console.print("[bold red]🚨 WHAT YOU MISSED IN YOUR RESPONSE:[/bold red]\n")
    for spot in blind_spots[:3]:
        console.print(f"  • {spot}")


def _render_growth_edge(edge: str):
    """Display emotional growth edge"""
    
    console.print("\n")
    console.print(Panel(
        edge,
        title="🌱 Your Emotional Growth Edge",
        border_style="green"
    ))


def _render_better_response(response: str):
    """Display higher EQ response"""
    
    console.print("\n")
    console.print(Panel(
        f"[bold]What a more emotionally intelligent you would say:[/bold]\n\n"
        f"{response}",
        title="💎 Higher EQ Response",
        border_style="cyan"
    ))


def _render_eq_exercises(exercises: list):
    """Display EQ building exercises"""
    
    console.print("\n")
    console.print("[bold]🏋️ DAILY EQ EXERCISES:[/bold]\n")
    
    for ex in exercises:
        console.print(f"[bold cyan]{ex['exercise']}[/bold cyan]")
        console.print(f"  Practice: {ex['practice']}")
        console.print(f"  Why: {ex['why']}\n")


def _render_belief_audit(audit: dict):
    """Display belief audit"""
    
    console.print("\n")
    console.print(Panel(
        f"[bold]BELIEF:[/bold] {audit['belief']}\n\n"
        f"[bold]ORIGIN:[/bold] {audit['origin']}\n"
        f"[bold]EXAMINATION:[/bold] {audit['examination']}\n\n"
        f"[bold yellow]VERDICT:[/bold yellow] {audit['verdict']}",
        title="🔍 Belief Audit",
        border_style="yellow"
    ))


def _render_cui_bono(who_benefits: str):
    """Display cui bono analysis"""
    
    console.print("\n")
    console.print(Panel(
        who_benefits,
        title="👥 Cui Bono? (Who Benefits?)",
        border_style="red"
    ))


def _render_belief_cost(cost: dict):
    """Display belief cost analysis"""
    
    console.print("\n")
    console.print(Panel(
        f"[bold]OPPORTUNITY COST:[/bold] {cost['opportunity_cost']}\n"
        f"[bold]TIME COST:[/bold] {cost['time_cost']}\n"
        f"[bold]IDENTITY COST:[/bold] {cost['identity_cost']}\n"
        f"[bold]RELATIONSHIP COST:[/bold] {cost['relationship_cost']}\n"
        f"[bold]FINANCIAL COST:[/bold] {cost['financial_cost']}\n\n"
        f"[bold red]{cost['total_cost']}[/bold red]",
        title="💰 Cost of This Belief",
        border_style="red"
    ))


def _render_alternatives(alternatives: list):
    """Display alternative beliefs"""
    
    console.print("\n")
    console.print("[bold green]💡 ALTERNATIVE BELIEFS:[/bold green]\n")
    
    for alt in alternatives[:5]:
        console.print(f"  • {alt}")


def _render_experiment(experiment: dict):
    """Display belief experiment"""
    
    console.print("\n")
    console.print(Panel(
        f"[bold]HYPOTHESIS:[/bold] {experiment['hypothesis']}\n\n"
        f"[bold]EXPERIMENT:[/bold] {experiment['experiment']}\n\n"
        f"[bold]DATA COLLECTION:[/bold] {experiment['data_collection']}\n\n"
        f"[bold]ANALYSIS:[/bold] {experiment['analysis']}\n\n"
        f"[bold]UPDATE:[/bold] {experiment['update']}",
        title="🧪 Test Your Belief",
        border_style="cyan"
    ))


if __name__ == "__main__":
    app()
