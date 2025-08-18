#!/usr/bin/env python3
"""Non-interactive generator for ALL reports (Experian/Equifax/TransUnion).

Processes every PDF in consumerreport/ (recursively), applies the current parsing
and filtering policy, and regenerates bureau and creditor letters without prompts.

This is useful for CI/automation or quick refresh after parser updates.
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF

from extract_account_details import (
    extract_account_details,
    merge_accounts_by_key,
    filter_negative_accounts,
    detect_bureau_from_pdf,
    create_organized_folders,
    generate_all_letters,
)
from clean_workspace import cleanup_workspace


def main() -> None:
    # Ensure Smart Clean non-interactively
    os.environ.setdefault("CLEAN_CHOICE", "2")
    cleanup_workspace(auto_mode=True)

    consumerreport_dir = Path("consumerreport")
    pdf_files = sorted(consumerreport_dir.glob("**/*.pdf"), key=lambda p: p.name.lower())
    if not pdf_files:
        print("No PDFs found under consumerreport/. Nothing to do.")
        return

    date_str = datetime.now().strftime('%Y-%m-%d')

    total_generated: list[Path] = []

    for pdf_path in pdf_files:
        try:
            with fitz.open(str(pdf_path)) as doc:
                text = "".join(page.get_text() for page in doc)
        except Exception as e:
            print(f"❌ Failed to read {pdf_path.name}: {e}")
            continue

        # Parse + merge + filter
        accounts = extract_account_details(text)
        accounts = merge_accounts_by_key(accounts)
        if not accounts:
            print(f"ℹ️  No accounts parsed: {pdf_path.name}")
            continue

        bureau = detect_bureau_from_pdf(text, pdf_path.name) or "Unknown Bureau"
        negatives = filter_negative_accounts(accounts)
        if not negatives:
            print(f"🎉 No negative accounts in {pdf_path.name}")
            continue

        # Folders by bureau
        folders = create_organized_folders(bureau)

        # Minimal non-interactive consumer placeholders
        consumer_name = 'Auto User'
        consumer_address_lines = ['123 Main St', 'City, ST 00000', '555-555-5555', 'auto@example.com']

        # Strategy 3 = Maximum Pressure (bureau + furnishers) with Round 1
        generated = generate_all_letters(
            user_choice=3,
            accounts=negatives,
            consumer_name=consumer_name,
            bureau_detected=bureau,
            folders=folders,
            round_number=1,
            consumer_address_lines=consumer_address_lines,
            certified_tracking=None,
            ag_state=None,
            report_stem=pdf_path.stem,
        )

        total_generated.extend(generated)
        print(f"✅ {pdf_path.name}: Generated {len(generated)} files")

    if total_generated:
        print("\n=== NON-INTERACTIVE GENERATION COMPLETE ===")
        for p in total_generated:
            print(p)
    else:
        print("\nNo files generated.")


if __name__ == "__main__":
    main()


