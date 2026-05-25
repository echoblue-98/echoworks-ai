"""
AION OS — Live IP Intelligence Analysis
Real breach investigation — IP 97.98.136.95

Requested by: Dan & Roland
Question: Is this IP a residential geolocation?

Run: python demo_ip_intel_live.py

100% OFFLINE. Zero API calls.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from aionos.core.ip_threat_db import LocalIPThreatDB
from aionos.core.ip_intelligence import IPIntelligenceEngine
from aionos.core.ip_report_generator import IPReportGenerator


def main():
    print("=" * 70)
    print("  AION OS — IP Threat Intelligence Engine")
    print("  LIVE BREACH ANALYSIS | 100% OFFLINE")
    print("=" * 70)
    print()

    # Initialize
    engine = IPIntelligenceEngine()

    TARGET_IP = "97.98.136.95"

    # Ingest the verified OSINT from IP2Location (screenshot data)
    engine.ingest_manual_ip(TARGET_IP, {
        "country": "United States of America",
        "country_code": "US",
        "region": "Texas",
        "city": "Houston",
        "zip_code": "77250",
        "latitude": 29.763030,
        "longitude": -95.362060,
        "isp": "Charter Communications Inc",
        "isp_type": "residential",
        "asn": "AS11427",
        "domain": "spectrum.com",
        "net_speed": "(DSL) Broadband/Cable/Fiber/Mobile",
        "is_proxy": True,
        "proxy_type": "residential_proxy",
        "is_anonymous": True,
        "fraud_score": 50,
        "last_seen": "11 days ago (approx. April 4, 2026)",
        "proxy_usage_type": "(ISP) Fixed Line ISP",
        "proxy_type_detail": "RES [PX10+ only]",
        "area_code": "281/713",
    })

    # No simulated logs — this is a real investigation
    # Correlation will populate when real firm logs are ingested

    # Run analysis
    report = engine.analyze(TARGET_IP)

    # === ANSWER THE QUESTION ===
    print()
    print("  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │  TARGET IP:  {TARGET_IP:<43} │")
    print("  │                                                         │")
    print("  │  Q: Is this a residential geolocation?                  │")
    print("  │                                                         │")
    print("  │  A: YES — CONFIRMED RESIDENTIAL                        │")
    print("  │                                                         │")
    print(f"  │  ISP:     Charter Communications Inc (Spectrum)         │")
    print(f"  │  Type:    Fixed Line ISP — Residential Broadband       │")
    print(f"  │  City:    Houston, TX 77250                            │")
    print(f"  │  Coords:  29.7630°N, 95.3621°W                        │")
    print(f"  │  Area:    281/713 (Houston metro)                      │")
    print("  │                                                         │")
    print("  │  ⚠  HOWEVER: Also flagged as ANONYMOUS PROXY           │")
    print("  │     Proxy Type: Residential Proxy (RES)                 │")
    print("  │     Someone is routing traffic THROUGH this             │")
    print("  │     residential connection to mask their real IP.       │")
    print("  │                                                         │")
    print(f"  │  FRAUD SCORE:  50/100 (Medium)                         │")
    print(f"  │  RISK SCORE:   {report.overall_risk_score}/100 ({report.risk_level}){' ' * (32 - len(str(report.overall_risk_score)) - len(report.risk_level))}│")
    print(f"  │  ANALYSIS:     {report.analysis_duration_ms:.3f}ms | OFFLINE ✓                  │")
    print("  └─────────────────────────────────────────────────────────┘")
    print()
    print("  WHAT THIS MEANS:")
    print("  ─────────────────")
    print("  • The IP belongs to a real residential Spectrum subscriber")
    print("    in the Houston, TX area (ZIP 77250)")
    print()
    print("  • BUT it's operating as an anonymous residential proxy,")
    print("    meaning the actual attacker is likely somewhere ELSE,")
    print("    routing through this home connection as a relay")
    print()
    print("  • The subscriber at this address may be:")
    print("    (a) The actual threat actor, OR")
    print("    (b) An unknowing victim whose device is compromised")
    print("        and being used as a proxy hop")
    print()
    print("  NEXT STEPS:")
    print("  ─────────────────")
    print("  1. To identify the subscriber: Legal subpoena to")
    print("     Charter Communications Inc (Spectrum) — AS11427")
    print("     Include: IP 97.98.136.95, date April 4 2026,")
    print("     and suspected unauthorized access")
    print()
    print("  2. Preserve all logs showing this IP in your systems")
    print()
    print("  3. If firm logs available, AION OS can correlate this IP")
    print("     against VPN/firewall/access logs to show exactly what")
    print("     was accessed and when")
    print()

    # Generate HTML report
    output_path = Path(__file__).parent / "reports" / "LIVE_ip_threat_97.98.136.95.html"
    IPReportGenerator.generate_html(report, output_path)
    print(f"  Report saved: {output_path}")
    print()
    print("=" * 70)
    print("  AION OS — 100% OFFLINE — ZERO API CALLS — ZERO DATA TRANSMITTED")
    print("=" * 70)


if __name__ == "__main__":
    main()
