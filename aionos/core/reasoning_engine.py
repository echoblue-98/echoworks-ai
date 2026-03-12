"""
AION OS - LLM Reasoning Engine

Detects novel attack patterns through semantic reasoning, not just pattern matching.
Works with Claude API (cloud) or Ollama (local Llama 3).

This catches attacks that:
- Don't match any known pattern
- Are within "normal" behavioral baselines individually
- But semantically suggest malicious intent when viewed together
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class LLMProvider(Enum):
    CLAUDE = "claude"
    OLLAMA = "ollama"    # Local Llama 3
    LMSTUDIO = "lmstudio"  # Local LM Studio (OpenAI-compatible)
    MOCK = "mock"        # For testing without API


@dataclass
class ReasoningResult:
    """Result from LLM threat reasoning"""
    threat_detected: bool
    confidence: float  # 0-1
    threat_type: str
    reasoning: str
    recommended_actions: List[str]
    events_analyzed: int
    inference_time_ms: int


# Lazy-load clients to avoid import penalty
_anthropic_client = None
_ollama_available = None
_lmstudio_available = None


def _get_anthropic():
    """Lazy-load Anthropic client"""
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        _anthropic_client = Anthropic()
    return _anthropic_client


def _check_ollama() -> bool:
    """Check if Ollama is running locally"""
    global _ollama_available
    if _ollama_available is None:
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=1)
            _ollama_available = resp.status_code == 200
        except:
            _ollama_available = False
    return _ollama_available


def _check_lmstudio() -> bool:
    """Check if LM Studio is running locally (OpenAI-compatible API)"""
    global _lmstudio_available
    if _lmstudio_available is None:
        try:
            import requests
            resp = requests.get("http://localhost:1234/v1/models", timeout=2)
            data = resp.json()
            _lmstudio_available = resp.status_code == 200 and len(data.get("data", [])) > 0
        except:
            _lmstudio_available = False
    return _lmstudio_available


class LLMReasoningEngine:
    """
    Uses LLM to reason about security events and detect novel threats.
    
    Unlike pattern matching (exact signature) or baseline (statistical deviation),
    this engine can recognize semantic patterns humans would notice.
    """
    
    SYSTEM_PROMPT = """You are AION, an expert insider threat analyst. You analyze sequences of security events to detect potential threats that might not match any known attack pattern.

Your job is to look for SEMANTIC patterns - things that individually seem normal but together suggest malicious intent.

Examples of what you should catch:
- LinkedIn updates + accessing client lists + unusual file downloads = departure theft preparation
- Accessing payroll data + org charts + email to personal account = potential data theft
- After-hours VPN from new location + bulk exports + credential changes = compromised account
- Resume editing + job site visits + database queries for "top clients" = pre-departure reconnaissance

For each analysis, provide:
1. threat_detected: true/false
2. confidence: 0.0-1.0 (how confident you are)
3. threat_type: category of threat (departure_theft, account_compromise, data_exfiltration, reconnaissance, none)
4. reasoning: 2-3 sentences explaining your analysis
5. recommended_actions: list of 2-4 specific actions

Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""

    def __init__(self, provider: LLMProvider = None):
        """Initialize with specified provider or auto-detect best available."""
        if provider is None:
            # Auto-detect: prefer local LM Studio > Ollama > Claude > Mock
            if _check_lmstudio():
                self.provider = LLMProvider.LMSTUDIO
            elif _check_ollama():
                self.provider = LLMProvider.OLLAMA
            elif os.getenv("ANTHROPIC_API_KEY"):
                self.provider = LLMProvider.CLAUDE
            else:
                self.provider = LLMProvider.MOCK
        else:
            self.provider = provider
        
        self.model = self._get_model_name()
        
    def _get_model_name(self) -> str:
        """Get model name for the provider"""
        if self.provider == LLMProvider.CLAUDE:
            return "claude-sonnet-4-20250514"
        elif self.provider == LLMProvider.OLLAMA:
            return "llama3:8b"
        elif self.provider == LLMProvider.LMSTUDIO:
            try:
                import requests
                resp = requests.get("http://localhost:1234/v1/models", timeout=2)
                models = resp.json().get("data", [])
                return models[0]["id"] if models else "lmstudio-model"
            except:
                return "lmstudio-model"
        return "mock"
    
    def analyze_events(self, user_id: str, events: List[Dict], prior_history: str = '') -> ReasoningResult:
        """
        Analyze a sequence of events for a user using LLM reasoning.
        
        Args:
            user_id: The user whose events to analyze
            events: List of event dicts with type, timestamp, details
            prior_history: Optional text summary of prior investigations for this user
                          (injected into prompt for case-level memory)
            
        Returns:
            ReasoningResult with threat assessment
        """
        if not events:
            return ReasoningResult(
                threat_detected=False,
                confidence=0.0,
                threat_type="none",
                reasoning="No events to analyze",
                recommended_actions=[],
                events_analyzed=0,
                inference_time_ms=0
            )
        
        # Build prompt
        prompt = self._build_prompt(user_id, events, prior_history)
        
        # Run inference
        start = datetime.now()
        
        if self.provider == LLMProvider.CLAUDE:
            response = self._call_claude(prompt)
        elif self.provider == LLMProvider.OLLAMA:
            response = self._call_ollama(prompt)
        elif self.provider == LLMProvider.LMSTUDIO:
            response = self._call_lmstudio(prompt)
        else:
            response = self._mock_response(events)
        
        elapsed_ms = int((datetime.now() - start).total_seconds() * 1000)
        
        # Parse response
        result = self._parse_response(response, len(events), elapsed_ms)
        return result
    
    def _build_prompt(self, user_id: str, events: List[Dict], prior_history: str = '') -> str:
        """Build the analysis prompt with optional case history"""
        events_text = []
        for i, e in enumerate(events[-20:], 1):  # Last 20 events max
            ts = e.get("timestamp", "unknown time")
            etype = e.get("type", e.get("event_type", "unknown"))
            details = e.get("details", {})
            events_text.append(f"{i}. [{ts}] {etype}: {json.dumps(details)}")
        
        history_block = ''
        if prior_history:
            history_block = f"""\n\nIMPORTANT CONTEXT — This user has been investigated before:
{prior_history}

Factor this history into your analysis. Repeated suspicious behavior increases threat confidence.\n"""
        
        return f"""Analyze these security events for user {user_id}:

{chr(10).join(events_text)}
{history_block}
Look for semantic patterns that suggest insider threat behavior. Remember: individual events may seem normal, but the combination may indicate malicious intent.

Respond with JSON only."""

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API"""
        try:
            client = _get_anthropic()
            response = client.messages.create(
                model=self.model,
                max_tokens=500,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return json.dumps({
                "threat_detected": False,
                "confidence": 0.0,
                "threat_type": "error",
                "reasoning": f"Claude API error: {str(e)}",
                "recommended_actions": ["Check API key and retry"]
            })
    
    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama (Llama 3)"""
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{self.SYSTEM_PROMPT}\n\nUser: {prompt}\n\nAssistant:",
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=30
            )
            return response.json().get("response", "{}")
        except Exception as e:
            return json.dumps({
                "threat_detected": False,
                "confidence": 0.0,
                "threat_type": "error",
                "reasoning": f"Ollama error: {str(e)}",
                "recommended_actions": ["Check Ollama is running: ollama serve"]
            })
    
    def _call_lmstudio(self, prompt: str) -> str:
        """Call local LM Studio via OpenAI-compatible API"""
        try:
            import requests
            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=60
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return json.dumps({
                "threat_detected": False,
                "confidence": 0.0,
                "threat_type": "error",
                "reasoning": f"LM Studio error: {str(e)}",
                "recommended_actions": ["Check LM Studio is running on localhost:1234"]
            })

    def _mock_response(self, events: List[Dict]) -> str:
        """Mock response for testing without LLM"""
        # Simple heuristic-based mock
        event_types = [e.get("type", e.get("event_type", "")) for e in events]
        
        # Check for suspicious combinations
        has_linkedin = any("linkedin" in str(e).lower() for e in events)
        has_file_download = any("download" in t.lower() for t in event_types)
        has_database = any("database" in t.lower() or "query" in t.lower() for t in event_types)
        has_after_hours = any("after_hours" in t.lower() for t in event_types)
        
        if has_linkedin and has_file_download:
            return json.dumps({
                "threat_detected": True,
                "confidence": 0.75,
                "threat_type": "departure_theft",
                "reasoning": "User updated LinkedIn profile and downloaded files. This pattern suggests preparation for departure with company data.",
                "recommended_actions": [
                    "Review files downloaded in last 7 days",
                    "Check for email forwarding rules",
                    "Verify employment status"
                ]
            })
        elif has_after_hours and has_database:
            return json.dumps({
                "threat_detected": True,
                "confidence": 0.65,
                "threat_type": "data_exfiltration",
                "reasoning": "After-hours database access is unusual. Combined with other activities, suggests potential data theft.",
                "recommended_actions": [
                    "Review database queries executed",
                    "Check for data exports",
                    "Enable enhanced monitoring"
                ]
            })
        else:
            return json.dumps({
                "threat_detected": False,
                "confidence": 0.9,
                "threat_type": "none",
                "reasoning": "Events appear to be normal business activity. No concerning patterns detected.",
                "recommended_actions": []
            })
    
    def _parse_response(self, response: str, event_count: int, elapsed_ms: int) -> ReasoningResult:
        """Parse LLM response into structured result"""
        try:
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            
            # Handle array responses (some models wrap in a list)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            # Handle non-dict responses
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data).__name__}")
            
            return ReasoningResult(
                threat_detected=data.get("threat_detected", False),
                confidence=float(data.get("confidence", 0.0)),
                threat_type=data.get("threat_type", "unknown"),
                reasoning=data.get("reasoning", ""),
                recommended_actions=data.get("recommended_actions", []),
                events_analyzed=event_count,
                inference_time_ms=elapsed_ms
            )
        except (json.JSONDecodeError, KeyError) as e:
            return ReasoningResult(
                threat_detected=False,
                confidence=0.0,
                threat_type="parse_error",
                reasoning=f"Failed to parse LLM response: {response[:200]}",
                recommended_actions=["Manual review required"],
                events_analyzed=event_count,
                inference_time_ms=elapsed_ms
            )


# Singleton instance
_reasoning_engine = None

def get_reasoning_engine() -> LLMReasoningEngine:
    """Get or create the reasoning engine singleton"""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = LLMReasoningEngine()
    return _reasoning_engine


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo the LLM reasoning engine"""
    print("=" * 60)
    print("🧠 AION OS - LLM Reasoning Engine")
    print("=" * 60)
    
    engine = LLMReasoningEngine(provider=LLMProvider.MOCK)  # Use mock for demo
    print(f"\nProvider: {engine.provider.value}")
    print(f"Model: {engine.model}")
    
    # Scenario 1: Departure preparation (should detect)
    print("\n" + "-" * 40)
    print("📋 SCENARIO 1: Pre-Departure Reconnaissance")
    print("-" * 40)
    
    events_departure = [
        {"timestamp": "2026-01-20T09:00:00", "type": "linkedin_update", "details": {"action": "changed status to 'Open to Work'"}},
        {"timestamp": "2026-01-21T14:30:00", "type": "file_download", "details": {"path": "/clients/top_50_accounts.xlsx", "size_mb": 2.3}},
        {"timestamp": "2026-01-22T11:00:00", "type": "database_query", "details": {"query": "SELECT * FROM clients WHERE revenue > 1000000"}},
        {"timestamp": "2026-01-23T16:45:00", "type": "email_forward", "details": {"to": "personal@gmail.com", "subject": "Client contacts"}},
    ]
    
    result = engine.analyze_events("srevino@typhoon.com", events_departure)
    print(f"\n🔍 Threat Detected: {result.threat_detected}")
    print(f"📊 Confidence: {result.confidence:.0%}")
    print(f"🏷️  Type: {result.threat_type}")
    print(f"💭 Reasoning: {result.reasoning}")
    print(f"⚡ Actions: {result.recommended_actions}")
    print(f"⏱️  Inference: {result.inference_time_ms}ms")
    
    # Scenario 2: Normal activity (should not detect)
    print("\n" + "-" * 40)
    print("📋 SCENARIO 2: Normal Business Activity")
    print("-" * 40)
    
    events_normal = [
        {"timestamp": "2026-01-20T09:00:00", "type": "vpn_access", "details": {"location": "Austin, TX"}},
        {"timestamp": "2026-01-20T10:30:00", "type": "file_download", "details": {"path": "/projects/q1_report.docx", "size_mb": 0.5}},
        {"timestamp": "2026-01-20T14:00:00", "type": "email_send", "details": {"to": "client@company.com", "subject": "Meeting follow-up"}},
    ]
    
    result = engine.analyze_events("jsmith@company.com", events_normal)
    print(f"\n🔍 Threat Detected: {result.threat_detected}")
    print(f"📊 Confidence: {result.confidence:.0%}")
    print(f"🏷️  Type: {result.threat_type}")
    print(f"💭 Reasoning: {result.reasoning}")
    
    print("\n" + "=" * 60)
    print("✅ LLM Reasoning Engine Ready")
    print("=" * 60)
    print("\nThis engine catches attacks that:")
    print("  • Don't match known patterns")
    print("  • Are individually within 'normal' ranges")
    print("  • But semantically suggest malicious intent")
    print("\nTo use with real LLM:")
    print("  • Claude: Set ANTHROPIC_API_KEY env var")
    print("  • Llama 3: Run 'ollama serve' and 'ollama pull llama3:8b'")


if __name__ == "__main__":
    demo()
