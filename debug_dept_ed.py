#!/usr/bin/env python3
"""Debug DEPT OF EDUCATION accounts in TransUnion"""

from extract_account_details import extract_account_details, merge_accounts_by_key, filter_negative_accounts
import fitz

with fitz.open('consumerreport/input/transunion.pdf') as doc:
    text = ''.join(page.get_text() for page in doc)

accounts = merge_accounts_by_key(extract_account_details(text))
dept_ed = [a for a in accounts if 'EDUCATION' in (a.get('creditor') or '') or 'NELN' in (a.get('creditor') or '')]

print("DEPT OF EDUCATION accounts BEFORE filtering:")
for a in dept_ed:
    print(f'Creditor: {a.get("creditor")}')
    print(f'Status: {a.get("status")}')
    print(f'Late entries: {a.get("late_entries")}')
    print(f'Negative items: {a.get("negative_items")}')
    print('---')

negatives = filter_negative_accounts(accounts)
dept_ed_negatives = [a for a in negatives if 'EDUCATION' in (a.get('creditor') or '') or 'NELN' in (a.get('creditor') or '')]

print("\nDEPT OF EDUCATION accounts AFTER filtering:")
if dept_ed_negatives:
    for a in dept_ed_negatives:
        print(f'Creditor: {a.get("creditor")}')
        print(f'Status: {a.get("status")}')
        print(f'Late entries: {a.get("late_entries")}')
        print(f'Negative items: {a.get("negative_items")}')
else:
    print("NO DEPT OF EDUCATION accounts in negatives - THIS IS THE PROBLEM!")
