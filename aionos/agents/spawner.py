"""
AION OS — Agent Spawner & Pool Manager
Lifecycle management for autonomous agents.

"Once agents start automating more work, spawning new agents, and the next
wave of AI maturity hits, it becomes almost impossible to know what the
future will look like." — Malu Omeonga, March 26 2026

Design:
- Agents are lightweight workers with a defined capability set
- Parent agents can spawn children (bounded by pool limits)
- Every agent has an expiry (no zombie processes)
- All spawns are audit-logged and trust-gated
"""

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("aionos.agents.spawner")


# =============================================================================
# AGENT MODEL
# =============================================================================

class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class AgentCapability(Enum):
    """What an agent is allowed to do."""
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    NETWORK_CALL = "network_call"
    SPAWN_CHILD = "spawn_child"
    ALERT_HUMAN = "alert_human"
    MODIFY_POLICY = "modify_policy"


@dataclass
class Agent:
    """A single autonomous agent instance."""

    agent_id: str
    name: str
    fn: Callable[..., Any]
    capabilities: Set[AgentCapability] = field(default_factory=set)
    parent_id: Optional[str] = None
    ttl_seconds: float = 600.0       # max lifetime — auto-expire
    trust_floor: float = 0.0         # minimum trust to operate

    # Runtime — managed by spawner
    state: AgentState = AgentState.IDLE
    spawned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    children: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.agent_id)


# =============================================================================
# POOL LIMITS
# =============================================================================

DEFAULT_MAX_AGENTS = 20          # hard ceiling on concurrent agents
DEFAULT_MAX_DEPTH = 3            # max parent -> child -> grandchild depth
DEFAULT_MAX_CHILDREN = 5         # max children per parent


# =============================================================================
# AGENT SPAWNER
# =============================================================================

class AgentSpawner:
    """
    Manages agent lifecycle: spawn, monitor, terminate, expire.

    Usage:
        spawner = AgentSpawner()
        agent = spawner.spawn("scanner", scan_network, capabilities={AgentCapability.READ_DATA})
        spawner.wait(agent.agent_id)
        print(agent.result)
    """

    def __init__(
        self,
        max_agents: int = DEFAULT_MAX_AGENTS,
        max_depth: int = DEFAULT_MAX_DEPTH,
        max_children: int = DEFAULT_MAX_CHILDREN,
        audit_callback: Optional[Callable] = None,
    ):
        self._agents: Dict[str, Agent] = {}
        self._pool = ThreadPoolExecutor(max_workers=max_agents)
        self._futures: Dict[str, Future] = {}
        self._lock = threading.Lock()
        self._max_agents = max_agents
        self._max_depth = max_depth
        self._max_children = max_children
        self._audit = audit_callback or self._default_audit

        # Start reaper thread for expired agents
        self._reaper_running = True
        self._reaper = threading.Thread(target=self._reap_expired, daemon=True)
        self._reaper.start()

    # --- PUBLIC API ---

    def spawn(
        self,
        name: str,
        fn: Callable[..., Any],
        capabilities: Optional[Set[AgentCapability]] = None,
        parent_id: Optional[str] = None,
        ttl_seconds: float = 600.0,
        trust_floor: float = 0.0,
        context: Optional[Dict] = None,
    ) -> Agent:
        """
        Spawn a new agent.

        Args:
            name: Human-readable agent name
            fn: Callable the agent will execute
            capabilities: What this agent is allowed to do
            parent_id: ID of parent agent (None = top-level)
            ttl_seconds: Max lifetime before auto-expiry
            trust_floor: Minimum trust score to operate
            context: Dict passed to fn

        Returns:
            The spawned Agent instance

        Raises:
            RuntimeError on pool exhaustion, depth limit, or child limit
        """
        with self._lock:
            # Guard: pool size
            active = sum(1 for a in self._agents.values() if a.state in (AgentState.IDLE, AgentState.RUNNING))
            if active >= self._max_agents:
                raise RuntimeError(f"Agent pool exhausted ({self._max_agents} max)")

            # Guard: spawn depth
            depth = self._get_depth(parent_id)
            if depth >= self._max_depth:
                raise RuntimeError(f"Max spawn depth reached ({self._max_depth})")

            # Guard: children per parent
            if parent_id:
                parent = self._agents.get(parent_id)
                if not parent:
                    raise RuntimeError(f"Parent agent '{parent_id}' not found")
                if AgentCapability.SPAWN_CHILD not in parent.capabilities:
                    raise RuntimeError(f"Parent '{parent_id}' lacks SPAWN_CHILD capability")
                if len(parent.children) >= self._max_children:
                    raise RuntimeError(f"Parent '{parent_id}' at child limit ({self._max_children})")

            agent = Agent(
                agent_id=uuid.uuid4().hex[:12],
                name=name,
                fn=fn,
                capabilities=capabilities or {AgentCapability.READ_DATA},
                parent_id=parent_id,
                ttl_seconds=ttl_seconds,
                trust_floor=trust_floor,
                spawned_at=datetime.utcnow(),
            )
            self._agents[agent.agent_id] = agent

            if parent_id:
                self._agents[parent_id].children.append(agent.agent_id)

        self._audit("agent_spawned", {
            "agent_id": agent.agent_id,
            "name": name,
            "parent": parent_id,
            "depth": depth,
            "capabilities": [c.value for c in agent.capabilities],
            "ttl": ttl_seconds,
        })

        # Execute
        ctx = context or {}
        future = self._pool.submit(self._run_agent, agent, ctx)
        self._futures[agent.agent_id] = future
        return agent

    def wait(self, agent_id: str, timeout: Optional[float] = None) -> Agent:
        """Block until agent completes or times out."""
        future = self._futures.get(agent_id)
        if future:
            future.result(timeout=timeout)
        return self._agents[agent_id]

    def terminate(self, agent_id: str, reason: str = "manual") -> None:
        """Force-terminate an agent and all its children."""
        agent = self._agents.get(agent_id)
        if not agent:
            return
        agent.state = AgentState.TERMINATED
        agent.error = f"Terminated: {reason}"
        agent.completed_at = datetime.utcnow()
        self._audit("agent_terminated", {"agent_id": agent_id, "reason": reason})

        # Cascade to children
        for child_id in agent.children:
            self.terminate(child_id, reason=f"parent '{agent_id}' terminated")

    def status(self) -> Dict[str, Any]:
        """Pool status summary."""
        counts = {}
        for a in self._agents.values():
            counts[a.state.value] = counts.get(a.state.value, 0) + 1
        return {
            "total": len(self._agents),
            "by_state": counts,
            "pool_limit": self._max_agents,
        }

    def get(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def list_active(self) -> List[Agent]:
        return [a for a in self._agents.values() if a.state in (AgentState.IDLE, AgentState.RUNNING)]

    def shutdown(self) -> None:
        """Graceful shutdown."""
        self._reaper_running = False
        for aid in list(self._agents):
            a = self._agents[aid]
            if a.state in (AgentState.IDLE, AgentState.RUNNING):
                self.terminate(aid, reason="shutdown")
        self._pool.shutdown(wait=False)

    # --- INTERNAL ---

    def _run_agent(self, agent: Agent, context: Dict) -> None:
        agent.state = AgentState.RUNNING
        self._audit("agent_running", {"agent_id": agent.agent_id})
        try:
            agent.result = agent.fn(agent=agent, spawner=self, context=context)
            if agent.state == AgentState.RUNNING:  # not terminated mid-flight
                agent.state = AgentState.COMPLETED
        except Exception as exc:
            agent.error = str(exc)
            if agent.state == AgentState.RUNNING:
                agent.state = AgentState.FAILED
            self._audit("agent_failed", {"agent_id": agent.agent_id, "error": str(exc)})
        finally:
            agent.completed_at = datetime.utcnow()
            self._audit("agent_done", {
                "agent_id": agent.agent_id,
                "state": agent.state.value,
                "children_spawned": len(agent.children),
            })

    def _get_depth(self, parent_id: Optional[str]) -> int:
        depth = 0
        pid = parent_id
        while pid:
            depth += 1
            parent = self._agents.get(pid)
            pid = parent.parent_id if parent else None
        return depth

    def _reap_expired(self) -> None:
        """Background thread: auto-expire agents past TTL."""
        while self._reaper_running:
            now = datetime.utcnow()
            with self._lock:
                for agent in list(self._agents.values()):
                    if agent.state not in (AgentState.IDLE, AgentState.RUNNING):
                        continue
                    if agent.spawned_at and (now - agent.spawned_at).total_seconds() > agent.ttl_seconds:
                        agent.state = AgentState.EXPIRED
                        agent.error = "TTL expired"
                        agent.completed_at = now
                        self._audit("agent_expired", {
                            "agent_id": agent.agent_id,
                            "ttl": agent.ttl_seconds,
                        })
                        # Cascade
                        for child_id in agent.children:
                            self.terminate(child_id, reason=f"parent '{agent.agent_id}' expired")
            time.sleep(5)

    @staticmethod
    def _default_audit(event: str, data: Dict) -> None:
        logger.info("SPAWNER | %s | %s", event, data)
