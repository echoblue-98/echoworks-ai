"""
AION OS — Sales Engine
======================
Per-vertical go-to-market engine for EchoWorks AI.
Codifies threat patterns, buyer personas, regulatory hooks,
objection handling, and outbound sequences for each vertical.

Verticals:
  - Legal   (law firms — attorney departure theft)
  - Health  (healthcare — billing fraud, HIPAA, credential compromise)
  - Realty  (real estate — wire fraud BEC, money laundering)
"""

from aionos.sales.engine import SalesEngine
from aionos.sales.models import Vertical, BuyerPersona, ThreatScenario
from aionos.sales.prospects import Pipeline
from aionos.sales.messages import MessageGenerator

__all__ = [
    "SalesEngine", "Vertical", "BuyerPersona", "ThreatScenario",
    "Pipeline", "MessageGenerator",
]
