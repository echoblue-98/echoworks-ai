"""
AION OS — Ollama Sandbox: Spawned Agent + Tool Registry + Trace

Demonstrates the full agentic loop end-to-end, fully offline:

  user query
    -> spawned agent (with capability scope)
       -> sees only the tools its capabilities permit
       -> Ollama proposes tool name + args (JSON)
       -> ToolRegistry validates + executes
       -> ToolCallTrace captures the step
    -> result returned to caller

Run:
    1. Start Ollama:        ollama serve
    2. Pull a model:        ollama pull qwen2.5:7b-instruct
    3. Run the sandbox:     python examples/ollama_agent_sandbox.py

All tool calls are written to logs/ollama_sandbox_traces.jsonl.
After the run, the script prints summary metrics.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make the project importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from aionos.agents import (
    AgentCapability,
    AgentSpawner,
    ToolRegistry,
    ToolSpec,
)
from aionos.observability.tool_trace import TraceAnalyzer, TraceWriter

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
TRACE_PATH = Path("logs/ollama_sandbox_traces.jsonl")


# ---------------------------------------------------------------------------
# SANDBOX TOOLS  — three deliberately overlapping examples
# (lets us watch the model pick the right one, or fumble)
# ---------------------------------------------------------------------------

POLICY_DB = {
    "data retention": "Client data is retained for 7 years post-matter close, "
                      "then cryptographically destroyed.",
    "breach response": "All breaches are reported to the managing partner within "
                       "1 hour. External notification follows GA OCGA 10-1-911.",
    "ai vendor review": "All AI vendors must complete the 14-point sovereignty "
                        "audit before any client data is processed.",
}

CONTRACT_TERMS = {
    "indemnification cap": "Vendor liability capped at 12 months of fees paid.",
    "data training": "Vendor may use client data to train models unless opted out in writing.",
    "termination": "Either party may terminate with 30 days written notice.",
}


def kb_search(query: str) -> dict:
    """Internal policy search — exact-keyword for sandbox simplicity."""
    q = query.lower()
    for k, v in POLICY_DB.items():
        if k in q or q in k:
            return {"policy": k, "text": v}
    return {}


def contract_lookup(clause: str) -> dict:
    """Vendor contract clause lookup."""
    c = clause.lower()
    for k, v in CONTRACT_TERMS.items():
        if k in c or c in k:
            return {"clause": k, "text": v}
    return {}


def calculate_breach_cost(billable_hours_lost: float, hourly_rate: float) -> dict:
    """Side-effecting math — not really side-effecting, but we mark it so to
    exercise the capability gate."""
    return {
        "lost_revenue_usd": round(billable_hours_lost * hourly_rate, 2),
        "hours": billable_hours_lost,
        "rate": hourly_rate,
    }


# ---------------------------------------------------------------------------
# REGISTER TOOLS WITH CONTRACTS
# ---------------------------------------------------------------------------

def build_registry(audit_callback) -> ToolRegistry:
    reg = ToolRegistry(audit_callback=audit_callback)

    reg.register(
        ToolSpec(
            name="kb_search",
            purpose=(
                "Search internal firm policy knowledge base for topics like "
                "data retention, breach response, AI vendor review. "
                "Do NOT use for vendor contract clauses or numeric calculations."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 3},
                },
                "required": ["query"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "policy": {"type": "string"},
                    "text": {"type": "string"},
                },
            },
            capabilities_required={AgentCapability.READ_DATA},
            side_effects=False,
        ),
        fn=kb_search,
    )

    reg.register(
        ToolSpec(
            name="contract_lookup",
            purpose=(
                "Look up specific clauses in a vendor contract (indemnification, "
                "data training rights, termination). Do NOT use for internal "
                "firm policy questions."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "clause": {"type": "string", "minLength": 3},
                },
                "required": ["clause"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "clause": {"type": "string"},
                    "text": {"type": "string"},
                },
            },
            capabilities_required={AgentCapability.READ_DATA},
            side_effects=False,
        ),
        fn=contract_lookup,
    )

    reg.register(
        ToolSpec(
            name="calculate_breach_cost",
            purpose=(
                "Compute the lost-revenue dollar amount when AI downtime "
                "causes billable hours to be lost. "
                "Use ONLY when both hours and hourly rate are provided."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "billable_hours_lost": {"type": "number", "minimum": 0},
                    "hourly_rate": {"type": "number", "minimum": 0},
                },
                "required": ["billable_hours_lost", "hourly_rate"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "lost_revenue_usd": {"type": "number"},
                },
            },
            capabilities_required={AgentCapability.READ_DATA},
            side_effects=False,
        ),
        fn=calculate_breach_cost,
    )

    return reg


# ---------------------------------------------------------------------------
# OLLAMA TOOL-CALLING LOOP
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a tool-calling agent for AION OS. \
Given a user question and a list of available tools, select EXACTLY ONE tool \
and produce its arguments. Respond ONLY with a single-line JSON object of the form:

{"tool": "<tool_name>", "args": {...}}

Rules:
- Pick the tool whose 'purpose' best matches the user question.
- Read the negative guidance ("Do NOT use for...") carefully.
- If no tool fits, respond exactly: {"tool": null, "args": {}}
- Never invent a tool name. Never add commentary outside the JSON.
"""


def ask_ollama(visible_tools: list, user_question: str) -> dict:
    """Send the prompt to Ollama and parse the JSON response."""
    catalog = json.dumps(visible_tools, indent=2)
    prompt = (
        f"Available tools:\n{catalog}\n\n"
        f"User question: {user_question}\n\n"
        f"Respond with the JSON tool call now."
    )
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "format": "json",  # forces JSON-only output
            "options": {"temperature": 0.1},
        },
        timeout=120,
    )
    resp.raise_for_status()
    raw = resp.json().get("response", "")
    return json.loads(raw)


def sandbox_agent(agent, spawner, context):
    """Body of the spawned agent."""
    registry: ToolRegistry = context["registry"]
    question: str = context["question"]

    visible = registry.describe_for_model(agent.capabilities)
    print(f"\n[agent={agent.name}] visible tools: {[t['name'] for t in visible]}")
    print(f"[agent={agent.name}] question: {question}")

    try:
        proposal = ask_ollama(visible, question)
    except Exception as exc:
        import traceback
        print(f"[agent={agent.name}] !! ollama call failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return {"ok": False, "error": f"ollama call failed: {exc}"}

    tool = proposal.get("tool")
    args = proposal.get("args", {}) or {}
    print(f"[agent={agent.name}] model proposed: tool={tool} args={args}")

    if tool is None:
        return {"ok": False, "reason": "no tool selected"}

    result = registry.invoke(tool, args, caller_capabilities=agent.capabilities)
    print(f"[agent={agent.name}] registry result: ok={result.ok} "
          f"err={result.error.code.value if result.error else None}")
    return result.to_dict()


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

def check_ollama_ready() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        models = [m["name"] for m in r.json().get("models", [])]
        if not models:
            print(f"!! Ollama is running but no models pulled. Run: ollama pull {OLLAMA_MODEL}")
            return False
        if not any(OLLAMA_MODEL in m for m in models):
            print(f"!! Configured model '{OLLAMA_MODEL}' not found. Available: {models}")
            print(f"   Run: ollama pull {OLLAMA_MODEL}  (or set OLLAMA_MODEL env var)")
            return False
        return True
    except Exception as exc:
        print(f"!! Ollama not reachable at {OLLAMA_URL}: {exc}")
        print( "   Start it with:  ollama serve")
        return False


def main():
    if not check_ollama_ready():
        sys.exit(1)

    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TRACE_PATH.exists():
        TRACE_PATH.unlink()

    writer = TraceWriter(TRACE_PATH)
    registry = build_registry(audit_callback=writer.from_registry_event)
    spawner = AgentSpawner()

    questions = [
        "What is our policy on data retention?",
        "What does the vendor contract say about indemnification cap?",
        "We lost 8 billable hours at $450/hour. What's the cost?",
        "How do we handle a breach response?",
        "What's the weather in Atlanta?",  # should select null
    ]

    for q in questions:
        agent = spawner.spawn(
            name=f"sandbox_{questions.index(q)}",
            fn=sandbox_agent,
            capabilities={AgentCapability.READ_DATA},
            ttl_seconds=180,
            context={"registry": registry, "question": q},
        )
        spawner.wait(agent.agent_id, timeout=180)

    spawner.shutdown()

    print("\n" + "=" * 70)
    print("EVALUATION (from trace file)")
    print("=" * 70)
    analyzer = TraceAnalyzer.from_file(TRACE_PATH)
    print("Summary:", json.dumps(analyzer.summary(), indent=2))
    print("\nPer-tool breakdown:", json.dumps(analyzer.per_tool_breakdown(), indent=2))
    print("\nFailure modes ranked:", json.dumps(analyzer.failure_modes_ranked(), indent=2))
    print(f"\nFull traces: {TRACE_PATH.resolve()}")


if __name__ == "__main__":
    main()
