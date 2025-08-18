#!/usr/bin/env python3
"""
Quick validator for late-entry extraction.

Opens available bureau PDFs in consumerreport/input/ and prints the parsed
late entries for accounts likely matching Dept of Education / Nelnet.
"""
from pathlib import Path
import json

import fitz  # PyMuPDF

from extract_account_details import extract_account_details, merge_accounts_by_key


def analyze_pdf(pdf_path: Path):
    if not pdf_path.exists():
        print(f"SKIP: {pdf_path} not found")
        return
    print(f"\n=== Analyzing: {pdf_path.name} ===")
    text = ""
    with fitz.open(str(pdf_path)) as doc:
        for page in doc:
            text += page.get_text()
    accounts = merge_accounts_by_key(extract_account_details(text))
    # Focus on Dept of Education / Nelnet accounts for this check
    focus = [
        a for a in accounts
        if any(k in (a.get("creditor") or "").upper() for k in ["EDUCATION", "NELN", "NELNET", "DEPT OF ED"])
    ]
    if not focus:
        print("No matching Education/Nelnet accounts parsed.")
        return
    out = [
        {
            "creditor": a.get("creditor"),
            "status": a.get("status"),
            "late_entries": a.get("late_entries"),
        }
        for a in focus
    ]
    print(json.dumps(out, indent=2))


def main():
    base = Path("consumerreport/input")
    for name in ["Equifax.pdf", "Experian.pdf", "transunion.pdf"]:
        analyze_pdf(base / name)


if __name__ == "__main__":
    main()


