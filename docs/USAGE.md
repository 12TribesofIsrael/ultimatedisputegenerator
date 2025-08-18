# Usage

## Basic
```
python main.py  # or: python extract_account_details.py
```
Place your report PDF(s) under `consumerreport/` (subfolders OK). The tool auto-detects all PDFs and will prompt for your name and address once.

## Output
- `outputletter/[BUREAU]/EDITABLE_DISPUTE_LETTER_[NAME]_[DATE].txt`
- `outputletter/[BUREAU]/PROFESSIONAL_DELETION_DEMAND_[NAME]_[DATE].pdf`

## PDF Generation
```
python convert_to_professional_pdf.py          # create editable text version
python convert_to_professional_pdf.py pdf      # generate professional PDF
```

## Non-interactive cleanup
```
# Smart Clean without prompts (Windows CMD)
set CLEAN_CHOICE=2 && python main.py
```

## Notes
- OCR fallback triggers automatically if native PDF text extraction returns too little content.
- Knowledgebase features require FAISS and sentence-transformers; the tool still runs without them.
