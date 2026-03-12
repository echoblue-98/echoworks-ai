"""
Severity Triage - Prioritizes vulnerabilities by criticality

Prevents analysis paralysis by ranking issues P0-P4 and showing
only the most critical items first. Enables progressive disclosure.
"""

from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


class Severity(Enum):
    """Vulnerability severity levels"""
    P0_CRITICAL = "P0_CRITICAL"      # Will cause immediate failure
    P1_HIGH = "P1_HIGH"              # Likely to cause significant problems
    P2_MEDIUM = "P2_MEDIUM"          # Could cause problems
    P3_LOW = "P3_LOW"                # Minor issues
    P4_INFORMATIONAL = "P4_INFORMATIONAL"  # Nice-to-know


@dataclass
class Vulnerability:
    """A single vulnerability/weakness/flaw found by adversarial analysis"""
    
    id: str
    title: str
    description: str
    severity: Severity
    confidence: float  # 0.0-1.0, how confident the AI is this is a real issue
    impact: str
    exploitation_scenario: str
    remediation_steps: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "impact": self.impact,
            "exploitation_scenario": self.exploitation_scenario,
            "remediation_steps": self.remediation_steps,
            "references": self.references,
            "discovered_at": self.discovered_at.isoformat()
        }


class SeverityTriage:
    """
    Triages vulnerabilities by severity and confidence.
    
    Prevents overwhelming users with 50+ issues.
    Shows P0/P1 critical issues first, then progressive disclosure.
    """
    
    def __init__(self, confidence_threshold: float = 0.75):
        """
        Args:
            confidence_threshold: Minimum confidence to show vulnerability (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        self.all_vulnerabilities: List[Vulnerability] = []
    
    def add_vulnerability(self, vuln: Vulnerability):
        """Add a vulnerability to the triage system"""
        self.all_vulnerabilities.append(vuln)
    
    def get_critical_only(self) -> List[Vulnerability]:
        """Get only P0 critical vulnerabilities above confidence threshold"""
        return [
            v for v in self.all_vulnerabilities
            if v.severity == Severity.P0_CRITICAL
            and v.confidence >= self.confidence_threshold
        ]
    
    def get_actionable(self) -> List[Vulnerability]:
        """Get P0 and P1 vulnerabilities (actionable items)"""
        return [
            v for v in self.all_vulnerabilities
            if v.severity in [Severity.P0_CRITICAL, Severity.P1_HIGH]
            and v.confidence >= self.confidence_threshold
        ]
    
    def get_all_by_severity(self) -> Dict[Severity, List[Vulnerability]]:
        """Get all vulnerabilities grouped by severity"""
        grouped: Dict[Severity, List[Vulnerability]] = {
            severity: [] for severity in Severity
        }
        
        for vuln in self.all_vulnerabilities:
            if vuln.confidence >= self.confidence_threshold:
                grouped[vuln.severity].append(vuln)
        
        return grouped
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        by_severity = self.get_all_by_severity()
        
        return {
            "total_found": len(self.all_vulnerabilities),
            "above_confidence_threshold": sum(len(v) for v in by_severity.values()),
            "critical_p0": len(by_severity[Severity.P0_CRITICAL]),
            "high_p1": len(by_severity[Severity.P1_HIGH]),
            "medium_p2": len(by_severity[Severity.P2_MEDIUM]),
            "low_p3": len(by_severity[Severity.P3_LOW]),
            "info_p4": len(by_severity[Severity.P4_INFORMATIONAL]),
            "confidence_threshold": self.confidence_threshold
        }
    
    def format_output(self, max_shown: int = 10, show_all: bool = False) -> str:
        """
        Format vulnerabilities for display.
        
        Args:
            max_shown: Maximum number of vulnerabilities to show initially
            show_all: If True, show all vulnerabilities regardless of max_shown
        
        Returns:
            Formatted string output
        """
        actionable = self.get_actionable()
        summary = self.get_summary()
        
        output = []
        output.append("=" * 70)
        output.append("ADVERSARIAL ANALYSIS RESULTS")
        output.append("=" * 70)
        output.append("")
        
        # Summary
        output.append(f"TOTAL VULNERABILITIES FOUND: {summary['above_confidence_threshold']}")
        output.append(f"  ├─ P0 CRITICAL: {summary['critical_p0']}")
        output.append(f"  ├─ P1 HIGH:     {summary['high_p1']}")
        output.append(f"  ├─ P2 MEDIUM:   {summary['medium_p2']}")
        output.append(f"  ├─ P3 LOW:      {summary['low_p3']}")
        output.append(f"  └─ P4 INFO:     {summary['info_p4']}")
        output.append("")
        
        if not actionable:
            output.append("✓ No critical vulnerabilities found above confidence threshold.")
            output.append("")
            return "\n".join(output)
        
        # Show critical vulnerabilities
        output.append("CRITICAL ISSUES (P0/P1) - FIX THESE FIRST:")
        output.append("-" * 70)
        output.append("")
        
        vulnerabilities_to_show = actionable if show_all else actionable[:max_shown]
        
        for i, vuln in enumerate(vulnerabilities_to_show, 1):
            output.append(f"[{vuln.severity.value}] {vuln.title}")
            output.append(f"Confidence: {vuln.confidence:.0%}")
            output.append(f"")
            output.append(f"DESCRIPTION:")
            output.append(f"  {vuln.description}")
            output.append(f"")
            output.append(f"IMPACT:")
            output.append(f"  {vuln.impact}")
            output.append(f"")
            output.append(f"EXPLOITATION SCENARIO:")
            output.append(f"  {vuln.exploitation_scenario}")
            output.append(f"")
            
            if vuln.remediation_steps:
                output.append(f"REMEDIATION:")
                for step_num, step in enumerate(vuln.remediation_steps, 1):
                    output.append(f"  {step_num}. {step}")
                output.append(f"")
            
            if i < len(vulnerabilities_to_show):
                output.append("-" * 70)
                output.append("")
        
        if len(actionable) > max_shown and not show_all:
            remaining = len(actionable) - max_shown
            output.append(f"... and {remaining} more critical issues.")
            output.append(f"Use show_all=True to see all vulnerabilities.")
            output.append("")
        
        # Recommendation
        output.append("=" * 70)
        output.append("RECOMMENDATION:")
        if summary['critical_p0'] > 0:
            output.append(f"⚠️  You have {summary['critical_p0']} CRITICAL (P0) vulnerabilities.")
            output.append(f"   DO NOT PROCEED until these are fixed.")
        elif summary['high_p1'] > 0:
            output.append(f"⚠️  You have {summary['high_p1']} HIGH (P1) vulnerabilities.")
            output.append(f"   Strongly recommend fixing before proceeding.")
        else:
            output.append(f"✓ No P0/P1 vulnerabilities. Risk profile acceptable.")
        output.append("=" * 70)
        
        return "\n".join(output)
    
    def clear(self):
        """Clear all vulnerabilities"""
        self.all_vulnerabilities.clear()
