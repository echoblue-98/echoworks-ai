"""
Gemini API Client

Handles communication with the Gemini API for adversarial analysis.
"""

import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

# API key loaded silently - no debug output
api_key = os.getenv("GEMINI_API_KEY")

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    def analyze(self, content: str, context: Dict[str, Any], intensity: int) -> Dict[str, Any]:
        """
        Sends a request to the Gemini API for analysis.

        :param content: The content to analyze.
        :param context: Additional context for the analysis.
        :param intensity: The intensity level of the analysis (1-5).
        :return: The response from the Gemini API.
        """
        
        prompt = f"""
        Analyze the following content with an intensity of {intensity}/5.
        Context: {json.dumps(context)}
        Content:
        ---
        {content}
        ---
        
        Identify vulnerabilities, weaknesses, and potential exploits.
        Return the analysis in JSON format with a list of 'vulnerabilities', 
        each with 'title', 'description', and 'severity' (low, medium, high, critical).
        """

        headers = {
            "Content-Type": "application/json"
        }
        params = {'key': self.api_key}
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(self.api_url, params=params, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
        
        # Extract and parse the JSON content from the response
        try:
            api_response = response.json()
            generated_text = api_response['candidates'][0]['content']['parts'][0]['text']
            
            # Strip markdown code fences if present
            if generated_text.startswith("```json"):
                generated_text = generated_text[7:]  # Remove ```json
            if generated_text.startswith("```"):
                generated_text = generated_text[3:]  # Remove ```
            if generated_text.endswith("```"):
                generated_text = generated_text[:-3]  # Remove trailing ```
            generated_text = generated_text.strip()
            
            # Parse the JSON
            analysis_result = json.loads(generated_text)
            
            # Format the result to match the expected structure for the CLI
            vulnerabilities = analysis_result.get("vulnerabilities", [])
            formatted_vulns = []
            for vuln in vulnerabilities:
                formatted_vulns.append({
                    "title": vuln.get("title", "Unknown"),
                    "agent": "Gemini AI",
                    "severity": vuln.get("severity", "medium"),
                    "description": vuln.get("description", ""),
                    "full_findings": vuln.get("description", "")
                })
            
            return {
                "vulnerabilities": formatted_vulns,
                "cost": 0.0,
                "agents_used": ["Gemini 2.5 Flash"],
                "timestamp": None
            }
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Raw response: {response.text}")
            return {"vulnerabilities": [], "error": "Failed to parse Gemini response"}
# print(result)