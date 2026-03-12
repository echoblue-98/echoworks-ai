"""
Test Claude API Integration

Quick test to verify your API key is working.
"""

from aionos.core.adversarial_engine import AdversarialEngine, IntensityLevel
from rich.console import Console

console = Console()

def main():
    console.print("\n[bold cyan]Testing Claude API Integration...[/bold cyan]\n")
    
    # Initialize engine
    try:
        engine = AdversarialEngine(intensity=IntensityLevel.LEVEL_3_HOSTILE)
    except Exception as e:
        console.print(f"[red]Error initializing engine: {e}[/red]")
        return
    
    # Test query
    test_query = """
    We're launching a new legal tech product. Our strategy is to:
    1. Target small law firms
    2. Price at $99/month
    3. Launch in 30 days
    
    What could go wrong?
    """
    
    console.print("[yellow]Test Query:[/yellow]")
    console.print(test_query)
    console.print("\n[yellow]Running adversarial analysis...[/yellow]\n")
    
    try:
        result = engine.analyze(
            query=test_query,
            context={"domain": "legal_tech"},
            use_case_type="test"
        )
        
        if "error" in result:
            console.print(f"[red]Error: {result['error']}[/red]")
            console.print(f"[red]Message: {result.get('message', 'No details')}[/red]")
            return
        
        # Display results
        console.print(f"[green]✓ Analysis complete![/green]")
        console.print(f"[green]✓ Agents used: {len(result['agents_used'])}[/green]\n")
        
        for agent_result in result['results']:
            console.print(f"[bold cyan]Agent: {agent_result['agent']}[/bold cyan]")
            console.print(f"[dim]Perspective: {agent_result['perspective']}[/dim]")
            console.print(f"[dim]Severity: {agent_result['severity']}[/dim]")
            console.print(f"\n{agent_result['findings']}\n")
            console.print("-" * 80 + "\n")
        
        # Show usage stats
        if engine.usage_tracker:
            console.print("[bold yellow]API Usage:[/bold yellow]")
            console.print(f"Total cost: ${engine.usage_tracker.get_total_cost():.4f}")
            console.print(f"Budget remaining: ${engine.usage_tracker.get_budget_remaining():.2f}")
            console.print(f"Use cases: {engine.usage_tracker.get_total_use_cases()}")
        
    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

if __name__ == "__main__":
    main()
