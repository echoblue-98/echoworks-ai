"""
AION OS - Improvement Engine
=============================

Recursive self-improvement module for AION OS.
Safely proposes, tests, and deploys detection improvements
using LLM-assisted optimization grounded in human feedback and replay.

Architecture:
    ┌───────────────────────────────────────────────────────┐
    │  Feedback Collector  ←──  Analyst corrections,       │
    │                           outcome labels, notes       │
    └──────────┬────────────────────────────────────────────┘
               │
    ┌──────────▼────────────────────────────────────────────┐
    │  Evaluation Engine   ←──  Precision, recall,          │
    │                           time-to-detect metrics      │
    └──────────┬────────────────────────────────────────────┘
               │
    ┌──────────▼────────────────────────────────────────────┐
    │  Candidate Generator ←──  LLM proposes changes        │
    │                           offline                     │
    └──────────┬────────────────────────────────────────────┘
               │
    ┌──────────▼────────────────────────────────────────────┐
    │  Shadow Runner       ←──  Replays historical data     │
    │                           with candidate changes      │
    └──────────┬────────────────────────────────────────────┘
               │
    ┌──────────▼────────────────────────────────────────────┐
    │  Policy Store        ←──  Versioned, diffable,        │
    │                           rollback-able configs       │
    └──────────┬────────────────────────────────────────────┘
               │
    ┌──────────▼────────────────────────────────────────────┐
    │  Improvement Engine  ←──  Orchestrator: ties it all   │
    │                           together with guardrails    │
    └───────────────────────────────────────────────────────┘

Safety principles:
  - NEVER auto-modify auth, input validation, or resource limits
  - All changes run in shadow mode before promotion
  - Human approval required before production deployment
  - Hard invariants enforced by guardrails at every stage
  - Full audit trail for every proposed and applied change
"""

__version__ = "0.1.0"

from .policy_store import PolicyStore, PolicyVersion, PolicyDiff
from .evaluation_engine import EvaluationEngine, DetectionMetrics, AlertOutcome
from .candidate_generator import CandidateGenerator, CandidateChange
from .shadow_runner import ShadowRunner, ShadowResult
from .feedback_collector import FeedbackCollector, AnalystFeedback
from .improvement_engine import ImprovementEngine

__all__ = [
    "ImprovementEngine",
    "PolicyStore",
    "PolicyVersion",
    "PolicyDiff",
    "EvaluationEngine",
    "DetectionMetrics",
    "AlertOutcome",
    "CandidateGenerator",
    "CandidateChange",
    "ShadowRunner",
    "ShadowResult",
    "FeedbackCollector",
    "AnalystFeedback",
]
