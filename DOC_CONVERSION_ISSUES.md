# DOC File Conversion Issues Report

## Overview
- Total .doc files needing conversion: 71 files
- Location: `knowledgebase/unprocessable_files/`
- Current status: Not indexed due to conversion failures
- Goal: Convert to PDF for ingestion into knowledgebase index

## Attempted Solutions & Issues

### 1. Microsoft Word COM Automation (via pywin32)
```python
# Using win32com.client
error: (-2147221005, 'Invalid class string', None, None)
```
- Failed because MS Word is not installed
- Even with pywin32 installed, COM automation wasn't available

### 2. LibreOffice Command Line
```bash
soffice --headless --convert-to pdf
```
Issues:
- LibreOffice installation succeeded but conversion hangs
- Process requires manual "Press Enter to continue" even with --headless
- Unicode characters in filenames causing problems (æ, ô)
- Hanging soffice.exe processes need manual cleanup

### 3. docx2pdf Package
```python
from docx2pdf import convert
```
- Package installed but depends on same COM automation
- Falls back to LibreOffice but encounters same hanging issues

## Problem Files Sample
```
Credit Bureau Dispute, Creditor WonÆt Respond to Me.doc
Response to Stall Tactic ôWe DonÆt have your IDö.doc
```
- Special characters in filenames (Æ, ô) causing issues
- Spaces and punctuation in filenames

## Technical Details

### Environment
- Windows 10
- Python 3.x
- LibreOffice 25.2.5
- No MS Word installed

### File Locations
- Source files: `knowledgebase/unprocessable_files/*.doc`
- Target location: `knowledgebase/converted_docs/`
- Index manifest: `knowledgebase_index/ingestion_manifest.jsonl`

## Recommendations for Next Developer

1. **Pre-processing Needed**
   - Rename files to remove special characters before conversion
   - Use ASCII-only filenames
   - Remove spaces and problematic punctuation

2. **Conversion Options**
   - Install Microsoft Word (preferred solution)
   - Try different LibreOffice version
   - Consider commercial PDF conversion API
   - Try running conversions in Docker with LibreOffice

3. **Alternative Approaches**
   - Extract text directly from .doc without PDF conversion
   - Use OCR on printed documents to recreate content
   - Manual conversion as last resort

4. **Code Improvements**
   - Add retry mechanism for failed conversions
   - Better process management for LibreOffice
   - Implement filename sanitization
   - Add logging for debugging

## Required Dependencies
```bash
pip install pywin32 comtypes docx2pdf
winget install TheDocumentFoundation.LibreOffice
```

## Files to Review
- `convert_unindexed_doc_to_pdf.py` - Main conversion script
- `convert_doc_simple.py` - Simplified attempt
- `knowledgebase_index/INDEXING_STATUS.md` - Overall status
- `knowledgebase_index/not_indexed_list.txt` - List of files to process

## Next Steps
1. Fix filename encoding issues
2. Implement robust process management
3. Add proper error handling and logging
4. Consider batch processing to avoid memory issues
5. Implement progress saving for large batches
