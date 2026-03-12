"""
AION OS - Pattern Management CLI
Command-line interface for ingesting and managing departure patterns.

Usage:
    python -m aionos.api.pattern_cli ingest --file article.txt --type NEWS_ARTICLE
    python -m aionos.api.pattern_cli ingest --file article.txt --local   # 100% LOCAL - Zero LLM
    python -m aionos.api.pattern_cli ingest --url "https://law360.com/article"
    python -m aionos.api.pattern_cli list
    python -m aionos.api.pattern_cli stats
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional
import requests

from aionos.tools.pattern_extractor import PatternExtractor
from aionos.tools.local_pattern_extractor import LocalPatternExtractor
from aionos.api.gemini_client import GeminiClient

app = typer.Typer(help="AION Pattern Database Management")
console = Console()


@app.command()
def ingest(
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to document file (txt, pdf, etc.)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to fetch article from"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Direct text input"),
    source_type: str = typer.Option("NEWS_ARTICLE", "--type", help="Source type: NEWS_ARTICLE, COURT_DOCUMENT, ACADEMIC, COMPOSITE"),
    local: bool = typer.Option(False, "--local", "-l", help="Use 100% LOCAL extraction - Zero LLM calls"),
):
    """Ingest a new departure case and extract pattern."""
    
    if local:
        console.print("\n[bold magenta]🔒 AION LOCAL PATTERN INGESTION[/bold magenta]")
        console.print("[dim]100% Private - Zero LLM - Zero API calls[/dim]\n")
    else:
        console.print("\n[bold cyan]🔍 AION PATTERN INGESTION[/bold cyan]\n")
    
    # Get raw text
    raw_text = None
    source_url = None
    
    if file:
        if not file.exists():
            console.print(f"[red]❌ File not found: {file}[/red]")
            raise typer.Exit(1)
        
        with open(file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        console.print(f"📄 Loaded file: {file.name} ({len(raw_text)} chars)")
        
    elif url:
        console.print(f"🌐 Fetching from URL: {url}")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            raw_text = response.text
            source_url = url
            console.print(f"✅ Fetched {len(raw_text)} characters")
        except Exception as e:
            console.print(f"[red]❌ Failed to fetch URL: {e}[/red]")
            raise typer.Exit(1)
            
    elif text:
        raw_text = text
        console.print(f"📝 Using direct text input ({len(raw_text)} chars)")
        
    else:
        console.print("[red]❌ Must provide --file, --url, or --text[/red]")
        raise typer.Exit(1)
    
    # Initialize extractor based on mode
    if local:
        console.print("🔒 Using LOCAL extraction engine (Zero LLM)...")
        extractor = LocalPatternExtractor()
        success = extractor.extract_and_save(raw_text, source_type)
        
        if success:
            console.print("\n[bold green]✅ PATTERN EXTRACTED AND SAVED (100% LOCAL)[/bold green]")
            console.print("[dim]Zero data sent to any LLM provider.[/dim]")
            console.print("\n💡 Pattern now available for AION analysis.")
        else:
            console.print("\n[red]❌ EXTRACTION FAILED[/red]")
            console.print("   Check if document contains sufficient departure data.")
            raise typer.Exit(1)
    else:
        console.print("\n🤖 Initializing AI extraction engine...")
        try:
            gemini = GeminiClient()
            extractor = PatternExtractor(gemini_client=gemini)
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize: {e}[/red]")
            raise typer.Exit(1)
        
        # Extract pattern
        console.print(f"🔬 Extracting pattern (source type: {source_type})...\n")
        
        success = extractor.extract_and_save(raw_text, source_type, source_url)
        
        if success:
            console.print("\n[bold green]✅ PATTERN EXTRACTED AND SAVED[/bold green]")
            console.print("\n💡 Pattern now available for AION analysis.")
        else:
            console.print("\n[red]❌ EXTRACTION FAILED[/red]")
            console.print("   Check if document contains sufficient departure data.")
            raise typer.Exit(1)


@app.command()
def list():
    """List all patterns in the database."""
    
    console.print("\n[bold cyan]📚 AION PATTERN DATABASE[/bold cyan]\n")
    
    try:
        gemini = GeminiClient()
        extractor = PatternExtractor(gemini_client=gemini)
        patterns = extractor.list_patterns()
        
        if not patterns:
            console.print("[yellow]No patterns found in database.[/yellow]")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Case Name", style="white")
        table.add_column("Status", style="green")
        table.add_column("Confidence", justify="right")
        table.add_column("Source Type")
        table.add_column("Date")
        
        for p in patterns:
            confidence_pct = f"{p['confidence']:.0%}"
            table.add_row(
                p["id"][:30] + "...",
                p["case_name"][:40],
                p["status"],
                confidence_pct,
                p["source_type"],
                p["extracted_date"][:10]
            )
        
        console.print(table)
        console.print(f"\n[bold]Total Patterns: {len(patterns)}[/bold]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stats():
    """Show database statistics."""
    
    console.print("\n[bold cyan]📊 PATTERN DATABASE STATISTICS[/bold cyan]\n")
    
    try:
        gemini = GeminiClient()
        extractor = PatternExtractor(gemini_client=gemini)
        patterns = extractor.list_patterns()
        
        if not patterns:
            console.print("[yellow]No patterns found in database.[/yellow]")
            return
        
        # Calculate stats
        total = len(patterns)
        by_status = {}
        by_source = {}
        avg_confidence = sum(p["confidence"] for p in patterns) / total if total > 0 else 0
        
        for p in patterns:
            status = p["status"]
            source = p["source_type"]
            by_status[status] = by_status.get(status, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
        
        # Display stats
        stats_panel = f"""
[bold]Total Patterns:[/bold] {total}
[bold]Average Confidence:[/bold] {avg_confidence:.0%}

[bold]By Status:[/bold]
{chr(10).join(f"  • {status}: {count}" for status, count in by_status.items())}

[bold]By Source Type:[/bold]
{chr(10).join(f"  • {source}: {count}" for source, count in by_source.items())}
        """
        
        console.print(Panel(stats_panel, title="Database Metrics", border_style="cyan"))
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def fetch_recent(
    limit: int = typer.Option(5, "--limit", "-n", help="Number of articles to fetch"),
    practice: Optional[str] = typer.Option(None, "--practice", "-p", help="Filter by practice area")
):
    """Fetch recent departure news from Above The Law and auto-ingest."""
    
    console.print("\n[bold cyan]🌐 FETCHING RECENT DEPARTURES[/bold cyan]\n")
    console.print("[yellow]⚠️  Web scraping feature coming soon...[/yellow]")
    console.print("\n💡 For now, use: python -m aionos.api.pattern_cli ingest --url <article_url>")


@app.command()
def validate(
    pattern_id: str = typer.Argument(..., help="Pattern ID to validate")
):
    """Manually validate an extracted pattern."""
    
    console.print(f"\n[bold cyan]✅ VALIDATING PATTERN: {pattern_id}[/bold cyan]\n")
    console.print("[yellow]⚠️  Manual validation feature coming soon...[/yellow]")
    console.print("\n💡 Will allow human review of AI-extracted patterns before marking as VALIDATED")


if __name__ == "__main__":
    app()
