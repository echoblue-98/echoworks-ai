"""
Attorney Departure Risk Assessment CLI

Executive-ready command-line interface for attorney departure risk analysis.
Designed for demos, client presentations, and professional deliverables.

Usage:
    python -m aionos.api.departure_cli assess \
        --attorney "Sarah Mitchell (Managing Partner)" \
        --practice "Corporate M&A" \
        --years 22

    python -m aionos.api.departure_cli assess \
        --attorney "Michael Chen" \
        --practice "IP Litigation" \
        --years 15 \
        --destination "Tech Law Group" \
        --export-pdf report.pdf
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional, Dict
import time

from ..modules.attorney_departure_gem import (
    AttorneyDepartureGem,
    format_executive_report
)

app = typer.Typer(help="Attorney Departure Risk Assessment - Executive Edition")
console = Console()


@app.command()
def assess(
    attorney: str = typer.Option(..., "--attorney", "-a", help="Attorney name and title (e.g., 'Sarah Mitchell (Managing Partner)')"),
    practice: str = typer.Option(..., "--practice", "-p", help="Practice area (e.g., 'Corporate M&A')"),
    years: int = typer.Option(..., "--years", "-y", help="Years at firm"),
    destination: str = typer.Option("Unknown", "--destination", "-d", help="Destination firm (if known)"),
    notice_days: int = typer.Option(30, "--notice-days", "-n", help="Days until departure"),
    export_pdf: Optional[str] = typer.Option(None, "--export-pdf", help="Export to PDF file"),
    use_claude: bool = typer.Option(False, "--claude", help="Use Claude instead of Gemini"),
):
    """
    Assess attorney departure risk with executive-ready analysis
    
    Produces professional risk assessment suitable for C-suite presentation,
    client deliverables, and demo scenarios.
    """
    
    console.print()
    console.print(Panel.fit(
        "[bold white]AION OS - Attorney Departure Risk Assessment[/bold white]\n"
        "[dim]Adversarial Intelligence for Law Firm Security[/dim]",
        border_style="red"
    ))
    console.print()
    
    # Display analysis parameters
    params_table = Table(show_header=False, box=None, padding=(0, 2))
    params_table.add_column(style="cyan")
    params_table.add_column(style="white")
    
    params_table.add_row("Attorney:", attorney)
    params_table.add_row("Practice Area:", practice)
    params_table.add_row("Tenure:", f"{years} years")
    params_table.add_row("Destination:", destination)
    params_table.add_row("Notice Period:", f"{notice_days} days")
    params_table.add_row("AI Engine:", "Claude Sonnet 4" if use_claude else "Google Gemini 2.0")
    
    console.print(params_table)
    console.print()
    
    # Run analysis with progress indicator
    gem = AttorneyDepartureGem(use_gemini=not use_claude)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task1 = progress.add_task("[cyan]Running adversarial analysis...", total=None)
        time.sleep(0.5)
        
        try:
            assessment = gem.assess_departure_risk(
                attorney_name=attorney,
                practice_area=practice,
                years_tenure=years,
                destination=destination,
                notice_days=notice_days
            )
            
            progress.update(task1, description="[green]Analysis complete!")
            time.sleep(0.3)
            
        except Exception as e:
            console.print(f"\n[red]Error during analysis: {e}[/red]")
            raise typer.Exit(1)
    
    console.print()
    
    # Display Executive Summary
    summary = assessment["executive_summary"]
    
    console.print(Panel(
        f"[bold white]EXECUTIVE SUMMARY[/bold white]\n\n"
        f"[yellow]Financial Risk:[/yellow]\n"
        f"  Expected Loss:  [red bold]{summary.expected_loss}[/red bold]\n"
        f"  AION Cost:      [green]{summary.aion_cost}[/green]\n"
        f"  ROI Multiple:   [green bold]{summary.roi_multiple}[/green bold]\n\n"
        f"[yellow]Risk Profile:[/yellow]\n"
        f"  Critical:       [red bold]{summary.critical_vulnerabilities}[/red bold]\n"
        f"  High:           [yellow]{summary.high_vulnerabilities}[/yellow]\n"
        f"  Total:          {summary.total_vulnerabilities}\n\n"
        f"[yellow]Timeline:[/yellow]\n"
        f"  Departure:      {summary.departure_date}\n"
        f"  Urgency:        [red bold]{summary.urgency_level}[/red bold]",
        title="[bold red]⚠ RISK ASSESSMENT[/bold red]",
        border_style="red"
    ))
    console.print()
    
    # Pattern Match
    pattern = assessment.get("pattern_match")
    if pattern:
        console.print(Panel(
            f"[bold cyan]Historical Pattern Match[/bold cyan]\n\n"
            f"Similar Case:     {pattern['pattern_name']}\n"
            f"Similarity:       [yellow]{pattern['similarity']}[/yellow]\n"
            f"Previous Outcome: {pattern['previous_outcome']}",
            border_style="cyan"
        ))
        console.print()
    
    # Top Risk Findings
    findings = assessment["risk_findings"]
    if findings:
        console.print("[bold white]TOP RISK FINDINGS[/bold white]")
        console.print()
        
        findings_table = Table(show_header=True, header_style="bold cyan")
        findings_table.add_column("#", width=3)
        findings_table.add_column("Severity", width=10)
        findings_table.add_column("Finding", width=50)
        findings_table.add_column("Impact", width=30)
        
        for i, finding in enumerate(findings[:5], 1):
            severity_style = {
                "CRITICAL": "[red bold]",
                "HIGH": "[yellow]",
                "MEDIUM": "[blue]",
                "LOW": "[dim]"
            }.get(finding.severity.value, "")
            
            findings_table.add_row(
                str(i),
                f"{severity_style}{finding.severity.value}[/]",
                finding.title,
                finding.impact
            )
        
        console.print(findings_table)
        console.print()
    
    # Immediate Actions
    actions = assessment["immediate_actions"]
    if actions:
        console.print("[bold white]IMMEDIATE ACTIONS[/bold white]")
        console.print()
        
        actions_table = Table(show_header=True, header_style="bold green")
        actions_table.add_column("#", width=3)
        actions_table.add_column("Priority", width=10)
        actions_table.add_column("Action", width=50)
        actions_table.add_column("Timeline", width=15)
        actions_table.add_column("Owner", width=15)
        
        for i, action in enumerate(actions, 1):
            priority_style = {
                "CRITICAL": "[red bold]",
                "HIGH": "[yellow]",
                "MEDIUM": "[blue]"
            }.get(action.priority, "")
            
            actions_table.add_row(
                str(i),
                f"{priority_style}{action.priority}[/]",
                action.action,
                action.timeline,
                action.owner
            )
        
        console.print(actions_table)
        console.print()
    
    # Export to PDF if requested
    if export_pdf:
        console.print(f"[cyan]Exporting to PDF: {export_pdf}[/cyan]")
        try:
            export_to_pdf(assessment, export_pdf)
            console.print(f"[green]✓ PDF report generated: {export_pdf}[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ PDF export failed: {e}[/yellow]")
            console.print("[dim]Tip: Install reportlab: pip install reportlab[/dim]")
    
    # Footer
    console.print()
    console.print(Panel(
        f"[dim]Analysis complete. Prevention cost: {summary.aion_cost} | "
        f"Risk prevented: {summary.expected_loss} | ROI: {summary.roi_multiple}[/dim]",
        style="dim"
    ))
    console.print()


def export_to_pdf(assessment: Dict, filename: str):
    """Export assessment to PDF (placeholder - requires reportlab)"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        # Create PDF
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#ff4444'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph("ATTORNEY DEPARTURE RISK ASSESSMENT", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Executive Summary
        summary = assessment["executive_summary"]
        
        summary_data = [
            ["Attorney:", summary.attorney_name],
            ["Practice Area:", summary.practice_area],
            ["Tenure:", f"{summary.years_tenure} years"],
            ["Destination:", summary.destination],
            ["Departure Date:", summary.departure_date],
            ["", ""],
            ["Expected Loss:", summary.expected_loss],
            ["AION Cost:", summary.aion_cost],
            ["ROI Multiple:", summary.roi_multiple],
            ["", ""],
            ["Critical Vulnerabilities:", str(summary.critical_vulnerabilities)],
            ["High Vulnerabilities:", str(summary.high_vulnerabilities)],
            ["Total Vulnerabilities:", str(summary.total_vulnerabilities)],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#444444')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
        
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Risk Findings
        story.append(Paragraph("TOP RISK FINDINGS", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        findings = assessment["risk_findings"]
        for i, finding in enumerate(findings[:5], 1):
            story.append(Paragraph(
                f"<b>{i}. [{finding.severity.value}] {finding.title}</b>",
                styles['Normal']
            ))
            story.append(Paragraph(f"Impact: {finding.impact}", styles['Normal']))
            story.append(Paragraph(f"Recommendation: {finding.recommendation}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Immediate Actions
        story.append(PageBreak())
        story.append(Paragraph("IMMEDIATE ACTIONS", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        actions = assessment["immediate_actions"]
        for i, action in enumerate(actions, 1):
            story.append(Paragraph(
                f"<b>{i}. [{action.priority}] {action.action}</b>",
                styles['Normal']
            ))
            story.append(Paragraph(
                f"Timeline: {action.timeline} | Owner: {action.owner}",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        
    except ImportError:
        # Fallback to text export
        text_report = format_executive_report(assessment)
        with open(filename.replace('.pdf', '.txt'), 'w') as f:
            f.write(text_report)
        raise Exception("reportlab not installed - exported as .txt instead")


if __name__ == "__main__":
    app()
