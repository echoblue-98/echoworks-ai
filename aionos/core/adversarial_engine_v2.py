"""
Adversarial Engine - Real Claude API Integration

Core multi-agent attack system powered by Claude API.
Tracks usage for pilot phase (50-100 use cases).
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .severity_triage import Vulnerability, Severity, SeverityTriage
from .intent_classifier import IntentClassifier, IntentType
from .usage_tracker import UsageTracker, BudgetExceededError

# Load environment variables
load_dotenv()


class AgentPerspective(Enum):
    """Different adversarial perspectives"""
    LEGAL_OPPONENT = "legal_opponent"
    SECURITY_ATTACKER = "security_attacker"
    BUSINESS_COMPETITOR = "business_competitor"
    TECHNICAL_FAILURE = "technical_failure"
    ETHICAL_CRITIC = "ethical_critic"


class IntensityLevel(Enum):
    """Adversarial intensity levels"""
    LEVEL_1_GENTLE = 1
    LEVEL_2_ACTIVE = 2
    LEVEL_3_HOSTILE = 3
    LEVEL_4_REDTEAM = 4
    LEVEL_5_MAXIMUM = 5


class AdversarialAgent:
    """Single adversarial agent"""
    
    def __init__(self, name: str, perspective: AgentPerspective):
        self.name = name
        self.perspective = perspective


class AdversarialEngine:
    """
    Core adversarial intelligence engine.
    
    Powers AION OS with real Claude API calls + usage tracking.
    """
    
    def __init__(self, intensity: IntensityLevel = IntensityLevel.LEVEL_3_HOSTILE):
        self.intensity = intensity
        self.agents: List[AdversarialAgent] = []
        self.intent_classifier = IntentClassifier()
        self.severity_triage = SeverityTriage()
        
        # Claude API setup
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.use_real_api = (
            api_key is not None 
            and api_key != "your_anthropic_key_here" 
            and ANTHROPIC_AVAILABLE
        )
        
        if self.use_real_api:
            self.client = Anthropic(api_key=api_key)
            self.model = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")
            self.usage_tracker = UsageTracker()
            print(f"✓ Claude API connected (Model: {self.model})")
        else:
            self.client = None
            self.usage_tracker = None
            if not ANTHROPIC_AVAILABLE:
                print("⚠ Anthropic package not installed. Install with: pip install anthropic>=0.39.0")
            else:
                print("⚠ Claude API not configured - using mock responses")
                print("  Set ANTHROPIC_API_KEY in .env to use real API")
        
        self._register_default_agents()
    
    def _register_default_agents(self):
        """Register default adversarial agents"""
        self.register_agent("Legal Opponent", AgentPerspective.LEGAL_OPPONENT)
        self.register_agent("Security Attacker", AgentPerspective.SECURITY_ATTACKER)
        self.register_agent("Business Competitor", AgentPerspective.BUSINESS_COMPETITOR)
        self.register_agent("Technical Auditor", AgentPerspective.TECHNICAL_FAILURE)
        self.register_agent("Ethics Critic", AgentPerspective.ETHICAL_CRITIC)
    
    def register_agent(self, name: str, perspective: AgentPerspective):
        """Register a new adversarial agent"""
        agent = AdversarialAgent(name, perspective)
        self.agents.append(agent)
    
    def analyze(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_case_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Run adversarial analysis with all agents.
        
        Args:
            query: What to analyze
            context: Additional context
            use_case_type: Type for usage tracking (legal, security, attorney_departure, etc.)
        """
        
        # Intent classification
        intent_result = self.intent_classifier.classify(query)
        if intent_result.intent == IntentType.OFFENSIVE:
            return {
                "error": "Offensive intent detected",
                "intent_classification": intent_result.__dict__,
                "message": "AION OS operates in defensive mode only."
            }
        
        # Run multi-agent analysis
        results = []
        agents_used = []
        
        if context:
            use_case_type = context.get("use_case_type", use_case_type)
        
        for agent in self.agents:
            try:
                agent_result = self._run_agent_analysis(agent, query, context, use_case_type)
                results.append(agent_result)
                agents_used.append(agent.name)
            except BudgetExceededError as e:
                return {
                    "error": "API budget exceeded",
                    "message": str(e),
                    "results_partial": results,
                    "agents_completed": agents_used
                }
            except Exception as e:
                print(f"Warning: Agent {agent.name} failed: {str(e)}")
                continue
        
        return {
            "intent_classification": intent_result.__dict__,
            "agents_used": agents_used,
            "results": results,
            "intensity": self.intensity.value,
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_agent_analysis(
        self,
        agent: AdversarialAgent,
        query: str,
        context: Optional[Dict],
        use_case_type: str
    ) -> Dict[str, Any]:
        """Run analysis from single agent perspective"""
        
        # Build prompts
        system_prompt = self._build_agent_system_prompt(agent)
        user_prompt = self._build_user_prompt(agent, query, context)
        
        # Call Claude API (or mock)
        response = self._call_claude(user_prompt, system_prompt, use_case_type)
        
        return {
            "agent": agent.name,
            "perspective": agent.perspective.value,
            "findings": response,
            "severity": self._extract_severity(response)
        }
    
    def _call_claude(self, prompt: str, system_prompt: str, use_case_type: str) -> str:
        """Call Claude API with usage tracking"""
        
        if not self.use_real_api:
            return self._generate_mock_response(prompt)
        
        # Check budget
        if self.usage_tracker.is_budget_exceeded():
            raise BudgetExceededError(
                f"API budget limit reached: ${self.usage_tracker.get_total_cost():.2f} / "
                f"${self.usage_tracker.budget_limit:.2f}"
            )
        
        try:
            # Make API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track usage
            self.usage_tracker.log_usage(
                use_case_id=str(uuid.uuid4()),
                use_case_type=use_case_type,
                tokens_input=response.usage.input_tokens,
                tokens_output=response.usage.output_tokens,
                model=self.model
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"API Error: {str(e)}")
            raise
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate mock response when no API available"""
        return (
            "[MOCK RESPONSE - No API key configured]\n\n"
            "This is a simulated adversarial analysis. "
            "To use real Claude API:\n\n"
            "1. Get API key from https://console.anthropic.com/\n"
            "2. Add to .env: ANTHROPIC_API_KEY=your-key-here\n"
            "3. Install: pip install anthropic>=0.39.0\n\n"
            "The real system would provide harsh but constructive "
            "adversarial feedback identifying specific vulnerabilities."
        )
    
    def _build_agent_system_prompt(self, agent: AdversarialAgent) -> str:
        """Build system prompt based on agent perspective"""
        
        base = (
            "You are part of AION OS, an adversarial intelligence system. "
            "Your role is to challenge assumptions, find vulnerabilities, and provide harsh but constructive feedback. "
            f"Intensity level: {self.intensity.value} (1=gentle, 5=maximum).\n\n"
        )
        
        perspective_prompts = {
            AgentPerspective.LEGAL_OPPONENT: (
                "You are opposing counsel. Find every weakness in the legal argument, "
                "identify factual inconsistencies, spot procedural errors, and anticipate counterarguments. "
                "Be ruthless but professional. Focus on what will actually fail in court."
            ),
            AgentPerspective.SECURITY_ATTACKER: (
                "You are a sophisticated attacker. Find vulnerabilities, identify entry points, "
                "map attack chains, and exploit weaknesses. Assume breach mentality. "
                "Focus on what would actually work in a real attack."
            ),
            AgentPerspective.BUSINESS_COMPETITOR: (
                "You are a ruthless competitor. Find strategic weaknesses, identify market vulnerabilities, "
                "spot execution risks, and exploit business gaps. "
                "Focus on what would actually threaten this business."
            ),
            AgentPerspective.TECHNICAL_FAILURE: (
                "You are a technical auditor. Find edge cases, identify scalability issues, "
                "spot technical debt, and predict system failures. "
                "Focus on what would actually break in production."
            ),
            AgentPerspective.ETHICAL_CRITIC: (
                "You are an ethics reviewer. Find ethical issues, identify potential harms, "
                "spot conflicts of interest, and raise moral concerns. "
                "Focus on what would actually cause ethical problems."
            ),
        }
        
        return base + perspective_prompts.get(
            agent.perspective,
            "Analyze from an adversarial perspective."
        )
    
    def _build_user_prompt(self, agent: AdversarialAgent, query: str, context: Optional[Dict]) -> str:
        """Build user prompt with query and context"""
        
        prompt = f"Analyze the following from your adversarial perspective:\n\n{query}\n\n"
        
        if context:
            prompt += "Context:\n"
            for key, value in context.items():
                if key not in ["use_case_type"]:  # Skip metadata
                    prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        prompt += (
            "Provide a harsh but constructive adversarial analysis. "
            "Identify specific vulnerabilities, explain exploitation scenarios, "
            "and suggest remediation steps. Be direct and actionable."
        )
        
        return prompt
    
    def _extract_severity(self, response: str) -> str:
        """Extract severity from response"""
        response_lower = response.lower()
        if any(word in response_lower for word in ["critical", "severe", "dangerous", "catastrophic"]):
            return "high"
        elif any(word in response_lower for word in ["moderate", "medium", "concerning"]):
            return "medium"
        else:
            return "low"
    
    def set_intensity(self, level: IntensityLevel):
        """Change adversarial intensity"""
        self.intensity = level
