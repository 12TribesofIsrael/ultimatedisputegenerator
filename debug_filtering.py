#!/usr/bin/env python3
"""Debug script to test filtering logic after positive status fixes"""

import fitz
from extract_account_details import extract_account_details, merge_accounts_by_key, filter_negative_accounts

def debug_filtering():
    # Extract text from TransUnion PDF
    doc = fitz.open('consumerreport/input/transunion.pdf')
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    # Run full extraction pipeline
    all_accounts = extract_account_details(text)
    merged_accounts = merge_accounts_by_key(all_accounts)
    negative_accounts = filter_negative_accounts(merged_accounts)
    
    print(f"=== FILTERING RESULTS ===")
    print(f"Total accounts: {len(all_accounts)}")
    print(f"After merging: {len(merged_accounts)}")
    print(f"After filtering: {len(negative_accounts)}")
    
    # Focus on the previously problematic accounts
    problem_creditors = ['CAPITAL ONE', 'WEBBANK/FINGERHUT', 'NAVY FCU']
    
    print(f"\n=== BEFORE FILTERING ===")
    for creditor in problem_creditors:
        matching = [acc for acc in merged_accounts if creditor.upper() in acc.get('creditor', '').upper()]
        for acc in matching:
            print(f"{creditor}:")
            print(f"  Status: {acc.get('status')}")
            print(f"  Negative Items: {acc.get('negative_items', [])}")
            print(f"  Late Entries: {acc.get('late_entries', [])}")
            print()
    
    print(f"\n=== AFTER FILTERING ===")
    for creditor in problem_creditors:
        matching = [acc for acc in negative_accounts if creditor.upper() in acc.get('creditor', '').upper()]
        if matching:
            print(f"{creditor}: STILL INCLUDED (should be excluded!)")
            for acc in matching:
                print(f"  Status: {acc.get('status')}")
                print(f"  Negative Items: {acc.get('negative_items', [])}")
                print(f"  Late Entries: {acc.get('late_entries', [])}")
        else:
            print(f"{creditor}: ✅ EXCLUDED (correct!)")
        print()

if __name__ == "__main__":
    debug_filtering()
