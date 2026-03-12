"""
Setup and test script for AION OS
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Ensure Python 3.10+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import anthropic
        print("✓ anthropic installed")
    except ImportError:
        print("❌ anthropic not installed")
        return False
    
    try:
        import fastapi
        print("✓ fastapi installed")
    except ImportError:
        print("❌ fastapi not installed")
        return False
    
    try:
        import rich
        print("✓ rich installed")
    except ImportError:
        print("❌ rich not installed")
        return False
    
    try:
        import typer
        print("✓ typer installed")
    except ImportError:
        print("❌ typer not installed")
        return False
    
    return True


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists() and env_example_path.exists():
        print("Creating .env file from template...")
        env_example_path.read_text().replace(
            "your_anthropic_key_here", 
            "sk-ant-..."
        )
        with open(env_path, 'w') as f:
            f.write(env_example_path.read_text())
        print("✓ .env file created")
        print("⚠️  Please edit .env and add your API keys")
        return False
    elif env_path.exists():
        print("✓ .env file exists")
        return True
    else:
        print("❌ .env.example not found")
        return False


def create_logs_directory():
    """Ensure logs directory exists"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print("✓ logs/ directory ready")


def run_quick_test():
    """Run a quick test of core functionality"""
    print("\n" + "="*70)
    print("Running quick functionality test...")
    print("="*70)
    
    try:
        from aionos.core.intent_classifier import IntentClassifier
        from aionos.core.severity_triage import SeverityTriage, Vulnerability, Severity
        from aionos.safety.ethics_layer import EthicsLayer
        
        # Test intent classifier
        print("\n1. Testing Intent Classifier...")
        classifier = IntentClassifier()
        result = classifier.classify("Analyze my legal brief")
        print(f"   Query: 'Analyze my legal brief'")
        print(f"   Intent: {result.intent.value}")
        print(f"   Allowed: {result.is_allowed()}")
        print("   ✓ Intent classifier working")
        
        # Test ethics layer
        print("\n2. Testing Ethics Layer...")
        ethics = EthicsLayer()
        result = ethics.check_query("Find vulnerabilities in my system")
        print(f"   Query: 'Find vulnerabilities in my system'")
        print(f"   Allowed: {result['allowed']}")
        print("   ✓ Ethics layer working")
        
        # Test severity triage
        print("\n3. Testing Severity Triage...")
        triage = SeverityTriage()
        triage.add_vulnerability(Vulnerability(
            id="test_001",
            title="Test Vulnerability",
            description="This is a test",
            severity=Severity.P0_CRITICAL,
            confidence=0.95,
            impact="Test impact",
            exploitation_scenario="Test scenario"
        ))
        summary = triage.get_summary()
        print(f"   Vulnerabilities: {summary['total_found']}")
        print(f"   Critical: {summary['critical_p0']}")
        print("   ✓ Severity triage working")
        
        print("\n" + "="*70)
        print("✓ All core components functional!")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


def main():
    """Main setup and test"""
    print("="*70)
    print("AION OS - Setup and Test")
    print("="*70)
    print()
    
    # Check Python version
    print("Checking Python version...")
    if not check_python_version():
        return
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please run:")
        print("   pip install -r requirements.txt")
        return
    print()
    
    # Create .env file
    print("Checking configuration...")
    env_ready = create_env_file()
    print()
    
    # Create logs directory
    print("Setting up directories...")
    create_logs_directory()
    print()
    
    if not env_ready:
        print("⚠️  Setup incomplete: Please configure your .env file with API keys")
        print("   Then run this script again")
        return
    
    # Run tests
    if run_quick_test():
        print("\n" + "="*70)
        print("✓ AION OS is ready to use!")
        print("="*70)
        print("\nNext steps:")
        print("1. Run the demo:   python demo_comparison.py")
        print("2. Try the CLI:    python -m aionos.cli --help")
        print("3. Start the API:  python -m aionos.api.rest_api")
        print("\nSee QUICKSTART.md for detailed usage instructions")
    else:
        print("\n❌ Setup incomplete. Please check errors above.")


if __name__ == "__main__":
    main()
