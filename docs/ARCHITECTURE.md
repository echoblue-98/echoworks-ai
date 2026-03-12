# AION OS - Project Structure

```
codetyphoons-aionos26/
│
├── aionos/                          # Main package
│   ├── __init__.py                  # Package initialization
│   ├── __main__.py                  # CLI entry point
│   │
│   ├── core/                        # Core adversarial engine
│   │   ├── __init__.py
│   │   ├── adversarial_engine.py    # Multi-agent attack system
│   │   ├── intent_classifier.py     # Defensive vs offensive detection
│   │   └── severity_triage.py       # Vulnerability prioritization
│   │
│   ├── modules/                     # Domain-specific modules
│   │   ├── __init__.py
│   │   ├── legal_analyzer.py        # Legal adversarial analysis
│   │   ├── security_redteam.py      # Cybersecurity red teaming
│   │   └── business_strategy.py     # (Future) Business analysis
│   │
│   ├── safety/                      # Safety and ethics
│   │   ├── __init__.py
│   │   ├── ethics_layer.py          # Ethical boundary enforcement
│   │   └── audit_logger.py          # Usage audit logging
│   │
│   └── api/                         # API interfaces
│       ├── __init__.py
│       ├── cli.py                   # Command-line interface
│       └── rest_api.py              # REST API server
│
├── examples/                        # Example files
│   ├── sample_brief.txt             # Sample legal brief
│   └── sample_infrastructure.txt    # Sample security config
│
├── logs/                            # Audit logs (created at runtime)
│   └── audit.log
│
├── demo_comparison.py               # Main demo showing categorical difference
├── setup.py                         # Setup and test script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── .env                            # Your API keys (not in git)
├── README.md                        # Main documentation
├── QUICKSTART.md                    # Quick start guide
└── ARCHITECTURE.md                  # This file
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INPUT                                  │
│                    (Query, Document, Config)                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SAFETY LAYER                                    │
│  ┌────────────────────┐    ┌──────────────────┐                     │
│  │ Intent Classifier  │ → │  Ethics Layer    │                     │
│  │ (Defensive/        │    │  (Boundary       │                     │
│  │  Offensive)        │    │   Enforcement)   │                     │
│  └────────────────────┘    └──────────────────┘                     │
│                                 │                                    │
│                                 ▼                                    │
│                          ALLOWED / BLOCKED                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ (if allowed)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ADVERSARIAL ENGINE (Multi-Agent System)                 │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Agent 1    │  │   Agent 2    │  │   Agent 3    │              │
│  │              │  │              │  │              │              │
│  │   Legal      │  │  Security    │  │  Business    │              │
│  │  Opponent    │  │  Attacker    │  │ Competitor   │              │
│  │              │  │              │  │              │              │
│  │ Attacks from │  │ Attacks from │  │ Attacks from │              │
│  │ legal angle  │  │  technical   │  │  strategic   │              │
│  │              │  │    angle     │  │    angle     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                      │
│         └─────────────────┼──────────────────┘                      │
│                           ▼                                         │
│                  All agents attack                                  │
│                   simultaneously                                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SEVERITY TRIAGE                                   │
│                                                                      │
│  Vulnerabilities found → Ranked by severity                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ P0 CRITICAL  (Must fix immediately)                    │         │
│  │ P1 HIGH      (Fix before proceeding)                   │         │
│  │ P2 MEDIUM    (Should fix)                              │         │
│  │ P3 LOW       (Nice to fix)                             │         │
│  │ P4 INFO      (Informational)                           │         │
│  └────────────────────────────────────────────────────────┘         │
│                           │                                         │
│                           ▼                                         │
│                Progressive Disclosure                               │
│            (Show P0/P1 first, then others on demand)                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FORMATTED OUTPUT                                  │
│                                                                      │
│  1. Summary (total vulnerabilities, breakdown by severity)          │
│  2. Critical Issues (P0/P1) with:                                   │
│     - Description                                                   │
│     - Impact                                                        │
│     - Exploitation scenario                                         │
│     - Remediation steps                                             │
│  3. Recommendation (proceed / fix first)                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       AUDIT LOGGER                                   │
│              (All interactions logged for:)                          │
│  • Security audit trails                                            │
│  • Compliance (SOC2, HIPAA, etc.)                                   │
│  • Misuse detection                                                 │
│  • Usage analytics                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Adversarial by Default
- Every agent is trained to ATTACK, not assist
- Default stance: "How does this fail?"
- No validation or agreement - only challenge

### 2. Safety Through Constraints
- Intent classification blocks offensive use
- Ethics layer enforces boundaries
- Audit logging creates accountability
- But doesn't soften the adversarial punch

### 3. Multi-Perspective Analysis
- Different agents attack from different angles
- Legal: opposing counsel perspective
- Security: attacker perspective
- Business: competitor perspective
- Comprehensive coverage of attack surface

### 4. Intelligent Triage
- Prevents analysis paralysis
- Shows critical issues first
- Progressive disclosure for full picture
- Enables action instead of overwhelm

### 5. Intensity Calibration
- Level 1: Gentle skepticism (novices)
- Level 3: Hostile analysis (default)
- Level 5: Maximum adversarial (experts)
- Matches user readiness

## Component Interactions

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    CLI       │────▶│  Adversarial │────▶│   Legal      │
│   Interface  │     │    Engine    │     │   Analyzer   │
└──────────────┘     └──────────────┘     └──────────────┘
                             │
┌──────────────┐             │             ┌──────────────┐
│   REST       │─────────────┘             │   Security   │
│    API       │                           │   Red Team   │
└──────────────┘                           └──────────────┘
        │                                           │
        │                                           │
        ▼                                           ▼
┌──────────────────────────────────────────────────────────┐
│              Safety Layer + Audit Logger                  │
└──────────────────────────────────────────────────────────┘
```

## Data Flow Example

**User Query:** "Analyze my legal brief"

1. **Intent Classifier**: 
   - Detects "my" → defensive intent
   - Classification: ALLOWED

2. **Ethics Layer**:
   - Checks for violations
   - No unauthorized target → PASS

3. **Adversarial Engine**:
   - Activates Legal Opponent agent
   - Intensity Level 3 (Hostile)

4. **Legal Opponent Agent**:
   - Analyzes brief
   - Finds 3 vulnerabilities:
     - P0: Ambiguous contract language
     - P1: Contradictory evidence
     - P2: Weak precedent

5. **Severity Triage**:
   - Ranks vulnerabilities
   - Shows P0 and P1 first
   - Recommends: "Fix P0 before filing"

6. **Output**:
   - Formatted report
   - Exploitation scenarios
   - Remediation steps

7. **Audit Logger**:
   - Logs entire interaction
   - Stores for compliance

## Extension Points

### Adding New Domains
```python
# Create new module: aionos/modules/financial_analyzer.py
class FinancialAnalyzer:
    def analyze_strategy(self, strategy: str) -> Dict:
        # Use adversarial engine with business perspective
        pass
```

### Adding New Agent Perspectives
```python
# In adversarial_engine.py
class AgentPerspective(Enum):
    LEGAL_OPPONENT = "legal_opponent"
    SECURITY_ATTACKER = "security_attacker"
    YOUR_NEW_PERSPECTIVE = "your_new_perspective"  # Add here
```

### Custom Intensity Levels
User can define custom intensity for specific use cases

### Integration with External Tools
- REST API enables integration with existing workflows
- CLI can be wrapped by other scripts
- Python API for direct integration

## Why This Architecture Works

1. **Modular**: Each component has single responsibility
2. **Extensible**: Easy to add new domains/perspectives
3. **Safe**: Multiple safety layers without softening adversarial power
4. **Scalable**: Multi-agent approach parallelizes naturally
5. **Auditable**: Every interaction logged for compliance
6. **Categorical**: Fundamentally different from assistive AI

## Comparison: Standard AI vs AION OS Architecture

**Standard AI:**
```
User Input → Helpful Response Generator → Validated Output
```

**AION OS:**
```
User Input → Safety Check → Multi-Agent Attack → Triage → Harsh Truth + Fix Path
```

The architecture itself enforces the adversarial paradigm.
