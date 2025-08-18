# Codebase Analysis and Fix Plan

## Overview
This report summarizes issues identified in the repository and provides a prioritized fix plan. Focus areas include documentation consistency, project structure, code quality, missing OCR fallback, and dependency hygiene.

## Critical Issues

- Documentation consistency: Dates, versions, and messages vary across multiple markdown files. Ensure dates and version numbers are consistent and accurate across `README.md`, `CHANGELOG*`, and related docs.
- Overly verbose README: Current `README.md` is very long and mixes usage, marketing, and deep technical details, making onboarding harder.
- Dispersed documentation: Many overlapping `.md` files cause duplication and drift.
- Unclear single entry point: Users run multiple scripts; there is no simple `main.py` entry.
- OCR fallback missing: Image-only PDFs will return little or no text; extraction should fall back to OCR.

## Moderate Issues

- Many debug/utility scripts in root: `debug_*.py`, `quick_*.py`, etc., clutter the top level and are not grouped.
- Broad exception handling and optional-dependency paths (FAISS, sentence-transformers) lack user-facing guidance when unavailable.
- Requirements are unpinned (>=). Consider adding a constraints/pins strategy to improve reproducibility.
- Conversion workflow for legacy `.doc` files requires clearer guidance and process management.

## Recommendations for Fixes

### Phase 1: Documentation and Structure

1) Create a concise, developer-focused `README.md` (<200 lines) with:
   - Overview, Quick Start, How it works, and Links to detailed docs.
2) Archive the current long README under `docs/README_FULL.md`.
3) Add core docs under `docs/`:
   - `INSTALLATION.md` – OS deps (Tesseract for OCR), Python setup
   - `USAGE.md` – CLI usage, batch/non-interactive modes
   - `DEVELOPMENT.md` – architecture, debugging, contribution
   - Keep `CHANGELOG_v2.1.md` for history; add `docs/CHANGELOG.md` as an index pointing to versioned logs
4) Add a clear entry point `main.py` that calls the existing workflow.

### Phase 2: Functionality and Code Quality

1) Implement OCR fallback for image-only PDFs:
   - Create `utils/ocr_fallback.py` using `pdf2image` + `pytesseract`.
   - In `extract_account_details.py`, if extracted text length < threshold or on exception, run OCR fallback and proceed if successful.
2) Improve error messages for optional dependencies (FAISS / embeddings) to guide users when knowledgebase search is unavailable.
3) Group debug scripts in a `debug/` directory (future step; avoid breaking imports now).

### Phase 3: Dependency Hygiene

1) Keep `requirements.txt` as-is for now to avoid breakage; add notes in `INSTALLATION.md` about recommended versions and platform specifics.
2) Optionally add a constraints file later (`constraints.txt`) with tested pins.

## Priority Matrix

| Item | Impact | Effort | Priority |
| --- | --- | --- | --- |
| Concise README + docs | High | Low | High |
| OCR fallback | High | Medium | High |
| Entry point `main.py` | Medium | Low | High |
| Group debug scripts | Medium | Medium | Medium |
| Dependency pinning strategy | Medium | Low | Medium |

## Deliverables Implemented (in this change set)

- `CODEBASE_ANALYSIS.md` (this report)
- `docs/README_FULL.md` – archived full README
- New concise `README.md` linking to docs
- `docs/INSTALLATION.md`, `docs/USAGE.md`, `docs/DEVELOPMENT.md`
- `utils/ocr_fallback.py` – OCR utility
- `main.py` – single entry point
- `extract_account_details.py` updated to use OCR fallback if needed


