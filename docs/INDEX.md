# AION OS - Project Index

## 📖 Documentation Files

### Start Here
- **[README.md](README.md)** - Main project overview and introduction
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide with usage examples
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Strategic summary and business case

### Technical Documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed technical architecture
- **[requirements.txt](requirements.txt)** - Python dependencies

### Configuration
- **[.env.example](.env.example)** - Environment variables template
- **[.env](.env)** - Your API keys (create from .env.example)

---

## 🚀 Runnable Scripts

### Demos & Tests
- **[visual_summary.py](visual_summary.py)** - Visual overview of entire project
  ```bash
  python visual_summary.py
  ```

- **[demo_comparison.py](demo_comparison.py)** - Side-by-side Standard AI vs AION OS
  ```bash
  python demo_comparison.py
  ```

- **[test_core.py](test_core.py)** - Test all core components (no API keys needed)
  ```bash
  python test_core.py
  ```

- **[setup.py](setup.py)** - Setup and validation script
  ```bash
  python setup.py
  ```

### CLI Commands
```bash
# Analyze legal document
python -m aionos.cli analyze-legal --file examples/sample_brief.txt

# Red team security infrastructure
python -m aionos.cli red-team --file examples/sample_infrastructure.txt

# View audit logs
python -m aionos.cli audit-logs

# Show statistics
python -m aionos.cli stats

# Get help
python -m aionos.cli --help
```

### API Server
```bash
# Start REST API
python -m aionos.api.rest_api

# Then visit:
# http://localhost:8000/docs (API documentation)
# http://localhost:8000/health (health check)
```

---

## 📂 Source Code Structure

### Core Engine (`aionos/core/`)
- **[adversarial_engine.py](aionos/core/adversarial_engine.py)** - Multi-agent attack system
- **[intent_classifier.py](aionos/core/intent_classifier.py)** - Defensive vs offensive detection
- **[severity_triage.py](aionos/core/severity_triage.py)** - Vulnerability prioritization (P0-P4)

### Domain Modules (`aionos/modules/`)
- **[legal_analyzer.py](aionos/modules/legal_analyzer.py)** - Legal adversarial analysis
- **[security_redteam.py](aionos/modules/security_redteam.py)** - Cybersecurity red teaming

### Safety Layer (`aionos/safety/`)
- **[ethics_layer.py](aionos/safety/ethics_layer.py)** - Ethical boundary enforcement
- **[audit_logger.py](aionos/safety/audit_logger.py)** - Usage audit logging

### API Interfaces (`aionos/api/`)
- **[cli.py](aionos/api/cli.py)** - Command-line interface
- **[rest_api.py](aionos/api/rest_api.py)** - REST API server

---

## 📝 Example Files (`examples/`)
- **[sample_brief.txt](examples/sample_brief.txt)** - Sample legal brief for testing
- **[sample_infrastructure.txt](examples/sample_infrastructure.txt)** - Sample security config for testing

---

## 🎯 Quick Navigation by Task

### I want to understand what AION OS is
1. Read [README.md](README.md)
2. Run `python visual_summary.py`
3. Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

### I want to see it in action
1. Run `python test_core.py` (no API keys needed)
2. Run `python demo_comparison.py` (shows the difference)
3. Try CLI: `python -m aionos.cli analyze-legal --file examples/sample_brief.txt`

### I want to understand the technical architecture
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Review source code in `aionos/core/`
3. Look at module implementations in `aionos/modules/`

### I want to use it in my project
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Install: `pip install -r requirements.txt`
3. Configure: Copy `.env.example` to `.env` and add API keys
4. Use CLI, API, or Python integration

### I want to extend it
1. Study [ARCHITECTURE.md](ARCHITECTURE.md) - Extension Points section
2. Look at existing modules in `aionos/modules/`
3. Add new `AgentPerspective` in `adversarial_engine.py`
4. Create new domain module following `legal_analyzer.py` pattern

---

## 🔍 Find Something Specific

| I'm looking for... | Go to... |
|-------------------|----------|
| Market opportunity | [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Market Positioning |
| Competitive advantage | [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Key Differentiators |
| Technical design | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Usage examples | [QUICKSTART.md](QUICKSTART.md) |
| Safety mechanisms | [aionos/safety/](aionos/safety/) folder |
| Multi-agent system | [aionos/core/adversarial_engine.py](aionos/core/adversarial_engine.py) |
| Legal analysis | [aionos/modules/legal_analyzer.py](aionos/modules/legal_analyzer.py) |
| Security red team | [aionos/modules/security_redteam.py](aionos/modules/security_redteam.py) |
| API documentation | Start API server and visit `/docs` |
| CLI commands | Run `python -m aionos.cli --help` |

---

## 📊 Project Statistics

```
Total Files: 20+ Python files
Total Lines: 3500+ lines of code
Documentation: 2500+ lines

Core Components:
✅ Adversarial Engine
✅ Multi-Agent System
✅ Intent Classifier
✅ Ethics Layer
✅ Audit Logger
✅ Severity Triage
✅ Legal Analyzer
✅ Security Red Team
✅ CLI Interface
✅ REST API
✅ Comprehensive Documentation
```

---

## 🎬 Recommended First Steps

1. **Understand the concept**: `python visual_summary.py`
2. **See it work**: `python test_core.py`
3. **See the difference**: `python demo_comparison.py`
4. **Try it yourself**: `python -m aionos.cli analyze-legal --file examples/sample_brief.txt`
5. **Read the docs**: [README.md](README.md) → [QUICKSTART.md](QUICKSTART.md) → [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 💬 The Core Insight

**Standard AI tells you what you want to hear.**  
**AION OS tells you what your opponents are thinking.**

That's the categorical difference.  
That's why it's a new market category.  
That's why it's defensible.

---

*Last Updated: December 21, 2025*
