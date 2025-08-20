# 🚀 Ultimate Dispute Letter Generator v2.3.3 – Status Classification Hardening

Release Date: 2025-08-19

## Summary
Critical fixes to ensure charge-offs and collections are never misclassified as Late, plus tooling to regenerate all letters safely.

## Fixes
- Inline Status parsing: correctly captures embedded segments like `... | Status: Charge Off` on creditor rows
- Grid CO recognition: detects repeated `CO` codes in payment grids (ignoring legend/key/how-to-read/definitions lines)
- Late guard: blocks adding Late when charge-off indicators are present in the same account block
- Collection enforcement: honors explicit collection sections and explicit Status lines

## Tooling
- Non-interactive generators updated to support auto pathing and batch regeneration
  - debug/noninteractive_generate.py (single report)
  - debug/noninteractive_generate_all.py (all reports)
- Diagnostic: debug/scan_pdf_tokens.py to quickly verify presence of Charge Off / Collection tokens in source PDFs

## Impact
- Letters regenerated (.md) reflect correct Charge Off / Collection statuses
- Eliminates prior edge case where inline `Status:` wasn’t recognized
- Reduces false Late classifications

## Files Changed
- extract_account_details.py – status parsing and guards
- debug/noninteractive_generate*.py – import path and discovery fixes
- debug/scan_pdf_tokens.py – new diagnostic
- README.md – updated Recent Updates

## Compatibility
- Backward compatible; no new dependencies
