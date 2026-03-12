"""
AION OS - Human Capacity Gem
Custom AI configuration for advancing human potential through adversarial growth

This module embodies AION's confrontational philosophy applied to personal development:
- Challenge comfort zones
- Expose blind spots
- Accelerate growth through adversarial honesty
- Build emotional resilience through direct feedback

Security: All interactions are private and never shared with external systems.
"""

import os
import json
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class GrowthIntensity(Enum):
    """Levels of confrontational honesty"""
    GENTLE = 1          # Supportive but direct
    CHALLENGING = 2     # Push boundaries constructively  
    CONFRONTATIONAL = 3 # Unfiltered truth-telling
    ADVERSARIAL = 4     # Maximum growth through discomfort
    TRANSFORMATIONAL = 5 # Crisis-level intervention


class HumanCapacityGem:
    """
    AION's Human Capacity Gem - Adversarial AI for personal growth.
    
    Philosophy: Most AI coddles you. This one challenges you.
    
    Purpose: Accelerate human potential by exposing:
    - Self-deception patterns
    - Unexplored capabilities
    - Limiting beliefs
    - Untapped emotional intelligence
    - Strategic blind spots
    
    Privacy: All conversations stay local. Nothing sent to external APIs.
    """
    
    def __init__(self, intensity: GrowthIntensity = GrowthIntensity.CHALLENGING):
        self.intensity = intensity
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_history = []
        
    def analyze_capacity_gap(
        self,
        current_state: str,
        desired_state: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Identify the gap between where you are and where you want to be.
        Then challenge every excuse keeping you there.
        
        Args:
            current_state: Where you are now (be honest)
            desired_state: Where you want to be (be ambitious)
            context: Additional context (fears, obstacles, past failures)
            
        Returns:
            Adversarial analysis of what's actually stopping you
        """
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "intensity_level": self.intensity.value,
            "gap_analysis": self._analyze_gap(current_state, desired_state),
            "blind_spots": self._expose_blind_spots(current_state, context),
            "confrontational_questions": self._generate_hard_questions(current_state, desired_state),
            "growth_prescription": self._prescribe_growth_path(current_state, desired_state, context),
            "accountability_metrics": self._define_accountability(desired_state)
        }
        
        self.conversation_history.append({
            "type": "capacity_gap_analysis",
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis
        })
        
        return analysis
    
    def _analyze_gap(self, current: str, desired: str) -> Dict[str, Any]:
        """Quantify the gap without sugar-coating"""
        
        return {
            "current_reality_check": self._reality_check(current),
            "desired_state_feasibility": self._feasibility_check(desired),
            "gap_severity": self._calculate_gap_severity(current, desired),
            "time_cost": "Every day you stay where you are, the gap widens",
            "hidden_costs": [
                "Opportunities missed while you hesitate",
                "Compounding effect of delayed action",
                "Self-respect erosion from unfulfilled potential",
                "Regret accumulation (irreversible)"
            ]
        }
    
    def _expose_blind_spots(self, current: str, context: Optional[Dict]) -> List[str]:
        """
        Surface the things you're not seeing about yourself.
        Most people have 3-5 major blind spots blocking growth.
        """
        
        blind_spots = [
            {
                "category": "Self-Deception",
                "pattern": "You say you want change, but your actions say you want comfort",
                "evidence": "Check your calendar - where's the time for this goal?",
                "confrontation": "If it was truly a priority, you'd have started yesterday"
            },
            {
                "category": "Capability Underestimation",
                "pattern": "You're more capable than you believe",
                "evidence": "Past achievements you're discounting or attributing to luck",
                "confrontation": "What if you're playing small because it's safer, not because you're incapable?"
            },
            {
                "category": "Fear Masquerading as Logic",
                "pattern": "Your 'rational reasons' are emotional protection",
                "evidence": "Notice how your obstacles are conveniently insurmountable?",
                "confrontation": "Name the fear. Stop pretending it's logic."
            },
            {
                "category": "Delayed Ownership",
                "pattern": "You're waiting for perfect conditions that will never come",
                "evidence": "How long have you been 'preparing' vs actually doing?",
                "confrontation": "Ready is a lie you tell yourself. Start messy."
            },
            {
                "category": "Low Standards Disguised as Realism",
                "pattern": "You call it 'being realistic' but it's settling",
                "evidence": "Notice who you compare yourself to - always people below you?",
                "confrontation": "You're capable of 10x more. You just don't want to try."
            }
        ]
        
        return blind_spots
    
    def _generate_hard_questions(self, current: str, desired: str) -> List[str]:
        """
        Questions designed to make you uncomfortable.
        If you can't answer these, you're not ready to change.
        """
        
        questions = [
            "What would you do if failure had no consequences?",
            "If you died tomorrow, what would you regret not attempting?",
            "Who are you trying to impress by playing it safe?",
            "What evidence do you have that you CAN'T do this?",
            "If your child was in your position, what would you tell them?",
            "What's the worst case scenario? Can you survive it?",
            "How many years are you willing to waste before you try?",
            "What percentage of your potential are you using? Why so low?",
            "If someone offered you $1M to achieve this in 6 months, would you? Then why aren't you?",
            "What lie are you telling yourself to justify staying where you are?"
        ]
        
        return [
            {
                "question": q,
                "purpose": "Force clarity on what's actually stopping you",
                "warning": "If you deflect this question, that's your answer"
            }
            for q in questions
        ]
    
    def _prescribe_growth_path(
        self,
        current: str,
        desired: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Not advice. A prescription. Do this or stay where you are.
        """
        
        return {
            "immediate_action": {
                "what": "One uncomfortable thing you can do in the next 24 hours",
                "why": "Because thinking without action is just procrastination with better vocabulary",
                "accountability": "If you don't do this, you're not serious"
            },
            "7_day_sprint": {
                "what": "Small wins that prove you can change",
                "why": "Momentum compounds. Start small, get evidence, build belief",
                "warning": "Don't overcommit. Do less, but do it."
            },
            "30_day_transformation": {
                "what": "Visible progress that changes how you see yourself",
                "why": "This is where identity shift happens",
                "milestone": "You should be unrecognizable to yourself in 30 days"
            },
            "90_day_breakthrough": {
                "what": "Capability level that seemed impossible 90 days ago",
                "why": "This is the timeframe for real transformation",
                "success_criteria": "Others should ask 'What happened to you?'"
            },
            "non_negotiables": [
                "Show up daily (consistency > intensity)",
                "Embrace discomfort (growth lives here)",
                "Track progress (what gets measured gets improved)",
                "Get external accountability (your brain will lie to you)",
                "Fail fast (iteration speed determines transformation speed)"
            ]
        }
    
    def _define_accountability(self, desired: str) -> Dict[str, Any]:
        """
        Hard metrics. No hiding. No excuses.
        """
        
        return {
            "what_gets_measured": "What specific metrics prove you're moving forward?",
            "public_commitment": "Tell 5 people what you're doing (creates pressure)",
            "consequence_design": "What happens if you don't follow through? (Make it painful)",
            "weekly_review": "Every Sunday: Did I do what I said? No bullshit.",
            "red_flags": [
                "Making excuses instead of progress",
                "Changing the goal when it gets hard",
                "Blaming circumstances instead of improving effort",
                "Celebrating participation instead of results"
            ],
            "truth_serum": "If you're not tracking it, you don't want it badly enough"
        }
    
    def _reality_check(self, current: str) -> str:
        """Strip away the narrative, describe reality"""
        return f"Current state without the story: {current}"
    
    def _feasibility_check(self, desired: str) -> Dict[str, Any]:
        """Is this actually possible, or are you setting up failure?"""
        
        return {
            "achievability": "Probably harder than you think, but absolutely possible",
            "timeframe": "Longer than you want, shorter than you fear",
            "effort_required": "More than you've ever given anything. That's the point.",
            "likelihood_of_success": "100% if you don't quit. 0% if you do."
        }
    
    def _calculate_gap_severity(self, current: str, desired: str) -> str:
        """How far are you from where you want to be?"""
        
        severity_levels = {
            "minor": "Small adjustments. Execute.",
            "moderate": "Requires discipline. Doable.",
            "major": "Life overhaul needed. Hard but necessary.",
            "severe": "Complete identity transformation. This will hurt.",
            "extreme": "You're asking for a miracle. Good. That's worth pursuing."
        }
        
        # Default to severe - most people underestimate their gap
        return severity_levels["severe"]
    
    def emotional_intelligence_challenge(
        self,
        situation: str,
        your_response: str,
        intensity: GrowthIntensity = None
    ) -> Dict[str, Any]:
        """
        Analyze emotional patterns that are holding you back.
        
        This isn't therapy. This is pattern recognition.
        """
        
        intensity = intensity or self.intensity
        
        return {
            "your_pattern": self._identify_emotional_pattern(situation, your_response),
            "what_you_missed": self._identify_blind_spots_in_response(situation, your_response),
            "growth_edge": self._find_emotional_growth_edge(situation, your_response),
            "alternative_response": self._generate_higher_eq_response(situation, intensity),
            "practice_exercises": self._prescribe_eq_exercises(situation)
        }
    
    def _identify_emotional_pattern(self, situation: str, response: str) -> Dict[str, Any]:
        """What emotional pattern are you stuck in?"""
        
        common_patterns = [
            {
                "pattern": "Defensive Reactivity",
                "signal": "Feeling attacked when receiving feedback",
                "cost": "Can't learn, can't grow, stay stuck",
                "upgrade": "Curiosity replaces defensiveness"
            },
            {
                "pattern": "People-Pleasing",
                "signal": "Prioritizing others' comfort over truth",
                "cost": "Lose respect (others' and your own)",
                "upgrade": "Honest and kind can coexist"
            },
            {
                "pattern": "Emotional Avoidance",
                "signal": "Changing topics when uncomfortable",
                "cost": "Never process emotions, just accumulate them",
                "upgrade": "Lean into discomfort, process in real-time"
            },
            {
                "pattern": "Validation Seeking",
                "signal": "Need external approval for decisions",
                "cost": "Can't trust yourself, outsource your power",
                "upgrade": "Internal validation > external validation"
            },
            {
                "pattern": "Anger as Shield",
                "signal": "Using anger to avoid vulnerability",
                "cost": "Push people away, never get connection",
                "upgrade": "Name the hurt underneath the anger"
            }
        ]
        
        return {
            "likely_pattern": common_patterns[0],  # Default to defensive reactivity
            "why_this_matters": "This pattern is a growth ceiling",
            "confrontation": "You've been doing this for years. Ready to change?"
        }
    
    def _identify_blind_spots_in_response(self, situation: str, response: str) -> List[str]:
        """What did you miss in your response?"""
        
        return [
            "You made it about you when it wasn't",
            "You deflected instead of taking ownership",
            "You used logic to avoid feeling",
            "You minimized the other person's experience",
            "You chose comfort over truth"
        ]
    
    def _find_emotional_growth_edge(self, situation: str, response: str) -> str:
        """Where's your next level of emotional maturity?"""
        
        return (
            "Your growth edge is staying present with discomfort. "
            "You default to escape (logic, deflection, anger). "
            "High EQ means: Feel it. Process it. Respond consciously. "
            "Not: React immediately to make the discomfort stop."
        )
    
    def _generate_higher_eq_response(self, situation: str, intensity: GrowthIntensity) -> str:
        """What would a more emotionally intelligent version of you say?"""
        
        return (
            "I notice I'm feeling defensive. Let me pause. "
            "What's actually being said here? "
            "Can I hear this without making it mean something about me? "
            "What's the truth in this feedback?"
        )
    
    def _prescribe_eq_exercises(self, situation: str) -> List[Dict[str, str]]:
        """Daily practices to build emotional capacity"""
        
        return [
            {
                "exercise": "Name Your Emotions Daily",
                "practice": "3x per day, stop and identify exactly what you're feeling",
                "why": "Can't regulate what you can't name"
            },
            {
                "exercise": "Pause Before Reacting",
                "practice": "5-second pause before responding to anything emotional",
                "why": "Space between stimulus and response = emotional intelligence"
            },
            {
                "exercise": "Ask 'What Am I Avoiding?'",
                "practice": "When you feel strong emotion, ask what you're protecting",
                "why": "Emotions are messengers. Stop shooting the messenger."
            },
            {
                "exercise": "Process Before Communicating",
                "practice": "Feel it fully before speaking. Don't vomit emotions on others.",
                "why": "Maturity is feeling intensely and responding calmly"
            },
            {
                "exercise": "Seek Discomfort",
                "practice": "One uncomfortable conversation per week",
                "why": "Comfort zone expands through use, not theory"
            }
        ]
    
    def confrontational_feedback(
        self,
        your_belief: str,
        evidence_for: List[str],
        evidence_against: List[str]
    ) -> Dict[str, Any]:
        """
        Challenge your beliefs adversarially.
        Most beliefs are inherited, not examined.
        """
        
        return {
            "belief_audit": self._audit_belief(your_belief, evidence_for, evidence_against),
            "who_benefits": self._ask_cui_bono(your_belief),
            "cost_of_belief": self._calculate_belief_cost(your_belief),
            "alternative_beliefs": self._generate_alternatives(your_belief),
            "experiment": self._design_belief_experiment(your_belief)
        }
    
    def _audit_belief(
        self,
        belief: str,
        evidence_for: List[str],
        evidence_against: List[str]
    ) -> Dict[str, Any]:
        """Is this belief serving you or sabotaging you?"""
        
        return {
            "belief": belief,
            "strength": "How tightly are you holding this?",
            "origin": "Where did this belief come from? (Probably not from you)",
            "examination": "Have you ever questioned this, or just accepted it?",
            "verdict": "Beliefs should serve you. Does this one?"
        }
    
    def _ask_cui_bono(self, belief: str) -> str:
        """Who benefits from you believing this?"""
        
        return (
            "Cui bono? (Who benefits?) "
            "If you believe you're not capable - who wins? "
            "If you believe you need permission - who has power? "
            "If you believe you're too late - who avoids competition? "
            "Your limiting beliefs serve someone. Usually not you."
        )
    
    def _calculate_belief_cost(self, belief: str) -> Dict[str, Any]:
        """What is this belief costing you?"""
        
        return {
            "opportunity_cost": "What could you do if you didn't believe this?",
            "time_cost": "How many years have you believed this?",
            "identity_cost": "How does this belief shape who you're becoming?",
            "relationship_cost": "How does this belief affect your connections?",
            "financial_cost": "What money have you not made because of this belief?",
            "total_cost": "This belief is expensive. Can you afford to keep it?"
        }
    
    def _generate_alternatives(self, belief: str) -> List[str]:
        """What if the opposite were true?"""
        
        return [
            "What if you're more capable than you think?",
            "What if the timing is perfect?",
            "What if failure is just feedback?",
            "What if you don't need permission?",
            "What if others' opinions don't matter?",
            "What if your past doesn't determine your future?",
            "What if you're playing a game you can actually win?"
        ]
    
    def _design_belief_experiment(self, belief: str) -> Dict[str, str]:
        """Test the belief. Get data. Update accordingly."""
        
        return {
            "hypothesis": "What if this belief is wrong?",
            "experiment": "Act as if the opposite is true for 7 days",
            "data_collection": "Track what happens when you don't believe this",
            "analysis": "Was the belief protecting you or limiting you?",
            "update": "Keep the belief or replace it based on evidence"
        }
    
    def generate_session_report(self) -> Dict[str, Any]:
        """
        Summary of confrontations, insights, and next actions.
        """
        
        return {
            "session_id": self.session_id,
            "intensity_level": self.intensity.name,
            "interactions": len(self.conversation_history),
            "key_confrontations": self._extract_key_confrontations(),
            "growth_edges_identified": self._summarize_growth_edges(),
            "immediate_actions": self._compile_action_items(),
            "accountability_tracker": self._generate_accountability_dashboard(),
            "next_session_focus": self._recommend_next_focus()
        }
    
    def _extract_key_confrontations(self) -> List[str]:
        """The hard truths surfaced this session"""
        return ["List of confrontations that challenged comfort zones"]
    
    def _summarize_growth_edges(self) -> List[str]:
        """Where growth opportunity is highest"""
        return ["Identified areas for immediate expansion"]
    
    def _compile_action_items(self) -> List[Dict[str, str]]:
        """Do these or nothing changes"""
        return [
            {"action": "First uncomfortable thing", "deadline": "24 hours", "accountability": "Public commitment required"}
        ]
    
    def _generate_accountability_dashboard(self) -> Dict[str, Any]:
        """Track progress or track excuses"""
        return {
            "metrics": "What you said you'd measure",
            "status": "Green/Yellow/Red based on actions vs words",
            "next_review": "Weekly check-in scheduled"
        }
    
    def _recommend_next_focus(self) -> str:
        """Where to direct energy next"""
        return "Recommendation for next session based on progress"


def create_capacity_session(intensity: str = "challenging") -> HumanCapacityGem:
    """
    Create a new Human Capacity session.
    
    Intensity levels:
    - gentle: Supportive but direct
    - challenging: Push boundaries (recommended)
    - confrontational: Unfiltered truth
    - adversarial: Maximum growth through discomfort
    - transformational: Crisis-level intervention
    """
    
    intensity_map = {
        "gentle": GrowthIntensity.GENTLE,
        "challenging": GrowthIntensity.CHALLENGING,
        "confrontational": GrowthIntensity.CONFRONTATIONAL,
        "adversarial": GrowthIntensity.ADVERSARIAL,
        "transformational": GrowthIntensity.TRANSFORMATIONAL
    }
    
    return HumanCapacityGem(intensity=intensity_map.get(intensity.lower(), GrowthIntensity.CHALLENGING))
