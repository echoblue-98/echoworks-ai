"""
Intent Classifier - Determines if usage is defensive or offensive

This is the first safety layer that evaluates whether a user is:
- Analyzing their OWN materials (defensive, allowed)
- Attacking someone else's materials (offensive, blocked)
"""

from enum import Enum
from typing import Dict, Any
from datetime import datetime


class IntentType(Enum):
    """Classification of user intent"""
    DEFENSIVE = "defensive"  # Analyzing own work - ALLOWED
    OFFENSIVE = "offensive"  # Attacking others - BLOCKED
    UNCLEAR = "unclear"      # Needs clarification


class IntentClassification:
    """Result of intent classification"""
    
    def __init__(
        self,
        intent: IntentType,
        confidence: float,
        reasoning: str,
        flagged_terms: list[str] = None
    ):
        self.intent = intent
        self.confidence = confidence
        self.reasoning = reasoning
        self.flagged_terms = flagged_terms or []
        self.timestamp = datetime.utcnow()
    
    def is_allowed(self) -> bool:
        """Check if intent allows processing"""
        return self.intent == IntentType.DEFENSIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "flagged_terms": self.flagged_terms,
            "timestamp": self.timestamp.isoformat(),
            "allowed": self.is_allowed()
        }


class IntentClassifier:
    """
    Classifies user intent to enforce ethical boundaries.
    
    DEFENSIVE (allowed):
    - "Analyze MY legal brief"
    - "Find vulnerabilities in MY system"
    - "Challenge MY assumptions"
    
    OFFENSIVE (blocked):
    - "Attack this company's website"
    - "Find dirt on opposing counsel"
    - "Generate exploit for [unauthorized target]"
    """
    
    # Keywords indicating defensive intent
    DEFENSIVE_INDICATORS = [
        "my", "our", "my own", "our own",
        "my argument", "my case", "my system",
        "prepare me", "challenge me", "test me",
        "what am i missing", "where am i weak",
        "stress-test my", "red-team my"
    ]
    
    # Keywords indicating offensive intent
    OFFENSIVE_INDICATORS = [
        "hack", "exploit", "attack", "breach",
        "their system", "their network", "their company",
        "opposing party", "competitor's system",
        "find dirt on", "expose", "destroy",
        "generate payload", "create exploit",
        "social engineering attack on"
    ]
    
    # Context that indicates authorized defensive work
    AUTHORIZED_CONTEXT = [
        "trial preparation", "case preparation",
        "penetration test", "security audit",
        "red team exercise", "authorized assessment",
        "internal review", "pre-mortem analysis"
    ]
    
    def __init__(self):
        self.classification_history = []
    
    def classify(self, user_input: str, context: Dict[str, Any] = None) -> IntentClassification:
        """
        Classify user intent based on input and context.
        
        Args:
            user_input: The user's query or command
            context: Additional context (user_role, target_ownership, authorization, etc.)
        
        Returns:
            IntentClassification with intent type, confidence, and reasoning
        """
        user_input_lower = user_input.lower()
        context = context or {}
        
        # Check for explicit authorization markers
        if context.get("authorized_pen_test") or context.get("owns_target"):
            return self._defensive_classification(
                user_input,
                "User has explicit authorization or owns target",
                confidence=0.95
            )
        
        # Score defensive indicators
        defensive_score = sum(
            1 for indicator in self.DEFENSIVE_INDICATORS
            if indicator in user_input_lower
        )
        
        # Score offensive indicators
        offensive_score = sum(
            1 for indicator in self.OFFENSIVE_INDICATORS
            if indicator in user_input_lower
        )
        
        # Score authorized context
        authorized_score = sum(
            1 for indicator in self.AUTHORIZED_CONTEXT
            if indicator in user_input_lower
        )
        
        # Collect flagged terms
        flagged = [
            term for term in self.OFFENSIVE_INDICATORS
            if term in user_input_lower
        ]
        
        # Decision logic
        if offensive_score > 0 and defensive_score == 0 and authorized_score == 0:
            # Clear offensive intent
            return self._offensive_classification(
                user_input,
                f"Detected offensive indicators: {', '.join(flagged)}",
                confidence=0.90,
                flagged_terms=flagged
            )
        
        if defensive_score > offensive_score:
            # Likely defensive
            return self._defensive_classification(
                user_input,
                "User appears to be analyzing own materials",
                confidence=0.80 + (defensive_score * 0.05)
            )
        
        if authorized_score > 0:
            # Has authorization context
            return self._defensive_classification(
                user_input,
                "Detected authorized assessment context",
                confidence=0.85
            )
        
        # Unclear intent - need more information
        return IntentClassification(
            intent=IntentType.UNCLEAR,
            confidence=0.5,
            reasoning="Cannot determine if analysis is of own materials or unauthorized target",
            flagged_terms=flagged
        )
    
    def _defensive_classification(
        self,
        user_input: str,
        reasoning: str,
        confidence: float
    ) -> IntentClassification:
        """Create defensive classification result"""
        result = IntentClassification(
            intent=IntentType.DEFENSIVE,
            confidence=confidence,
            reasoning=reasoning
        )
        self.classification_history.append(result)
        return result
    
    def _offensive_classification(
        self,
        user_input: str,
        reasoning: str,
        confidence: float,
        flagged_terms: list[str]
    ) -> IntentClassification:
        """Create offensive classification result"""
        result = IntentClassification(
            intent=IntentType.OFFENSIVE,
            confidence=confidence,
            reasoning=reasoning,
            flagged_terms=flagged_terms
        )
        self.classification_history.append(result)
        return result
    
    def requires_clarification(self, classification: IntentClassification) -> bool:
        """Check if user input needs clarification"""
        return classification.intent == IntentType.UNCLEAR or classification.confidence < 0.7
    
    def get_clarification_prompt(self, classification: IntentClassification) -> str:
        """Generate prompt to ask user for clarification"""
        return (
            "To proceed, I need to confirm: Are you analyzing your own materials/systems, "
            "or are you requesting analysis of someone else's materials? "
            "AION OS only operates in defensive mode - analyzing YOUR work to prepare YOU for opposition."
        )
