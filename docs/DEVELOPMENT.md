# Development

## Structure
- `extract_account_details.py` – main workflow (also invoked by `main.py`)
- `convert_to_professional_pdf.py` – text/PDF conversion
- `utils/ocr_fallback.py` – OCR extraction using pdf2image + pytesseract
- `docs/` – documentation (INSTALLATION, USAGE, DEVELOPMENT)

## Entry point
```
python main.py
```

## OCR fallback
- If native PyMuPDF extraction returns <100 chars, the code attempts OCR via `utils.ocr_fallback.extract_text_via_ocr`.
- Dependencies are optional and loaded lazily. If unavailable, the tool skips OCR and continues to next file.

## Optional dependencies and guidance
- FAISS and sentence-transformers are optional. When absent, knowledgebase search is skipped gracefully.

## Roadmap (from analysis)
- Group debug scripts into a `debug/` directory
- Add DOFD/re-aging detection and hard inquiry parsing
- Expand Metro 2/CDIA validation checks
- Add tests and a constraints file for pinned dependencies
