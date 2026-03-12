"""
Example usage of AION OS Human Capacity Gem
Demonstrates adversarial intelligence for personal growth
"""

from aionos.modules.human_capacity_gem import create_capacity_session
from rich.console import Console
from rich.panel import Panel

console = Console()


def demo_capacity_gap():
    """Demo: Capacity Gap Analysis"""
    
    console.print("\n" + "="*70, style="bold cyan")
    console.print("DEMO 1: CAPACITY GAP ANALYSIS", style="bold cyan")
    console.print("="*70 + "\n", style="bold cyan")
    
    # Create session with CHALLENGING intensity
    gem = create_capacity_session("challenging")
    
    # Analyze gap
    analysis = gem.analyze_capacity_gap(
        current_state="Mid-level manager at tech company. Comfortable $150k salary. Been coasting for 2 years. Know I'm capable of more but scared to make a move.",
        desired_state="VP of Product leading a team of 50+, driving strategy, making real impact, $300k+ compensation.",
        context={
            "fears": "Failure, losing financial security, disappointing my family, being exposed as not good enough",
            "obstacles": "No VP experience, mortgage, kids in private school, comfortable lifestyle dependencies",
            "past_failures": "Tried to start a side business 3 years ago, gave up after 4 months when it got hard"
        }
    )
    
    # Display key sections
    console.print(Panel(
        f"[bold]Current Reality:[/bold] {analysis['gap_analysis']['current_reality_check']}\n\n"
        f"[bold]Gap Severity:[/bold] {analysis['gap_analysis']['gap_severity']}\n\n"
        f"[bold]Time Cost:[/bold] {analysis['gap_analysis']['time_cost']}",
        title="📊 GAP ANALYSIS",
        border_style="yellow"
    ))
    
    console.print("\n[bold red]🚨 BLIND SPOTS DETECTED:[/bold red]\n")
    for i, spot in enumerate(analysis['blind_spots'][:3], 1):
        console.print(f"[bold cyan]{i}. {spot['category']}[/bold cyan]")
        console.print(f"   {spot['confrontation']}\n")
    
    console.print("\n[bold yellow]❓ HARD QUESTIONS:[/bold yellow]\n")
    for i, q in enumerate(analysis['confrontational_questions'][:5], 1):
        console.print(f"{i}. {q['question']}")
    
    console.print("\n")
    console.print(Panel(
        f"[bold]DO THIS IN 24 HOURS:[/bold]\n{analysis['growth_prescription']['immediate_action']['what']}\n\n"
        f"[bold]WHY:[/bold] {analysis['growth_prescription']['immediate_action']['why']}",
        title="⏰ IMMEDIATE ACTION",
        border_style="red"
    ))


def demo_eq_challenge():
    """Demo: Emotional Intelligence Challenge"""
    
    console.print("\n\n" + "="*70, style="bold cyan")
    console.print("DEMO 2: EMOTIONAL INTELLIGENCE CHALLENGE", style="bold cyan")
    console.print("="*70 + "\n", style="bold cyan")
    
    gem = create_capacity_session("confrontational")
    
    # Analyze emotional pattern
    analysis = gem.emotional_intelligence_challenge(
        situation="My boss gave me critical feedback in front of the entire team during a meeting. Said my project was 'sloppy' and 'not up to our standards.'",
        your_response="I immediately got defensive and explained all the reasons why the timeline was impossible and it wasn't my fault. Spent 10 minutes justifying why I made those choices."
    )
    
    # Display pattern
    pattern = analysis['your_pattern']['likely_pattern']
    console.print(Panel(
        f"[bold red]PATTERN:[/bold red] {pattern['pattern']}\n\n"
        f"[bold]Signal:[/bold] {pattern['signal']}\n"
        f"[bold]Cost:[/bold] {pattern['cost']}\n"
        f"[bold green]Upgrade:[/bold green] {pattern['upgrade']}\n\n"
        f"[bold yellow]{analysis['your_pattern']['confrontation']}[/bold yellow]",
        title="🎭 YOUR EMOTIONAL PATTERN",
        border_style="red"
    ))
    
    console.print("\n[bold red]🚨 WHAT YOU MISSED:[/bold red]\n")
    for miss in analysis['what_you_missed'][:3]:
        console.print(f"  • {miss}")
    
    console.print("\n")
    console.print(Panel(
        analysis['growth_edge'],
        title="🌱 YOUR GROWTH EDGE",
        border_style="green"
    ))
    
    console.print("\n")
    console.print(Panel(
        f"[bold]Higher EQ Response:[/bold]\n\n{analysis['alternative_response']}",
        title="💎 WHAT YOU SHOULD HAVE SAID",
        border_style="cyan"
    ))
    
    console.print("\n[bold]🏋️ DAILY PRACTICES:[/bold]\n")
    for ex in analysis['practice_exercises'][:3]:
        console.print(f"[bold cyan]• {ex['exercise']}[/bold cyan]")
        console.print(f"  {ex['practice']}")
        console.print(f"  [dim]Why: {ex['why']}[/dim]\n")


def demo_belief_challenge():
    """Demo: Belief Challenge"""
    
    console.print("\n\n" + "="*70, style="bold cyan")
    console.print("DEMO 3: BELIEF CHALLENGE", style="bold cyan")
    console.print("="*70 + "\n", style="bold cyan")
    
    gem = create_capacity_session("adversarial")
    
    # Challenge belief
    analysis = gem.confrontational_feedback(
        your_belief="I'm not a 'natural leader' so I shouldn't pursue leadership roles",
        evidence_for=["I'm introverted", "I don't like public speaking", "Other leaders seem more confident"],
        evidence_against=["I've successfully led small teams", "People ask me for advice", "I care about team success"]
    )
    
    # Display audit
    console.print(Panel(
        f"[bold]BELIEF:[/bold] {analysis['belief_audit']['belief']}\n\n"
        f"[bold]ORIGIN:[/bold] {analysis['belief_audit']['origin']}\n\n"
        f"[bold yellow]VERDICT:[/bold yellow] {analysis['belief_audit']['verdict']}",
        title="🔍 BELIEF AUDIT",
        border_style="yellow"
    ))
    
    console.print("\n")
    console.print(Panel(
        analysis['who_benefits'],
        title="👥 CUI BONO? (Who Benefits?)",
        border_style="red"
    ))
    
    console.print("\n")
    console.print(Panel(
        f"[bold]OPPORTUNITY COST:[/bold] {analysis['cost_of_belief']['opportunity_cost']}\n"
        f"[bold]TIME COST:[/bold] {analysis['cost_of_belief']['time_cost']}\n"
        f"[bold]IDENTITY COST:[/bold] {analysis['cost_of_belief']['identity_cost']}\n\n"
        f"[bold red]{analysis['cost_of_belief']['total_cost']}[/bold red]",
        title="💰 COST OF THIS BELIEF",
        border_style="red"
    ))
    
    console.print("\n[bold green]💡 ALTERNATIVE BELIEFS:[/bold green]\n")
    for alt in analysis['alternative_beliefs'][:5]:
        console.print(f"  • {alt}")
    
    console.print("\n")
    console.print(Panel(
        f"[bold]EXPERIMENT:[/bold] {analysis['experiment']['experiment']}\n\n"
        f"[bold]DATA COLLECTION:[/bold] {analysis['experiment']['data_collection']}\n\n"
        f"[bold]UPDATE:[/bold] {analysis['experiment']['update']}",
        title="🧪 TEST YOUR BELIEF",
        border_style="cyan"
    ))


def show_philosophy():
    """Display AION Capacity philosophy"""
    
    console.print("\n\n" + "="*70, style="bold magenta")
    console.print("AION CAPACITY GEM - PHILOSOPHY", style="bold magenta")
    console.print("="*70 + "\n", style="bold magenta")
    
    philosophy = """
[bold]Most AI coddles you. AION challenges you.[/bold]

Traditional AI coaching: "You're amazing! You can do anything! Believe in yourself!"
AION Capacity: "You're lying to yourself. Here's how. Here's what it's costing you. Fix it or stay stuck."

[bold cyan]Core Principles:[/bold cyan]

1. [bold]Truth over comfort[/bold]
   Most people prefer comfortable lies to uncomfortable truths.
   Growth requires the opposite.

2. [bold]Adversarial honesty[/bold]
   Challenge every excuse. Question every belief. Expose every blind spot.
   Not to be cruel—to be effective.

3. [bold]Confrontational growth[/bold]
   You have 10x more capacity than you're using.
   The gap is filled with fear masquerading as logic.

4. [bold]Private transformation[/bold]
   Your vulnerabilities are sacred. 100% local processing.
   No cloud. No tracking. No judgment.

5. [bold]Actionable intensity[/bold]
   Not motivation. Prescription.
   Do this or stay where you are. Your choice.

[bold yellow]⚠️  Warning:[/bold yellow]
This will make you uncomfortable. That's the point.
If you want affirmation, use ChatGPT.
If you want transformation, use AION Capacity.

[bold green]The Question:[/bold green]
Are you willing to confront what's stopping you?

If yes → Run the commands above.
If no → Stay comfortable. That's okay too.
"""
    
    console.print(Panel(philosophy, border_style="magenta", padding=(1, 2)))


if __name__ == "__main__":
    console.print("\n")
    console.print("╔═══════════════════════════════════════════════════════════════════╗", style="bold cyan")
    console.print("║           AION OS - HUMAN CAPACITY GEM DEMONSTRATION             ║", style="bold cyan")
    console.print("║              Adversarial Intelligence for Growth                  ║", style="bold cyan")
    console.print("╚═══════════════════════════════════════════════════════════════════╝", style="bold cyan")
    
    show_philosophy()
    
    console.print("\n")
    console.input("[bold yellow]Press Enter to run Demo 1: Capacity Gap Analysis...[/bold yellow]")
    demo_capacity_gap()
    
    console.print("\n")
    console.input("[bold yellow]Press Enter to run Demo 2: EQ Challenge...[/bold yellow]")
    demo_eq_challenge()
    
    console.print("\n")
    console.input("[bold yellow]Press Enter to run Demo 3: Belief Challenge...[/bold yellow]")
    demo_belief_challenge()
    
    console.print("\n\n" + "="*70, style="bold green")
    console.print("DEMO COMPLETE", style="bold green")
    console.print("="*70, style="bold green")
    
    console.print("\n[bold]To use in your own context:[/bold]\n")
    console.print("python -m aionos.api.capacity_cli analyze-gap --current \"...\" --desired \"...\"")
    console.print("python -m aionos.api.capacity_cli eq-challenge --situation \"...\" --response \"...\"")
    console.print("python -m aionos.api.capacity_cli challenge-belief --belief \"...\"\n")
    
    console.print("[dim]Privacy: All processing is 100% local. Nothing sent to external APIs.[/dim]\n")
