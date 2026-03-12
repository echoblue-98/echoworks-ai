"""Domain-specific adversarial modules."""

from .legal_analyzer import LegalAnalyzer
from .security_redteam import SecurityRedTeam
from .quantum_adversarial import QuantumAdversarialEngine
from .attorney_departure import AttorneyDepartureAnalyzer

__all__ = [
    "LegalAnalyzer",
    "SecurityRedTeam",
    "QuantumAdversarialEngine",
    "AttorneyDepartureAnalyzer"
]
