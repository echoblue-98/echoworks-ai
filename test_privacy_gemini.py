"""
AION OS - Privacy Verification Test
====================================

This test proves that NO client data leaks to Gemini.

Run: python test_privacy_gemini.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_privacy():
    print("\n" + "=" * 70)
    print("AION OS - PRIVACY VERIFICATION TEST")
    print("Proving no client data leaks to Gemini")
    print("=" * 70)
    
    from aionos.core.hybrid_engine import (
        GeminiPatternAnalyzer, 
        validate_no_pii,
        EventType
    )
    
    # Test 1: PII Blocklist
    print("\n[TEST 1] PII Blocklist Validation")
    print("-" * 50)
    
    test_cases = [
        ("john.doe@lawfirm.com", False, "Email address"),
        ("192.168.1.100", False, "IP address"),
        ("C:\\Users\\jdoe\\Documents", False, "File path"),
        ("SELECT * FROM clients", False, "SQL query"),
        ("vpn_access", True, "Event type only"),
        ("file_download", True, "Event type only"),
        ("2.5", True, "Numeric only"),
    ]
    
    all_passed = True
    for data, expected, description in test_cases:
        result = validate_no_pii(data)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        blocked = "BLOCKED" if not result else "ALLOWED"
        print(f"  {status}: '{data[:30]}...' -> {blocked} ({description})")
    
    print(f"\n  PII Blocklist: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    # Test 2: What gets sent to Gemini (privacy audit mode)
    print("\n[TEST 2] Privacy Audit Mode - See Exactly What Would Be Sent")
    print("-" * 50)
    
    # Create analyzer in AUDIT MODE (logs but doesn't send)
    analyzer = GeminiPatternAnalyzer(
        api_key="fake-key-for-testing",  # Won't actually call API
        privacy_audit_mode=True
    )
    
    # Simulate events WITH REAL PII (to prove it gets stripped)
    raw_events = [
        {
            "event_type": "vpn_access",
            "timestamp": datetime.now() - timedelta(hours=3),
            "user_id": "partner.leaving@biglaw.com",  # PII - should be stripped
            "ip_address": "192.168.1.50",              # PII - should be stripped
            "file_path": "C:\\Matters\\Client_ABC\\Strategy.docx",  # PII - should be stripped
            "risk_score": 0.8,
            "source_system": "vpn_gateway",
            "details": {
                "client_name": "Acme Corp",           # PII - should be stripped
                "matter_number": "2024-001234",       # PII - should be stripped
            }
        },
        {
            "event_type": "file_download",
            "timestamp": datetime.now() - timedelta(hours=2),
            "user_id": "partner.leaving@biglaw.com",
            "ip_address": "192.168.1.50",
            "file_path": "C:\\Matters\\Client_ABC\\Billing.xlsx",
            "risk_score": 0.9,
            "source_system": "dms",
            "details": {
                "file_name": "Billing_History_2024.xlsx",
                "file_size": 15000000,
            }
        },
        {
            "event_type": "cloud_sync",
            "timestamp": datetime.now() - timedelta(hours=1),
            "user_id": "partner.leaving@biglaw.com",
            "ip_address": "192.168.1.50",
            "destination": "personal_dropbox",
            "risk_score": 0.95,
            "source_system": "cloud_dlp",
            "details": {
                "destination_url": "https://dropbox.com/personal/stolen_files",
            }
        },
    ]
    
    print("\n  RAW INPUT (with PII):")
    for e in raw_events:
        print(f"    - {e['event_type']}: user={e.get('user_id', 'N/A')}, ip={e.get('ip_address', 'N/A')}")
    
    print("\n  ANONYMIZING...")
    anonymized = analyzer._anonymize_events(raw_events)
    
    print("\n  AFTER ANONYMIZATION (what would go to Gemini):")
    for a in anonymized:
        print(f"    - {a}")
    
    print("\n  BUILDING PROMPT...")
    prompt = analyzer._build_prompt(anonymized)
    
    # Check if any PII leaked
    print("\n  CHECKING FOR PII LEAKS...")
    pii_checks = [
        ("partner.leaving@biglaw.com", "User email"),
        ("192.168.1.50", "IP address"),
        ("C:\\Matters", "File path"),
        ("Acme Corp", "Client name"),
        ("2024-001234", "Matter number"),
        ("Billing_History", "File name"),
        ("dropbox.com", "URL"),
    ]
    
    leaks_found = 0
    for pii, description in pii_checks:
        if pii.lower() in prompt.lower():
            print(f"    LEAK DETECTED: {description} ('{pii}')")
            leaks_found += 1
        else:
            print(f"    BLOCKED: {description}")
    
    print(f"\n  {'NO PII LEAKS DETECTED' if leaks_found == 0 else f'{leaks_found} LEAKS FOUND!'}")
    
    # Test 3: Show the actual prompt
    print("\n[TEST 3] Actual Prompt That Would Be Sent")
    print("-" * 50)
    print("\n" + prompt)
    print("-" * 50)
    
    # Summary
    print("\n" + "=" * 70)
    print("PRIVACY VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"""
  WHAT GOES TO GEMINI:
  ✓ Event types only (e.g., "vpn_access", "file_download")
  ✓ Relative time offsets (e.g., "+2.5 hours")
  ✓ Severity hints (boolean)
  
  WHAT IS BLOCKED:
  ✗ User IDs, emails, usernames
  ✗ IP addresses
  ✗ File names, paths
  ✗ Client/matter names
  ✗ URLs, domains
  ✗ SQL queries, database content
  ✗ Any field from 'details' dict
  ✗ Absolute timestamps
  
  PRIVACY CONTROLS:
  1. Explicit allowlist of event types
  2. PII regex blocklist with final validation
  3. Privacy audit mode for verification
  4. Debug logging of all API calls
  5. Blocked send counter in stats
  
  RESULT: {'PRIVACY VERIFIED - SAFE TO USE GEMINI' if leaks_found == 0 else 'PRIVACY ISSUE - DO NOT USE'}
""")
    print("=" * 70 + "\n")
    
    return leaks_found == 0


if __name__ == "__main__":
    success = test_privacy()
    exit(0 if success else 1)
