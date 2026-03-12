#!/usr/bin/env python3
"""
AION Pattern Hunter - Quick extraction workflow
Usage: python hunt.py "paste article text here"
   or: python hunt.py --file article.txt
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from aionos.tools.local_pattern_extractor import LocalPatternExtractor

def hunt(text: str = None, file_path: str = None):
    """Quick pattern extraction"""
    
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    
    if not text:
        print("❌ No text provided")
        print("Usage: python hunt.py --file article.txt")
        print("   or: python hunt.py \"paste article text here\"")
        return
    
    extractor = LocalPatternExtractor()
    result = extractor.extract_from_text(text)
    
    if not result:
        print("❌ Could not extract pattern from text")
        return
    
    # Quick summary
    print("\n" + "="*60)
    print("🎯 PATTERN EXTRACTED")
    print("="*60)
    print(f"📋 Case: {result.case_name}")
    print(f"👤 Attorney: {result.attorney_name}")
    print(f"⚖️  Practice: {result.practice_area}")
    print(f"📅 Years: {result.years_at_firm or 'Unknown'}")
    print(f"➡️  Destination: {result.destination_firm or 'Unknown'}")
    print(f"💰 Revenue at Risk: ${result.revenue_at_risk or 0:,.0f}")
    print(f"👥 Clients Taken: {result.clients_taken or 0}")
    print(f"🚨 Vulnerabilities: {len(result.vulnerabilities)}")
    for v in result.vulnerabilities:
        print(f"   • {v}")
    print(f"📊 Confidence: {int(result.confidence_score * 100)}%")
    print("="*60)
    
    # Ask to save
    if result.confidence_score >= 0.5:
        save = input("\n💾 Save to database? (y/n): ").strip().lower()
        if save == 'y':
            extractor.save_pattern(result)
            print(f"✅ Saved: {result.id}")
            
            # Show current count
            import json
            patterns_file = Path(__file__).parent / "aionos" / "knowledge" / "legal_patterns.json"
            with open(patterns_file, 'r') as f:
                data = json.load(f)
            print(f"📊 Total patterns in database: {len(data.get('patterns', []))}")
    else:
        print("\n⚠️  Low confidence - review manually before saving")
        print("   Use: python -m aionos.api.pattern_cli ingest --file article.txt --local")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--file" and len(sys.argv) > 2:
            hunt(file_path=sys.argv[2])
        else:
            # Treat as pasted text
            hunt(text=" ".join(sys.argv[1:]))
    else:
        # Interactive mode
        print("🎯 AION PATTERN HUNTER")
        print("Paste article text (press Enter twice when done):")
        print("-" * 40)
        lines = []
        while True:
            line = input()
            if line == "":
                if lines and lines[-1] == "":
                    break
            lines.append(line)
        
        text = "\n".join(lines[:-1])  # Remove trailing empty line
        if text.strip():
            hunt(text=text)
        else:
            print("❌ No text provided")
