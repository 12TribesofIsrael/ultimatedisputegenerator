#!/usr/bin/env python3
"""Debug script to examine positive account filtering"""

import fitz
import re
from extract_account_details import extract_account_details, filter_negative_accounts

def debug_positive_accounts():
    # Extract text from TransUnion PDF (where the issue is most apparent)
    doc = fitz.open('consumerreport/input/transunion.pdf')
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    lines = text.split('\n')
    
    # Find positive accounts that should be excluded
    positive_creditors = ['CAPITAL ONE', 'WEBBANK/FINGERHUT', 'NAVY FCU']
    
    for creditor in positive_creditors:
        print(f"\n=== EXAMINING {creditor} ===")
        
        # Find lines with this creditor
        creditor_lines = []
        for i, line in enumerate(lines):
            if creditor.upper() in line.upper():
                creditor_lines.append(i)
        
        print(f"Found {creditor} at lines: {creditor_lines}")
        
        # Show context around each occurrence
        for creditor_idx in creditor_lines:
            print(f"\n--- {creditor} CONTEXT (Line {creditor_idx}) ---")
            start = max(0, creditor_idx - 5)
            end = min(len(lines), creditor_idx + 15)
            
            for i in range(start, end):
                marker = ">>> " if i == creditor_idx else "    "
                line_text = lines[i]
                
                # Highlight positive patterns
                if re.search(r'never\s*late|paid.*closed.*never\s*late|exceptional\s*payment|paid\s*as\s*agreed', line_text, re.IGNORECASE):
                    marker = "+POS"
                elif re.search(r'late\s*payment|past\s*due|\b(?:30|60|90)\s*days?\s*(?:late|past\s*due)', line_text, re.IGNORECASE):
                    marker = "LATE"
                elif re.search(r'current|paid|closed', line_text, re.IGNORECASE):
                    marker = " ok "
                    
                print(f"{marker} Line {i:4d}: {line_text}")
    
    # Run extraction and filtering
    print(f"\n=== EXTRACTION AND FILTERING RESULTS ===")
    all_accounts = extract_account_details(text)
    print(f"Total accounts extracted: {len(all_accounts)}")
    
    # Show all accounts before filtering
    print(f"\n--- ALL ACCOUNTS (before filtering) ---")
    for i, acc in enumerate(all_accounts):
        creditor = acc.get('creditor', '')
        if any(pos_cred in creditor.upper() for pos_cred in positive_creditors):
            print(f"  {i+1}. {creditor}")
            print(f"     Status: {acc.get('status')}")
            print(f"     Negative Items: {acc.get('negative_items', [])}")
            print(f"     Late Entries: {acc.get('late_entries', [])}")
    
    # Filter negative accounts
    negative_accounts = filter_negative_accounts(all_accounts)
    print(f"\n--- NEGATIVE ACCOUNTS (after filtering) ---")
    print(f"Filtered to {len(negative_accounts)} negative accounts")
    
    for i, acc in enumerate(negative_accounts):
        creditor = acc.get('creditor', '')
        if any(pos_cred in creditor.upper() for pos_cred in positive_creditors):
            print(f"  {i+1}. {creditor} (SHOULD BE EXCLUDED!)")
            print(f"     Status: {acc.get('status')}")
            print(f"     Negative Items: {acc.get('negative_items', [])}")
            print(f"     Late Entries: {acc.get('late_entries', [])}")

if __name__ == "__main__":
    debug_positive_accounts()
