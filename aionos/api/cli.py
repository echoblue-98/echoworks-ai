"""
CLI - Terminal-native interface for AION OS

Portable, pipe-friendly adversarial intelligence you can take anywhere.
"""

import typer
import sys
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from typing import Optional

from aionos.modules.legal_analyzer import LegalAnalyzer
from aionos.modules.security_redteam import SecurityRedTeam
from aionos.modules.heist_planner import HeistPlanner
from aionos.core.adversarial_engine import IntensityLevel
from aionos.safety.audit_logger import AuditLogger


app = typer.Typer(
    name="aionos",
    help="AION OS - Terminal-native adversarial intelligence",
    add_completion=True,
    no_args_is_help=True
)
console = Console()
audit_logger = AuditLogger()


def _show_executive_summary(result: dict):
    """Display executive summary with ROI front and center"""
    financial = result.get('financial_analysis')
    timeline = result.get('timeline_analysis')
    vulnerabilities = result.get('vulnerabilities', [])
    
    # Count critical vulnerabilities
    critical_count = sum(1 for v in vulnerabilities if v.get('severity') in ['critical', 'high'])
    
    if financial:
        expected_loss = financial['total_financial_risk']['expected']
        roi_multiple = financial['aion_roi']['roi_multiple']
        analysis_cost = financial['aion_roi']['analysis_cost']
        
        # Build the summary box
        summary_box = f"""
╔════════════════════════════════════════════════════════════╗
║                   EXECUTIVE SUMMARY                        ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  FINANCIAL RISK:     ${expected_loss:,.0f}                ║
║  AION COST:          ${analysis_cost:,.0f}                ║
║  ROI MULTIPLIER:     {roi_multiple}x                       ║
║                                                            ║
║  ⚠️  {critical_count} CRITICAL VULNERABILITIES FOUND               ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
"""
        console.print(f"[bold red]{summary_box}[/bold red]")
        
        # Show urgency if timeline available
        if timeline:
            departure_info = timeline['departure_timeline']
            days_left = departure_info.get('days_until_departure', 30)
            
            if days_left <= 7:
                urgency = "[bold red]⚠️ CRITICAL - 72 HOURS TO ACT[/bold red]"
            elif days_left <= 14:
                urgency = "[bold yellow]⚠️ URGENT - 2 WEEKS OR LESS[/bold yellow]"
            elif days_left <= 30:
                urgency = "[bold yellow]⚠️ HIGH PRIORITY - 30 DAYS[/bold yellow]"
            else:
                urgency = "[yellow]⚠️ MONITOR CLOSELY[/yellow]"
            
            console.print(f"\n{urgency}\n")


console = Console()
audit_logger = AuditLogger()


def output_result(result: dict, format: str = "pretty"):
    """Output results in requested format"""
    if format == "json":
        console.print_json(data=result)
    elif format == "markdown":
        md = _format_markdown(result)
        console.print(Markdown(md))
    else:  # pretty (default)
        _print_pretty(result)


def _format_markdown(result: dict) -> str:
    """Format results as markdown"""
    lines = [
        f"# AION OS Analysis",
        f"\n**Timestamp:** {result.get('timestamp', 'N/A')}",
        f"**Agents Used:** {len(result.get('agents_used', []))}",
        f"**Vulnerabilities:** {len(result.get('vulnerabilities', []))}",
        f"**Cost:** ${result.get('cost', 0):.4f}",
        f"\n## Findings\n"
    ]
    
    for vuln in result.get('vulnerabilities', []):
        lines.append(f"### {vuln.get('title', 'Finding')}")
        lines.append(f"**Severity:** {vuln.get('severity', 'unknown')}")
        lines.append(f"{vuln.get('description', '')}\n")
    
    return "\n".join(lines)


def _print_pretty(result: dict):
    """Pretty print with live adversarial attack visualization"""
    
    # Executive summary moved to separate function - called before this
    
    # Show agents attacking in real-time style
    console.print("\n[bold red]═══ DETAILED VULNERABILITY ANALYSIS ═══[/bold red]\n")
    
    for i, vuln in enumerate(result.get('vulnerabilities', []), 1):
        agent = vuln.get('agent', 'Unknown Agent')
        severity = vuln.get('severity', 'medium')
        description = vuln.get('full_findings', vuln.get('description', ''))[:150]  # Reduced from 200
        
        # Color coding
        severity_color = {
            'critical': 'red',
            'high': 'orange1', 
            'medium': 'yellow',
            'low': 'green'
        }.get(severity, 'white')
        
        severity_icon = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(severity, '⚪')
        
        # Print agent attack
        console.print(f"[bold cyan]▶ Agent {i}: {agent}[/bold cyan]")
        console.print(f"  [italic]\"{description}...\"[/italic]")
        console.print(f"  [{severity_color}]{severity_icon} {severity.upper()}[/{severity_color}]\n")
    
    # Summary
    cost = result.get('cost', 0)
    console.print(f"[bold red]{'─' * 50}[/bold red]")
    console.print(f"[bold white]ATTACK COMPLETE:[/bold white] {len(result.get('vulnerabilities', []))} vulnerabilities found")
    console.print(f"[dim]Cost: ${cost:.4f}[/dim]\n")
    
    # Display pattern match if found
    pattern_match = result.get('pattern_match')
    if pattern_match and pattern_match.get('pattern_match_found'):
        console.print("[bold yellow]📊 HISTORICAL PATTERN MATCH[/bold yellow]")
        similar_case = pattern_match['similar_case']
        console.print(f"  Similar to: [cyan]{similar_case['name']}[/cyan] ({similar_case['similarity']} match)")
        console.print(f"  Previous outcome: [dim]{similar_case['outcome']}[/dim]\n")
    
    # Display financial ROI analysis
    financial = result.get('financial_analysis')
    if financial:
        console.print("[bold green]💰 FINANCIAL RISK ANALYSIS[/bold green]")
        total_risk = financial['total_financial_risk']
        console.print(f"  Total Risk: [red]${total_risk['minimum']:,.0f} - ${total_risk['maximum']:,.0f}[/red]")
        console.print(f"  Expected Loss: [red bold]${total_risk['expected']:,.0f}[/red bold]")
        
        roi = financial['aion_roi']
        console.print(f"\n  AION Analysis Cost: [green]${roi['analysis_cost']:,.0f}[/green]")
        console.print(f"  ROI Multiple: [bold green]{roi['roi_multiple']}[/bold green]")
        console.print(f"  Net Value: [green]${roi['net_value']:,.0f}[/green]\n")
        
        # Executive summary
        console.print(f"  [italic]{financial['executive_summary']}[/italic]\n")
    
    # Display timeline analysis
    timeline = result.get('timeline_analysis')
    if timeline:
        console.print("[bold magenta]📅 TIMELINE BREACH ANALYSIS[/bold magenta]")
        departure_info = timeline['departure_timeline']
        console.print(f"  Departure Date: [yellow]{departure_info['departure_date']}[/yellow] ({departure_info['days_until_departure']} days)")
        console.print(f"  Current Phase: [red]{departure_info['current_phase'].upper()}[/red]\n")
        
        # Show high-risk windows
        high_risk = timeline['high_risk_windows']
        if high_risk:
            console.print("  [bold]High-Risk Windows:[/bold]")
            for window in high_risk[:3]:  # Show top 3
                console.print(f"    • [{window['risk_level']}] {window['window_name']}")
                console.print(f"      {window['date_range']}")
                console.print(f"      [dim]{window['description']}[/dim]\n")
        
        # Show critical dates
        critical_dates = timeline['critical_audit_dates']
        if critical_dates:
            console.print("  [bold]Critical Audit Dates:[/bold]")
            for date_info in critical_dates[:3]:  # Show top 3
                console.print(f"    • [yellow]{date_info['date']}[/yellow]: {date_info['event']}")
                console.print(f"      [dim]{date_info['action']}[/dim]\n")
    
    # Add immediate actions section
    _show_immediate_actions(result)


def _show_immediate_actions(result: dict):
    """Display concrete actions to take immediately"""
    timeline = result.get('timeline_analysis')
    vulnerabilities = result.get('vulnerabilities', [])
    
    console.print("\n[bold yellow]═══ IMMEDIATE ACTIONS (NEXT 72 HOURS) ═══[/bold yellow]\n")
    
    # Extract top 3 actionable items
    critical_vulns = [v for v in vulnerabilities if v.get('severity') in ['critical', 'high']][:3]
    
    if critical_vulns:
        actions = [
            "1. [bold]Audit email forwarding rules[/bold] - Check rules created in last 30 days",
            "2. [bold]Review VPN access logs[/bold] - Flag after-hours or unusual locations", 
            "3. [bold]Monitor document downloads[/bold] - Set alerts for bulk file access"
        ]
        
        # If we have timeline data, make it more specific
        if timeline:
            departure_info = timeline.get('departure_timeline', {})
            days_left = departure_info.get('days_until_departure', 30)
            
            if days_left <= 7:
                actions = [
                    "1. [bold red]DISABLE VPN ACCESS[/bold red] outside business hours - effective immediately",
                    "2. [bold red]ESCORT POLICY[/bold red] - No unattended office access during final week",
                    "3. [bold red]FREEZE SYSTEM PERMISSIONS[/bold red] - Revoke document management write access"
                ]
        
        for action in actions:
            console.print(f"   {action}")
        
        console.print(f"\n[dim]Full action plan available in detailed report above.[/dim]")
        console.print(f"[bold cyan]→ Schedule follow-up: Contact your AION consultant[/bold cyan]\n")
    else:
        console.print("   [green]✓ No critical actions required at this time[/green]")
        console.print("   [dim]Continue quarterly monitoring as planned.[/dim]\n")



@app.command()
def legal(
    file: Optional[Path] = typer.Argument(None, help="Legal document to analyze"),
    intensity: int = typer.Option(3, "--intensity", "-i", help="Attack intensity (1-5)"),
    format: str = typer.Option("pretty", "--format", "-f", help="Output: pretty, json, markdown"),
    stdin: bool = typer.Option(False, "--stdin", help="Read from stdin (pipe support)"),
    use_gemini: bool = typer.Option(False, "--gemini", help="Use Gemini API for analysis")
):
    """
    Analyze legal documents - briefs, contracts, arguments.
    
    Examples:
        aionos legal brief.txt
        aionos legal brief.txt --intensity 5 --format json
        cat contract.txt | aionos legal --stdin
    """
    
    # Read content from file or stdin
    if stdin or not sys.stdin.isatty():
        content = sys.stdin.read()
    elif file and file.exists():
        content = file.read_text(encoding='utf-8')
    else:
        console.print("[red]Error: Provide a file or pipe content via stdin[/red]")
        raise typer.Exit(1)
    
    if not content.strip():
        console.print("[red]Error: No content to analyze[/red]")
        raise typer.Exit(1)
    
    # Run analysis
    console.print(f"\n[bold yellow]Deploying 5 adversarial agents against your brief...[/bold yellow]")
    console.print("[dim]Each agent will attack from a different perspective[/dim]\n")
    
    with console.status(f"[bold red]Agents attacking...", spinner="dots"):
        analyzer = LegalAnalyzer(intensity=IntensityLevel(intensity), use_gemini=use_gemini)
        result = analyzer.analyze_brief(content, {})
    
    # Output
    output_result(result, format)


@app.command()
def security(
    file: Path = typer.Option(..., "--file", "-f", help="Path to infrastructure config"),
    intensity: int = typer.Option(4, "--intensity", "-i", help="Intensity level (1-5)", min=1, max=5),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to file"),
    user_id: str = typer.Option("cli_user", "--user", help="User ID for audit logging"),
    use_gemini: bool = typer.Option(False, "--gemini", help="Use Gemini API for analysis")
):
    """
    Red team security infrastructure.
    
    Assumes breach mentality to find:
    - Configuration vulnerabilities
    - Attack vectors
    - Privilege escalation paths
    - Lateral movement opportunities
    """
    console.print(Panel.fit(
        "[bold red]AION OS - Security Red Team[/bold red]\n"
        "Adversarial intelligence mode: MAXIMUM",
        border_style="red"
    ))
    
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)
    
    # Read file
    content = file.read_text(encoding='utf-8')
    console.print(f"\n[yellow]Red teaming: {file}[/yellow]")
    console.print(f"[yellow]Intensity Level: {intensity}/5[/yellow]")
    console.print("[yellow]Assuming breach...[/yellow]\n")
    
    # Log query
    query_id = audit_logger.log_query(
        user_id=user_id,
        query=f"Red team infrastructure: {file.name}",
        context={"file_path": str(file), "intensity": intensity}
    )
    
    # Run analysis
    red_team = SecurityRedTeam(intensity=IntensityLevel(intensity), use_gemini=use_gemini)
    result = red_team.scan_infrastructure(content)
    
    # Log analysis
    summary = result.get("summary", {})
    audit_logger.log_analysis(
        query_id=query_id,
        user_id=user_id,
        analysis_type="security_red_team",
        perspectives_used=result.get("perspectives_used", result.get("agents_used", [])),
        vulnerabilities_found=len(result.get("vulnerabilities", [])),
        critical_count=summary.get("critical_p0", 0) + summary.get("high_p1", 0),
        blocked=result.get("blocked", False)
    )
    
    # Display results
    if use_gemini:
        output_result(result, "pretty")
    else:
        console.print(result["formatted_output"])
    
    # Save to file if requested
    if output:
        if use_gemini:
            output.write_text(json.dumps(result, indent=2), encoding='utf-8')
        else:
            output.write_text(result["formatted_output"], encoding='utf-8')
        console.print(f"\n[green]Results saved to: {output}[/green]")


@app.command()
def audit_logs(
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    event_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by event type"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results to show")
):
    """
    Query audit logs.
    
    View logged queries, analyses, and ethical violations.
    """
    console.print(Panel.fit(
        "[bold cyan]AION OS - Audit Logs[/bold cyan]",
        border_style="cyan"
    ))
    
    logs = audit_logger.query_logs(
        user_id=user,
        event_type=event_type,
        limit=limit
    )
    
    if not logs:
        console.print("[yellow]No logs found matching criteria[/yellow]")
        return
    
    for log in logs:
        timestamp = log.get("timestamp", "Unknown")
        event = log.get("event_type", "unknown")
        user_id = log.get("user_id", "unknown")
        
        console.print(f"\n[cyan]{timestamp}[/cyan] | [yellow]{event}[/yellow] | User: {user_id}")
        
        if event == "query":
            query = log.get("query", "")[:100]
            console.print(f"  Query: {query}...")
        
        elif event == "analysis":
            analysis_type = log.get("analysis_type", "unknown")
            vulns = log.get("vulnerabilities_found", 0)
            critical = log.get("critical_vulnerabilities", 0)
            console.print(f"  Type: {analysis_type} | Vulns: {vulns} | Critical: {critical}")
        
        elif event == "ethical_violation":
            violation_type = log.get("violation_type", "unknown")
            message = log.get("violation_message", "")
            console.print(f"  [red]VIOLATION: {violation_type}[/red]")
            console.print(f"  {message}")


@app.command()
def stats():
    """
    Show AION OS statistics.
    
    Display usage statistics and audit log summary.
    """
    console.print(Panel.fit(
        "[bold green]AION OS - Statistics[/bold green]",
        border_style="green"
    ))
    
    stats = audit_logger.get_statistics()
    
    console.print(f"\n[cyan]Total Log Entries:[/cyan] {stats['total_entries']}")
    console.print(f"[cyan]Ethical Violations:[/cyan] {stats['violations']}")
    
    console.print("\n[yellow]Events by Type:[/yellow]")
    for event_type, count in stats.get("by_event_type", {}).items():
        console.print(f"  {event_type}: {count}")
    
    if stats.get("by_severity"):
        console.print("\n[yellow]Events by Severity:[/yellow]")
        for severity, count in stats["by_severity"].items():
            console.print(f"  {severity}: {count}")


@app.command()
def demo():
    """
    Run the comparison demo.
    
    Shows side-by-side comparison of Standard AI vs AION OS.
    """
    from demo_comparison import run_full_demo
    run_full_demo()


@app.command()
def attorney(
    name: str = typer.Option(..., "--name", "-n", help="Attorney name"),
    practice: str = typer.Option(..., "--practice", "-p", help="Practice area"),
    years: int = typer.Option(5, "--years", "-y", help="Years at firm"),
    cases: str = typer.Option("", "--cases", "-c", help="Active cases"),
    clients: str = typer.Option("", "--clients", help="Client relationships"),
    access: str = typer.Option("Email, Document Management, Case Management", "--access", "-a", help="System access"),
    destination: str = typer.Option("Unknown", "--destination", "-d", help="Destination firm"),
    departure_days: str = typer.Option("30 days", "--departure", help="When they're leaving"),
    format: str = typer.Option("pretty", "--format", "-f", help="Output format: pretty, json, markdown"),
    use_gemini: bool = typer.Option(False, "--gemini", help="Use Gemini API for analysis"),
    use_llama: bool = typer.Option(False, "--llama", help="Use self-hosted Llama (100% local privacy)")
):
    """
    Analyze attorney departure EXIT SECURITY RISK.
    
    Chained adversarial analysis identifies:
    - What they could exploit with current access
    - Security gaps to close before departure
    - Defense checklist with prioritized actions
    
    AI Backends:
    - Default: Claude (Anthropic) - Best quality
    - --gemini: Google Gemini - Free tier available
    - --llama: Self-hosted Llama - 100% local, maximum privacy
    
    Example:
        aionos attorney --name "Sarah Chen" --practice "Corporate M&A" --years 8 \\
                       --cases "TechCorp Merger, StartupCo Acquisition" \\
                       --clients "TechCorp CEO, StartupCo Board" \\
                       --access "Email, DocMgmt, Westlaw, Client Portal" \\
                       --destination "Competitor Law LLP"
    """
    from aionos.modules.heist_planner import HeistPlanner
    import time
    
    console.print(Panel.fit(
        "[bold yellow]AION OS - The Heist Crew[/bold yellow]\n"
        "Assembling the crew to plan the exfiltration...",
        border_style="yellow"
    ))
    
    # Real-time progress callback for Claude (shows each agent as they report)
    def show_agent_progress(stage: int, agent_name: str, heist_role: str, findings: str, severity: str):
        """Display each Heist Crew agent as they report in real-time"""
        severity_color = {
            'critical': 'red',
            'high': 'orange1', 
            'medium': 'yellow',
            'low': 'green'
        }.get(severity, 'white')
        
        severity_icon = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(severity, '⚪')
        
        console.print(f"\n[bold red]═══ STAGE {stage}: {heist_role} ═══[/bold red]")
        console.print(f"[dim]Agent: {agent_name}[/dim]")
        
        # Show first 100 chars only - keep it punchy
        preview = findings[:100].replace('\n', ' ').strip()
        if len(findings) > 100:
            preview += "..."
        console.print(f"[italic]\"{preview}\"[/italic]")
        console.print(f"[{severity_color}]{severity_icon} {severity.upper()}[/{severity_color}]")
    
    planner = HeistPlanner(use_gemini=use_gemini, use_llama=use_llama)
    
    attorney_profile = {
        "attorney_name": name,
        "practice_area": practice,
        "active_cases": cases,
        "client_relationships": clients,
        "system_access": access,
        "years_at_firm": years,
        "destination_firm": destination,
        "departure_date": departure_days
    }
    
    # Only use callback for Claude (non-Gemini) since it supports streaming
    progress_cb = show_agent_progress if not use_gemini and not use_llama else None
    
    # Show ROI summary FIRST (before agents run)
    console.print("\n[bold cyan]▶ Deploying Heist Crew...[/bold cyan]\n")
    result = planner.analyze_departure_risk(attorney_profile, progress_callback=progress_cb)
    
    console.print("\n[bold red]═══ ANALYSIS COMPLETE ═══[/bold red]\n")
    
    # Show executive summary immediately
    _show_executive_summary(result)
    
    console.print()  # Spacing
    output_result(result, format)


@app.command()
def version():
    """Show AION OS version."""
    from aionos import __version__
    console.print(f"AION OS version {__version__}")
    console.print("The AI that prepares you for the fight.")


if __name__ == "__main__":
    app()
