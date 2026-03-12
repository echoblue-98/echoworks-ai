"""
Attorney Departure Risk Analysis Demo

Demonstrates the critical enterprise feature for law firms:
analyzing vulnerabilities when attorneys leave.
"""

from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aionos.modules.attorney_departure import (
    AttorneyDepartureAnalyzer,
    AttorneyProfile,
    ActiveCase
)


def main():
    console = Console()
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold red]ATTORNEY DEPARTURE RISK ANALYSIS[/bold red]\n\n"
        "[yellow]Enterprise Feature for Law Firms[/yellow]\n"
        "When attorneys leave, vulnerability windows open.\n"
        "AION OS identifies risks BEFORE they become problems.",
        border_style="red",
        padding=(1, 2)
    ))
    console.print("="*80 + "\n")
    
    # Scenario setup
    console.print("[bold cyan]SCENARIO:[/bold cyan]")
    console.print("Senior partner with 12 years at firm is departing to competitor.")
    console.print("5 active cases worth $10M+ total")
    console.print("Trial in 45 days on largest case")
    console.print("Notice period: 30 days")
    console.print()
    
    # Create departing attorney profile
    attorney = AttorneyProfile(
        attorney_id="ATT001",
        name="Sarah Chen, Partner",
        practice_area="Complex Commercial Litigation & Securities",
        years_at_firm=12,
        active_cases=["CASE001", "CASE002", "CASE003", "CASE004", "CASE005"],
        client_relationships=[
            "MegaCorp Industries ($2M annual)",
            "TechStartup Ventures ($1.5M annual)",
            "Global Finance Inc ($3M annual)",
            "Manufacturing Co ($800K annual)"
        ],
        specialized_knowledge=[
            "Securities fraud litigation (expert level)",
            "Class action defense strategy",
            "Expert witness cross-examination techniques",
            "Federal court procedure (9th Circuit)",
            "Complex e-discovery management"
        ],
        system_access=[
            "Case Management System (admin)",
            "Document Repository (full access)",
            "Client Portal (all clients)",
            "Billing System",
            "Email with 12 years of correspondence",
            "VPN (remote access)",
            "Physical building key",
            "Partner-level dashboards"
        ],
        departure_date=datetime.now() + timedelta(days=30),
        destination_firm="Wheeler & Associates LLP (Competitor)",
        notice_period_days=30
    )
    
    # Create active cases
    cases = [
        ActiveCase(
            case_id="CASE001",
            case_name="MegaCorp v. Securities Commission",
            client="MegaCorp Industries",
            lead_attorney="Sarah Chen",
            supporting_attorneys=["Junior Associate (2 years experience)"],
            trial_date=datetime.now() + timedelta(days=45),
            case_value=5000000,
            complexity_score=9,
            documentation_completeness=0.45  # Only 45% documented!
        ),
        ActiveCase(
            case_id="CASE002",
            case_name="TechStartup Class Action Defense",
            client="TechStartup Ventures",
            lead_attorney="Sarah Chen",
            supporting_attorneys=[],  # No support!
            trial_date=datetime.now() + timedelta(days=120),
            case_value=3000000,
            complexity_score=8,
            documentation_completeness=0.55
        ),
        ActiveCase(
            case_id="CASE003",
            case_name="Global Finance v. Regulatory Authority",
            client="Global Finance Inc",
            lead_attorney="Sarah Chen",
            supporting_attorneys=["Mid-level Associate"],
            trial_date=datetime.now() + timedelta(days=180),
            case_value=2500000,
            complexity_score=7,
            documentation_completeness=0.60
        ),
        ActiveCase(
            case_id="CASE004",
            case_name="Manufacturing Co Contract Dispute",
            client="Manufacturing Co",
            lead_attorney="Sarah Chen",
            supporting_attorneys=["Junior Associate"],
            case_value=800000,
            complexity_score=5,
            documentation_completeness=0.70
        ),
        ActiveCase(
            case_id="CASE005",
            case_name="MegaCorp Employment Matter",
            client="MegaCorp Industries",
            lead_attorney="Sarah Chen",
            supporting_attorneys=["Senior Associate"],
            case_value=400000,
            complexity_score=6,
            documentation_completeness=0.65
        ),
    ]
    
    # Display case overview
    case_table = Table(title="Active Cases at Risk", border_style="yellow")
    case_table.add_column("Case", style="cyan")
    case_table.add_column("Value", justify="right", style="green")
    case_table.add_column("Trial Date", style="yellow")
    case_table.add_column("Docs %", justify="right", style="red")
    
    for case in cases:
        trial_str = case.trial_date.strftime("%Y-%m-%d") if case.trial_date else "No trial set"
        case_table.add_row(
            case.case_name[:35],
            f"${case.case_value:,.0f}",
            trial_str,
            f"{case.documentation_completeness*100:.0f}%"
        )
    
    console.print(case_table)
    console.print()
    
    # Run adversarial analysis
    console.print("[bold red]>>> RUNNING ADVERSARIAL ANALYSIS...[/bold red]\n")
    
    analyzer = AttorneyDepartureAnalyzer()
    result = analyzer.analyze_departure(
        attorney=attorney,
        active_cases=cases,
        firm_context={
            "firm_size": 150,
            "practice_areas": ["Litigation", "Corporate", "IP"],
            "conflict_check_system": "automated"
        }
    )
    
    # Display risk score
    console.print("="*80)
    risk_score = result["risk_score"]
    risk_level = result["risk_level"]
    
    risk_color = "red" if risk_score >= 70 else "yellow" if risk_score >= 50 else "green"
    console.print(
        f"[bold {risk_color}]OVERALL RISK SCORE: {risk_score}/100 ({risk_level})[/bold {risk_color}]"
    )
    console.print("="*80 + "\n")
    
    # Display vulnerabilities
    console.print(result["formatted_output"])
    
    # Display critical actions
    console.print("\n" + "="*80)
    console.print("[bold red]CRITICAL ACTIONS REQUIRED (Next 48 Hours):[/bold red]")
    console.print("="*80)
    
    for i, action in enumerate(result["critical_actions"], 1):
        console.print(f"{i}. {action}")
    
    # Display transition plan
    console.print("\n" + "="*80)
    console.print("[bold cyan]30-DAY TRANSITION PLAN:[/bold cyan]")
    console.print("="*80 + "\n")
    
    plan = result["transition_plan"]
    
    for phase, actions in plan.items():
        console.print(f"[bold yellow]{phase.upper().replace('_', ' ')}:[/bold yellow]")
        for action in actions:
            console.print(f"  • {action}")
        console.print()
    
    # Value proposition
    console.print("="*80)
    console.print(Panel.fit(
        "[bold green]ENTERPRISE VALUE PROPOSITION[/bold green]\n\n"
        "[yellow]Without AION OS:[/yellow]\n"
        "• Knowledge walks out the door\n"
        "• Cases suffer from transition gaps\n"
        "• Clients leave during confusion\n"
        "• Opposing counsel exploits weakness\n"
        "• Security breaches and data exfiltration\n"
        "• Average cost per partner departure: $500K-$2M\n\n"
        "[green]With AION OS:[/green]\n"
        "• Vulnerabilities identified in 24 hours\n"
        "• Structured transition plan\n"
        "• No knowledge loss\n"
        "• Client retention >90%\n"
        "• Security risks mitigated\n"
        "• ROI: 10-20x on prevented losses\n\n"
        "[bold cyan]Pricing: $10K-$50K per partner departure analysis[/bold cyan]",
        border_style="green",
        padding=(1, 2)
    ))
    console.print("="*80 + "\n")
    
    # Real-world impact
    console.print("[bold magenta]REAL-WORLD IMPACT:[/bold magenta]")
    console.print()
    console.print("This scenario (trial in 45 days, 45% documentation) is EXTREMELY common.")
    console.print("Most law firms discover these gaps AFTER the attorney leaves.")
    console.print("By then, it's too late:")
    console.print("  • Opposing counsel has filed complex motions")
    console.print("  • Clients are panicking")
    console.print("  • Successor attorney is drowning")
    console.print()
    console.print("[bold red]AION OS identifies the problem BEFORE departure,[/bold red]")
    console.print("[bold red]giving you 30 days to close the gap.[/bold red]")
    console.print()
    console.print("That's the difference between losing a $5M case and winning it.")
    console.print()


if __name__ == "__main__":
    main()
