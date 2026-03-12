"""
Llama Client - Self-Hosted LLM for Maximum Privacy

PLACEHOLDER for future enterprise customers who require on-premise deployment.
Currently NOT NEEDED because:
- Claude/Gemini already receive ZERO proprietary pattern data
- Pattern database stays 100% local
- Only attorney profiles + generic instructions sent to APIs

WHEN TO IMPLEMENT:
- Enterprise customer demands on-premise deployment
- API costs exceed $500/month at scale
- Customer has ITAR/classified data requirements

SETUP (when needed):
1. Deploy Llama 3 70B or similar via:
   - Ollama (easiest): ollama run llama3:70b
   - vLLM (fastest): pip install vllm
   - Together.ai API (managed): https://api.together.xyz
   
2. Set environment variable:
   LLAMA_API_URL=http://localhost:11434/api/generate  # Ollama default
   
3. Update HeistPlanner to use LlamaClient instead of Claude/Gemini

Author: AION OS Team
Status: PLACEHOLDER - Not yet implemented
"""

import os
import json
import requests
from typing import Dict, Any, Optional


class LlamaClient:
    """
    Self-hosted Llama client for maximum data privacy.
    
    100% of data stays on your infrastructure - nothing sent to cloud.
    """
    
    def __init__(self):
        self.api_url = os.getenv("LLAMA_API_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("LLAMA_MODEL", "llama3:70b")
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Llama server is running"""
        try:
            # Ollama health check
            response = requests.get(self.api_url.replace("/api/generate", "/"), timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def analyze(self, content: str, context: Dict[str, Any], intensity: int) -> Dict[str, Any]:
        """
        Sends analysis request to self-hosted Llama.
        
        PRIVACY: 100% local - nothing leaves your infrastructure.
        
        :param content: The heist brief to analyze
        :param context: Additional context (should be empty {} for privacy)
        :param intensity: Analysis intensity (1-5)
        :return: Analysis result with vulnerabilities
        """
        
        if not self._available:
            raise RuntimeError(
                "Llama server not available. Start with:\n"
                "  ollama serve\n"
                "  ollama run llama3:70b\n\n"
                "Or use Claude/Gemini (already privacy-protected)."
            )
        
        prompt = f"""You are a security analyst conducting an authorized defensive assessment.
Analyze the following scenario with intensity {intensity}/5.

{content}

Context: {json.dumps(context) if context else "None"}

Identify vulnerabilities, weaknesses, and potential data exfiltration vectors.
Return your analysis as JSON with a list of 'vulnerabilities', each containing:
- title: Brief vulnerability name
- description: Detailed explanation
- severity: critical, high, medium, or low
- countermeasures: List of recommended actions

Respond ONLY with valid JSON, no additional text."""

        try:
            # Ollama API format
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 4096
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=120  # Llama can be slow on CPU
            )
            
            if response.status_code != 200:
                raise Exception(f"Llama API error: {response.status_code}")
            
            result = response.json()
            generated_text = result.get("response", "")
            
            # Parse JSON from response
            return self._parse_response(generated_text)
            
        except requests.exceptions.Timeout:
            return {
                "vulnerabilities": [],
                "error": "Llama request timed out. Consider using GPU or smaller model."
            }
        except Exception as e:
            return {
                "vulnerabilities": [],
                "error": f"Llama error: {str(e)}"
            }
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse Llama response into structured format"""
        
        # Strip markdown code fences if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        text = text.strip()
        
        try:
            analysis = json.loads(text)
            vulnerabilities = analysis.get("vulnerabilities", [])
            
            # Format for CLI compatibility
            formatted = []
            for vuln in vulnerabilities:
                formatted.append({
                    "title": vuln.get("title", "Unknown"),
                    "agent": "Llama (Self-Hosted)",
                    "severity": vuln.get("severity", "medium").lower(),
                    "description": vuln.get("description", ""),
                    "full_findings": vuln.get("description", ""),
                    "countermeasures": vuln.get("countermeasures", [])
                })
            
            return {
                "vulnerabilities": formatted,
                "cost": 0.0,  # Self-hosted = free
                "agents_used": [f"Llama ({self.model})"],
                "privacy_mode": "MAXIMUM - 100% local"
            }
            
        except json.JSONDecodeError:
            # Return raw text if JSON parsing fails
            return {
                "vulnerabilities": [{
                    "title": "Llama Analysis",
                    "agent": "Llama (Self-Hosted)",
                    "severity": "medium",
                    "description": text[:1000],
                    "full_findings": text
                }],
                "cost": 0.0,
                "agents_used": [f"Llama ({self.model})"],
                "privacy_mode": "MAXIMUM - 100% local"
            }


def check_llama_available() -> bool:
    """Quick check if Llama is available"""
    client = LlamaClient()
    return client.is_available


# Placeholder for future vLLM support
class VLLMClient:
    """
    vLLM client for high-performance self-hosted inference.
    
    PLACEHOLDER - Implement when:
    - Need >10 concurrent analyses
    - Have GPU infrastructure
    - Want fastest self-hosted option
    """
    
    def __init__(self):
        raise NotImplementedError(
            "vLLM support coming soon. Use LlamaClient (Ollama) for now."
        )


# Placeholder for Together.ai API (managed Llama)
class TogetherClient:
    """
    Together.ai client for managed Llama hosting.
    
    PLACEHOLDER - Implement when:
    - Want Llama quality without self-hosting
    - Need enterprise SLA
    - API cost is acceptable ($0.20/1M tokens)
    """
    
    def __init__(self):
        raise NotImplementedError(
            "Together.ai support coming soon. Use LlamaClient (Ollama) for now."
        )
