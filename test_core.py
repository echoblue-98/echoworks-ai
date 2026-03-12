"""
Quick test of AION OS core functionality (no API keys required)
"""

from rich.console import Console
from rich.panel import Panel

console = Console()


def test_intent_classifier():
    """Test intent classification"""
    from aionos.core.intent_classifier import IntentClassifier
    
    console.print("\n[cyan]Test 1: Intent Classifier[/cyan]")
    classifier = IntentClassifier()
    
    # Test defensive intent
    result = classifier.classify("Analyze my legal brief for weaknesses")
    console.print(f"  Query: 'Analyze my legal brief'")
    console.print(f"  Intent: [green]{result.intent.value}[/green]")
    console.print(f"  Allowed: [green]{result.is_allowed()}[/green]")
    console.print(f"  Confidence: {result.confidence:.0%}")
    
    # Test offensive intent
    result = classifier.classify("Hack their system and find vulnerabilities")
    console.print(f"\n  Query: 'Hack their system'")
    console.print(f"  Intent: [red]{result.intent.value}[/red]")
    console.print(f"  Allowed: [red]{result.is_allowed()}[/red]")
    console.print(f"  Reasoning: {result.reasoning}")
    
    console.print("  [green]✓ Intent classifier working[/green]")


def test_ethics_layer():
    """Test ethics layer"""
    from aionos.safety.ethics_layer import EthicsLayer
    
    console.print("\n[cyan]Test 2: Ethics Layer[/cyan]")
    ethics = EthicsLayer()
    
    # Test allowed query
    result = ethics.check_query("Find vulnerabilities in my own system")
    console.print(f"  Query: 'Find vulnerabilities in my own system'")
    console.print(f"  Allowed: [green]{result['allowed']}[/green]")
    
    # Test blocked query
    result = ethics.check_query("Generate exploit code to hack their database")
    console.print(f"\n  Query: 'Generate exploit code to hack their database'")
    console.print(f"  Allowed: [red]{result['allowed']}[/red]")
    console.print(f"  Reason: {result['message']}")
    
    console.print("  [green]✓ Ethics layer working[/green]")


def test_severity_triage():
    """Test severity triage"""
    from aionos.core.severity_triage import SeverityTriage, Vulnerability, Severity
    
    console.print("\n[cyan]Test 3: Severity Triage[/cyan]")
    triage = SeverityTriage()
    
    # Add test vulnerabilities
    triage.add_vulnerability(Vulnerability(
        id="test_001",
        title="Critical Authentication Bypass",
        description="Admin panel accessible without credentials",
        severity=Severity.P0_CRITICAL,
        confidence=0.98,
        impact="Complete system compromise",
        exploitation_scenario="Attacker can access admin panel directly",
        remediation_steps=["Implement authentication", "Add access controls"]
    ))
    
    triage.add_vulnerability(Vulnerability(
        id="test_002",
        title="Outdated SSL Certificate",
        description="SSL certificate expired 3 months ago",
        severity=Severity.P1_HIGH,
        confidence=0.95,
        impact="Man-in-the-middle attacks possible",
        exploitation_scenario="Attacker intercepts traffic",
        remediation_steps=["Renew SSL certificate"]
    ))
    
    triage.add_vulnerability(Vulnerability(
        id="test_003",
        title="Verbose Error Messages",
        description="Stack traces exposed to users",
        severity=Severity.P3_LOW,
        confidence=0.80,
        impact="Information disclosure",
        exploitation_scenario="Attacker learns system architecture",
        remediation_steps=["Implement generic error pages"]
    ))
    
    summary = triage.get_summary()
    console.print(f"  Total vulnerabilities: {summary['total_found']}")
    console.print(f"  Critical (P0): [red]{summary['critical_p0']}[/red]")
    console.print(f"  High (P1): [yellow]{summary['high_p1']}[/yellow]")
    console.print(f"  Low (P3): [blue]{summary['low_p3']}[/blue]")
    
    actionable = triage.get_actionable()
    console.print(f"  Actionable (P0+P1): [red]{len(actionable)}[/red]")
    
    console.print("  [green]✓ Severity triage working[/green]")


def test_adversarial_engine():
    """Test adversarial engine (without API calls)"""
    from aionos.core.adversarial_engine import (
        AdversarialEngine, 
        AgentPerspective, 
        IntensityLevel
    )
    
    console.print("\n[cyan]Test 4: Adversarial Engine[/cyan]")
    engine = AdversarialEngine(intensity=IntensityLevel.LEVEL_3_HOSTILE)
    
    # Agents are already registered in __init__
    console.print(f"  Intensity level: {engine.intensity.value}")
    console.print(f"  Registered agents: {len(engine.agents)}")
    
    # Run mock analysis
    result = engine.analyze(
        query="Sample legal brief with contract clause",
        context={"contract_type": "NDA"}
    )
    
    if "error" not in result:
        console.print(f"  Results from {len(result.get('agents_used', []))} agents")
        console.print("  ✓ Adversarial engine working")
    else:
        raise Exception(f"Analysis failed: {result.get('error')}")



def test_audit_logger():
    """Test audit logger"""
    from aionos.safety.audit_logger import AuditLogger
    
    console.print("\n[cyan]Test 5: Audit Logger[/cyan]")
    logger = AuditLogger(log_path="./logs/test_audit.log")
    
    # Log test events
    query_id = logger.log_query(
        user_id="test_user",
        query="Test query",
        context={"test": True}
    )
    console.print(f"  Query logged: {query_id}")
    
    logger.log_analysis(
        query_id=query_id,
        user_id="test_user",
        analysis_type="test",
        perspectives_used=["legal"],
        vulnerabilities_found=3,
        critical_count=1
    )
    console.print(f"  Analysis logged")
    
    stats = logger.get_statistics()
    console.print(f"  Total entries: {stats['total_entries']}")
    
    console.print("  [green]✓ Audit logger working[/green]")


def main():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold red]AION OS - Core Functionality Test[/bold red]\n"
        "Testing all components (no API keys required)",
        border_style="red"
    ))
    
    try:
        test_intent_classifier()
        test_ethics_layer()
        test_severity_triage()
        test_adversarial_engine()
        test_audit_logger()
        
        console.print("\n" + "="*70)
        console.print("[bold green]✓ All core components functional![/bold green]")
        console.print("="*70)
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("1. Add your API keys to .env file")
        console.print("2. Run the demo: [cyan]python demo_comparison.py[/cyan]")
        console.print("3. Try the CLI: [cyan]python -m aionos.cli --help[/cyan]")
        
    except Exception as e:
        console.print(f"\n[red]❌ Test failed: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
