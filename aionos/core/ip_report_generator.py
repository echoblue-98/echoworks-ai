"""
AION OS — IP Threat Intelligence Report Generator
Produces professional HTML reports from IP intelligence analysis.
100% OFFLINE. Zero external dependencies.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from aionos.core.ip_intelligence import IPIntelReport
from aionos.core.ip_threat_db import ThreatCategory, ProxyType, ISPType


class IPReportGenerator:
    """Generate professional HTML threat reports from IP analysis."""

    @staticmethod
    def generate_html(report: IPIntelReport, output_path: Optional[Path] = None) -> str:
        """Generate a complete HTML threat report."""
        
        ip = report.ip_record
        corr = report.correlation
        
        # Risk level colors
        risk_colors = {
            "CRITICAL": "#e74c3c",
            "HIGH": "#e67e22",
            "MEDIUM": "#f39c12",
            "LOW": "#3498db",
            "INFORMATIONAL": "#2ecc71",
            "UNKNOWN": "#95a5a6",
        }
        risk_color = risk_colors.get(report.risk_level, "#95a5a6")
        
        # Threat category badge
        threat_badges = {
            ThreatCategory.CRITICAL: ("CRITICAL", "#e74c3c"),
            ThreatCategory.HIGH_RISK: ("HIGH RISK", "#e67e22"),
            ThreatCategory.MEDIUM_RISK: ("MEDIUM RISK", "#f39c12"),
            ThreatCategory.LOW_RISK: ("LOW RISK", "#3498db"),
            ThreatCategory.CLEAN: ("CLEAN", "#2ecc71"),
            ThreatCategory.KNOWN_MALICIOUS: ("KNOWN MALICIOUS", "#c0392b"),
        }
        
        threat_label, threat_color = threat_badges.get(
            ip.threat_category if ip else ThreatCategory.CLEAN,
            ("UNKNOWN", "#95a5a6")
        )
        
        # Proxy info
        proxy_html = ""
        if ip and ip.is_proxy:
            proxy_type_display = ip.proxy_type.value.replace("_", " ").upper()
            proxy_html = f"""
            <div class="alert-box critical">
                <div class="alert-icon">&#9888;</div>
                <div class="alert-content">
                    <strong>ANONYMOUS PROXY DETECTED</strong><br>
                    Type: {proxy_type_display}<br>
                    This IP is deliberately obfuscating the true origin of traffic.
                    {"Residential proxy pattern suggests a compromised device being used as a relay." if ip.proxy_type == ProxyType.RESIDENTIAL_PROXY else ""}
                </div>
            </div>
            """
        
        # Threat reasons
        reasons_html = ""
        if ip and ip.threat_reasons:
            reasons_items = "".join(
                f'<li class="threat-reason">{r}</li>' for r in ip.threat_reasons
            )
            reasons_html = f"""
            <div class="section">
                <h3>Threat Indicators</h3>
                <ul class="threat-list">{reasons_items}</ul>
            </div>
            """
        
        # Correlation section
        correlation_html = ""
        if corr:
            if corr.event_count > 0:
                events_rows = ""
                for e in corr.matching_events[:20]:  # Cap at 20 for readability
                    events_rows += f"""
                    <tr>
                        <td>{e.timestamp}</td>
                        <td>{e.user or 'N/A'}</td>
                        <td>{e.access_type.value}</td>
                        <td>{e.resource or 'N/A'}</td>
                        <td>{e.bytes_transferred:,} bytes</td>
                    </tr>
                    """
                
                notes_items = "".join(
                    f'<li class="correlation-note">{n}</li>' for n in corr.correlation_notes
                )
                
                correlation_html = f"""
                <div class="section">
                    <h3>Internal Activity Correlation</h3>
                    <div class="stat-grid">
                        <div class="stat-card">
                            <div class="stat-value">{corr.event_count}</div>
                            <div class="stat-label">Matching Events</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{len(corr.unique_users)}</div>
                            <div class="stat-label">Users Identified</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{corr.total_bytes / 1_000_000:.1f} MB</div>
                            <div class="stat-label">Data Transferred</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{len(corr.access_types)}</div>
                            <div class="stat-label">Access Types</div>
                        </div>
                    </div>
                    {f'<ul class="notes-list">{notes_items}</ul>' if notes_items else ''}
                    <table class="events-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>User</th>
                                <th>Access Type</th>
                                <th>Resource</th>
                                <th>Data Volume</th>
                            </tr>
                        </thead>
                        <tbody>{events_rows}</tbody>
                    </table>
                    {f'<p class="timeline-range">Activity window: {corr.first_seen_internal} — {corr.last_seen_internal}</p>' if corr.first_seen_internal else ''}
                </div>
                """
            else:
                correlation_html = """
                <div class="section">
                    <h3>Internal Activity Correlation</h3>
                    <p class="no-data">No matching events found in ingested firm access logs. 
                    Ingest VPN, firewall, and application logs to enable correlation.</p>
                </div>
                """
        
        # Recommendations
        recs_html = ""
        if report.recommendations:
            recs_items = ""
            for i, rec in enumerate(report.recommendations, 1):
                priority = "high" if rec.startswith("IMMEDIATE") else "normal"
                recs_items += f'<li class="rec-item {priority}"><span class="rec-num">{i}</span> {rec}</li>'
            recs_html = f"""
            <div class="section">
                <h3>Recommendations</h3>
                <ol class="rec-list">{recs_items}</ol>
            </div>
            """
        
        # IOCs
        iocs_html = ""
        if report.iocs:
            iocs_items = "".join(f'<li class="ioc-item"><code>{ioc}</code></li>' for ioc in report.iocs)
            iocs_html = f"""
            <div class="section">
                <h3>Indicators of Compromise (IOCs)</h3>
                <ul class="ioc-list">{iocs_items}</ul>
            </div>
            """
        
        # Full HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AION OS — IP Threat Intelligence Report: {report.target_ip}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 24px;
        }}
        
        /* Header */
        .report-header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #1a1a2e;
            margin-bottom: 32px;
        }}
        
        .logo {{
            font-size: 14px;
            letter-spacing: 4px;
            color: #00d4ff;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        
        .report-title {{
            font-size: 28px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }}
        
        .report-subtitle {{
            font-size: 14px;
            color: #888;
        }}
        
        .classification {{
            display: inline-block;
            background: rgba(231, 76, 60, 0.15);
            color: #e74c3c;
            padding: 4px 16px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 16px;
        }}
        
        /* Risk Banner */
        .risk-banner {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 24px;
            background: rgba({','.join(str(int(risk_color.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4))}, 0.1);
            border: 1px solid {risk_color}40;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 32px;
        }}
        
        .risk-score {{
            font-size: 64px;
            font-weight: 800;
            color: {risk_color};
            line-height: 1;
        }}
        
        .risk-details {{
            text-align: left;
        }}
        
        .risk-level {{
            font-size: 24px;
            font-weight: 700;
            color: {risk_color};
            text-transform: uppercase;
        }}
        
        .risk-label {{ color: #888; font-size: 13px; }}
        
        /* Alert Box */
        .alert-box {{
            display: flex;
            gap: 16px;
            padding: 16px 20px;
            border-radius: 6px;
            margin-bottom: 24px;
        }}
        
        .alert-box.critical {{
            background: rgba(231, 76, 60, 0.1);
            border-left: 4px solid #e74c3c;
        }}
        
        .alert-icon {{ font-size: 24px; }}
        .alert-content {{ font-size: 14px; line-height: 1.6; }}
        .alert-content strong {{ color: #e74c3c; }}
        
        /* Section */
        .section {{
            background: #12121a;
            border: 1px solid #1a1a2e;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        
        .section h3 {{
            font-size: 16px;
            color: #00d4ff;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #1a1a2e;
        }}
        
        /* IP Details Grid */
        .ip-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        
        .ip-field {{
            display: flex;
            justify-content: space-between;
            padding: 8px 12px;
            background: #0a0a0f;
            border-radius: 4px;
        }}
        
        .ip-field-label {{ color: #888; font-size: 13px; }}
        .ip-field-value {{ color: #fff; font-weight: 600; font-size: 13px; }}
        .ip-field-value.highlight {{ color: #e74c3c; }}
        .ip-field-value.safe {{ color: #2ecc71; }}
        
        /* Stats Grid */
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }}
        
        .stat-card {{
            text-align: center;
            padding: 16px 8px;
            background: #0a0a0f;
            border-radius: 6px;
            border: 1px solid #1a1a2e;
        }}
        
        .stat-value {{
            font-size: 28px;
            font-weight: 800;
            color: #00d4ff;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }}
        
        /* Tables */
        .events-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            font-size: 13px;
        }}
        
        .events-table th {{
            background: #0a0a0f;
            padding: 10px 12px;
            text-align: left;
            color: #888;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 1px;
        }}
        
        .events-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #1a1a2e;
            color: #ccc;
        }}
        
        .events-table tr:hover td {{
            background: rgba(0, 212, 255, 0.05);
        }}
        
        /* Lists */
        .threat-list, .rec-list, .ioc-list, .notes-list {{
            list-style: none;
            padding: 0;
        }}
        
        .threat-reason, .correlation-note {{
            padding: 8px 12px;
            margin-bottom: 6px;
            background: rgba(231, 76, 60, 0.08);
            border-left: 3px solid #e74c3c;
            border-radius: 0 4px 4px 0;
            font-size: 14px;
        }}
        
        .rec-item {{
            padding: 10px 12px 10px 48px;
            margin-bottom: 8px;
            background: #0a0a0f;
            border-radius: 4px;
            font-size: 14px;
            position: relative;
        }}
        
        .rec-item.high {{
            border-left: 3px solid #e74c3c;
            background: rgba(231, 76, 60, 0.05);
        }}
        
        .rec-num {{
            position: absolute;
            left: 12px;
            top: 10px;
            color: #00d4ff;
            font-weight: 700;
            font-size: 14px;
        }}
        
        .ioc-item {{
            padding: 6px 12px;
            margin-bottom: 4px;
        }}
        
        .ioc-item code {{
            background: #0a0a0f;
            padding: 2px 8px;
            border-radius: 3px;
            font-family: 'Fira Code', 'Consolas', monospace;
            color: #f39c12;
            font-size: 13px;
        }}
        
        .no-data {{
            color: #666;
            font-style: italic;
            padding: 16px;
            text-align: center;
        }}
        
        .timeline-range {{
            color: #888;
            font-size: 12px;
            margin-top: 12px;
            text-align: right;
        }}
        
        /* Summary */
        .summary-text {{
            font-size: 15px;
            line-height: 1.8;
            color: #ccc;
            padding: 8px 0;
        }}
        
        /* Footer */
        .report-footer {{
            text-align: center;
            padding: 32px 0;
            border-top: 1px solid #1a1a2e;
            margin-top: 32px;
        }}
        
        .footer-badge {{
            display: inline-block;
            background: #12121a;
            border: 1px solid #1a1a2e;
            padding: 8px 20px;
            border-radius: 4px;
            font-size: 12px;
            color: #888;
            letter-spacing: 1px;
        }}
        
        .footer-badge span {{ color: #00d4ff; }}
        
        .footer-meta {{
            font-size: 11px;
            color: #555;
            margin-top: 12px;
        }}
        
        @media print {{
            body {{ background: #fff; color: #333; }}
            .section {{ border-color: #ddd; background: #fafafa; }}
            .risk-banner {{ border-color: #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <div class="logo">AION OS</div>
            <div class="report-title">IP Threat Intelligence Report</div>
            <div class="report-subtitle">Target: {report.target_ip} | Generated: {report.analysis_timestamp[:19]}</div>
            <div class="classification">CONFIDENTIAL — AUTHORIZED RECIPIENTS ONLY</div>
        </div>
        
        <!-- Risk Banner -->
        <div class="risk-banner">
            <div class="risk-score">{report.overall_risk_score}</div>
            <div class="risk-details">
                <div class="risk-level">{report.risk_level} RISK</div>
                <div class="risk-label">Overall Threat Assessment</div>
            </div>
        </div>
        
        {proxy_html}
        
        <!-- Executive Summary -->
        <div class="section">
            <h3>Executive Summary</h3>
            <p class="summary-text">{report.executive_summary}</p>
        </div>
        
        <!-- IP Details -->
        <div class="section">
            <h3>IP Intelligence</h3>
            <div class="ip-grid">
                <div class="ip-field">
                    <span class="ip-field-label">IP Address</span>
                    <span class="ip-field-value">{ip.ip if ip else 'N/A'}</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">Location</span>
                    <span class="ip-field-value">{ip.city if ip else 'N/A'}, {ip.region if ip else 'N/A'} ({ip.country_code if ip else 'N/A'})</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">ISP</span>
                    <span class="ip-field-value">{ip.isp if ip else 'N/A'}</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">ISP Type</span>
                    <span class="ip-field-value">{ip.isp_type.value.upper() if ip else 'N/A'}</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">ASN</span>
                    <span class="ip-field-value">{ip.asn if ip else 'N/A'}</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">Domain</span>
                    <span class="ip-field-value">{ip.domain if ip else 'N/A'}</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">Anonymous Proxy</span>
                    <span class="ip-field-value {'highlight' if ip and ip.is_anonymous else 'safe'}">{'YES' if ip and ip.is_anonymous else 'NO'}</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">Proxy Type</span>
                    <span class="ip-field-value {'highlight' if ip and ip.is_proxy else ''}">
                        {ip.proxy_type.value.replace('_', ' ').upper() if ip and ip.is_proxy else 'NONE'}
                    </span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">Threat Score</span>
                    <span class="ip-field-value">{ip.threat_score if ip else 0}/100</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">Threat Category</span>
                    <span class="ip-field-value" style="color: {threat_color}">{threat_label}</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">Net Speed</span>
                    <span class="ip-field-value">{ip.net_speed if ip and ip.net_speed else 'N/A'}</span>
                </div>
                <div class="ip-field">
                    <span class="ip-field-label">ZIP Code</span>
                    <span class="ip-field-value">{ip.zip_code if ip and ip.zip_code else 'N/A'}</span>
                </div>
            </div>
        </div>
        
        {reasons_html}
        {correlation_html}
        {recs_html}
        {iocs_html}
        
        <!-- Footer -->
        <div class="report-footer">
            <div class="footer-badge">
                <span>AION OS</span> — IP Intelligence Engine v{report.engine_version} | 100% OFFLINE
            </div>
            <div class="footer-meta">
                Analysis completed in {report.analysis_duration_ms:.1f}ms | No external API calls | No data transmitted
            </div>
        </div>
    </div>
</body>
</html>"""
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")
        
        return html
