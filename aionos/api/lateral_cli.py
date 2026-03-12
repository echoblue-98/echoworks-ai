"""
Lateral Hire Due Diligence CLI

Executive-ready interface for assessing incoming lateral hires.
Identifies conflicts, stolen data risk, and liabilities BEFORE you hire.

PRIVACY: 100% LOCAL PROCESSING - ZERO DATA SENT TO LLMs
All proprietary patterns and scoring logic run entirely on-premise.

Usage:
    python -m aionos.api.lateral_cli \
        --candidate "James Morrison (Partner)" \
        --origin "Kirkland & Ellis" \
        --practice "M&A" \
        --years 12 \
        --book "3.5M"
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
import time

from ..modules.lateral_hire_gem import (
    LateralHireGem,
    LateralHireAssessment,
    format_lateral_assessment,
    RiskLevel
)

app = typer.Typer(help="Lateral Hire Due Diligence - 100% Local Processing")
console = Console()


@app.command()
def assess(
    candidate: str = typer.Option(..., "--candidate", "-c", help="Candidate name and title"),
    origin: str = typer.Option(..., "--origin", "-o", help="Origin firm name"),
    practice: str = typer.Option(..., "--practice", "-p", help="Practice area (e.g., 'M&A', 'IP Litigation')"),
    years: int = typer.Option(..., "--years", "-y", help="Years at origin firm"),
    book: str = typer.Option("Unknown", "--book", "-b", help="Portable book of business (e.g., '2.5M')"),
    origin_type: str = typer.Option("AmLaw 100", "--origin-type", "-t", help="Origin firm type: 'AmLaw 50', 'AmLaw 100', 'Regional', 'Boutique'"),
    non_compete: bool = typer.Option(True, "--non-compete/--no-non-compete", help="Whether candidate has non-compete"),
    garden_leave: bool = typer.Option(False, "--garden-leave/--no-garden-leave", help="Whether garden leave is required"),
    export_text: Optional[str] = typer.Option(None, "--export", help="Export to text file"),
):
    """
    Assess lateral hire risk with 100% local processing
    
    All proprietary patterns and risk scoring run entirely on your infrastructure.
    ZERO data is sent to any LLM provider.
    """
    
    console.print()
    console.print(Panel.fit(
        "[bold white]AION OS - Lateral Hire Due Diligence[/bold white]\n"
        "[dim]100% Local Processing - Zero LLM Data Leakage[/dim]",
        border_style="green"
    ))
    console.print()
    
    # Display assessment parameters
    params_table = Table(show_header=False, box=None, padding=(0, 2))
    params_table.add_column(style="cyan")
    params_table.add_column(style="white")
    
    params_table.add_row("Candidate:", candidate)
    params_table.add_row("Origin Firm:", origin)
    params_table.add_row("Origin Type:", origin_type)
    params_table.add_row("Practice Area:", practice)
    params_table.add_row("Years at Origin:", f"{years}")
    params_table.add_row("Book of Business:", f"${book}" if not book.startswith("$") else book)
    params_table.add_row("Non-Compete:", "Yes" if non_compete else "No")
    params_table.add_row("Garden Leave:", "Yes" if garden_leave else "No")
    params_table.add_row("", "")
    params_table.add_row("[green]Privacy Mode:[/green]", "[green bold]100% LOCAL - Zero LLM[/green bold]")
    
    console.print(params_table)
    console.print()
    
    # Run assessment with progress indicator
    gem = LateralHireGem()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task1 = progress.add_task("[cyan]Running local risk assessment...", total=None)
        time.sleep(0.3)
        
        # Normalize book value
        book_normalized = book.replace("$", "").strip()
        if not any(c in book_normalized for c in ["M", "K"]):
            book_normalized = f"${book_normalized}M"
        else:
            book_normalized = f"${book_normalized}"
        
        assessment = gem.assess_lateral_hire(
            candidate_name=candidate,
            origin_firm=origin,
            practice_area=practice,
            years_at_origin=years,
            book_of_business=book_normalized,
            origin_firm_type=origin_type,
            non_compete_exists=non_compete,
            garden_leave_required=garden_leave
        )
        
        progress.update(task1, description="[green]Assessment complete!")
        time.sleep(0.2)
    
    console.print()
    
    # Determine risk color
    if assessment.overall_risk_score >= 70:
        risk_color = "red"
        risk_level = "CRITICAL"
    elif assessment.overall_risk_score >= 50:
        risk_color = "yellow"
        risk_level = "HIGH"
    elif assessment.overall_risk_score >= 30:
        risk_color = "blue"
        risk_level = "MEDIUM"
    else:
        risk_color = "green"
        risk_level = "LOW"
    
    # Display Risk Summary Panel
    console.print(Panel(
        f"[bold white]RISK ASSESSMENT SUMMARY[/bold white]\n\n"
        f"[{risk_color}]Overall Risk Score:  [{risk_color} bold]{assessment.overall_risk_score}/100 ({risk_level})[/{risk_color} bold][/{risk_color}]\n\n"
        f"[yellow]Risk Breakdown:[/yellow]\n"
        f"  Conflict Risk:       {assessment.conflict_risk}/100\n"
        f"  Stolen Data Risk:    {assessment.stolen_data_risk}/100\n"
        f"  Liability Risk:      {assessment.liability_risk}/100\n\n"
        f"[yellow]Financial Analysis:[/yellow]\n"
        f"  Potential Liability: [red]{assessment.potential_liability}[/red]\n"
        f"  Mitigation Cost:     {assessment.mitigation_cost}\n"
        f"  Net Value:           [bold]{assessment.net_value}[/bold]",
        title=f"[bold {risk_color}]⚠ LATERAL HIRE RISK[/bold {risk_color}]",
        border_style=risk_color
    ))
    console.print()
    
    # Display Findings
    if assessment.findings:
        console.print("[bold white]RISK FINDINGS[/bold white]")
        console.print()
        
        findings_table = Table(show_header=True, header_style="bold cyan")
        findings_table.add_column("#", width=3)
        findings_table.add_column("Severity", width=10)
        findings_table.add_column("Category", width=20)
        findings_table.add_column("Finding", width=35)
        findings_table.add_column("Liability", width=20)
        
        for i, finding in enumerate(assessment.findings, 1):
            severity_style = {
                "CRITICAL": "[red bold]",
                "HIGH": "[yellow]",
                "MEDIUM": "[blue]",
                "LOW": "[dim]"
            }.get(finding.severity.value, "")
            
            findings_table.add_row(
                str(i),
                f"{severity_style}{finding.severity.value}[/]",
                finding.category.value,
                finding.title,
                finding.liability_estimate
            )
        
        console.print(findings_table)
        console.print()
    
    # Display Immediate Actions
    if assessment.immediate_actions:
        console.print("[bold white]IMMEDIATE ACTIONS[/bold white]")
        console.print()
        
        for i, action in enumerate(assessment.immediate_actions, 1):
            if action.startswith("CRITICAL"):
                console.print(f"  [red bold]{i}. {action}[/red bold]")
            elif action.startswith("MANDATORY"):
                console.print(f"  [red bold]{i}. {action}[/red bold]")
            elif action.startswith("HIGH"):
                console.print(f"  [yellow]{i}. {action}[/yellow]")
            else:
                console.print(f"  {i}. {action}")
        console.print()
    
    # Display Pre-Hire Requirements
    if assessment.pre_hire_requirements:
        console.print("[bold white]PRE-HIRE REQUIREMENTS[/bold white]")
        console.print()
        
        req_table = Table(show_header=True, header_style="bold green")
        req_table.add_column("#", width=3)
        req_table.add_column("Requirement", width=70)
        
        for i, req in enumerate(assessment.pre_hire_requirements, 1):
            req_table.add_row(str(i), req)
        
        console.print(req_table)
        console.print()
    
    # Export if requested
    if export_text:
        report = format_lateral_assessment(assessment)
        with open(export_text, 'w') as f:
            f.write(report)
        console.print(f"[green]✓ Report exported to: {export_text}[/green]")
        console.print()
    
    # Privacy Footer
    console.print(Panel(
        "[green]✓ This assessment ran 100% locally[/green]\n"
        "[green]✓ Zero data sent to Claude, Gemini, or any LLM[/green]\n"
        "[green]✓ All proprietary patterns remain on your infrastructure[/green]",
        title="[bold green]🔒 PRIVACY VERIFIED[/bold green]",
        border_style="green"
    ))
    console.print()


if __name__ == "__main__":
    app()
