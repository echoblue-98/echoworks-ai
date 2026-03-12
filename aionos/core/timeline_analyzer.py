"""
Timeline Breach Analyzer

Maps attack vectors to specific time windows and generates forensic audit checklists.
Shows law firms exactly WHEN and WHERE to look for data exfiltration.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta


class TimelineAnalyzer:
    """
    Analyzes when data exfiltration is most likely to occur
    and generates time-specific forensic audit recommendations.
    """
    
    # Typical departure timeline phases
    PHASES = {
        'pre_notice': {
            'days': (-30, 0),  # 30 days before notice given
            'description': 'Silent preparation phase',
            'risk_level': 'CRITICAL'
        },
        'notice_period': {
            'days': (0, 30),  # 30-day notice period
            'description': 'Active transition phase',
            'risk_level': 'EXTREME'
        },
        'final_week': {
            'days': (23, 30),  # Last 7 days
            'description': 'Last-chance exfiltration window',
            'risk_level': 'MAXIMUM'
        },
        'post_departure': {
            'days': (30, 90),  # First 60 days after leaving
            'description': 'Remote access abuse window',
            'risk_level': 'HIGH'
        }
    }
    
    def __init__(self):
        pass
    
    def analyze_timeline(self, attorney_profile: Dict[str, Any], 
                        vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate timeline-based breach analysis with specific audit windows.
        
        Args:
            attorney_profile: Departing attorney details
            vulnerabilities: Vulnerabilities found by adversarial analysis
            
        Returns:
            Detailed timeline with high-risk windows and forensic checklist
        """
        # Parse departure timeline
        departure_info = self._parse_departure_timeline(attorney_profile)
        
        # Map vulnerabilities to timeline
        timeline_map = self._map_vulnerabilities_to_timeline(vulnerabilities, departure_info)
        
        # Generate high-risk windows
        high_risk_windows = self._identify_high_risk_windows(timeline_map, departure_info)
        
        # Create forensic audit checklist
        forensic_checklist = self._generate_forensic_checklist(timeline_map, departure_info)
        
        # Predict most likely exfiltration methods by phase
        exfiltration_predictions = self._predict_exfiltration_methods(vulnerabilities, departure_info)
        
        return {
            'departure_timeline': departure_info,
            'timeline_map': timeline_map,
            'high_risk_windows': high_risk_windows,
            'forensic_checklist': forensic_checklist,
            'exfiltration_predictions': exfiltration_predictions,
            'critical_audit_dates': self._generate_critical_dates(departure_info),
            'executive_summary': self._generate_timeline_summary(high_risk_windows, departure_info)
        }
    
    def _parse_departure_timeline(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Parse departure timeline from profile"""
        departure_str = profile.get('departure_date', '30 days')
        
        # Extract days (simple parsing)
        if 'day' in departure_str.lower():
            try:
                days = int(''.join(filter(str.isdigit, departure_str)))
            except:
                days = 30  # Default
        else:
            days = 30
        
        today = datetime.now()
        notice_date = today  # Assume notice already given
        departure_date = today + timedelta(days=days)
        
        # Estimate when they likely started planning (30-60 days before notice)
        planning_start = notice_date - timedelta(days=45)
        
        return {
            'planning_start_date': planning_start.strftime('%Y-%m-%d'),
            'notice_given_date': notice_date.strftime('%Y-%m-%d'),
            'departure_date': departure_date.strftime('%Y-%m-%d'),
            'days_until_departure': days,
            'current_phase': self._determine_current_phase(days),
            'timeline_description': f"{days} days from notice to departure"
        }
    
    def _determine_current_phase(self, days_remaining: int) -> str:
        """Determine which phase we're currently in"""
        if days_remaining > 7:
            return 'notice_period'
        elif days_remaining > 0:
            return 'final_week'
        else:
            return 'post_departure'
    
    def _map_vulnerabilities_to_timeline(self, vulnerabilities: List[Dict[str, Any]], 
                                         timeline: Dict[str, Any]) -> Dict[str, List]:
        """Map each vulnerability to the timeline phase when it's most exploitable"""
        timeline_map = {
            'pre_notice': [],
            'notice_period': [],
            'final_week': [],
            'post_departure': []
        }
        
        for vuln in vulnerabilities:
            description = vuln.get('description', '').lower()
            severity = vuln.get('severity', 'medium')
            
            # Map based on attack vector characteristics
            if any(term in description for term in ['email', 'forward', 'cloud storage', 'sync']):
                # These can be set up early and persist
                timeline_map['pre_notice'].append({
                    'vulnerability': vuln.get('title', 'Unknown'),
                    'severity': severity,
                    'window': 'Can be configured 30-60 days before notice',
                    'detection': 'Check email rules, cloud sync settings from past 60 days'
                })
            
            if any(term in description for term in ['access', 'download', 'document', 'data']):
                # Active exfiltration during notice period
                timeline_map['notice_period'].append({
                    'vulnerability': vuln.get('title', 'Unknown'),
                    'severity': severity,
                    'window': 'Bulk downloads during work hours to avoid suspicion',
                    'detection': 'Audit download logs, VPN access, file access patterns'
                })
            
            if any(term in description for term in ['print', 'physical', 'photo', 'usb']):
                # Physical exfiltration in final days
                timeline_map['final_week'].append({
                    'vulnerability': vuln.get('title', 'Unknown'),
                    'severity': severity,
                    'window': 'Physical document removal in final 7 days',
                    'detection': 'Check printer logs, badge swipes during off-hours, photos of screens'
                })
            
            if any(term in description for term in ['client', 'relationship', 'solicitation']):
                # Client poaching after departure
                timeline_map['post_departure'].append({
                    'vulnerability': vuln.get('title', 'Unknown'),
                    'severity': severity,
                    'window': 'Client solicitation within 90 days of departure',
                    'detection': 'Monitor client contact attempts, competitive intelligence'
                })
        
        return timeline_map
    
    def _identify_high_risk_windows(self, timeline_map: Dict[str, List], 
                                    timeline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific date ranges with highest exfiltration risk"""
        windows = []
        
        # Pre-notice window (if we can audit historical data)
        notice_date = datetime.strptime(timeline['notice_given_date'], '%Y-%m-%d')
        pre_notice_start = notice_date - timedelta(days=60)
        pre_notice_end = notice_date
        
        if timeline_map['pre_notice']:
            windows.append({
                'window_name': 'Pre-Notice Setup Phase',
                'date_range': f"{pre_notice_start.strftime('%Y-%m-%d')} to {pre_notice_end.strftime('%Y-%m-%d')}",
                'risk_level': 'CRITICAL',
                'vulnerability_count': len(timeline_map['pre_notice']),
                'description': 'Email forwarding rules and cloud sync likely configured during this window',
                'audit_priority': 'HIGH - Check historical logs for configuration changes'
            })
        
        # Notice period window
        departure_date = datetime.strptime(timeline['departure_date'], '%Y-%m-%d')
        
        if timeline_map['notice_period']:
            windows.append({
                'window_name': 'Active Exfiltration Phase',
                'date_range': f"{notice_date.strftime('%Y-%m-%d')} to {departure_date.strftime('%Y-%m-%d')}",
                'risk_level': 'EXTREME',
                'vulnerability_count': len(timeline_map['notice_period']),
                'description': 'Bulk data downloads, document access spikes expected',
                'audit_priority': 'CRITICAL - Real-time monitoring required'
            })
        
        # Final week (highest risk)
        final_week_start = departure_date - timedelta(days=7)
        
        if timeline_map['final_week'] or timeline['days_until_departure'] <= 7:
            windows.append({
                'window_name': 'Final Week - Maximum Risk',
                'date_range': f"{final_week_start.strftime('%Y-%m-%d')} to {departure_date.strftime('%Y-%m-%d')}",
                'risk_level': 'MAXIMUM',
                'vulnerability_count': len(timeline_map['final_week']),
                'description': 'Physical document theft, after-hours access, rushed exfiltration attempts peak',
                'audit_priority': 'CRITICAL - Daily monitoring, badge swipe tracking, off-hours alerts'
            })
        
        # Post-departure window
        post_departure_end = departure_date + timedelta(days=90)
        
        if timeline_map['post_departure']:
            windows.append({
                'window_name': 'Post-Departure Client Poaching Window',
                'date_range': f"{departure_date.strftime('%Y-%m-%d')} to {post_departure_end.strftime('%Y-%m-%d')}",
                'risk_level': 'HIGH',
                'vulnerability_count': len(timeline_map['post_departure']),
                'description': 'Client solicitation and competitive intelligence gathering',
                'audit_priority': 'MEDIUM - Monitor client communications, track competitive activity'
            })
        
        return windows
    
    def _generate_forensic_checklist(self, timeline_map: Dict[str, List], 
                                    timeline: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate specific forensic audit checklist by timeline phase"""
        checklist = {}
        
        # Pre-notice forensic tasks
        checklist['Historical Audit (Past 60 Days)'] = [
            "Review email forwarding rules configured in past 60 days",
            "Check cloud storage (Dropbox, OneDrive, Google Drive) sync settings changes",
            "Audit external email recipients (personal Gmail, competitor domains)",
            "Review VPN access logs for unusual times (late night, weekends)",
            "Check if personal devices were connected to network",
            "Audit shared folder access patterns for anomalies"
        ]
        
        # Current monitoring tasks
        departure_days = timeline['days_until_departure']
        if departure_days > 7:
            checklist['Active Monitoring (Next 7-30 Days)'] = [
                "Enable real-time alerts for bulk document downloads (>100 files)",
                "Monitor printer logs for high-volume printing",
                "Track file access to client lists, billing data, strategic plans",
                "Set alerts for email attachments to personal/competitor addresses",
                "Review cloud storage upload activity daily",
                "Audit database queries for bulk client data exports"
            ]
        else:
            checklist['Critical Final Week Monitoring'] = [
                "DAILY: Review all file access logs",
                "DAILY: Check badge swipes for after-hours office access",
                "DAILY: Monitor printer logs (especially early AM/late PM)",
                "Alert on ANY external email attachment from attorney's account",
                "Disable VPN access outside business hours",
                "Review office security camera footage for physical document removal",
                "Check mobile device photos (if BYOD policy allows)"
            ]
        
        # Technical forensic tasks
        checklist['IT System Audit'] = [
            "Pull complete email export for forensic review (if legally permissible)",
            "Audit all USB device connections in past 30 days",
            "Check for unauthorized software installations (cloud sync, encrypted drives)",
            "Review browser history for personal cloud storage logins",
            "Audit all shared drive access permissions granted by departing attorney",
            "Check for scheduled email send (delayed delivery to personal email)"
        ]
        
        # Post-departure tasks
        checklist['Post-Departure Monitoring'] = [
            "Immediately disable all system access on departure day",
            "Monitor client communications for unusual contact patterns",
            "Track social media connections (LinkedIn) with firm's clients",
            "Set Google Alerts for attorney's name + client names",
            "Review competitor's website for new hire announcement",
            "Monitor job postings at destination firm for institutional knowledge indicators"
        ]
        
        return checklist
    
    def _predict_exfiltration_methods(self, vulnerabilities: List[Dict[str, Any]], 
                                     timeline: Dict[str, Any]) -> Dict[str, Dict]:
        """Predict most likely exfiltration methods by phase"""
        predictions = {}
        
        days_remaining = timeline['days_until_departure']
        
        # Pre-notice methods (stealth required)
        predictions['Pre-Notice (Stealth Phase)'] = {
            'primary_methods': [
                "Email auto-forwarding rules to personal account",
                "Cloud storage sync (Dropbox, OneDrive) configured to personal folder",
                "Gradual downloads spread over weeks to avoid detection"
            ],
            'probability': '80%',
            'detection_difficulty': 'HIGH - Requires historical log analysis'
        }
        
        # Active notice period methods
        predictions['Notice Period (Active Phase)'] = {
            'primary_methods': [
                "Bulk document downloads during business hours",
                "Email attachments to personal/competitor addresses",
                "Database queries to export client lists",
                "Access to strategic plans, pitch decks, fee structures"
            ],
            'probability': '90%',
            'detection_difficulty': 'MEDIUM - Real-time monitoring can catch'
        }
        
        # Final week methods (desperate/rushed)
        if days_remaining <= 7:
            predictions['Final Week (Urgent Phase)'] = {
                'primary_methods': [
                    "Physical document printing and removal",
                    "Photos of computer screen with mobile phone",
                    "USB drive copying of files",
                    "After-hours office access to print/photograph documents"
                ],
                'probability': '70%',
                'detection_difficulty': 'LOW - Physical evidence, badge swipes'
            }
        
        # Post-departure methods
        predictions['Post-Departure (Client Poaching)'] = {
            'primary_methods': [
                "Direct client solicitation using exfiltrated contact lists",
                "Leveraging insider knowledge of client needs/budgets",
                "Recruiting former colleagues using institutional knowledge"
            ],
            'probability': '60%',
            'detection_difficulty': 'MEDIUM - Requires client communication monitoring'
        }
        
        return predictions
    
    def _generate_critical_dates(self, timeline: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate specific dates requiring elevated monitoring"""
        departure_date = datetime.strptime(timeline['departure_date'], '%Y-%m-%d')
        
        critical_dates = []
        
        # T-7 days
        critical_dates.append({
            'date': (departure_date - timedelta(days=7)).strftime('%Y-%m-%d'),
            'event': 'Final Week Begins',
            'action': 'Escalate monitoring to CRITICAL. Daily log reviews required.'
        })
        
        # T-3 days
        critical_dates.append({
            'date': (departure_date - timedelta(days=3)).strftime('%Y-%m-%d'),
            'event': 'Final 72 Hours',
            'action': 'Disable VPN access outside business hours. Monitor all file access in real-time.'
        })
        
        # T-1 day
        critical_dates.append({
            'date': (departure_date - timedelta(days=1)).strftime('%Y-%m-%d'),
            'event': 'Final Day - Maximum Risk',
            'action': 'Physical presence required. No after-hours access. Escort during packing.'
        })
        
        # Departure day
        critical_dates.append({
            'date': departure_date.strftime('%Y-%m-%d'),
            'event': 'DEPARTURE DAY',
            'action': 'Disable ALL system access immediately. Collect devices. Exit interview.'
        })
        
        # T+1 day
        critical_dates.append({
            'date': (departure_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            'event': 'Post-Departure Day 1',
            'action': 'Verify all access disabled. Begin forensic log analysis. Monitor client contacts.'
        })
        
        return critical_dates
    
    def _generate_timeline_summary(self, windows: List[Dict], timeline: Dict) -> str:
        """Generate executive summary of timeline analysis"""
        days_remaining = timeline['days_until_departure']
        critical_windows = len([w for w in windows if w['risk_level'] in ['CRITICAL', 'EXTREME', 'MAXIMUM']])
        
        if days_remaining <= 7:
            urgency = "IMMEDIATE ACTION REQUIRED - Final week is maximum risk window"
        elif days_remaining <= 14:
            urgency = "URGENT - Approaching high-risk final week"
        else:
            urgency = "HIGH PRIORITY - Implement monitoring now"
        
        return (f"Timeline analysis identifies {critical_windows} critical risk windows over {days_remaining} days. "
                f"{urgency}. Specific forensic audit dates and methods provided above.")
