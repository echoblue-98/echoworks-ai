"""
Enrich Typhoon pattern with court document data and Cloudflare integration.
"""
import json
from pathlib import Path
from datetime import datetime

patterns_file = Path('aionos/knowledge/legal_patterns.json')
with open(patterns_file, 'r') as f:
    db = json.load(f)

# Create the enriched Typhoon pattern from court document
enriched_pattern = {
    "id": "pattern_typhoon_001_enriched",
    "case_name": "Typhoon Advertising v. Michael Knowles, Sarah Trevino, et al.",
    "case_number": "2:21-cv-00194-NDF (D. Wyo.)",
    "court": "United States District Court, District of Wyoming",
    "date_filed": "2021-10-06",
    "date_amended": "2022-08-02",
    "date_terminated": "2025-01-16",
    "litigation_duration_months": 39,
    
    "parties": {
        "plaintiff": "Typhoon Advertising (Wyoming corporation)",
        "plaintiff_principal": "Dan Eisele, President and CEO",
        "plaintiff_counsel": ["Hathaway & Kunz, LLP", "Davis & Cannon, LLP"],
        "defendant_1": {
            "name": "Michael Knowles",
            "location": "Katy, Texas",
            "role": "Former VP Client Services, Shareholder, Officer, Director",
            "tenure": "March 2017 - June 25, 2020"
        },
        "defendant_2": {
            "name": "Sarah Trevino",
            "location": "Oklahoma City, Oklahoma",
            "role": "Co-conspirator, Contractor"
        },
        "john_jane_does": "Does 2-10 (unknown co-conspirators)"
    },
    
    "vulnerability_type": "Insider Threat - Long-term Infiltration with Planned Sabotage",
    "industry": "Marketing/Advertising Agency",
    
    "attack_phases": {
        "phase_1_infiltration": {
            "timeframe": "March 2017",
            "description": "Knowles joined as contractor with pre-planned malicious intent",
            "evidence": [
                "Possessed replacement hard drives BEFORE or DURING onboarding",
                "Communicated with co-conspirators (Trevino) during Spring 2017 about planned actions",
                "Never intended legitimate employment - fraudulent from day one"
            ]
        },
        "phase_2_trust_building": {
            "timeframe": "2017-2019",
            "description": "Earned trust, promoted to shareholder/officer/director",
            "access_gained": [
                "Full access to company email and domains",
                "Vendor account credentials",
                "Customer relationship access",
                "Financial institution communications",
                "All cyber properties of company"
            ]
        },
        "phase_3_inside_attack": {
            "timeframe": "2019-2020",
            "description": "Active sabotage while maintaining insider position",
            "actions": [
                "Damaged customer and vendor relationships",
                "Made material misrepresentations to financial institutions",
                "Impersonated other employees in vendor communications",
                "Shared company passwords with external co-conspirators",
                "Used sophisticated home server hardware for attacks",
                "Used SPOOFED IP ADDRESSES to access company systems",
                "Spied on company from inside to coordinate with outside co-conspirators"
            ]
        },
        "phase_4_departure_destruction": {
            "date": "June 25, 2020",
            "description": "Resignation followed by evidence destruction",
            "actions": [
                "Resigned but refused to return laptops (held hostage for share payment)",
                "DESTROYED 5.8 MILLION FILES from company laptop",
                "Replaced original Dell hard drives with KNOCK-OFF drives",
                "Wiped all work product from both company laptops",
                "Returned sanitized laptops September 2, 2020 (68 days later)"
            ]
        },
        "phase_5_post_departure": {
            "timeframe": "July 2020+",
            "description": "Continued unauthorized access after leaving",
            "actions": [
                "Accessed company email WITHOUT AUTHORIZATION",
                "DELETED company emails containing valuable information",
                "Used spoofed IP addresses to mask access",
                "Coordinated ongoing attacks with Trevino and Does"
            ]
        }
    },
    
    "legal_claims": [
        {"count": "I", "claim": "Tortious Interference", "basis": "Sabotaged customer/vendor relationships"},
        {"count": "II", "claim": "Fraudulent Misrepresentation", "basis": "Never intended legitimate employment"},
        {"count": "III", "claim": "Breach of Fiduciary Duty", "basis": "As officer/director, worked against company"},
        {"count": "IV", "claim": "Computer Fraud and Abuse Act (CFAA)", "basis": "Unauthorized access, 5.8M files destroyed"},
        {"count": "V", "claim": "Trade Secret Misappropriation", "basis": "Stole company data and shared externally"},
        {"count": "VI", "claim": "Civil Conspiracy", "basis": "Coordinated with Trevino and Does"},
        {"count": "VII", "claim": "Civil RICO", "basis": "Pattern of racketeering over multiple years"}
    ],
    
    "damages": {
        "claimed_minimum": 75000,
        "actual_estimated": "Millions - lost clients, financing opportunity, 39 months litigation",
        "litigation_cost": "39 months federal litigation",
        "jury_demand": True
    },
    
    "detection_failures": [
        {
            "failure": "No detection of replacement hard drives",
            "what_aion_would_catch": "USB/storage device anomaly detection",
            "detection_window": "Day 1"
        },
        {
            "failure": "Password sharing with external parties undetected",
            "what_aion_would_catch": "Credential sharing pattern in email/comms",
            "detection_window": "Real-time"
        },
        {
            "failure": "Spoofed IP access not flagged",
            "what_aion_would_catch": "VPN/Geo anomaly detection - impossible travel",
            "detection_window": "Real-time"
        },
        {
            "failure": "5.8M file deletion not caught",
            "what_aion_would_catch": "Bulk deletion/access pattern alert",
            "detection_window": "Same day"
        },
        {
            "failure": "Post-departure email access allowed",
            "what_aion_would_catch": "Credential revocation enforcement",
            "detection_window": "Should be impossible"
        },
        {
            "failure": "Email deletion after resignation",
            "what_aion_would_catch": "Audit log alerts on data destruction",
            "detection_window": "Real-time"
        }
    ],
    
    "cloudflare_integration": {
        "note": "Client uses Cloudflare for security infrastructure",
        "relevant_signals": [
            "Cloudflare Access logs for VPN/Zero Trust",
            "DNS query patterns (data exfiltration via DNS)",
            "WAF alerts for unusual API access",
            "Geographic anomalies in access patterns",
            "Bot detection for automated scraping",
            "Rate limiting violations"
        ],
        "aion_connector_needed": "CloudflareConnector",
        "api_endpoints": [
            "Cloudflare Zero Trust Access logs",
            "Cloudflare Gateway DNS logs",
            "Cloudflare Audit logs",
            "Cloudflare Analytics API"
        ],
        "detection_capabilities": [
            "Impossible travel detection via Access logs",
            "Data exfiltration via DNS tunneling",
            "Unusual access patterns post-departure",
            "Geographic anomaly from spoofed IPs",
            "Credential stuffing/brute force detection"
        ]
    },
    
    "key_evidence": {
        "home_server": "Knowles used sophisticated server hardware at home for attacks",
        "ip_spoofing": "Used impersonated/spoofed IP addresses",
        "file_destruction": "5.8 million files destroyed",
        "hard_drive_swap": "Original Dell drives replaced with knock-offs",
        "communication_trail": "Coordinated with Trevino via email/messaging for over a year",
        "laptop_delay": "68 days between resignation and laptop return"
    },
    
    "lessons_learned": [
        "Insider threats can be PLANNED from day one - not just disgruntled employees",
        "Trust building over years can mask malicious intent",
        "Officers/directors have maximum access - maximum risk",
        "Hard drive swaps indicate premeditation and forensic awareness",
        "IP spoofing suggests technical sophistication",
        "Post-departure access must be IMPOSSIBLE, not just monitored",
        "39 months litigation = detection failure cost multiplied 1000x",
        "Laptop retention is a red flag - immediate escalation required"
    ],
    
    "aion_application": [
        "Flag hardware changes (USB, drives) especially at onboarding",
        "Monitor for spoofed/VPN IP patterns that do not match baseline",
        "Alert on credential sharing patterns",
        "Track bulk file operations (delete, copy, download)",
        "IMMEDIATE credential revocation on departure",
        "Post-departure access = CRITICAL alert, not info",
        "Pattern match against this case for advertising/marketing clients",
        "Integrate with Cloudflare for complete visibility"
    ],
    
    "status": "VALIDATED_FROM_COURT_DOCUMENT",
    "confidence_score": 0.99,
    "source": {
        "document": "First Amended Complaint (w Jury Demand)",
        "filing_date": "2022-08-02",
        "docket_number": 39,
        "file_hash": "e71e175767b59e6b",
        "pages": 22
    },
    "founder_case": True,
    "enriched_date": datetime.now().isoformat()
}

# Update the original pattern with new data
for i, p in enumerate(db['patterns']):
    if p['id'] == 'pattern_typhoon_001':
        db['patterns'][i]['status'] = 'SUPERSEDED_BY_ENRICHED'
        db['patterns'][i]['superseded_by'] = 'pattern_typhoon_001_enriched'
        break

# Remove the auto-ingested pattern (less detailed)
db['patterns'] = [p for p in db['patterns'] if p.get('id') != 'pattern_e71e175767b59e6b']

# Add enriched pattern at the top
db['patterns'].insert(0, enriched_pattern)

# Update metadata
db['metadata']['last_updated'] = datetime.now().isoformat()
db['metadata']['total_patterns'] = len(db['patterns'])

# Save
with open(patterns_file, 'w') as f:
    json.dump(db, f, indent=2)

print('✅ PATTERN DATABASE UPDATED')
print(f'   Total Patterns: {len(db["patterns"])}')
print('   Enriched Typhoon pattern: pattern_typhoon_001_enriched')
print('   Cloudflare integration notes: ADDED')
print('')
print('🔒 100% LOCAL - Zero cloud calls')
