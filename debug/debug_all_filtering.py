#!/usr/bin/env python3
"""Debug all account filtering to see what's included/excluded"""

from extract_account_details import extract_account_details, merge_accounts_by_key, filter_negative_accounts
import fitz

with fitz.open('consumerreport/input/transunion.pdf') as doc:
    text = ''.join(page.get_text() for page in doc)

accounts = merge_accounts_by_key(extract_account_details(text))
negatives = filter_negative_accounts(accounts)

print("=== ALL ACCOUNTS INCLUDED IN DISPUTE ===")
for i, a in enumerate(negatives, 1):
    print(f"{i}. {a.get('creditor')} - {a.get('status')} - Late entries: {len(a.get('late_entries', []))}")
    if a.get('late_entries'):
        entries = a.get('late_entries', [])
        formatted = [f"{e.get('month')} {e.get('year') or ''} ({e.get('severity')})" for e in entries]
        print(f"   Late details: {', '.join(formatted)}")
    print()
