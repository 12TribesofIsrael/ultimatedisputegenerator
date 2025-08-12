#!/usr/bin/env python3
"""Debug NAVY FCU status detection"""

from extract_account_details import extract_account_details, merge_accounts_by_key
import fitz

with fitz.open('consumerreport/input/transunion.pdf') as doc:
    text = ''.join(page.get_text() for page in doc)

accounts = merge_accounts_by_key(extract_account_details(text))
navy = [a for a in accounts if 'NAVY' in (a.get('creditor') or '')]

print('NAVY FCU account status detection:')
for a in navy:
    if a.get('balance') == '$490':  # The one with balance
        status = a.get('status') or ''
        print(f'Status text: "{status}"')
        print(f'Status lower: "{status.lower()}"')
        print(f'Has "exceptional payment history"?: {"exceptional payment history" in status.lower()}')
        print(f'Has "paid as agreed"?: {"paid as agreed" in status.lower()}')
        print(f'Late entries: {a.get("late_entries")}')
        break
