#!/usr/bin/env python3
import fitz
from extract_account_details import extract_account_details, merge_accounts_by_key, filter_negative_accounts, classify_account_policy

def main():
    path = 'consumerreport/input/Equifax.pdf'
    doc = fitz.open(path)
    text = ''
    for page in doc:
        text += page.get_text()
    doc.close()

    all_accounts = extract_account_details(text)
    merged = merge_accounts_by_key(all_accounts)
    negatives = filter_negative_accounts(merged)

    def show(tag, accounts):
        print(f"\n=== {tag} ({len(accounts)}) ===")
        for a in accounts:
            if 'CAPITAL ONE' in (a.get('creditor') or ''):
                print(f"Creditor: {a.get('creditor')} | Status: {a.get('status')} | Policy: {classify_account_policy(a)}")
                print(f"  Negative Items: {a.get('negative_items')}")
                print(f"  Late Entries: {a.get('late_entries')}")

    show('MERGED', merged)
    show('NEGATIVE AFTER FILTER', negatives)

if __name__ == '__main__':
    main()


