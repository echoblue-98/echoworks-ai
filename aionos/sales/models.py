"""
Sales Engine — Data Models
===========================
Structured types for verticals, personas, threat scenarios,
regulatory hooks, objection responses, and outbound sequences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class VerticalID(str, Enum):
    LEGAL = "legal"
    HEALTHCARE = "healthcare"
    REALESTATE = "realestate"


class BuyerRole(str, Enum):
    DECISION_MAKER = "decision_maker"
    INFLUENCER = "influencer"
    TECHNICAL = "technical"
    CHAMPION = "champion"


class DealStage(str, Enum):
    COLD = "cold"
    ENGAGED = "engaged"          # replied or accepted connection
    DEMO_SCHEDULED = "demo_scheduled"
    DEMO_COMPLETED = "demo_completed"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


@dataclass
class RegulatoryHook:
    """A regulation or standard that creates buying pressure."""
    name: str
    citation: str
    penalty_range: str
    relevance: str  # why it forces the prospect to act


@dataclass
class ThreatScenario:
    """A specific threat chain AION OS detects for a vertical."""
    name: str
    description: str
    event_chain: List[str]           # ordered sequence of events
    detection_speed: str             # e.g. "< 3 seconds"
    financial_impact: str            # dollar value of the threat
    pattern_engine_bypass: bool      # True = pure pattern, no LLM needed


@dataclass
class Objection:
    """Common objection and the response that neutralizes it."""
    objection: str
    response: str
    proof_point: Optional[str] = None


@dataclass
class BuyerPersona:
    """Target buyer within a vertical."""
    title: str
    role: BuyerRole
    pain_points: List[str]
    trigger_events: List[str]       # events that make them ready to buy
    linkedin_search: str            # search query to find them
    email_subject: str
    opening_line: str


@dataclass
class PricingTier:
    """Pricing for a vertical."""
    tier_name: str
    monthly: int
    includes: List[str]


@dataclass
class OutboundSequence:
    """Multi-touch outbound cadence for a vertical."""
    day: int
    channel: str       # "email", "linkedin", "phone"
    action: str        # what to do
    template_key: str  # reference to message template


@dataclass
class Vertical:
    """Complete sales configuration for one vertical."""
    id: VerticalID
    display_name: str
    tagline: str

    # What we detect
    threat_scenarios: List[ThreatScenario]

    # Who we sell to
    buyer_personas: List[BuyerPersona]

    # Why they must buy
    regulatory_hooks: List[RegulatoryHook]

    # How we handle pushback
    objections: List[Objection]

    # Pricing
    pricing: List[PricingTier]

    # Outbound cadence
    sequence: List[OutboundSequence]

    # Competitive positioning
    competitors: Dict[str, str] = field(default_factory=dict)  # name → weakness

    # Key stats for the pitch
    stats: Dict[str, str] = field(default_factory=dict)
