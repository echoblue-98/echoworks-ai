"""
AION OS - Adversarial Intelligence Operating System

The AI that challenges instead of validates.
The AI that prepares you for opposition.
"""

__version__ = "0.1.0"
__author__ = "AION OS Team"

from .core.adversarial_engine import AdversarialEngine
from .core.intent_classifier import IntentClassifier
from .core.severity_triage import SeverityTriage
from .improvement import ImprovementEngine

__all__ = [
    "AdversarialEngine",
    "IntentClassifier", 
    "SeverityTriage",
    "ImprovementEngine",
]
