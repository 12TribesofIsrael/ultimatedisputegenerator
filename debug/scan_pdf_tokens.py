#!/usr/bin/env python3
"""
Quick scanner: extract text from the first found PDF under consumerreport/ and
print counts of key tokens used for classifying negative items.
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception as e:
    raise SystemExit(f"PyMuPDF required: {e}")


def find_report() -> Path | None:
    base = Path('consumerreport')
    if not base.exists():
        return None
    preferred = base / 'input' / 'Equifax.pdf'
    if preferred.exists():
        return preferred
    for p in base.rglob('*.pdf'):
        try:
            if p.is_file():
                return p
        except Exception:
            continue
    return None


def main() -> None:
    pdf = find_report()
    if not pdf:
        print('No PDF found under consumerreport/.')
        return
    print(f"Scanning: {pdf}")
    with fitz.open(str(pdf)) as d:
        text = "\n".join(page.get_text() for page in d)
    low = text.lower()

    tokens = [
        'charge off', 'charge-off', 'charged off', 'charged off account', 'profit and loss',
        'written off', 'write off', 'charged to profit', 'co ', ' co', ' co ',
        'collection', 'collection account', 'placed for collection', 'collection accounts',
        'late', 'past due', 'delinquent', 'payment code', 'pymt code', 'pay code',
        'status:', 'current status:', 'legend', '24 month history', 'how to read', 'narrative code'
    ]
    print('\nToken counts:')
    for t in tokens:
        print(f"{t:24s} -> {low.count(t)}")

    # Show a sample window around the first occurrence of 'charge' and 'collection'
    for key in ['charge', 'collection', 'status:', 'co ']:
        idx = low.find(key)
        print(f"\nSample around '{key}':")
        if idx == -1:
            print('<none>')
        else:
            start = max(0, idx - 400)
            end = min(len(text), idx + 400)
            print(text[start:end])


if __name__ == '__main__':
    main()


