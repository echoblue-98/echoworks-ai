"""
AION OS — Tool Call Trace (Step 7: Evaluation)

Captures step-level traces of every tool invocation so the agent layer can
be evaluated, not just observed. Without this, debugging a production
failure in a spawned-agent chain is guesswork.

Tracked per call:
- Tool selected (was it the right one?)
- Arguments passed (valid on first attempt?)
- Result envelope (success / typed error / empty)
- Reasoning step that proposed the call (model context window, optional)
- Recovery action taken if the call failed
- Parent / spawn context (which agent, which workflow run)

Storage: append-only JSONL on disk. Same file format as the rest of the
audit pipeline so existing observability tooling reads it for free.

Usage:
    from aionos.observability.tool_trace import ToolCallTrace, TraceWriter

    writer = TraceWriter("logs/tool_traces.jsonl")
    registry = ToolRegistry(audit_callback=writer.from_registry_event)

    # later, evaluate
    from aionos.observability.tool_trace import TraceAnalyzer
    stats = TraceAnalyzer.from_file("logs/tool_traces.jsonl").summary()
    # -> {'tool_selection_accuracy': 0.91, 'first_attempt_arg_validity': 0.86, ...}
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger("aionos.observability.tool_trace")


# =============================================================================
# TRACE EVENT
# =============================================================================

@dataclass
class ToolCallTrace:
    """
    Single tool invocation, fully traced.

    Fields are designed to answer the four questions the article calls out
    for tool-layer evaluation:
      1. Was the right tool selected?
      2. Were the arguments valid on first attempt?
      3. Did the error propagate into the final answer?
      4. How clean was the recovery?
    """
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    # --- WHAT
    tool_name: str = ""
    args: Dict[str, Any] = field(default_factory=dict)

    # --- WHO (spawn / workflow context)
    agent_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    workflow_run_id: Optional[str] = None
    caller_capabilities: List[str] = field(default_factory=list)

    # --- WHY (model reasoning, optional)
    reasoning_summary: Optional[str] = None      # one-sentence justification
    alternatives_considered: List[str] = field(default_factory=list)
    proposed_by_model: Optional[str] = None      # e.g. "ollama/llama3.1:8b"

    # --- OUTCOME
    ok: bool = False
    error_code: Optional[str] = None             # ToolErrorCode value
    error_message: Optional[str] = None
    duration_ms: float = 0.0
    output_size_bytes: Optional[int] = None      # for cost/perf analysis

    # --- EVAL SIGNALS (set by harness, not the agent itself)
    expected_tool: Optional[str] = None          # ground truth, if known
    selection_correct: Optional[bool] = None
    args_valid_first_try: Optional[bool] = None
    recovery_action: Optional[str] = None        # "retried", "fallback_tool", "abandoned", "asked_human"

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))


# =============================================================================
# WRITER
# =============================================================================

class TraceWriter:
    """Thread-safe append-only JSONL writer."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def write(self, trace: ToolCallTrace) -> None:
        line = trace.to_json_line()
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def from_registry_event(self, event: str, data: Dict[str, Any]) -> None:
        """
        Adapter so a ToolRegistry can be wired straight into the writer
        via its audit_callback. Captures only invocation outcomes —
        registration / unauthorized events are logged but not traced.
        """
        if event not in ("tool_success", "tool_failed", "tool_invalid_input",
                         "tool_unauthorized", "tool_invoked"):
            return
        # tool_invoked starts a span; tool_success/tool_failed close it.
        # For simplicity we emit one trace at close time (the close events
        # carry the duration). tool_invoked can be ignored here.
        if event == "tool_invoked":
            return

        trace = ToolCallTrace(
            tool_name=data.get("tool", ""),
            ok=(event == "tool_success"),
            error_code=None if event == "tool_success" else event.replace("tool_", ""),
            error_message=data.get("error"),
            duration_ms=data.get("duration_ms", 0.0),
        )
        self.write(trace)


# =============================================================================
# ANALYZER  (Step 7: iterate on definitions from evaluation signals)
# =============================================================================

class TraceAnalyzer:
    """
    Read a trace file and surface the four metrics the article calls out:
    selection accuracy, first-attempt arg validity, error propagation,
    recovery quality. Plus a per-tool breakdown for definition iteration.
    """

    def __init__(self, traces: List[ToolCallTrace]):
        self.traces = traces

    # --- LOADERS ---

    @classmethod
    def from_file(cls, path: str | Path) -> "TraceAnalyzer":
        traces: List[ToolCallTrace] = []
        p = Path(path)
        if not p.exists():
            return cls(traces)
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    traces.append(ToolCallTrace(**obj))
                except (json.JSONDecodeError, TypeError) as exc:
                    logger.warning("Skipping malformed trace line: %s", exc)
        return cls(traces)

    # --- METRICS ---

    def summary(self) -> Dict[str, Any]:
        if not self.traces:
            return {"trace_count": 0}

        total = len(self.traces)
        ok = sum(1 for t in self.traces if t.ok)

        # Selection accuracy (only counts traces with ground truth)
        labelled = [t for t in self.traces if t.expected_tool is not None]
        selection_correct = sum(1 for t in labelled if t.selection_correct)
        selection_accuracy = (selection_correct / len(labelled)) if labelled else None

        # First-attempt arg validity
        validity_labelled = [t for t in self.traces if t.args_valid_first_try is not None]
        valid_first = sum(1 for t in validity_labelled if t.args_valid_first_try)
        arg_validity = (valid_first / len(validity_labelled)) if validity_labelled else None

        # Recovery quality (of the failures, how many recovered cleanly?)
        failures = [t for t in self.traces if not t.ok]
        recovered = sum(1 for t in failures
                        if t.recovery_action in ("retried", "fallback_tool"))
        recovery_rate = (recovered / len(failures)) if failures else None

        # Cost signal: total tool latency
        total_latency_ms = sum(t.duration_ms for t in self.traces)

        return {
            "trace_count": total,
            "success_rate": ok / total,
            "tool_selection_accuracy": selection_accuracy,
            "first_attempt_arg_validity": arg_validity,
            "recovery_rate": recovery_rate,
            "total_latency_ms": round(total_latency_ms, 2),
            "avg_latency_ms": round(total_latency_ms / total, 2),
        }

    def per_tool_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """
        Surface the per-tool stats that drive definition iteration:
          - high error rate → description likely unclear
          - high redundant-call rate (proxy: many calls with same args) → scope problem
        """
        by_tool: Dict[str, List[ToolCallTrace]] = {}
        for t in self.traces:
            by_tool.setdefault(t.tool_name, []).append(t)

        out: Dict[str, Dict[str, Any]] = {}
        for tool, items in by_tool.items():
            n = len(items)
            errors = [i for i in items if not i.ok]
            error_codes: Dict[str, int] = {}
            for i in errors:
                if i.error_code:
                    error_codes[i.error_code] = error_codes.get(i.error_code, 0) + 1

            # Redundant-call proxy: identical arg payloads invoked > 1x
            arg_signatures: Dict[str, int] = {}
            for i in items:
                sig = json.dumps(i.args, sort_keys=True)
                arg_signatures[sig] = arg_signatures.get(sig, 0) + 1
            redundant = sum(c - 1 for c in arg_signatures.values() if c > 1)

            out[tool] = {
                "calls": n,
                "error_rate": round(len(errors) / n, 3),
                "error_codes": error_codes,
                "redundant_calls": redundant,
                "avg_latency_ms": round(sum(i.duration_ms for i in items) / n, 2),
            }
        return out

    def failure_modes_ranked(self) -> List[Dict[str, Any]]:
        """Highest-frequency failures first — drives the next iteration cycle."""
        breakdown = self.per_tool_breakdown()
        rows: List[Dict[str, Any]] = []
        for tool, stats in breakdown.items():
            for code, count in stats["error_codes"].items():
                rows.append({"tool": tool, "error_code": code, "count": count})
        rows.sort(key=lambda r: r["count"], reverse=True)
        return rows
