"""
AION OS — Agentic Computing Framework

Built from the thesis: "The near-term opportunity is agentic computing.
Agents automating work, spawning new agents — that's the 2-3 year window."

Four pillars:
1. WorkflowEngine   — DAG-based task orchestration
2. AgentSpawner     — Agent lifecycle management & pool control
3. TrustGate        — Trust-scored execution boundaries
4. FrictionReducer  — Auto-delegation to minimize human touchpoints
"""

from aionos.agents.workflow import WorkflowEngine, Task, TaskStatus
from aionos.agents.spawner import AgentSpawner, Agent, AgentState
from aionos.agents.trust_gate import TrustGate, TrustLevel
from aionos.agents.friction import FrictionReducer

__all__ = [
    "WorkflowEngine", "Task", "TaskStatus",
    "AgentSpawner", "Agent", "AgentState",
    "TrustGate", "TrustLevel",
    "FrictionReducer",
]
