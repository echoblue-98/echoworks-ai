"""
Sales Engine — Core Router
============================
Central hub that loads all vertical configs and provides:
  - Vertical lookup by ID
  - Prospect qualification (which vertical fits)
  - Objection lookup by keyword
  - Outbound sequence generation
  - Competitive battle card retrieval
  - Deal stage tracking helpers
"""

from __future__ import annotations

from typing import Dict, List, Optional

from aionos.sales.models import (
    BuyerPersona, DealStage, Objection, OutboundSequence,
    Vertical, VerticalID,
)
from aionos.sales.verticals.legal import LEGAL_VERTICAL
from aionos.sales.verticals.healthcare import HEALTHCARE_VERTICAL
from aionos.sales.verticals.realestate import REALESTATE_VERTICAL


class SalesEngine:
    """
    Per-vertical sales engine for EchoWorks AI.

    Usage:
        engine = SalesEngine()
        v = engine.get_vertical("legal")
        personas = engine.get_personas("legal", role="decision_maker")
        objection = engine.find_objection("legal", "already have DLP")
        sequence = engine.get_sequence("legal")
        card = engine.battle_card("legal", "Relativity Trace")
    """

    def __init__(self) -> None:
        self._verticals: Dict[VerticalID, Vertical] = {
            VerticalID.LEGAL: LEGAL_VERTICAL,
            VerticalID.HEALTHCARE: HEALTHCARE_VERTICAL,
            VerticalID.REALESTATE: REALESTATE_VERTICAL,
        }

    # ── Vertical access ───────────────────────────────────────────

    @property
    def vertical_ids(self) -> List[str]:
        """All available vertical IDs."""
        return [v.value for v in self._verticals]

    def get_vertical(self, vertical_id: str) -> Vertical:
        """Get full vertical config by ID."""
        vid = VerticalID(vertical_id)
        return self._verticals[vid]

    def list_verticals(self) -> List[Dict[str, str]]:
        """Summary of all verticals."""
        return [
            {
                "id": v.id.value,
                "name": v.display_name,
                "tagline": v.tagline,
                "scenarios": len(v.threat_scenarios),
                "personas": len(v.buyer_personas),
            }
            for v in self._verticals.values()
        ]

    # ── Persona lookup ────────────────────────────────────────────

    def get_personas(
        self, vertical_id: str, role: Optional[str] = None
    ) -> List[BuyerPersona]:
        """Get buyer personas, optionally filtered by role."""
        v = self.get_vertical(vertical_id)
        if role is None:
            return v.buyer_personas
        return [p for p in v.buyer_personas if p.role.value == role]

    def get_decision_maker(self, vertical_id: str) -> Optional[BuyerPersona]:
        """Get the primary decision maker persona."""
        makers = self.get_personas(vertical_id, role="decision_maker")
        return makers[0] if makers else None

    # ── Objection handling ────────────────────────────────────────

    def find_objection(self, vertical_id: str, keyword: str) -> Optional[Objection]:
        """Find best matching objection by keyword search."""
        v = self.get_vertical(vertical_id)
        keyword_lower = keyword.lower()
        for obj in v.objections:
            if keyword_lower in obj.objection.lower():
                return obj
        # fuzzy: check response text too
        for obj in v.objections:
            if keyword_lower in obj.response.lower():
                return obj
        return None

    def all_objections(self, vertical_id: str) -> List[Objection]:
        """Get all objections for a vertical."""
        return self.get_vertical(vertical_id).objections

    # ── Outbound sequences ────────────────────────────────────────

    def get_sequence(self, vertical_id: str) -> List[OutboundSequence]:
        """Get the full outbound cadence for a vertical."""
        return self.get_vertical(vertical_id).sequence

    def get_next_action(
        self, vertical_id: str, current_day: int
    ) -> Optional[OutboundSequence]:
        """Get the next action in the sequence after current_day."""
        seq = self.get_sequence(vertical_id)
        upcoming = [s for s in seq if s.day > current_day]
        return upcoming[0] if upcoming else None

    # ── Competitive battle cards ──────────────────────────────────

    def battle_card(self, vertical_id: str, competitor: str) -> Optional[str]:
        """Get competitive weakness for a specific competitor."""
        v = self.get_vertical(vertical_id)
        for name, weakness in v.competitors.items():
            if competitor.lower() in name.lower():
                return f"**{name}**: {weakness}"
        return None

    def all_competitors(self, vertical_id: str) -> Dict[str, str]:
        """Get full competitive landscape for a vertical."""
        return self.get_vertical(vertical_id).competitors

    # ── Regulatory hooks ──────────────────────────────────────────

    def get_regulatory_hooks(self, vertical_id: str) -> List[Dict[str, str]]:
        """Get all regulatory pressure points for a vertical."""
        v = self.get_vertical(vertical_id)
        return [
            {
                "regulation": h.name,
                "citation": h.citation,
                "penalty": h.penalty_range,
                "why_it_matters": h.relevance,
            }
            for h in v.regulatory_hooks
        ]

    # ── Pricing ───────────────────────────────────────────────────

    def get_pricing(self, vertical_id: str) -> List[Dict[str, object]]:
        """Get pricing tiers for a vertical."""
        v = self.get_vertical(vertical_id)
        return [
            {
                "tier": t.tier_name,
                "monthly": t.monthly,
                "annual": t.monthly * 12,
                "includes": t.includes,
            }
            for t in v.pricing
        ]

    def get_baseline_price(self, vertical_id: str) -> int:
        """Get the entry-level monthly price for a vertical."""
        v = self.get_vertical(vertical_id)
        return v.pricing[0].monthly if v.pricing else 0

    # ── Prospect qualification ────────────────────────────────────

    def qualify_prospect(self, industry_keywords: List[str]) -> List[str]:
        """
        Given keywords from a prospect's LinkedIn/website,
        return matching vertical IDs ranked by relevance.
        """
        scores: Dict[str, int] = {}

        keyword_map = {
            VerticalID.LEGAL: [
                "law firm", "attorney", "legal", "litigation",
                "partner", "associate", "imanage", "netdocuments",
                "amlaw", "counsel", "barrister",
            ],
            VerticalID.HEALTHCARE: [
                "hospital", "healthcare", "clinic", "medical",
                "physician", "hipaa", "ehr", "emr", "epic",
                "cerner", "nursing", "compliance officer",
                "health system", "urgent care",
            ],
            VerticalID.REALESTATE: [
                "real estate", "title company", "escrow",
                "brokerage", "closing", "settlement",
                "wire", "mortgage", "realty", "fincen",
            ],
        }

        prospect_text = " ".join(k.lower() for k in industry_keywords)

        for vid, keywords in keyword_map.items():
            score = sum(1 for kw in keywords if kw in prospect_text)
            if score > 0:
                scores[vid.value] = score

        return sorted(scores, key=scores.get, reverse=True)

    # ── Stats / pitch data ────────────────────────────────────────

    def get_stats(self, vertical_id: str) -> Dict[str, str]:
        """Get key statistics for the pitch."""
        return self.get_vertical(vertical_id).stats

    # ── Threat scenarios ──────────────────────────────────────────

    def get_scenarios(self, vertical_id: str) -> List[Dict[str, object]]:
        """Get threat scenarios for a vertical."""
        v = self.get_vertical(vertical_id)
        return [
            {
                "name": s.name,
                "description": s.description,
                "event_chain": s.event_chain,
                "detection_speed": s.detection_speed,
                "financial_impact": s.financial_impact,
                "pure_pattern": s.pattern_engine_bypass,
            }
            for s in v.threat_scenarios
        ]

    # ── Summary ───────────────────────────────────────────────────

    def pitch_summary(self, vertical_id: str) -> str:
        """Generate a concise pitch summary for a vertical."""
        v = self.get_vertical(vertical_id)
        dm = self.get_decision_maker(vertical_id)
        scenarios = ", ".join(s.name for s in v.threat_scenarios)
        regs = ", ".join(h.name for h in v.regulatory_hooks)
        price = v.pricing[0].monthly if v.pricing else "TBD"

        lines = [
            f"=== {v.display_name} — {v.tagline} ===",
            f"",
            f"THREATS DETECTED: {scenarios}",
            f"REGULATORY PRESSURE: {regs}",
            f"TARGET BUYER: {dm.title if dm else 'TBD'}",
            f"ENTRY PRICE: ${price:,}/mo",
            f"DETECTION SPEED: {v.threat_scenarios[0].detection_speed}",
            f"",
            f"COMPETITORS WE BEAT:",
        ]
        for comp, weakness in v.competitors.items():
            lines.append(f"  • {comp}: {weakness}")

        return "\n".join(lines)
