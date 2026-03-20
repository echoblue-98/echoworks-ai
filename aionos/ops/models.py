"""
EchoWorks Ops Engine -- Models
================================
Structured types for memos, playbooks, metrics, and reviews.
All local. Zero cloud.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class MemoStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class MemoCategory(str, Enum):
    SALES = "sales"
    PRODUCT = "product"
    THREAT_ENGINE = "threat_engine"
    LEGAL = "legal"
    OPERATIONS = "operations"
    HIRING = "hiring"
    FINANCE = "finance"
    STRATEGY = "strategy"


class PlaybookStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class MetricType(str, Enum):
    COUNT = "count"          # e.g. emails sent
    CURRENCY = "currency"   # e.g. revenue
    PERCENT = "percent"     # e.g. conversion rate
    DURATION = "duration"   # e.g. days to close


@dataclass
class MemoStep:
    """A concrete next-step within a memo."""
    description: str
    owner: str = ""
    due: str = ""           # ISO date
    done: bool = False


@dataclass
class Memo:
    """
    Structured operational memo.
    Format: Issue -> Strategy -> Trade-offs -> Metrics -> Next Steps
    """
    id: int = 0
    title: str = ""
    category: str = "strategy"
    status: str = "draft"
    issue: str = ""         # What problem are we solving?
    strategy: str = ""      # How will we solve it?
    tradeoffs: str = ""     # What are we NOT doing and why?
    metrics: str = ""       # How do we measure success?
    next_steps: str = ""    # JSON list of MemoStep dicts
    created: str = ""
    updated: str = ""
    review_date: str = ""   # When to review this memo


@dataclass
class PlaybookStep:
    """A single step in an executable playbook."""
    step_num: int
    action: str
    details: str = ""
    owner: str = ""
    status: str = "not_started"
    completed_date: str = ""
    notes: str = ""


@dataclass
class Playbook:
    """
    Executable playbook -- a repeatable process anyone can run.
    """
    id: int = 0
    name: str = ""
    category: str = "operations"
    description: str = ""
    trigger: str = ""       # What event starts this playbook?
    steps: str = ""         # JSON list of PlaybookStep dicts
    status: str = "not_started"
    owner: str = ""
    created: str = ""
    updated: str = ""
    last_run: str = ""
    run_count: int = 0


@dataclass
class Metric:
    """A single KPI data point."""
    id: int = 0
    name: str = ""
    metric_type: str = "count"
    category: str = "sales"
    value: float = 0.0
    target: float = 0.0
    period: str = ""        # e.g. "2026-W12", "2026-03", "2026-Q1"
    recorded: str = ""
    notes: str = ""


@dataclass
class WeeklyReview:
    """Auto-generated weekly review."""
    id: int = 0
    week: str = ""          # e.g. "2026-W12"
    pipeline_summary: str = ""
    metrics_summary: str = ""
    wins: str = ""
    blockers: str = ""
    next_week_priorities: str = ""
    created: str = ""
