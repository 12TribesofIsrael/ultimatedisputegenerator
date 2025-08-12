#!/usr/bin/env python3
"""Debug script to examine APPLE CARD extraction"""

import fitz
import re
from extract_account_details import extract_account_details

def debug_apple_card():
    # Extract text from Experian PDF
    doc = fitz.open('consumerreport/input/Experian.pdf')
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    lines = text.split('\n')
    
    # Find APPLE CARD lines
    apple_lines = []
    for i, line in enumerate(lines):
        if 'APPLE CARD' in line.upper():
            apple_lines.append(i)
    
    print(f"Found APPLE CARD at lines: {apple_lines}")
    
    # Show context around APPLE CARD
    for apple_idx in apple_lines:
        print(f"\n=== APPLE CARD CONTEXT (Line {apple_idx}) ===")
        start = max(0, apple_idx - 10)
        end = min(len(lines), apple_idx + 15)
        
        for i in range(start, end):
            marker = ">>> " if i == apple_idx else "    "
            print(f"{marker}Line {i:4d}: {lines[i]}")
    
    # Run extraction and check APPLE CARD account
    print("\n=== EXTRACTION RESULTS ===")
    accounts = extract_account_details(text)
    
    apple_accounts = [acc for acc in accounts if 'APPLE CARD' in acc.get('creditor', '').upper()]
    
    print(f"Found {len(apple_accounts)} APPLE CARD accounts:")
    for acc in apple_accounts:
        print(f"  Creditor: {acc.get('creditor')}")
        print(f"  Status: {acc.get('status')}")
        print(f"  Balance: {acc.get('balance')}")
        print(f"  Negative Items: {acc.get('negative_items', [])}")
        print(f"  Late Entries: {acc.get('late_entries', [])}")
        print()

if __name__ == "__main__":
    debug_apple_card()
