#!/usr/bin/env python3
"""Non-interactive generator for TransUnion letter using current filtering policy."""

import fitz  # PyMuPDF
from pathlib import Path

from extract_account_details import (
    extract_account_details,
    merge_accounts_by_key,
    filter_negative_accounts,
    detect_bureau_from_pdf,
    create_organized_folders,
    generate_all_letters,
)


def main() -> None:
    pdf_path = Path('consumerreport/input/Transunion.pdf')
    if not pdf_path.exists():
        print('Transunion.pdf not found at consumerreport/input/Transunion.pdf')
        return

    with fitz.open(str(pdf_path)) as doc:
        text = "".join(page.get_text() for page in doc)

    accounts = extract_account_details(text)
    merged = merge_accounts_by_key(accounts)
    negatives = filter_negative_accounts(merged)

    bureau = detect_bureau_from_pdf(text, pdf_path.name) or 'TransUnion'
    folders = create_organized_folders(bureau_detected=bureau, base_path='outputletter')

    files = generate_all_letters(
        user_choice=1,
        accounts=negatives,
        consumer_name='Auto User',
        bureau_detected=bureau,
        folders=folders,
        round_number=1,
        consumer_address_lines=['123 Main St', 'City, ST 00000', '555-555-5555', 'auto@example.com'],
        certified_tracking=None,
        ag_state=None,
        report_stem=pdf_path.stem,
    )

    print('\n'.join(files))


if __name__ == '__main__':
    main()


