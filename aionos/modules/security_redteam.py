"""
Security Red Team - Adversarial cybersecurity analysis

Assumes breach mentality and simulates attacker perspective
to find vulnerabilities before real attackers do.
"""

from typing import Dict, Any, List
from datetime import datetime

from ..core.adversarial_engine import (
    AdversarialEngine,
    AgentPerspective,
    IntensityLevel
)
from ..core.severity_triage import Vulnerability, Severity
from ..api.gemini_client import GeminiClient


class SecurityRedTeam:
    """
    Adversarial cybersecurity analysis module.
    
    Operates as a malicious attacker to find:
    - Configuration vulnerabilities
    - Unpatched systems
    - Weak authentication
    - Attack vectors and lateral movement paths
    - Privilege escalation opportunities
    """
    
    def __init__(self, intensity: IntensityLevel = IntensityLevel.LEVEL_4_REDTEAM, use_gemini: bool = False):
        # Security analysis defaults to red team intensity
        self.engine = AdversarialEngine(intensity=intensity)
        self.scan_history = []
        self.use_gemini = use_gemini
        self.gemini_client = GeminiClient() if use_gemini else None

    def scan_infrastructure(
        self,
        infrastructure_config: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Scan infrastructure configuration for vulnerabilities.
        
        Args:
            infrastructure_config: Infrastructure description (network diagram, configs, etc.)
            context: Additional context (environment, compliance requirements, etc.)
        
        Returns:
            A dictionary containing the analysis results.
        """
        if self.use_gemini:
            return self.gemini_client.analyze(infrastructure_config, context, self.engine.intensity.value)

        perspectives = [
            AgentPerspective.SECURITY_ATTACKER,
            AgentPerspective.TECHNICAL_FAILURE
        ]
        
        result = self.engine.analyze(
            query=infrastructure_config,
            perspectives=perspectives,
            context={
                **(context or {}),
                "analysis_type": "infrastructure_scan",
                "use_case_type": "security_infrastructure",
                "authorized_pen_test": True
            }
        )
        
        self.scan_history.append({
            "type": "infrastructure_scan",
            "timestamp": datetime.utcnow(),
            "result": result
        })
        
        return result
    
    def analyze_security_posture(
        self,
        security_controls: List[str],
        threat_model: str = "external_attacker"
    ) -> Dict[str, Any]:
        """
        Analyze overall security posture and controls.
        
        Args:
            security_controls: List of implemented security controls
            threat_model: 'external_attacker', 'insider_threat', or 'nation_state'
        
        Returns:
            Analysis of security control effectiveness
        """
        controls_text = "\n".join(f"- {control}" for control in security_controls)
        
        target = f"""
THREAT MODEL: {threat_model}

IMPLEMENTED SECURITY CONTROLS:
{controls_text}
"""
        
        user_input = "Analyze my security posture"
        
        result = self.engine.analyze(
            target=target,
            perspectives=[AgentPerspective.SECURITY_ATTACKER],
            context={
                "analysis_type": "security_posture",
                "threat_model": threat_model,
                "authorized_pen_test": True
            },
            user_input=user_input
        )
        
        return result
    
    def simulate_attack_chain(
        self,
        entry_point: str,
        target_assets: List[str]
    ) -> Dict[str, Any]:
        """
        Simulate complete attack chain from entry point to target assets.
        
        Args:
            entry_point: Initial access vector (e.g., "phishing email to employees")
            target_assets: List of high-value assets attacker would target
        
        Returns:
            Likely attack path and vulnerabilities along the way
        """
        assets_text = "\n".join(f"- {asset}" for asset in target_assets)
        
        target = f"""
ENTRY POINT:
{entry_point}

TARGET ASSETS:
{assets_text}

Map the complete attack chain from entry point to target assets.
Identify all vulnerabilities that enable progression.
"""
        
        user_input = "Simulate attack chain on my systems"
        
        # Maximum intensity for attack chain simulation
        original_intensity = self.engine.intensity
        self.engine.set_intensity(IntensityLevel.LEVEL_5_MAXIMUM)
        
        result = self.engine.analyze(
            target=target,
            perspectives=[AgentPerspective.SECURITY_ATTACKER],
            context={
                "analysis_type": "attack_chain",
                "authorized_pen_test": True
            },
            user_input=user_input
        )
        
        # Restore original intensity
        self.engine.set_intensity(original_intensity)
        
        return result
    
    def continuous_red_team(
        self,
        system_description: str,
        scan_frequency: str = "daily"
    ) -> Dict[str, Any]:
        """
        Set up continuous red team monitoring (simulated).
        
        Args:
            system_description: Description of systems to monitor
            scan_frequency: How often to scan ('hourly', 'daily', 'weekly')
        
        Returns:
            Continuous monitoring configuration and initial scan
        """
        user_input = "Set up continuous red team monitoring"
        
        result = self.engine.analyze(
            target=system_description,
            perspectives=[
                AgentPerspective.SECURITY_ATTACKER,
                AgentPerspective.TECHNICAL_FAILURE
            ],
            context={
                "analysis_type": "continuous_monitoring",
                "scan_frequency": scan_frequency,
                "authorized_pen_test": True
            },
            user_input=user_input
        )
        
        return {
            **result,
            "monitoring_config": {
                "enabled": True,
                "frequency": scan_frequency,
                "next_scan": "scheduled"
            }
        }
    
    def assume_breach_analysis(
        self,
        compromised_asset: str,
        network_topology: str
    ) -> Dict[str, Any]:
        """
        Assume breach scenario - analyze lateral movement from compromised asset.
        
        Args:
            compromised_asset: Asset to assume is compromised (e.g., "user workstation")
            network_topology: Network layout and connectivity
        
        Returns:
            Lateral movement paths and privilege escalation opportunities
        """
        target = f"""
ASSUMED BREACH:
Attacker has compromised: {compromised_asset}

NETWORK TOPOLOGY:
{network_topology}

From this compromised position, identify:
1. All lateral movement paths
2. Privilege escalation opportunities
3. High-value targets within reach
4. Data exfiltration paths
"""
        
        user_input = "Assume breach analysis of my network"
        
        result = self.engine.analyze(
            target=target,
            perspectives=[AgentPerspective.SECURITY_ATTACKER],
            context={
                "analysis_type": "assume_breach",
                "initial_compromise": compromised_asset,
                "authorized_pen_test": True
            },
            user_input=user_input
        )
        
        return result
    
    def vulnerability_prioritization(
        self,
        known_vulnerabilities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prioritize known vulnerabilities by exploitation likelihood.
        
        Args:
            known_vulnerabilities: List of known CVEs or vulnerabilities
        
        Returns:
            Prioritized list with exploitation scenarios
        """
        vulns_text = ""
        for i, vuln in enumerate(known_vulnerabilities, 1):
            vulns_text += f"\n{i}. {vuln.get('cve', 'Unknown')}: {vuln.get('description', '')}"
        
        target = f"""
KNOWN VULNERABILITIES:
{vulns_text}

Prioritize these by:
1. Ease of exploitation
2. Impact if exploited
3. Likelihood of active exploitation
4. Available exploit code
"""
        
        user_input = "Prioritize vulnerabilities by exploitation risk"
        
        result = self.engine.analyze(
            target=target,
            perspectives=[AgentPerspective.SECURITY_ATTACKER],
            context={
                "analysis_type": "vulnerability_prioritization",
                "authorized_pen_test": True
            },
            user_input=user_input
        )
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get red team statistics"""
        return {
            "total_scans": len(self.scan_history),
            "engine_stats": self.engine.get_statistics()
        }


# Example usage functions
def example_infrastructure_scan():
    """Example: Red team infrastructure scan"""
    red_team = SecurityRedTeam()
    
    sample_infrastructure = """
    NETWORK TOPOLOGY:
    - DMZ Zone: Web servers (ports 80, 443 open)
    - Internal Zone: Application servers, database servers
    - Admin Zone: Management interfaces, monitoring systems
    
    FIREWALL RULES:
    - DMZ → Internet: Allow outbound HTTP/HTTPS
    - Internal → DMZ: Allow on ports 8080, 3306
    - Admin → Internal: Allow all traffic
    - DMZ → Internal: Allow on port 3306 (database access)
    
    AUTHENTICATION:
    - Web servers: No authentication required
    - Internal services: Basic authentication
    - Admin interfaces: Username/password
    
    PATCHING STATUS:
    - Web servers: Patched within 30 days
    - Internal servers: Patched quarterly
    - Legacy system in admin zone: Unpatched (EOL software)
    """
    
    result = red_team.scan_infrastructure(
        infrastructure_config=sample_infrastructure,
        context={
            "environment": "production",
            "compliance": ["PCI-DSS", "SOC2"]
        }
    )
    
    print(result["formatted_output"])


def example_assume_breach():
    """Example: Assume breach analysis"""
    red_team = SecurityRedTeam()
    
    network = """
    USER WORKSTATIONS
        ↓ (SMB, RDP allowed)
    FILE SERVERS
        ↓ (SQL connection)
    APPLICATION SERVERS
        ↓ (unrestricted)
    DATABASE SERVERS (contains PII, financial data)
        ↓ (admin credentials stored in config files)
    DOMAIN CONTROLLER (full network control)
    """
    
    result = red_team.assume_breach_analysis(
        compromised_asset="User workstation via phishing",
        network_topology=network
    )
    
    print(result["formatted_output"])


if __name__ == "__main__":
    print("AION OS - Security Red Team Demo")
    print("=" * 70)
    print("\nExample 1: Infrastructure Scan")
    print("-" * 70)
    example_infrastructure_scan()
    
    print("\n\nExample 2: Assume Breach Analysis")
    print("-" * 70)
    example_assume_breach()
