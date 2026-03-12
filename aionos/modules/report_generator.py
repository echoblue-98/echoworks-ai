"""
Professional PDF Report Generator for AION OS

Converts adversarial analysis results into polished, client-ready PDF reports
suitable for enterprise delivery ($10k-$500k engagements).
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import json


class ReportGenerator:
    """Generate professional PDF reports from adversarial analysis results."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles for professional reports."""
        
        # Only add if not already defined
        if 'CustomTitle' not in self.styles:
            # Title style
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        
        if 'Subtitle' not in self.styles:
            # Subtitle style
            self.styles.add(ParagraphStyle(
                name='Subtitle',
                parent=self.styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#666666'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica'
            ))
        
        if 'SectionHeader' not in self.styles:
            # Section header
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold'
            ))
        
        if 'VulnHeader' not in self.styles:
            # Vulnerability header
            self.styles.add(ParagraphStyle(
                name='VulnHeader',
                parent=self.styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#e74c3c'),
                spaceAfter=8,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            ))
        
        if 'ReportBody' not in self.styles:
            # Body text (renamed to avoid conflict)
            self.styles.add(ParagraphStyle(
                name='ReportBody',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#333333'),
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                fontName='Helvetica'
            ))
        
        if 'ExecutiveSummary' not in self.styles:
            # Executive summary
            self.styles.add(ParagraphStyle(
                name='ExecutiveSummary',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=10,
                alignment=TA_JUSTIFY,
                fontName='Helvetica',
                leftIndent=20,
                rightIndent=20,
                backColor=colors.HexColor('#ecf0f1'),
                borderPadding=10
            ))
    
    def generate_report(
        self,
        analysis_result: Dict[str, Any],
        output_path: str,
        report_type: str = "legal",
        customer_name: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> str:
        """
        Generate a professional PDF report from analysis results.
        
        Args:
            analysis_result: Dictionary containing adversarial analysis results
            output_path: Path where PDF should be saved
            report_type: Type of report ("legal", "security", "attorney_departure")
            customer_name: Name of customer/client
            project_name: Name of project/engagement
        
        Returns:
            Path to generated PDF file
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build document content
        story = []
        
        # Cover page
        story.extend(self._create_cover_page(
            report_type, customer_name, project_name
        ))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(analysis_result))
        story.append(PageBreak())
        
        # Detailed findings
        story.extend(self._create_detailed_findings(analysis_result))
        
        # Recommendations
        if 'recommendations' in analysis_result:
            story.append(PageBreak())
            story.extend(self._create_recommendations(analysis_result))
        
        # Appendix
        story.append(PageBreak())
        story.extend(self._create_appendix(analysis_result))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _create_cover_page(
        self,
        report_type: str,
        customer_name: Optional[str],
        project_name: Optional[str]
    ) -> List:
        """Create professional cover page."""
        elements = []
        
        # Spacer to center content
        elements.append(Spacer(1, 2*inch))
        
        # Report title
        title_map = {
            "legal": "Adversarial Legal Analysis Report",
            "security": "Security Red Team Assessment",
            "attorney_departure": "Attorney Departure Risk Analysis"
        }
        title = Paragraph(
            title_map.get(report_type, "Adversarial Analysis Report"),
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Project name
        if project_name:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(
                f"<b>Project:</b> {project_name}",
                self.styles['Subtitle']
            ))
        
        # Customer name
        if customer_name:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(
                f"<b>Prepared for:</b> {customer_name}",
                self.styles['Subtitle']
            ))
        
        # Date
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            datetime.now().strftime("%B %d, %Y"),
            self.styles['Subtitle']
        ))
        
        # Branding
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph(
            "<b>AION OS</b><br/>Adversarial Intelligence & Optimization System",
            self.styles['Subtitle']
        ))
        
        # Confidentiality notice
        elements.append(Spacer(1, 1*inch))
        elements.append(Paragraph(
            "<i>CONFIDENTIAL - This report contains privileged and confidential information. "
            "Unauthorized disclosure is prohibited.</i>",
            ParagraphStyle(
                'Confidential',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#888888'),
                alignment=TA_CENTER
            )
        ))
        
        return elements
    
    def _create_executive_summary(self, result: Dict[str, Any]) -> List:
        """Create executive summary section."""
        elements = []
        
        elements.append(Paragraph(
            "Executive Summary",
            self.styles['SectionHeader']
        ))
        
        # Summary statistics
        stats = self._extract_statistics(result)
        
        summary_text = f"""
        This adversarial analysis engaged {stats['agent_count']} independent 
        adversarial agents to systematically identify vulnerabilities, weaknesses, 
        and potential failure modes. The analysis uncovered {stats['vulnerability_count']} 
        significant findings, with {stats['critical_count']} rated as critical severity.
        """
        
        elements.append(Paragraph(summary_text, self.styles['ExecutiveSummary']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Key metrics table
        metrics_data = [
            ['Metric', 'Value'],
            ['Adversarial Agents', str(stats['agent_count'])],
            ['Total Findings', str(stats['vulnerability_count'])],
            ['Critical Severity', str(stats['critical_count'])],
            ['High Severity', str(stats['high_count'])],
            ['Medium Severity', str(stats['medium_count'])],
            ['Analysis Cost', f"${stats['cost']:.4f}"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(metrics_table)
        
        return elements
    
    def _create_detailed_findings(self, result: Dict[str, Any]) -> List:
        """Create detailed findings section."""
        elements = []
        
        elements.append(Paragraph(
            "Detailed Findings",
            self.styles['SectionHeader']
        ))
        
        # Extract vulnerabilities from each agent
        if 'vulnerabilities' in result:
            vulnerabilities = result['vulnerabilities']
        else:
            # Parse from agent responses
            vulnerabilities = self._extract_vulnerabilities(result)
        
        # Group by severity
        severity_order = ['critical', 'high', 'medium', 'low']
        grouped = {sev: [] for sev in severity_order}
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'medium').lower()
            if severity in grouped:
                grouped[severity].append(vuln)
        
        # Render each severity group
        for severity in severity_order:
            if grouped[severity]:
                elements.extend(self._render_severity_group(severity, grouped[severity]))
        
        return elements
    
    def _render_severity_group(self, severity: str, vulnerabilities: List[Dict]) -> List:
        """Render a group of vulnerabilities by severity."""
        elements = []
        
        # Severity header with color coding
        color_map = {
            'critical': '#c0392b',
            'high': '#e74c3c',
            'medium': '#f39c12',
            'low': '#3498db'
        }
        
        severity_header = Paragraph(
            f"{severity.upper()} Severity Findings ({len(vulnerabilities)})",
            ParagraphStyle(
                f'{severity}_header',
                parent=self.styles['SectionHeader'],
                textColor=colors.HexColor(color_map.get(severity, '#333333'))
            )
        )
        elements.append(severity_header)
        
        # Render each vulnerability
        for i, vuln in enumerate(vulnerabilities, 1):
            vuln_elements = []
            
            # Vulnerability title
            title = vuln.get('title', f'Finding {i}')
            vuln_elements.append(Paragraph(
                f"<b>{i}. {title}</b>",
                self.styles['VulnHeader']
            ))
            
            # Description
            if 'description' in vuln:
                vuln_elements.append(Paragraph(
                    vuln['description'],
                    self.styles['ReportBody']
                ))
            
            # Impact
            if 'impact' in vuln:
                vuln_elements.append(Paragraph(
                    f"<b>Impact:</b> {vuln['impact']}",
                    self.styles['ReportBody']
                ))
            
            # Exploitation scenario
            if 'exploitation' in vuln:
                vuln_elements.append(Paragraph(
                    f"<b>Exploitation Scenario:</b> {vuln['exploitation']}",
                    self.styles['ReportBody']
                ))
            
            # Remediation
            if 'remediation' in vuln:
                vuln_elements.append(Paragraph(
                    f"<b>Remediation:</b> {vuln['remediation']}",
                    self.styles['ReportBody']
                ))
            
            vuln_elements.append(Spacer(1, 0.15*inch))
            
            # Keep vulnerability together on same page
            elements.append(KeepTogether(vuln_elements))
        
        return elements
    
    def _create_recommendations(self, result: Dict[str, Any]) -> List:
        """Create recommendations section."""
        elements = []
        
        elements.append(Paragraph(
            "Recommendations",
            self.styles['SectionHeader']
        ))
        
        recommendations = result.get('recommendations', [])
        
        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(
                f"<b>{i}. {rec.get('title', 'Recommendation')}</b>",
                self.styles['VulnHeader']
            ))
            
            elements.append(Paragraph(
                rec.get('description', ''),
                self.styles['ReportBody']
            ))
            
            if 'priority' in rec:
                elements.append(Paragraph(
                    f"<b>Priority:</b> {rec['priority']}",
                    self.styles['ReportBody']
                ))
            
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_appendix(self, result: Dict[str, Any]) -> List:
        """Create appendix with technical details."""
        elements = []
        
        elements.append(Paragraph(
            "Appendix: Technical Details",
            self.styles['SectionHeader']
        ))
        
        # Agent perspectives used
        elements.append(Paragraph(
            "<b>Adversarial Agent Perspectives</b>",
            self.styles['VulnHeader']
        ))
        
        if 'agents_used' in result:
            for agent in result['agents_used']:
                elements.append(Paragraph(
                    f"• {agent}",
                    self.styles['ReportBody']
                ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Methodology
        elements.append(Paragraph(
            "<b>Methodology</b>",
            self.styles['VulnHeader']
        ))
        
        methodology_text = """
        This analysis employed multi-agent adversarial reasoning powered by 
        Claude Sonnet 4. Each agent independently evaluated the subject from 
        distinct adversarial perspectives (legal, security, business, technical, 
        ethical) to uncover non-obvious failure modes and vulnerabilities.
        """
        
        elements.append(Paragraph(methodology_text, self.styles['ReportBody']))
        
        return elements
    
    def _extract_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key statistics from analysis result."""
        stats = {
            'agent_count': len(result.get('agents_used', [])),
            'vulnerability_count': 0,
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'cost': result.get('cost', 0.0)
        }
        
        vulnerabilities = result.get('vulnerabilities', [])
        if not vulnerabilities:
            vulnerabilities = self._extract_vulnerabilities(result)
        
        stats['vulnerability_count'] = len(vulnerabilities)
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'medium').lower()
            if severity == 'critical':
                stats['critical_count'] += 1
            elif severity == 'high':
                stats['high_count'] += 1
            elif severity == 'medium':
                stats['medium_count'] += 1
        
        return stats
    
    def _extract_vulnerabilities(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract vulnerabilities from agent responses."""
        vulnerabilities = []
        
        # This is a simplified extraction - in production, you'd use
        # more sophisticated parsing of agent responses
        if 'analysis' in result:
            for agent_response in result.get('analysis', []):
                # Parse agent response for vulnerabilities
                # For now, create one entry per agent
                vulnerabilities.append({
                    'title': f"{agent_response.get('agent', 'Agent')} Analysis",
                    'description': agent_response.get('response', '')[:500] + '...',
                    'severity': agent_response.get('severity', 'medium'),
                    'agent': agent_response.get('agent', 'Unknown')
                })
        
        return vulnerabilities


def generate_legal_report(
    analysis_result: Dict[str, Any],
    output_path: str = "legal_analysis_report.pdf",
    **kwargs
) -> str:
    """Convenience function to generate legal analysis report."""
    generator = ReportGenerator()
    return generator.generate_report(
        analysis_result,
        output_path,
        report_type="legal",
        **kwargs
    )


def generate_security_report(
    analysis_result: Dict[str, Any],
    output_path: str = "security_assessment_report.pdf",
    **kwargs
) -> str:
    """Convenience function to generate security report."""
    generator = ReportGenerator()
    return generator.generate_report(
        analysis_result,
        output_path,
        report_type="security",
        **kwargs
    )


def generate_attorney_departure_report(
    analysis_result: Dict[str, Any],
    output_path: str = "attorney_departure_report.pdf",
    **kwargs
) -> str:
    """Convenience function to generate attorney departure report."""
    generator = ReportGenerator()
    return generator.generate_report(
        analysis_result,
        output_path,
        report_type="attorney_departure",
        **kwargs
    )

