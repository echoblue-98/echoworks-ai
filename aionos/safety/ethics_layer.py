"""
Ethics Layer - Enforces ethical boundaries for adversarial intelligence

Ensures AION OS is used for defensive purposes only and maintains
ethical standards while being adversarial.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class EthicalViolationType(Enum):
    """Types of ethical violations"""
    UNAUTHORIZED_TARGET = "unauthorized_target"
    MALICIOUS_INTENT = "malicious_intent"
    PRIVACY_VIOLATION = "privacy_violation"
    HARMFUL_OUTPUT = "harmful_output"
    EXPLOIT_GENERATION = "exploit_generation"


class EthicalBoundary:
    """Defines an ethical boundary that must not be crossed"""
    
    def __init__(
        self,
        name: str,
        description: str,
        violation_type: EthicalViolationType,
        check_function: callable
    ):
        self.name = name
        self.description = description
        self.violation_type = violation_type
        self.check_function = check_function
    
    def check(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Check if query violates this boundary.
        
        Returns:
            None if no violation, violation message if violated
        """
        return self.check_function(query, context)


class EthicsLayer:
    """
    Enforces ethical boundaries for AION OS.
    
    While AION OS is adversarial, it operates within ethical bounds:
    - Only analyzes materials user owns or is authorized to analyze
    - Won't generate weaponized exploits for unauthorized use
    - Won't assist in harassment, doxxing, or personal attacks
    - Won't fabricate evidence or encourage illegal activity
    """
    
    def __init__(self):
        self.boundaries: list[EthicalBoundary] = []
        self.violation_history = []
        self._register_default_boundaries()
    
    def _register_default_boundaries(self):
        """Register default ethical boundaries"""
        
        # Boundary 1: No unauthorized target analysis
        self.add_boundary(EthicalBoundary(
            name="Authorized Target Only",
            description="User must own or have authorization to analyze the target",
            violation_type=EthicalViolationType.UNAUTHORIZED_TARGET,
            check_function=self._check_authorized_target
        ))
        
        # Boundary 2: No weaponized exploit generation
        self.add_boundary(EthicalBoundary(
            name="No Weaponized Exploits",
            description="Won't generate ready-to-use exploits for unauthorized systems",
            violation_type=EthicalViolationType.EXPLOIT_GENERATION,
            check_function=self._check_exploit_generation
        ))
        
        # Boundary 3: No personal attack assistance
        self.add_boundary(EthicalBoundary(
            name="No Personal Attacks",
            description="Won't assist in harassment, doxxing, or personal attacks",
            violation_type=EthicalViolationType.MALICIOUS_INTENT,
            check_function=self._check_personal_attack
        ))
        
        # Boundary 4: No evidence fabrication
        self.add_boundary(EthicalBoundary(
            name="No Fabrication",
            description="Won't fabricate evidence, documents, or false information",
            violation_type=EthicalViolationType.HARMFUL_OUTPUT,
            check_function=self._check_fabrication
        ))
    
    def add_boundary(self, boundary: EthicalBoundary):
        """Add a new ethical boundary"""
        self.boundaries.append(boundary)
    
    def check_query(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Check if query violates any ethical boundaries.
        
        Args:
            query: User query to check
            context: Additional context
        
        Returns:
            Dict with 'allowed' (bool) and optional 'violation' info
        """
        context = context or {}
        
        for boundary in self.boundaries:
            violation_msg = boundary.check(query, context)
            
            if violation_msg:
                # Log violation
                violation = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "boundary_name": boundary.name,
                    "violation_type": boundary.violation_type.value,
                    "message": violation_msg,
                    "query": query[:200],  # First 200 chars for privacy
                    "context": context
                }
                self.violation_history.append(violation)
                
                return {
                    "allowed": False,
                    "violation": violation,
                    "message": f"Ethical boundary violated: {boundary.name}. {violation_msg}"
                }
        
        # No violations
        return {
            "allowed": True,
            "message": "Query within ethical boundaries"
        }
    
    def _check_authorized_target(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """Check if user has authorization for target"""
        query_lower = query.lower()
        
        # If context explicitly states ownership/authorization, allow
        if context.get("owns_target") or context.get("authorized_pen_test"):
            return None
        
        # Check for unauthorized target indicators
        unauthorized_indicators = [
            "hack their", "attack their", "exploit their",
            "break into", "penetrate their", "compromise their",
            "steal from", "access without permission"
        ]
        
        for indicator in unauthorized_indicators:
            if indicator in query_lower:
                return (
                    f"Query appears to target unauthorized systems. "
                    f"AION OS only analyzes YOUR materials with YOUR authorization."
                )
        
        return None
    
    def _check_exploit_generation(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """Check if query requests weaponized exploit generation"""
        query_lower = query.lower()
        
        exploit_patterns = [
            "generate exploit code",
            "create payload for",
            "write malware",
            "build ransomware",
            "create botnet"
        ]
        
        for pattern in exploit_patterns:
            if pattern in query_lower:
                # Allow if it's for authorized pen testing with explicit context
                if context.get("authorized_pen_test") and context.get("internal_use_only"):
                    return None
                
                return (
                    f"Won't generate weaponized exploits. AION OS finds vulnerabilities "
                    f"and suggests fixes, but doesn't create attack tools."
                )
        
        return None
    
    def _check_personal_attack(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """Check for personal attack requests"""
        query_lower = query.lower()
        
        personal_attack_indicators = [
            "find dirt on",
            "dig up information on",
            "expose person",
            "ruin reputation",
            "embarrass",
            "harass",
            "doxx"
        ]
        
        for indicator in personal_attack_indicators:
            if indicator in query_lower:
                return (
                    f"Won't assist with personal attacks or harassment. "
                    f"AION OS analyzes professional work, not people."
                )
        
        return None
    
    def _check_fabrication(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """Check for evidence fabrication requests"""
        query_lower = query.lower()
        
        fabrication_indicators = [
            "make up evidence",
            "fabricate document",
            "create false",
            "forge",
            "fake document"
        ]
        
        for indicator in fabrication_indicators:
            if indicator in query_lower:
                return (
                    f"Won't fabricate evidence or documents. "
                    f"AION OS analyzes real materials only."
                )
        
        return None
    
    def get_violation_stats(self) -> Dict[str, Any]:
        """Get statistics on ethical violations"""
        if not self.violation_history:
            return {
                "total_violations": 0,
                "by_type": {}
            }
        
        by_type = {}
        for violation in self.violation_history:
            v_type = violation["violation_type"]
            by_type[v_type] = by_type.get(v_type, 0) + 1
        
        return {
            "total_violations": len(self.violation_history),
            "by_type": by_type,
            "most_recent": self.violation_history[-1] if self.violation_history else None
        }


class UserLevelCalibration:
    """
    Calibrates adversarial intensity based on user maturity/experience.
    
    Prevents overwhelming novice users while giving experts full power.
    """
    
    def __init__(self):
        self.user_profiles = {}
    
    def get_user_level(self, user_id: str) -> int:
        """
        Get user's current adversarial readiness level (1-5).
        
        Returns:
            1: Novice - gentle feedback
            2: Intermediate - direct challenges
            3: Advanced - hostile analysis
            4: Expert - red team mode
            5: Master - maximum adversarial
        """
        profile = self.user_profiles.get(user_id)
        if not profile:
            return 1  # Default to novice
        
        return profile.get("level", 1)
    
    def initialize_user(self, user_id: str, starting_level: int = 1):
        """Initialize a new user profile"""
        self.user_profiles[user_id] = {
            "level": starting_level,
            "analyses_completed": 0,
            "challenges_accepted": 0,
            "feedback_positive": 0,
            "joined_at": datetime.utcnow()
        }
    
    def promote_user(self, user_id: str, reason: str = ""):
        """Promote user to next level"""
        if user_id not in self.user_profiles:
            self.initialize_user(user_id)
        
        profile = self.user_profiles[user_id]
        current_level = profile["level"]
        
        if current_level < 5:
            profile["level"] = current_level + 1
            profile["last_promotion"] = datetime.utcnow()
            profile["promotion_reason"] = reason
    
    def record_analysis(self, user_id: str, feedback_positive: bool = True):
        """Record completed analysis and feedback"""
        if user_id not in self.user_profiles:
            self.initialize_user(user_id)
        
        profile = self.user_profiles[user_id]
        profile["analyses_completed"] += 1
        
        if feedback_positive:
            profile["feedback_positive"] += 1
        
        # Auto-promote based on experience
        analyses = profile["analyses_completed"]
        level = profile["level"]
        
        # Promote every 10 analyses if feedback is positive
        if analyses >= (level * 10) and profile["feedback_positive"] >= (analyses * 0.7):
            self.promote_user(user_id, "Auto-promoted based on experience")
    
    def get_onboarding_message(self, level: int) -> str:
        """Get appropriate onboarding message for user level"""
        messages = {
            1: (
                "Welcome to AION OS. I'll gently point out issues in your work "
                "and help you strengthen your position. Ready to begin?"
            ),
            2: (
                "You're now at intermediate level. I'll actively challenge your "
                "assumptions and find contradictions. This will be more direct."
            ),
            3: (
                "Advanced level unlocked. I'll operate in hostile analysis mode, "
                "simulating real opposition. Expect ruthless feedback."
            ),
            4: (
                "Expert level. Red team mode activated. I'll actively try to "
                "break your arguments and find every vulnerability."
            ),
            5: (
                "Master level. Maximum adversarial mode. I'll find attack vectors "
                "you haven't even considered. No mercy."
            )
        }
        return messages.get(level, messages[1])
