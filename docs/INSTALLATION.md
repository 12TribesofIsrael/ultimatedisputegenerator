# Installation

## Prerequisites
- Python 3.10+
- Windows 10/11, macOS, or Linux
- Optional (for OCR fallback):
  - Tesseract OCR installed and available on PATH
  - Poppler (for pdf2image on Windows)

## Python Dependencies
```
pip install -r requirements.txt
```

## OCR Dependencies (Optional but Recommended)

### Windows
1. Install Tesseract OCR:
   - Official installer: https://github.com/UB-Mannheim/tesseract/wiki
   - Ensure `tesseract.exe` is on PATH
2. Install Poppler for Windows:
   - Download: https://github.com/oschwartz10612/poppler-windows/releases/
   - Add the `bin/` directory to PATH

### macOS
```
brew install tesseract poppler
```

### Linux (Debian/Ubuntu)
```
sudo apt update && sudo apt install -y tesseract-ocr poppler-utils
```

## Verify Installation
```
# Python deps
python -c "import fitz, pdf2image, pytesseract; print('OK')"

# Tesseract
tesseract --version
```

If OCR is not installed, the system will still work for text-based PDFs. Image-only PDFs will attempt OCR fallback if available.

## Optional: Use constraints for pinned versions
For reproducible installs, copy `constraints.example.txt` to `constraints.txt` and install with:
```
pip install -r requirements.txt -c constraints.txt
```
