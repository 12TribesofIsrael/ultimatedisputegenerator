#!/usr/bin/env python
"""
Simple DOC to PDF converter using docx2pdf
"""
import os
from pathlib import Path
import shutil
import sys
from typing import List

try:
    from docx2pdf import convert
except ImportError:
    print("Installing required package docx2pdf...")
    os.system(f"{sys.executable} -m pip install docx2pdf")
    from docx2pdf import convert

KB_DIR = Path("knowledgebase")
CONVERTED_DIR = KB_DIR / "converted_docs"

def find_doc_files() -> List[Path]:
    """Find all .doc files that need conversion"""
    doc_files = []
    for p in KB_DIR.rglob("*.doc"):
        if p.is_file() and "\\converted_docs\\" not in str(p):
            doc_files.append(p)
    return doc_files

def main():
    print("🔎 Finding .doc files...")
    doc_files = find_doc_files()
    print(f"Found {len(doc_files)} .doc files to convert")

    if not doc_files:
        print("No .doc files found!")
        return

    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    failed = 0
    
    for i, doc_file in enumerate(doc_files, 1):
        print(f"\nProcessing {i}/{len(doc_files)}: {doc_file.name}")
        
        # Create output path preserving directory structure
        rel_path = doc_file.relative_to(KB_DIR)
        out_pdf = CONVERTED_DIR / rel_path.with_suffix('.pdf')
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Convert to PDF
            convert(str(doc_file), str(out_pdf))
            
            if out_pdf.exists():
                print(f"✅ Successfully converted to: {out_pdf}")
                converted += 1
            else:
                print(f"❌ Conversion failed - no output file")
                failed += 1
        except Exception as e:
            print(f"❌ Error converting {doc_file.name}: {e}")
            failed += 1
    
    print("\n=== Conversion Summary ===")
    print(f"Total files: {len(doc_files)}")
    print(f"Converted: {converted}")
    print(f"Failed: {failed}")
    print(f"\nConverted PDFs are in: {CONVERTED_DIR}")

if __name__ == "__main__":
    main()
