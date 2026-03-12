"""
Legal Analyzer - Adversarial legal argument analysis

Simulates opposing counsel to find weaknesses in legal arguments,
contracts, briefs, and case strategies.
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


class LegalAnalyzer:
    """
    Adversarial legal analysis module.
    
    Operates as opposing counsel to find:
    - Weak arguments
    - Contradictions in evidence
    - Ambiguous contract language
    - Precedents that undermine the case
    - Procedural vulnerabilities
    """
    
    def __init__(self, intensity: IntensityLevel = IntensityLevel.LEVEL_3_HOSTILE, use_gemini: bool = False):
        self.engine = AdversarialEngine(intensity=intensity)
        self.analysis_history = []
        self.use_gemini = use_gemini
        self.gemini_client = GeminiClient() if use_gemini else None

    def analyze_brief(
        self,
        brief_content: str,
        case_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze a legal brief from opposing counsel's perspective.
        
        Args:
            brief_content: The legal brief text
            case_context: Additional context (jurisdiction, case type, etc.)
        
        Returns:
            A dictionary containing the analysis results.
        """
        if self.use_gemini:
            return self.gemini_client.analyze(brief_content, case_context, self.engine.intensity.value)

        perspectives = [
            AgentPerspective.LEGAL_OPPONENT,
            AgentPerspective.LEGAL_ADVISOR
        ]
        
        result = self.engine.analyze(
            query=brief_content,
            context={
                **(case_context or {}),
                "analysis_type": "legal_brief",
                "use_case_type": "legal_brief"
            },
            perspectives=perspectives
        )
        
        self.analysis_history.append({
            "type": "brief_analysis",
            "timestamp": datetime.utcnow(),
            "result": result
        })
        
        return result
    
    def analyze_contract(
        self,
        contract_content: str,
        party_position: str = "negotiating"
    ) -> Dict[str, Any]:
        """
        Analyze contract language for ambiguities and exploitable terms.
        
        Args:
            contract_content: Contract text
            party_position: 'negotiating', 'plaintiff', or 'defendant'
        
        Returns:
            Analysis with contract vulnerabilities
        """
        
        result = self.engine.analyze(
            query=contract_content,
            context={
                "analysis_type": "contract",
                "party_position": party_position,
                "use_case_type": "legal_contract"
            }
        )
        
        return result
    
    def simulate_cross_examination(
        self,
        witness_statement: str,
        case_theory: str
    ) -> Dict[str, Any]:
        """
        Simulate hostile cross-examination of witness statement.
        
        Args:
            witness_statement: Deposition or testimony
            case_theory: Your case theory that relies on this witness
        
        Returns:
            Potential vulnerabilities in testimony
        """
        combined_target = f"""
CASE THEORY:
{case_theory}

WITNESS STATEMENT:
{witness_statement}
"""
        
        
        result = self.engine.analyze(
            query=combined_target,
            context={
                "analysis_type": "cross_examination",
                "use_case_type": "legal_cross_exam"
            }
        )
        
        return result
    
    def analyze_argument_chain(
        self,
        argument: str,
        supporting_evidence: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze logical argument chain for fallacies and weak links.
        
        Args:
            argument: The legal argument
            supporting_evidence: List of evidence supporting the argument
        
        Returns:
            Logical vulnerabilities and counter-arguments
        """
        supporting_evidence = supporting_evidence or []
        
        target = f"""
ARGUMENT:
{argument}

SUPPORTING EVIDENCE:
"""
        for i, evidence in enumerate(supporting_evidence, 1):
            target += f"\n{i}. {evidence}"
        
        
        result = self.engine.analyze(
            query=argument_chain,
            context={
                "analysis_type": "argument_chain",
                "use_case_type": "legal_argument"
            }
        )
        
        return result
    
    def pre_trial_readiness(
        self,
        case_materials: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Comprehensive pre-trial analysis of all case materials.
        
        Args:
            case_materials: Dict with keys like 'brief', 'evidence', 'witnesses', etc.
        
        Returns:
            Complete adversarial analysis of trial readiness
        """
        # Combine all materials
        combined_target = ""
        for material_type, content in case_materials.items():
            combined_target += f"\n\n=== {material_type.upper()} ===\n{content}"
        
        
        # Use maximum intensity for pre-trial readiness
        original_intensity = self.engine.intensity
        self.engine.set_intensity(IntensityLevel.LEVEL_4_REDTEAM)
        
        result = self.engine.analyze(
            query=combined_target,
            context={
                "analysis_type": "pre_trial_readiness",
                "use_case_type": "legal_trial_prep",
                "comprehensive": True
            }
        )
        
        # Restore original intensity
        self.engine.set_intensity(original_intensity)
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            "total_analyses": len(self.analysis_history),
            "engine_stats": self.engine.get_statistics()
        }


# Example usage functions
def example_brief_analysis():
    """Example: Analyze a legal brief"""
    analyzer = LegalAnalyzer()
    
    sample_brief = """
    ARGUMENT:
    The defendant breached the contract by failing to deliver goods within a reasonable timeframe.
    Clause 5.2 of the agreement states: "Seller shall deliver goods in a reasonable timeframe."
    
    Our client waited 45 days with no delivery, which is clearly unreasonable.
    Therefore, the defendant is in material breach.
    """
    
    result = analyzer.analyze_brief(
        brief_content=sample_brief,
        case_context={
            "jurisdiction": "California",
            "case_type": "Contract Dispute",
            "client_position": "Plaintiff"
        }
    )
    
    print(result["formatted_output"])


def example_contract_analysis():
    """Example: Analyze contract language"""
    analyzer = LegalAnalyzer()
    
    sample_contract = """
    5.2 DELIVERY TERMS
    Seller shall deliver the goods to Buyer in a reasonable timeframe following receipt of payment.
    Buyer agrees that delivery delays due to circumstances beyond Seller's control shall not
    constitute breach.
    """
    
    result = analyzer.analyze_contract(
        contract_content=sample_contract,
        party_position="negotiating"
    )
    
    print(result["formatted_output"])


if __name__ == "__main__":
    print("AION OS - Legal Analyzer Demo")
    print("=" * 70)
    print("\nExample 1: Legal Brief Analysis")
    print("-" * 70)
    example_brief_analysis()
    
    print("\n\nExample 2: Contract Analysis")
    print("-" * 70)
    example_contract_analysis()
