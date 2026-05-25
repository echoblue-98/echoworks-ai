"""
AION OS — Live IP Threat Intelligence Demo
Analyzes IP 97.98.136.95 from Roland's breach case.

Run: python demo_ip_intel.py

100% OFFLINE. Zero API calls. Runs with WiFi off.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from aionos.core.ip_threat_db import LocalIPThreatDB, ProxyType, ISPType
from aionos.core.ip_intelligence import IPIntelligenceEngine, AccessEvent, AccessType
from aionos.core.ip_report_generator import IPReportGenerator


def main():
    print("=" * 70)
    print("  AION OS — IP Threat Intelligence Engine")
    print("  100% OFFLINE | Zero API Calls | Zero Cloud Dependencies")
    print("=" * 70)
    print()

    # =========================================================================
    # STEP 1: Initialize engine
    # =========================================================================
    print("[1/5] Initializing IP Intelligence Engine...")
    engine = IPIntelligenceEngine()
    db_stats = engine.threat_db.get_stats()
    print(f"       Local DB: {db_stats['cidr_ranges']} CIDR ranges, "
          f"{db_stats['known_proxy_domains']} proxy domains")
    print()

    # =========================================================================
    # STEP 2: Ingest the manual OSINT from IP2Location screenshot
    # =========================================================================
    TARGET_IP = "97.98.136.95"
    
    print(f"[2/5] Ingesting field intelligence for {TARGET_IP}...")
    
    # This is the data from Roland's IP2Location screenshot
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
    print(f"       ✓ Houston, TX | Charter/Spectrum | Anonymous Residential Proxy")
    print()

    # =========================================================================
    # STEP 3: Ingest simulated firm access logs for correlation
    # (In production, these come from real VPN/firewall/app logs)
    # =========================================================================
    print("[3/5] Ingesting firm access logs for correlation...")
    
    sample_events = [
        AccessEvent(
            timestamp="2026-04-04 02:17:33",
            ip_address=TARGET_IP,
            user="unknown",
            access_type=AccessType.VPN_LOGIN,
            resource="firm-vpn-gateway",
            bytes_transferred=0,
            success=True,
            details="VPN connection established from flagged IP"
        ),
        AccessEvent(
            timestamp="2026-04-04 02:19:45",
            ip_address=TARGET_IP,
            user="unknown",
            access_type=AccessType.FILE_SERVER,
            resource="\\\\fileserver\\client-matters\\active",
            bytes_transferred=45_000_000,
            success=True,
            details="Bulk access to active client matter directories"
        ),
        AccessEvent(
            timestamp="2026-04-04 02:34:12",
            ip_address=TARGET_IP,
            user="unknown",
            access_type=AccessType.DATABASE_QUERY,
            resource="billing-db: SELECT * FROM client_accounts",
            bytes_transferred=12_000_000,
            success=True,
            details="Full table export of client billing records"
        ),
        AccessEvent(
            timestamp="2026-04-04 02:41:58",
            ip_address=TARGET_IP,
            user="unknown",
            access_type=AccessType.EXTERNAL_TRANSFER,
            resource="cloud-upload: file-share.io/upload",
            bytes_transferred=67_000_000,
            success=True,
            details="Large data upload to external file sharing service"
        ),
    ]
    
    engine.ingest_access_logs(sample_events)
    print(f"       ✓ {len(sample_events)} access events ingested")
    print()

    # =========================================================================
    # STEP 4: Run analysis
    # =========================================================================
    print(f"[4/5] Analyzing {TARGET_IP}...")
    print()
    
    report = engine.analyze(TARGET_IP)
    
    # Print console summary
    print("  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │  TARGET: {report.target_ip:<47} │")
    print(f"  │  RISK:   {report.risk_level:<47} │")
    print(f"  │  SCORE:  {report.overall_risk_score}/100{' ' * 42}│")
    print(f"  │  TIME:   {report.analysis_duration_ms:.3f}ms{' ' * 39}│")
    print(f"  │  MODE:   {'OFFLINE ✓' if report.offline_mode else 'ONLINE':<47} │")
    print("  └─────────────────────────────────────────────────────────┘")
    print()

    # Key findings
    print("  KEY FINDINGS:")
    ip = report.ip_record
    if ip:
        print(f"    • Location: {ip.city}, {ip.region} ({ip.country_code})")
        print(f"    • ISP: {ip.isp} ({ip.domain})")
        print(f"    • Proxy: {'YES — ' + ip.proxy_type.value.replace('_', ' ').upper() if ip.is_proxy else 'NO'}")
        print(f"    • Anonymous: {'YES' if ip.is_anonymous else 'NO'}")
        print(f"    • Threat Score: {ip.threat_score}/100")
        if ip.threat_reasons:
            for reason in ip.threat_reasons:
                print(f"    ⚠ {reason}")
    print()

    # Correlation
    if report.correlation and report.correlation.event_count > 0:
        c = report.correlation
        print("  INTERNAL CORRELATION:")
        print(f"    • {c.event_count} matching access events")
        print(f"    • {len(c.unique_users)} user(s): {', '.join(c.unique_users)}")
        print(f"    • Data volume: {c.total_bytes / 1_000_000:.1f} MB")
        print(f"    • Activity: {', '.join(c.access_types)}")
        for note in c.correlation_notes:
            print(f"    ⚠ {note}")
        print()

    # Recommendations
    print("  RECOMMENDATIONS:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"    {i}. {rec}")
    print()

    # =========================================================================
    # STEP 5: Generate HTML report
    # =========================================================================
    output_path = Path(__file__).parent / "reports" / "ip_threat_report_97.98.136.95.html"
    
    print(f"[5/5] Generating professional HTML report...")
    
    generator = IPReportGenerator()
    generator.generate_html(report, output_path)
    
    print(f"       ✓ Report saved: {output_path}")
    print()
    print("=" * 70)
    print("  ANALYSIS COMPLETE — 100% OFFLINE — ZERO API CALLS")
    print("=" * 70)

    return report


if __name__ == "__main__":
    main()
