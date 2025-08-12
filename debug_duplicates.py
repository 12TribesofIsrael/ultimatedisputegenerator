#!/usr/bin/env python3
"""Debug script to examine duplicate account detection"""

import fitz
import re
from extract_account_details import extract_account_details, merge_accounts_by_key

def debug_duplicates():
    # Extract text from TransUnion PDF
    doc = fitz.open('consumerreport/input/transunion.pdf')
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    # Run extraction (before merging)
    print(f"=== BEFORE MERGING ===")
    all_accounts = extract_account_details(text)
    
    # Focus on problematic creditors
    problem_creditors = ['CAPITAL ONE', 'WEBBANK/FINGERHUT', 'NAVY FCU']
    
    for creditor in problem_creditors:
        print(f"\n--- {creditor} ACCOUNTS (before merge) ---")
        matching_accounts = [acc for acc in all_accounts if creditor.upper() in acc.get('creditor', '').upper()]
        
        for i, acc in enumerate(matching_accounts):
            print(f"  {i+1}. Creditor: {acc.get('creditor')}")
            print(f"     Account#: {acc.get('account_number')}")
            print(f"     Balance: {acc.get('balance')}")
            print(f"     Status: {acc.get('status')}")
            print(f"     Negative Items: {acc.get('negative_items', [])}")
            
            # Show merge key
            bal_key = acc.get('balance', '').replace('$', '').replace(',', '').strip() if acc.get('balance') else ''
            merge_key = (acc.get('creditor') or '', acc.get('account_number') or '', bal_key)
            print(f"     Merge Key: {merge_key}")
            print()
    
    # Run merging
    print(f"\n=== AFTER MERGING ===")
    merged_accounts = merge_accounts_by_key(all_accounts)
    
    for creditor in problem_creditors:
        print(f"\n--- {creditor} ACCOUNTS (after merge) ---")
        matching_accounts = [acc for acc in merged_accounts if creditor.upper() in acc.get('creditor', '').upper()]
        
        for i, acc in enumerate(matching_accounts):
            print(f"  {i+1}. Creditor: {acc.get('creditor')}")
            print(f"     Account#: {acc.get('account_number')}")
            print(f"     Balance: {acc.get('balance')}")
            print(f"     Status: {acc.get('status')}")
            print(f"     Negative Items: {acc.get('negative_items', [])}")
            print()

if __name__ == "__main__":
    debug_duplicates()
