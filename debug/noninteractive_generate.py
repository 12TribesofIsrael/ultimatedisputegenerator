#!/usr/bin/env python3
"""Non-interactive generator for Equifax letter using current filtering policy."""

import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime

from extract_account_details import (
    extract_account_details,
    merge_accounts_by_key,
    filter_negative_accounts,
    detect_bureau_from_pdf,
    create_organized_folders,
    generate_all_letters,
)


def main() -> None:
    pdf_path = Path('consumerreport/input/Equifax.pdf')
    if not pdf_path.exists():
        print('Equifax.pdf not found at consumerreport/input/Equifax.pdf')
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


