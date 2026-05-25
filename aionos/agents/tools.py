"""
AION OS — Tool Contracts for Spawned Agents

Implements Steps 2 & 3 of the tool-calling roadmap:
- Tool definitions as contracts (typed schemas, scope, negative guidance)
- Typed, interpretable error signals (not freeform strings)

Why this matters for AION OS:
A spawned child agent needs to *select* a tool from a registry without
guessing argument shapes or interpreting error strings as natural language.
ToolSpec gives every tool a contract; ToolError gives every failure a code.

Usage:
    from aionos.agents.tools import ToolSpec, ToolRegistry, ToolError, ToolResult

    spec = ToolSpec(
        name="kb_search",
        purpose="Search internal knowledge base. "
                "Use for firm-specific policies, prior matters, internal docs. "
                "Do NOT use for general legal research or web lookups.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 3},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array"},
                "result_count": {"type": "integer"},
            },
        },
        capabilities_required={AgentCapability.READ_DATA},
        side_effects=False,
    )

    registry = ToolRegistry()
    registry.register(spec, fn=do_kb_search)
    result = registry.invoke("kb_search", {"query": "data retention policy"})
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from aionos.agents.spawner import AgentCapability

logger = logging.getLogger("aionos.agents.tools")


# =============================================================================
# TYPED ERROR SIGNALS  (Step 3 — error handling)
# =============================================================================

class ToolErrorCode(Enum):
    """Stable error codes a reasoning agent can branch on."""

    INVALID_INPUT = "invalid_input"          # arg validation failed
    NOT_FOUND = "not_found"                  # resource missing
    UNAUTHORIZED = "unauthorized"            # capability or auth missing
    RATE_LIMITED = "rate_limited"            # transient, retry with backoff
    UPSTREAM_TIMEOUT = "upstream_timeout"    # transient
    UPSTREAM_ERROR = "upstream_error"        # downstream service broken
    CIRCUIT_OPEN = "circuit_open"            # circuit breaker tripped
    INTERNAL_ERROR = "internal_error"        # unexpected — investigate
    EMPTY_RESULT = "empty_result"            # not an error but signals void


@dataclass
class ToolError:
    """
    Structured error a model can reason from.

    The freeform `message` is for humans/logs; reasoning loops should
    branch on `code` and consult `retry_after` / `details`.
    """
    code: ToolErrorCode
    message: str
    retry_after: Optional[float] = None         # seconds, if transient
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code.value,
            "message": self.message,
            "retry_after": self.retry_after,
            "details": self.details,
        }


@dataclass
class ToolResult:
    """Uniform success-or-error envelope returned by every tool invocation."""
    ok: bool
    output: Any = None
    error: Optional[ToolError] = None
    duration_ms: float = 0.0
    tool_name: str = ""

    @classmethod
    def success(cls, output: Any, tool_name: str = "", duration_ms: float = 0.0) -> "ToolResult":
        return cls(ok=True, output=output, tool_name=tool_name, duration_ms=duration_ms)

    @classmethod
    def failure(cls, error: ToolError, tool_name: str = "", duration_ms: float = 0.0) -> "ToolResult":
        return cls(ok=False, error=error, tool_name=tool_name, duration_ms=duration_ms)

    def to_dict(self) -> Dict[str, Any]:
        if self.ok:
            return {"ok": True, "output": self.output, "tool": self.tool_name,
                    "duration_ms": self.duration_ms}
        return {"ok": False, "tool": self.tool_name,
                "duration_ms": self.duration_ms, **self.error.to_dict()}


# =============================================================================
# TOOL CONTRACT  (Step 2 — definitions as contracts)
# =============================================================================

@dataclass
class ToolSpec:
    """
    Contract for a tool a model (or spawned agent) can invoke.

    Required discipline:
    - `purpose` MUST include when NOT to use this tool (negative guidance)
    - `input_schema` MUST be valid JSON Schema (enums > open strings)
    - `output_schema` MUST describe success, empty, and partial results
    - `capabilities_required` MUST be the minimum needed (least privilege)
    """
    name: str                                    # snake_case, domain-prefixed
    purpose: str                                 # one sentence + negative guidance
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    capabilities_required: Set[AgentCapability] = field(default_factory=set)
    side_effects: bool = False                   # True = write/network/modify
    requires_human_approval: bool = False        # gate irreversible actions
    timeout_s: float = 30.0
    failure_threshold: int = 5                   # circuit breaker trip count
    cooldown_s: float = 60.0                     # circuit breaker reset

    def __post_init__(self) -> None:
        if not self.name or " " in self.name:
            raise ValueError(f"Tool name must be snake_case, got {self.name!r}")
        if len(self.purpose) < 20:
            raise ValueError(
                f"Tool '{self.name}' purpose too short. "
                "Include scope AND when NOT to use it."
            )
        if not isinstance(self.input_schema, dict) or "type" not in self.input_schema:
            raise ValueError(f"Tool '{self.name}' input_schema must be a JSON Schema dict")


# =============================================================================
# INPUT VALIDATION  (Step 1 — execution boundary)
# =============================================================================

def validate_against_schema(value: Any, schema: Dict[str, Any]) -> Optional[str]:
    """
    Minimal JSON-Schema-shaped validator (no external deps).
    Returns None if valid, else an error message.

    Covers the essentials needed for tool-call validation:
    type, required, properties (recursive), enum, minLength, minimum, maximum.
    For richer validation, swap to `jsonschema` lib later.
    """
    expected_type = schema.get("type")
    type_map = {
        "object": dict, "array": list, "string": str,
        "integer": int, "number": (int, float), "boolean": bool, "null": type(None),
    }
    if expected_type and expected_type in type_map:
        if not isinstance(value, type_map[expected_type]):
            # bool is a subclass of int — disallow that confusion
            if expected_type in ("integer", "number") and isinstance(value, bool):
                return f"Expected {expected_type}, got bool"
            return f"Expected {expected_type}, got {type(value).__name__}"

    if "enum" in schema and value not in schema["enum"]:
        return f"Value {value!r} not in enum {schema['enum']}"

    if expected_type == "string":
        if "minLength" in schema and len(value) < schema["minLength"]:
            return f"String shorter than minLength={schema['minLength']}"
    if expected_type in ("integer", "number"):
        if "minimum" in schema and value < schema["minimum"]:
            return f"Value {value} below minimum={schema['minimum']}"
        if "maximum" in schema and value > schema["maximum"]:
            return f"Value {value} above maximum={schema['maximum']}"

    if expected_type == "object":
        for key in schema.get("required", []):
            if key not in value:
                return f"Missing required field: {key!r}"
        for key, subschema in schema.get("properties", {}).items():
            if key in value:
                err = validate_against_schema(value[key], subschema)
                if err:
                    return f"{key}: {err}"
    return None


# =============================================================================
# CIRCUIT BREAKER  (Step 3 — persistent failure handling)
# =============================================================================

class _Breaker:
    """Per-tool circuit breaker. Opens after N failures, resets after cooldown."""

    def __init__(self, threshold: int, cooldown_s: float):
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self.failures = 0
        self.opened_at: Optional[float] = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.time() - self.opened_at >= self.cooldown_s:
            # Half-open: allow next call to attempt
            self.failures = 0
            self.opened_at = None
            return False
        return True

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = time.time()


# =============================================================================
# TOOL REGISTRY  (Step 5 — catalog management)
# =============================================================================

class ToolRegistry:
    """
    Holds tool specs + their executor functions.

    A spawned agent receives a *subset* of this registry filtered by its
    capabilities — that gives you dynamic tool loading (Step 5) and
    least-privilege enforcement (Step 6) in one boundary.
    """

    def __init__(self, audit_callback: Optional[Callable[[str, Dict], None]] = None):
        self._specs: Dict[str, ToolSpec] = {}
        self._fns: Dict[str, Callable[..., Any]] = {}
        self._breakers: Dict[str, _Breaker] = {}
        self._audit = audit_callback or self._default_audit

    # --- BUILD ---

    def register(self, spec: ToolSpec, fn: Callable[..., Any]) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Duplicate tool name: {spec.name}")
        self._specs[spec.name] = spec
        self._fns[spec.name] = fn
        self._breakers[spec.name] = _Breaker(spec.failure_threshold, spec.cooldown_s)
        self._audit("tool_registered", {"tool": spec.name,
                                        "capabilities": [c.value for c in spec.capabilities_required],
                                        "side_effects": spec.side_effects})

    # --- DISCOVERY ---

    def specs_for(self, capabilities: Set[AgentCapability]) -> List[ToolSpec]:
        """
        Return only the tools the caller has capabilities to invoke.
        This is the boundary an agent sees — narrower catalog, better selection.
        """
        return [s for s in self._specs.values()
                if s.capabilities_required.issubset(capabilities)]

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._specs.get(name)

    # --- EXECUTION ---

    def invoke(
        self,
        name: str,
        args: Dict[str, Any],
        caller_capabilities: Optional[Set[AgentCapability]] = None,
    ) -> ToolResult:
        """
        Validate, gate, execute, and wrap the result. Always returns ToolResult.
        Never raises — failures are typed errors so the reasoning loop can branch.
        """
        start = time.perf_counter()
        spec = self._specs.get(name)
        if spec is None:
            return ToolResult.failure(
                ToolError(ToolErrorCode.NOT_FOUND, f"No tool registered as {name!r}"),
                tool_name=name,
            )

        # Capability check (least privilege)
        if caller_capabilities is not None:
            if not spec.capabilities_required.issubset(caller_capabilities):
                missing = spec.capabilities_required - caller_capabilities
                self._audit("tool_unauthorized", {"tool": name,
                                                  "missing": [c.value for c in missing]})
                return ToolResult.failure(
                    ToolError(ToolErrorCode.UNAUTHORIZED,
                              f"Caller missing capabilities: {[c.value for c in missing]}",
                              details={"missing": [c.value for c in missing]}),
                    tool_name=name,
                )

        # Circuit breaker check
        breaker = self._breakers[name]
        if breaker.is_open():
            return ToolResult.failure(
                ToolError(ToolErrorCode.CIRCUIT_OPEN,
                          f"Tool {name!r} circuit open after {breaker.failures} failures",
                          retry_after=breaker.cooldown_s),
                tool_name=name,
            )

        # Input validation
        err = validate_against_schema(args, spec.input_schema)
        if err:
            self._audit("tool_invalid_input", {"tool": name, "error": err})
            return ToolResult.failure(
                ToolError(ToolErrorCode.INVALID_INPUT, err),
                tool_name=name,
            )

        # Execute
        self._audit("tool_invoked", {"tool": name,
                                     "side_effects": spec.side_effects})
        try:
            output = self._fns[name](**args)
            elapsed = (time.perf_counter() - start) * 1000

            if output is None or output == [] or output == {}:
                breaker.record_success()  # empty is not a failure
                return ToolResult.failure(
                    ToolError(ToolErrorCode.EMPTY_RESULT,
                              f"Tool {name!r} returned no results"),
                    tool_name=name, duration_ms=elapsed,
                )

            breaker.record_success()
            self._audit("tool_success", {"tool": name, "duration_ms": elapsed})
            return ToolResult.success(output, tool_name=name, duration_ms=elapsed)

        except TimeoutError as exc:
            breaker.record_failure()
            elapsed = (time.perf_counter() - start) * 1000
            return ToolResult.failure(
                ToolError(ToolErrorCode.UPSTREAM_TIMEOUT, str(exc), retry_after=5.0),
                tool_name=name, duration_ms=elapsed,
            )
        except Exception as exc:
            breaker.record_failure()
            elapsed = (time.perf_counter() - start) * 1000
            self._audit("tool_failed", {"tool": name, "error": str(exc),
                                        "consecutive_failures": breaker.failures})
            return ToolResult.failure(
                ToolError(ToolErrorCode.UPSTREAM_ERROR, str(exc),
                          details={"exception_type": type(exc).__name__}),
                tool_name=name, duration_ms=elapsed,
            )

    # --- INSPECTION ---

    def describe_for_model(self, capabilities: Set[AgentCapability]) -> List[Dict[str, Any]]:
        """
        Render the visible catalog for a reasoning model in a stable shape.
        This is what gets serialized into the LLM prompt — small + clear.
        """
        return [
            {
                "name": s.name,
                "purpose": s.purpose,
                "input_schema": s.input_schema,
                "output_schema": s.output_schema,
                "side_effects": s.side_effects,
                "requires_human_approval": s.requires_human_approval,
            }
            for s in self.specs_for(capabilities)
        ]

    @staticmethod
    def _default_audit(event: str, data: Dict) -> None:
        logger.info("TOOLS | %s | %s", event, data)
