#!/usr/bin/env python3
"""Test the positive account filtering fix"""

import fitz
from extract_account_details import extract_account_details, merge_accounts_by_key, filter_negative_accounts

def test_positive_fix():
    # Test on TransUnion PDF
    doc = fitz.open('consumerreport/input/transunion.pdf')
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    # Run extraction pipeline
    all_accounts = extract_account_details(text)
    merged_accounts = merge_accounts_by_key(all_accounts)
    negative_accounts = filter_negative_accounts(merged_accounts)
    
    print("=== POSITIVE ACCOUNT TEST ===")
    
    # Check the problematic accounts
    problem_creditors = ['CAPITAL ONE', 'WEBBANK/FINGERHUT', 'NAVY FCU', 'DISCOVER CARD']
    
    print(f"\n--- AFTER MERGING ({len(merged_accounts)} accounts) ---")
    for creditor in problem_creditors:
        matching = [acc for acc in merged_accounts if creditor.upper() in acc.get('creditor', '').upper()]
        for acc in matching:
            print(f"{creditor}:")
            print(f"  Status: {acc.get('status')}")
            print(f"  Negative Items: {acc.get('negative_items', [])}")
            print(f"  Should be excluded: {'YES' if acc.get('status') == 'Paid as agreed' and not acc.get('negative_items') else 'NO'}")
            print()
    
    print(f"\n--- AFTER FILTERING ({len(negative_accounts)} accounts) ---")
    excluded_count = 0
    for creditor in problem_creditors:
        matching = [acc for acc in negative_accounts if creditor.upper() in acc.get('creditor', '').upper()]
        if matching:
            print(f"{creditor}: ❌ STILL INCLUDED (should be excluded)")
            for acc in matching:
                print(f"  Status: {acc.get('status')}")
                print(f"  Negative Items: {acc.get('negative_items', [])}")
        else:
            print(f"{creditor}: ✅ EXCLUDED (correct)")
            excluded_count += 1
        print()
    
    print(f"Result: {excluded_count}/{len(problem_creditors)} positive accounts correctly excluded")
    
    return excluded_count == len(problem_creditors)

if __name__ == "__main__":
    success = test_positive_fix()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Positive account filtering")
