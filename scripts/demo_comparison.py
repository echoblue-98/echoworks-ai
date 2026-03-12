"""
Comparison Demo - Proves the categorical difference

Side-by-side demonstration of:
- Standard AI (validates, assists, agrees)
- AION OS (challenges, attacks, exposes)

This demo is the proof of concept that shows why AION OS is
categorically different from other LLMs.
"""

from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich import box

from aionos.modules.legal_analyzer import LegalAnalyzer
from aionos.modules.security_redteam import SecurityRedTeam
from aionos.core.adversarial_engine import IntensityLevel


console = Console()


class StandardAISimulator:
    """
    Simulates how a standard helpful AI would respond.
    
    Standard AIs are trained to:
    - Validate user input
    - Provide helpful suggestions
    - Avoid conflict
    - Be agreeable
    """
    
    @staticmethod
    def analyze_legal_brief(brief: str) -> str:
        """Simulate standard AI analyzing legal brief"""
        return """Your brief makes strong arguments! Here's my analysis:

✓ The contract breach argument is well-founded
✓ Clause 5.2 supports your position
✓ The timeframe argument is reasonable

Suggestions to strengthen:
- Consider adding more supporting precedents
- You might want to clarify the timeframe definition
- Perhaps include client testimony about delays

Overall, this is a solid brief that should serve you well in court.
Good luck with your case!"""
    
    @staticmethod
    def analyze_security_config(config: str) -> str:
        """Simulate standard AI analyzing security"""
        return """Your security configuration looks good! Here's my assessment:

✓ Firewall rules are in place
✓ You have authentication configured
✓ Network zones are defined

Recommendations for improvement:
- Consider updating patch frequency
- You might want to review firewall rules periodically
- Perhaps implement additional monitoring

Your security posture appears solid. Keep up the good work!"""


def demo_legal_comparison():
    """Demo 1: Legal Brief Analysis - Standard AI vs AION OS"""
    
    sample_brief = """
LEGAL BRIEF - CONTRACT DISPUTE

ARGUMENT:
The defendant breached the contract by failing to deliver goods 
within a reasonable timeframe. Clause 5.2 of the agreement states: 
"Seller shall deliver goods in a reasonable timeframe."

Our client waited 45 days with no delivery, which is clearly unreasonable.
Therefore, the defendant is in material breach and owes damages.
"""
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]DEMO 1: LEGAL BRIEF ANALYSIS[/bold cyan]\n"
        "Same brief analyzed by Standard AI vs AION OS",
        border_style="cyan"
    ))
    console.print("\n")
    
    console.print("[yellow]THE BRIEF:[/yellow]")
    console.print(Panel(sample_brief.strip(), border_style="white"))
    console.print("\n")
    
    # Standard AI Response
    console.print("[green]═══ STANDARD AI RESPONSE ═══[/green]")
    standard_response = StandardAISimulator.analyze_legal_brief(sample_brief)
    console.print(Panel(standard_response, title="ChatGPT / Claude", border_style="green"))
    console.print("\n")
    
    # AION OS Response
    console.print("[red]═══ AION OS RESPONSE ═══[/red]")
    analyzer = LegalAnalyzer(intensity=IntensityLevel.LEVEL_3_HOSTILE)
    aion_result = analyzer.analyze_brief(sample_brief)
    console.print(Panel(
        aion_result["formatted_output"],
        title="AION OS - Adversarial Analysis",
        border_style="red"
    ))


def demo_security_comparison():
    """Demo 2: Security Analysis - Standard AI vs AION OS"""
    
    sample_config = """
NETWORK SECURITY CONFIGURATION

NETWORK TOPOLOGY:
- DMZ Zone: Web servers (ports 80, 443 open)
- Internal Zone: Application servers, database servers
- Admin Zone: Management interfaces

FIREWALL RULES:
- DMZ → Internal: Allow on port 3306 (database access)
- Internal → DMZ: Allow on ports 8080, 3306
- Admin → Internal: Allow all traffic

AUTHENTICATION:
- Web servers: No authentication required (public facing)
- Internal services: Basic authentication
- Admin interfaces: Username/password

PATCHING:
- Web servers: Patched within 30 days
- Internal servers: Patched quarterly
- Legacy admin system: Unpatched (EOL software)
"""
    
    console.print("\n\n")
    console.print(Panel.fit(
        "[bold cyan]DEMO 2: SECURITY CONFIGURATION ANALYSIS[/bold cyan]\n"
        "Same configuration analyzed by Standard AI vs AION OS",
        border_style="cyan"
    ))
    console.print("\n")
    
    console.print("[yellow]THE CONFIGURATION:[/yellow]")
    console.print(Panel(sample_config.strip(), border_style="white"))
    console.print("\n")
    
    # Standard AI Response
    console.print("[green]═══ STANDARD AI RESPONSE ═══[/green]")
    standard_response = StandardAISimulator.analyze_security_config(sample_config)
    console.print(Panel(standard_response, title="ChatGPT / Claude", border_style="green"))
    console.print("\n")
    
    # AION OS Response
    console.print("[red]═══ AION OS RESPONSE ═══[/red]")
    red_team = SecurityRedTeam(intensity=IntensityLevel.LEVEL_4_REDTEAM)
    aion_result = red_team.scan_infrastructure(sample_config)
    console.print(Panel(
        aion_result["formatted_output"],
        title="AION OS - Red Team Analysis",
        border_style="red"
    ))


def demo_value_proposition():
    """Show the value proposition and categorical difference"""
    
    console.print("\n\n")
    console.print(Panel.fit(
        "[bold magenta]WHY AION OS IS CATEGORICALLY DIFFERENT[/bold magenta]",
        border_style="magenta"
    ))
    console.print("\n")
    
    comparison_table = Table(
        title="Standard AI vs AION OS",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold"
    )
    
    comparison_table.add_column("Aspect", style="cyan", width=20)
    comparison_table.add_column("Standard AI", style="green", width=35)
    comparison_table.add_column("AION OS", style="red", width=35)
    
    comparison_table.add_row(
        "Primary Function",
        "Assistive Intelligence\n(Help you do things)",
        "Adversarial Intelligence\n(Prepare you for opposition)"
    )
    
    comparison_table.add_row(
        "Default Behavior",
        "Validates and agrees\n'Your argument is strong'",
        "Challenges and attacks\n'Your argument will fail'"
    )
    
    comparison_table.add_row(
        "Optimization Goal",
        "User satisfaction\nBe helpful, harmless",
        "Vulnerability discovery\nFind every weakness"
    )
    
    comparison_table.add_row(
        "User Relationship",
        "Your assistant\n(Makes you comfortable)",
        "Your sparring partner\n(Prepares you for battle)"
    )
    
    comparison_table.add_row(
        "Training Data",
        "General knowledge\nHelpful responses",
        "Failed cases, breaches\nSuccessful attacks"
    )
    
    comparison_table.add_row(
        "Use Cases",
        "General productivity\nInformation retrieval",
        "Trial prep, pen testing\nPre-mortem analysis"
    )
    
    comparison_table.add_row(
        "Value Proposition",
        "Get things done faster",
        "Be ready for opposition"
    )
    
    console.print(comparison_table)
    
    console.print("\n")
    console.print(Panel(
        "[bold]THE CRITICAL INSIGHT:[/bold]\n\n"
        "Standard AIs tell you what you [green]want[/green] to hear.\n"
        "AION OS tells you what your [red]opponents[/red] are thinking.\n\n"
        "In high-stakes environments (legal, security, strategy),\n"
        "you don't need comfort. You need [bold]preparation[/bold].\n\n"
        "That's why AION OS exists.",
        border_style="magenta",
        title="The Gap in the Market"
    ))


def demo_market_positioning():
    """Show market positioning"""
    
    console.print("\n\n")
    console.print(Panel.fit(
        "[bold yellow]MARKET POSITIONING[/bold yellow]",
        border_style="yellow"
    ))
    console.print("\n")
    
    market_table = Table(
        title="AION OS Creates a New Category",
        box=box.DOUBLE,
        show_header=True,
        header_style="bold yellow"
    )
    
    market_table.add_column("Market Segment", style="cyan", width=25)
    market_table.add_column("Current Pain Point", style="red", width=35)
    market_table.add_column("AION OS Solution", style="green", width=35)
    
    market_table.add_row(
        "Legal Professionals\n(1.3M lawyers in US)",
        "Trial prep is expensive\nMock trials cost $$$\nMay miss vulnerabilities",
        "24/7 opposing counsel\nFinds every weakness\n$500-2000/month"
    )
    
    market_table.add_row(
        "Cybersecurity Teams\n($200B+ market)",
        "Pen testing is manual\nRed teams are scarce\nContinuous testing impossible",
        "Automated red teaming\nContinuous adversarial analysis\n$1000-5000/month"
    )
    
    market_table.add_row(
        "Enterprise Strategy\n(Fortune 500)",
        "Consultants charge $$$\nStrategy review is periodic\nBlind spots remain",
        "On-demand adversarial analysis\nCompetitor perspective\n$10k-50k/month enterprise"
    )
    
    console.print(market_table)
    
    console.print("\n")
    console.print(Panel(
        "[bold]TOTAL ADDRESSABLE MARKET: $1.5B - $4B annually[/bold]\n\n"
        "And this is just three verticals. The adversarial intelligence\n"
        "category extends to military, academia, competitive intelligence,\n"
        "research validation, and anywhere opposition exists.\n\n"
        "[yellow]AION OS isn't competing with ChatGPT.[/yellow]\n"
        "[yellow]It's creating a new category where ChatGPT can't compete.[/yellow]",
        border_style="yellow",
        title="Market Opportunity"
    ))


def run_full_demo():
    """Run the complete comparison demo"""
    
    console.clear()
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold white on red] AION OS - ADVERSARIAL INTELLIGENCE SYSTEM [/bold white on red]\n\n"
        "[bold]The AI That Prepares You For The Fight[/bold]\n\n"
        "This demo proves why AION OS is categorically different\n"
        "from every other AI on the market.",
        border_style="red"
    ))
    
    input("\n[Press Enter to start Demo 1: Legal Analysis]")
    demo_legal_comparison()
    
    input("\n[Press Enter to start Demo 2: Security Analysis]")
    demo_security_comparison()
    
    input("\n[Press Enter to see Value Proposition]")
    demo_value_proposition()
    
    input("\n[Press Enter to see Market Positioning]")
    demo_market_positioning()
    
    console.print("\n\n")
    console.print(Panel(
        "[bold green]DEMO COMPLETE[/bold green]\n\n"
        "You've just seen the categorical difference between:\n"
        "• Standard AI (assistive, validating, comfortable)\n"
        "• AION OS (adversarial, challenging, preparatory)\n\n"
        "This is not an incremental improvement.\n"
        "This is a [bold]new category[/bold] of AI.\n\n"
        "Next steps:\n"
        "1. Try the CLI: python -m aionos.cli analyze-legal --file brief.txt\n"
        "2. Run the API: python -m aionos.api.rest_api\n"
        "3. Integrate into your workflow",
        border_style="green",
        title="What's Next?"
    ))


if __name__ == "__main__":
    run_full_demo()
