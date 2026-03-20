"""
EchoWorks Ops Engine
=====================
Pure local operations system for EchoWorks AI.
No cloud -- SQLite + Python + zero external dependencies.

Four pillars:
  1. Structured memos   -- issue / strategy / tradeoffs / metrics / next-steps
  2. Executable playbooks -- repeatable step-by-step execution with tracking
  3. KPI metrics         -- count, currency, percent, duration with targets
  4. Weekly reviews      -- automated pipeline + metric summaries

Usage:
    python -m aionos.ops.cli daily          # daily ops report
    python -m aionos.ops.cli memo list      # all memos
    python -m aionos.ops.cli playbook list  # all playbooks
    python -m aionos.ops.cli metric list    # all metrics
    python -m aionos.ops.cli review generate
"""

from aionos.ops.store import OpsStore
from aionos.ops.runner import OpsRunner

__all__ = ["OpsStore", "OpsRunner"]
