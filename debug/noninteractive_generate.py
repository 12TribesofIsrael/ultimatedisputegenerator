#!/usr/bin/env python3
"""Non-interactive generator for Equifax letter using current filtering policy.

Enhancements:
- Auto-fix import path when run from any cwd
- Auto-discover a report PDF under consumerreport/ if Equifax.pdf is not present
"""

import os
import sys
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extract_account_details import (
    extract_account_details,
    merge_accounts_by_key,
    filter_negative_accounts,
    detect_bureau_from_pdf,
    create_organized_folders,
    generate_all_letters,
)


def _find_report_pdf() -> Path | None:
    # Prefer Equifax.pdf; else pick first PDF under consumerreport/
    preferred = Path('consumerreport/input/Equifax.pdf')
    if preferred.exists():
        return preferred
    base = Path('consumerreport')
    if not base.exists():
        return None
    for p in base.rglob('*.pdf'):
        try:
            if p.is_file():
                return p
        except Exception:
            continue
    return None


def main() -> None:
    pdf_path = _find_report_pdf()
    if not pdf_path:
        print('No report PDF found. Place a file under consumerreport/ (e.g., consumerreport/input/Equifax.pdf).')
        return

    # Extract text
    with fitz.open(str(pdf_path)) as doc:
        text = "".join(page.get_text() for page in doc)

    # Pipeline
    all_accounts = extract_account_details(text)
    merged_accounts = merge_accounts_by_key(all_accounts)
    negative_accounts = filter_negative_accounts(merged_accounts)

    bureau = detect_bureau_from_pdf(text, pdf_path.name) or 'Equifax'
    folders = create_organized_folders(bureau_detected=bureau, base_path='outputletter')

    # Minimal consumer placeholders
    consumer_name = 'Auto User'
    consumer_address_lines = ['123 Main St', 'City, ST 00000', '555-555-5555', 'auto@example.com']

    files = generate_all_letters(
        user_choice=1,  # Bureau letter only
        accounts=negative_accounts,
        consumer_name=consumer_name,
        bureau_detected=bureau,
        folders=folders,
        round_number=1,
        consumer_address_lines=consumer_address_lines,
        certified_tracking=None,
        ag_state=None,
        report_stem=pdf_path.stem,
    )

    print('Generated files:')
    for f in files:
        print(f)


if __name__ == '__main__':
    main()


