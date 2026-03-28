"""
AION OS — Agentic Workflow Engine
DAG-based task orchestration with dependency resolution.

"Businesses are most likely to adopt AI where it can solve a specific,
repeatable problem in a practical way." — Rich/Malu meeting, March 26 2026

Design principles:
- Tasks declare dependencies explicitly
- Parallel execution where dependencies allow
- Human-in-the-loop at trust boundaries
- Full audit trail on every state transition
"""

import logging
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("aionos.agents.workflow")


# =============================================================================
# TASK MODEL
# =============================================================================

class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"          # all deps satisfied
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"      # upstream failure
    AWAITING_APPROVAL = "awaiting_approval"  # trust gate held


@dataclass
class TaskResult:
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Single unit of work in a workflow DAG."""

    task_id: str
    name: str
    fn: Callable[..., Any]
    depends_on: List[str] = field(default_factory=list)
    trust_required: float = 0.0   # 0.0-1.0: min trust to auto-execute
    timeout_s: float = 300.0
    retries: int = 0
    tags: Set[str] = field(default_factory=set)

    # Runtime state — set by engine, not caller
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0

    def __hash__(self):
        return hash(self.task_id)


# =============================================================================
# WORKFLOW ENGINE
# =============================================================================

class WorkflowEngine:
    """
    DAG-based workflow orchestrator.

    Usage:
        engine = WorkflowEngine()
        t1 = Task("ingest", "Ingest events", fn=ingest_data)
        t2 = Task("correlate", "Correlate events", fn=correlate, depends_on=["ingest"])
        t3 = Task("alert", "Send alert", fn=alert, depends_on=["correlate"])
        engine.add_tasks([t1, t2, t3])
        results = engine.run()
    """

    def __init__(self, max_workers: int = 4, audit_callback: Optional[Callable] = None):
        self._tasks: Dict[str, Task] = {}
        self._dependents: Dict[str, List[str]] = defaultdict(list)  # task -> tasks that depend on it
        self._max_workers = max_workers
        self._audit = audit_callback or self._default_audit
        self._run_id: Optional[str] = None

    # --- BUILD PHASE ---

    def add_task(self, task: Task) -> "WorkflowEngine":
        if task.task_id in self._tasks:
            raise ValueError(f"Duplicate task_id: {task.task_id}")
        self._tasks[task.task_id] = task
        for dep in task.depends_on:
            self._dependents[dep].append(task.task_id)
        return self

    def add_tasks(self, tasks: List[Task]) -> "WorkflowEngine":
        for t in tasks:
            self.add_task(t)
        return self

    # --- VALIDATION ---

    def validate(self) -> List[str]:
        """Check for missing deps and cycles. Returns list of errors."""
        errors = []
        # missing deps
        for task in self._tasks.values():
            for dep in task.depends_on:
                if dep not in self._tasks:
                    errors.append(f"Task '{task.task_id}' depends on unknown task '{dep}'")
        # cycle detection via topological sort
        if not errors:
            in_degree = {t: 0 for t in self._tasks}
            for task in self._tasks.values():
                for dep in task.depends_on:
                    in_degree[task.task_id] += 1
            queue = deque(t for t, d in in_degree.items() if d == 0)
            visited = 0
            while queue:
                node = queue.popleft()
                visited += 1
                for child in self._dependents.get(node, []):
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)
            if visited < len(self._tasks):
                errors.append("Workflow contains a cycle — cannot execute")
        return errors

    # --- EXECUTION ---

    def run(self, trust_score: float = 1.0, context: Optional[Dict] = None) -> Dict[str, TaskResult]:
        """
        Execute the workflow DAG.

        Args:
            trust_score: Current operator trust level (0.0-1.0).
                         Tasks with trust_required > trust_score pause for approval.
            context: Shared context dict passed to every task fn.

        Returns:
            Dict mapping task_id -> TaskResult
        """
        errors = self.validate()
        if errors:
            raise RuntimeError("Workflow validation failed: " + "; ".join(errors))

        self._run_id = uuid.uuid4().hex[:12]
        context = context or {}
        results: Dict[str, TaskResult] = {}

        # Reset state
        for task in self._tasks.values():
            task.status = TaskStatus.PENDING
            task.result = None
            task.retry_count = 0

        self._audit("workflow_start", {
            "run_id": self._run_id,
            "task_count": len(self._tasks),
            "trust_score": trust_score,
        })

        # BFS execution
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures: Dict[str, Future] = {}
            self._mark_ready_tasks(trust_score)

            while self._has_pending_work(futures):
                # Submit ready tasks
                for tid, task in self._tasks.items():
                    if task.status == TaskStatus.READY and tid not in futures:
                        dep_results = {d: self._tasks[d].result for d in task.depends_on}
                        futures[tid] = pool.submit(
                            self._execute_task, task, dep_results, context
                        )

                # Collect completed futures
                done_ids = [tid for tid, f in futures.items() if f.done()]
                for tid in done_ids:
                    future = futures.pop(tid)
                    task = self._tasks[tid]
                    try:
                        task.result = future.result()
                        task.status = TaskStatus.COMPLETED
                    except Exception as exc:
                        task.result = TaskResult(error=str(exc))
                        if task.retry_count < task.retries:
                            task.retry_count += 1
                            task.status = TaskStatus.READY
                            self._audit("task_retry", {"task": tid, "attempt": task.retry_count})
                        else:
                            task.status = TaskStatus.FAILED
                            self._skip_dependents(tid)

                    task.completed_at = datetime.utcnow()
                    results[tid] = task.result
                    self._audit("task_done", {
                        "task": tid, "status": task.status.value,
                        "duration_ms": task.result.duration_ms,
                    })

                    # Unlock downstream
                    self._mark_ready_tasks(trust_score)

                if not done_ids:
                    time.sleep(0.05)  # prevent busy-spin

        self._audit("workflow_done", {
            "run_id": self._run_id,
            "completed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED),
            "skipped": sum(1 for t in self._tasks.values() if t.status == TaskStatus.SKIPPED),
        })

        return results

    def approve_task(self, task_id: str) -> None:
        """Manually approve a trust-gated task."""
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.AWAITING_APPROVAL:
            task.status = TaskStatus.READY
            self._audit("task_approved", {"task": task_id})

    # --- INTERNAL ---

    def _execute_task(self, task: Task, dep_results: Dict, context: Dict) -> TaskResult:
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        self._audit("task_start", {"task": task.task_id})

        start = time.perf_counter()
        try:
            output = task.fn(dep_results=dep_results, context=context)
            elapsed = (time.perf_counter() - start) * 1000
            return TaskResult(output=output, duration_ms=elapsed)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            raise RuntimeError(f"Task '{task.task_id}' failed: {exc}") from exc

    def _mark_ready_tasks(self, trust_score: float) -> None:
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                self._tasks[d].status == TaskStatus.COMPLETED
                for d in task.depends_on
            )
            if deps_met:
                if task.trust_required > trust_score:
                    task.status = TaskStatus.AWAITING_APPROVAL
                    self._audit("task_held", {
                        "task": task.task_id,
                        "required": task.trust_required,
                        "current": trust_score,
                    })
                else:
                    task.status = TaskStatus.READY

    def _skip_dependents(self, failed_id: str) -> None:
        for child_id in self._dependents.get(failed_id, []):
            child = self._tasks[child_id]
            if child.status == TaskStatus.PENDING:
                child.status = TaskStatus.SKIPPED
                child.result = TaskResult(error=f"Skipped: upstream '{failed_id}' failed")
                self._skip_dependents(child_id)

    def _has_pending_work(self, futures: Dict) -> bool:
        return bool(futures) or any(
            t.status in (TaskStatus.PENDING, TaskStatus.READY)
            for t in self._tasks.values()
        )

    @staticmethod
    def _default_audit(event: str, data: Dict) -> None:
        logger.info("WORKFLOW | %s | %s", event, data)
