# AION OS - Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env

# Edit .env and add your API keys
```

## Usage

### 1. Run the Comparison Demo

See the categorical difference between Standard AI and AION OS:

```bash
python demo_comparison.py
```

This shows side-by-side how:
- Standard AI validates and agrees
- AION OS challenges and attacks

### 2. Command-Line Interface

Analyze legal documents:
```bash
python -m aionos.cli analyze-legal --file examples/sample_brief.txt --intensity 3
```

Red team security infrastructure:
```bash
python -m aionos.cli red-team --file examples/sample_infrastructure.txt --intensity 4
```

View audit logs:
```bash
python -m aionos.cli audit-logs --limit 20
```

Get statistics:
```bash
python -m aionos.cli stats
```

### 3. REST API

Start the API server:
```bash
python -m aionos.api.rest_api
```

Then visit:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Example API call:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/legal" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your legal brief text here",
    "intensity": 3,
    "user_id": "test_user"
  }'
```

### 4. Python Integration

```python
from aionos.modules.legal_analyzer import LegalAnalyzer
from aionos.core.adversarial_engine import IntensityLevel

# Analyze legal brief
analyzer = LegalAnalyzer(intensity=IntensityLevel.LEVEL_3_HOSTILE)
result = analyzer.analyze_brief(
    brief_content="Your legal brief text",
    case_context={"jurisdiction": "California"}
)

print(result["formatted_output"])
```

```python
from aionos.modules.security_redteam import SecurityRedTeam

# Red team infrastructure
red_team = SecurityRedTeam()
result = red_team.scan_infrastructure(
    infrastructure_config="Your network config"
)

print(result["formatted_output"])
```

## Intensity Levels

1. **Level 1 (Gentle)**: Points out obvious issues
2. **Level 2 (Active)**: Finds logical flaws and contradictions
3. **Level 3 (Hostile)**: Assumes adversarial intent - ruthless
4. **Level 4 (Red Team)**: Actively tries to break everything
5. **Level 5 (Maximum)**: Finds attack vectors you haven't considered

## Safety Features

- **Intent Classification**: Blocks unauthorized target analysis
- **Ethics Layer**: Enforces defensive-only usage
- **Audit Logging**: All queries logged for accountability
- **User Calibration**: Adjusts intensity based on user experience

## Examples

The `examples/` directory contains:
- `sample_brief.txt` - Legal brief for analysis
- `sample_infrastructure.txt` - Network config for red teaming

## Architecture

```
User Input → Intent Classifier → Multi-Agent Attack System → Severity Triage → Output
                ↓                          ↓                         ↓
          Ethics Layer              Adversarial Agents        Vulnerability Ranking
                ↓                          ↓                         ↓
          Audit Logger              Legal/Security/etc.      P0/P1/P2/P3/P4
```

## What Makes AION OS Different

**Standard AI:**
- "Your argument looks strong!"
- Validates and assists
- Makes you comfortable

**AION OS:**
- "Your argument will fail. Here's how opposing counsel will destroy it."
- Challenges and attacks
- Prepares you for opposition

## Next Steps

1. Try the demo: `python demo_comparison.py`
2. Analyze your own documents with the CLI
3. Integrate into your workflow via API or Python
4. Set up audit logging for compliance
5. Calibrate intensity based on your needs

## Support

For questions or issues, see the README.md or documentation.

---

**Remember:** AION OS is not your assistant. It's your sparring partner.
