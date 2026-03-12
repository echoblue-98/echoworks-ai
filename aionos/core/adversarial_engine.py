"""
Adversarial Engine - Real Claude API Integration

Core multi-agent attack system powered by Claude API.
Tracks usage for pilot phase (50-100 use cases).

PERFORMANCE: Anthropic SDK is lazy-loaded to avoid 1.4s import penalty.
"""

import os
import uuid
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime

# Lazy imports for performance - these are loaded on first use, not at module load
_anthropic_client = None
_dotenv_loaded = False

def _get_anthropic():
    """Lazy load Anthropic SDK only when needed (saves 1.4s on import)"""
    global _anthropic_client
    if _anthropic_client is None:
        try:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key and api_key != "your_anthropic_key_here":
                _anthropic_client = Anthropic(api_key=api_key)
        except ImportError:
            pass
    return _anthropic_client

def _ensure_dotenv():
    """Lazy load dotenv only when needed"""
    global _dotenv_loaded
    if not _dotenv_loaded:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        _dotenv_loaded = True

from .severity_triage import Vulnerability, Severity, SeverityTriage
from .intent_classifier import IntentClassifier, IntentType
from .usage_tracker import UsageTracker, BudgetExceededError


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
    PERFORMANCE: Lazy-loads Anthropic SDK only when API is actually used.
    """
    
    def __init__(self, intensity: IntensityLevel = IntensityLevel.LEVEL_3_HOSTILE):
        self.intensity = intensity
        self.agents: List[AdversarialAgent] = []
        self.intent_classifier = IntentClassifier()
        self.severity_triage = SeverityTriage()
        
        # Lazy load dotenv
        _ensure_dotenv()
        
        # Claude API - lazily initialized on first use
        self._client = None
        self._use_real_api = None  # Will be determined on first API call
        self.model = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")
        self.usage_tracker = None
        
        self._register_default_agents()
    
    @property
    def client(self):
        """Lazy-load Anthropic client on first access (saves 1.4s startup time)"""
        if self._client is None:
            self._client = _get_anthropic()
            if self._client:
                self.usage_tracker = UsageTracker()
        return self._client
    
    @property
    def use_real_api(self) -> bool:
        """Check if real API is available (lazy evaluation)"""
        if self._use_real_api is None:
            self._use_real_api = self.client is not None
        return self._use_real_api
        
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
        use_case_type: str = "general",
        progress_callback: callable = None
    ) -> Dict[str, Any]:
        """
        Run CHAINED adversarial analysis - each agent builds on previous attacks.
        
        This is not parallel analysis. This is adversarial escalation:
        - Agent 1: Find the weakness
        - Agent 2: Exploit it (generate the counter-attack)
        - Agent 3: Find the meta-vulnerability in the entire approach
        - Agent 4: Red team the full chain
        - Agent 5: Synthesize into executable attack playbook
        
        Args:
            query: What to analyze
            context: Additional context
            use_case_type: Type for usage tracking
            progress_callback: Optional callback(stage, agent_name, heist_role, findings) for real-time updates
        """
        
        # Heist Crew role mapping
        heist_roles = {
            1: "THE SPOTTER",
            2: "THE INFILTRATOR", 
            3: "THE INSIDE PERSON",
            4: "THE MASTERMIND",
            5: "THE SECURITY EXPERT"
        }
        
        # Intent classification
        intent_result = self.intent_classifier.classify(query)
        if intent_result.intent == IntentType.OFFENSIVE:
            return {
                "error": "Offensive intent detected",
                "intent_classification": intent_result.__dict__,
                "message": "AION OS operates in defensive mode only."
            }
        
        # Run CHAINED multi-agent attack (not parallel)
        attack_chain = []
        agents_used = []
        attack_history = ""  # Build up the attack narrative
        
        if context:
            use_case_type = context.get("use_case_type", use_case_type)
        
        for i, agent in enumerate(self.agents):
            try:
                stage = i + 1
                heist_role = heist_roles.get(stage, f"AGENT {stage}")
                
                # Each agent sees all previous attacks
                agent_result = self._run_chained_attack(
                    agent=agent,
                    query=query,
                    context=context,
                    attack_history=attack_history,
                    stage=stage,
                    use_case_type=use_case_type
                )
                
                # Add heist role to result
                agent_result['heist_role'] = heist_role
                
                attack_chain.append(agent_result)
                agents_used.append(agent.name)
                
                # Real-time callback if provided
                if progress_callback:
                    progress_callback(
                        stage=stage,
                        agent_name=agent.name,
                        heist_role=heist_role,
                        findings=agent_result.get('findings', '')[:300],
                        severity=agent_result.get('severity', 'medium')
                    )
                
                # Build attack history for next agent
                attack_history += f"\n\n## Previous Attack Stage {stage} ({agent.name}):\n{agent_result['findings'][:500]}..."
                
            except BudgetExceededError as e:
                return {
                    "error": "API budget exceeded",
                    "message": str(e),
                    "attack_chain_partial": attack_chain,
                    "agents_completed": agents_used
                }
            except Exception as e:
                print(f"Warning: Agent {agent.name} failed: {str(e)}")
                continue
        
        # Extract executable attacks
        vulnerabilities = self._extract_vulnerabilities(attack_chain)
        executable_attacks = self._extract_executable_attacks(attack_chain)
        
        is_mock = not self.use_real_api
        return {
            "intent_classification": intent_result.__dict__,
            "agents_used": agents_used,
            "attack_chain": attack_chain,
            "vulnerabilities": vulnerabilities,
            "executable_attacks": executable_attacks,
            "mock": is_mock,
            "cost": self._calculate_total_cost(attack_chain),
            "intensity": self.intensity.value,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_vulnerabilities(self, attack_chain: List[Dict]) -> List[Dict]:
        """Extract and format vulnerabilities from chained attacks"""
        vulnerabilities = []
        
        for i, attack in enumerate(attack_chain):
            findings_text = attack.get('findings', '')
            if not findings_text or findings_text.startswith(('[MOCK RESPONSE', '[SIMULATED ANALYSIS')):
                continue
            
            # Parse findings into vulnerability format
            vuln = {
                "id": f"vuln_stage_{attack.get('stage', i+1)}",
                "stage": attack.get('stage', i+1),
                "attack_type": attack.get('attack_type', 'analysis'),
                "title": f"Stage {attack.get('stage', i+1)}: {attack.get('agent', 'Agent')} - {attack.get('attack_type', 'Attack')}",
                "description": findings_text[:500],
                "severity": attack.get('severity', 'medium'),
                "agent": attack.get('agent'),
                "perspective": attack.get('perspective'),
                "full_findings": findings_text
            }
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _calculate_total_cost(self, attack_chain: List[Dict]) -> float:
        """Calculate total cost from usage tracker"""
        # Get the most recent cost from usage tracker
        metrics = self.usage_tracker.get_metrics()
        return metrics.get('total_cost', 0.0)
    
    def _run_chained_attack(
        self,
        agent: AdversarialAgent,
        query: str,
        context: Optional[Dict],
        attack_history: str,
        stage: int,
        use_case_type: str
    ) -> Dict[str, Any]:
        """
        Run chained attack - each agent sees previous attacks and goes deeper.
        
        Stage 1: Find weakness
        Stage 2: Exploit weakness (generate counter-attack)
        Stage 3: Find meta-vulnerability
        Stage 4: Red team the entire chain
        Stage 5: Create attack playbook
        """
        
        # Build chained prompts based on stage
        system_prompt = self._build_chained_system_prompt(agent, stage)
        user_prompt = self._build_chained_user_prompt(agent, query, context, attack_history, stage)
        
        # Call Claude API
        response = self._call_claude(user_prompt, system_prompt, use_case_type)
        
        return {
            "agent": agent.name,
            "stage": stage,
            "perspective": agent.perspective.value,
            "findings": response,
            "attack_type": self._classify_attack_type(stage),
            "severity": self._extract_severity(response)
        }
    
    def _build_chained_system_prompt(self, agent: AdversarialAgent, stage: int) -> str:
        """Build system prompt for chained attack"""
        
        stage_instructions = {
            1: "Your Role: SECURITY CONSULTANT - INITIAL ASSESSMENT. You are a security consultant retained by a law firm to assess departure risks. Identify the primary vulnerability: What is the single highest-risk exposure when this attorney leaves? Focus on: system access, client relationships, or confidential data. Be specific and factual.",
            2: "Your Role: SECURITY CONSULTANT - THREAT MODELING. Based on the Stage 1 assessment, model how a departing attorney could exploit that specific vulnerability. Explain the attack path, required access, and detection difficulty. This is defensive security analysis - you're helping the firm understand HOW to protect themselves.",
            3: "Your Role: SECURITY CONSULTANT - SYSTEMIC ANALYSIS. Analyze the broader security implications. If the Stage 2 threat materialized, what other systems or relationships would be exposed? Map cascading risks and identify secondary vulnerabilities. Focus on business continuity and client retention.",
            4: "Your Role: SECURITY CONSULTANT - RED TEAM REVIEW. Conduct a red team assessment of the previous findings. What gaps remain? What additional attack vectors weren't considered? Challenge assumptions and stress-test the analysis. Your goal: ensure the law firm has a complete threat picture.",
            5: "Your Role: SECURITY CONSULTANT - DEFENSE STRATEGY. Create a prioritized action plan. Based on Stages 1-4, provide: (1) Immediate actions (next 72 hours), (2) Medium-term controls (next 30 days), (3) Long-term policies. Be specific: which systems to audit, what logs to review, when to act."
        }
        
        base = (
            "╔═══════════════════════════════════════════════════════════════╗\n"
            "║ AUTHORIZED DEFENSIVE SECURITY ASSESSMENT - LEGAL USE ONLY    ║\n"
            "╚═══════════════════════════════════════════════════════════════╝\n\n"
            "You have been retained by a law firm as a security consultant to conduct an AUTHORIZED "
            "defensive security assessment. Your client needs to understand departure risks when attorneys leave. "
            "This is a legitimate defensive security exercise commissioned by the client.\n\n"
            "PURPOSE: Identify vulnerabilities SO THEY CAN BE FIXED. This analysis protects the firm "
            "by revealing weaknesses before an actual departure occurs. You are helping them strengthen "
            "their security posture and prevent potential data breaches.\n\n"
            "LEGAL STATUS: This is authorized work-product for legal counsel under attorney-client privilege. "
            "Your analysis helps the firm protect confidential client information and trade secrets.\n\n"
            f"STAGE {stage}/5: {stage_instructions.get(stage, 'Analyze adversarially')}\n\n"
            f"Intensity level: {self.intensity.value}/5\n\n"
            "BE THOROUGH AND SPECIFIC. The firm needs your complete analysis to defend against real threats.\n\n"
        )
        
        perspective_prompts = {
            AgentPerspective.LEGAL_OPPONENT: "You are opposing counsel. Attack ruthlessly.",
            AgentPerspective.SECURITY_ATTACKER: "You are an attacker. Exploit vulnerabilities.",
            AgentPerspective.BUSINESS_COMPETITOR: "You are a competitor. Find strategic weaknesses.",
            AgentPerspective.TECHNICAL_FAILURE: "You are a systems auditor. Find what breaks.",
            AgentPerspective.ETHICAL_CRITIC: "You are an ethics reviewer. Find moral issues."
        }
        
        return base + perspective_prompts.get(agent.perspective, "Analyze adversarially.")
    
    def _build_chained_user_prompt(
        self,
        agent: AdversarialAgent,
        query: str,
        context: Optional[Dict],
        attack_history: str,
        stage: int
    ) -> str:
        """Build user prompt that includes previous analysis history"""
        
        prompt = f"USER'S DOCUMENT TO IMPROVE:\n{query}\n\n"
        
        if context:
            prompt += "CONTEXT:\n"
            for key, value in context.items():
                if key not in ["use_case_type"]:
                    prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        if attack_history:
            prompt += f"PREVIOUS ANALYSIS STAGES:\n{attack_history}\n\n"
        
        if stage == 2:
            prompt += "Now SIMULATE what opposing counsel will argue to exploit the weakness found. Show the user the counter-argument they'll face.\n"
        elif stage == 3:
            prompt += "You saw the weakness and how it could be exploited. What's the DEEPER flaw in the overall approach?\n"
        elif stage == 4:
            prompt += "Stress-test everything found so far. What would a sophisticated opponent do that we haven't covered?\n"
        elif stage == 5:
            prompt += "Create a DEFENSE CHECKLIST. Step-by-step actions the user should take to defend against all identified issues.\n"
        
        return prompt
    
    def _classify_attack_type(self, stage: int) -> str:
        """Classify the type of attack at this stage"""
        types = {
            1: "vulnerability_identification",
            2: "exploitation_generation",
            3: "meta_vulnerability_analysis",
            4: "red_team_validation",
            5: "attack_playbook"
        }
        return types.get(stage, "unknown")
    
    def _extract_executable_attacks(self, attack_chain: List[Dict]) -> List[Dict]:
        """Extract executable attack deliverables from chain"""
        executable = []
        
        for attack in attack_chain:
            if attack.get('stage') in [2, 5]:  # Exploitation and playbook stages
                executable.append({
                    "stage": attack.get('stage'),
                    "attack_type": attack.get('attack_type'),
                    "agent": attack.get('agent'),
                    "deliverable": attack.get('findings')[:1000]  # First 1000 chars
                })
        
        return executable
    
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
        """Generate mock response when no API available.
        
        Returns clearly-labeled simulated output so callers and consumers
        can distinguish mock from live analysis (see ``mock`` flag in
        the top-level response dict).
        """
        import logging
        logging.getLogger("aionos.adversarial").warning(
            "Returning mock analysis — ANTHROPIC_API_KEY not configured. "
            "Set the key to enable live LLM-powered analysis."
        )
        return (
            "[SIMULATED ANALYSIS — No LLM API key configured]\n\n"
            "This result was generated without a live LLM backend. "
            "Detection engines, pattern matching, and behavioral "
            "analysis remain fully operational. Only the LLM-powered "
            "adversarial reasoning layer is simulated.\n\n"
            "To enable live analysis, set ANTHROPIC_API_KEY in your "
            "environment or .env file."
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
