#!/usr/bin/env python
"""
Convert DOC files to PDF for easier processing
This will allow the existing ingestion scripts to process them
"""
import os
import sys
from pathlib import Path
import subprocess
import time

# Setup
KB_DIR = Path("knowledgebase")
CONVERTED_DIR = KB_DIR / "converted_docs"

def check_libreoffice():
    """Check if LibreOffice is available"""
    try:
        result = subprocess.run(['soffice', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True
    except:
        pass
    
    # Try Windows path
    try:
        result = subprocess.run(['C:\\Program Files\\LibreOffice\\program\\soffice.exe', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True
    except:
        pass
    
    return False

def convert_with_libreoffice(doc_file, output_dir):
    """Convert DOC to PDF using LibreOffice"""
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert using LibreOffice
        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(output_dir),
            str(doc_file)
        ]
        
        # Try Windows path if needed
        if not check_libreoffice():
            cmd[0] = 'C:\\Program Files\\LibreOffice\\program\\soffice.exe'
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Find the generated PDF
            pdf_name = doc_file.stem + '.pdf'
            pdf_path = output_dir / pdf_name
            if pdf_path.exists():
                return pdf_path
        else:
            print(f"   ❌ LibreOffice conversion failed: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ LibreOffice error: {e}")
    
    return None

def convert_with_python_libs(doc_file, output_dir):
    """Convert DOC to PDF using Python libraries"""
    try:
        from docx import Document
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read DOCX content
        doc = Document(doc_file)
        
        # Create PDF
        pdf_name = doc_file.stem + '.pdf'
        pdf_path = output_dir / pdf_name
        
        # Create PDF with content
        doc_pdf = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                p = Paragraph(paragraph.text, styles['Normal'])
                story.append(p)
        
        doc_pdf.build(story)
        return pdf_path
        
    except Exception as e:
        print(f"   ❌ Python conversion error: {e}")
        return None

def main():
    print("🔄 CONVERTING DOC FILES TO PDF")
    print("=" * 50)
    
    # Find all DOC files
    doc_files = list(KB_DIR.rglob("*.doc"))
    print(f"📁 Found {len(doc_files)} DOC files")
    
    if len(doc_files) == 0:
        print("✅ No DOC files found!")
        return
    
    # Check for conversion tools
    has_libreoffice = check_libreoffice()
    print(f"🔧 LibreOffice available: {has_libreoffice}")
    
    if not has_libreoffice:
        print("⚠️  LibreOffice not found. Installing Python dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx", "reportlab"])
            print("✅ Python dependencies installed")
        except:
            print("❌ Failed to install dependencies")
            print("💡 Please install LibreOffice manually:")
            print("   Download from: https://www.libreoffice.org/download/")
            return
    
    # Create converted directory
    CONVERTED_DIR.mkdir(exist_ok=True)
    
    # Convert files
    converted = 0
    failed = 0
    
    print(f"\n🚀 STARTING CONVERSION")
    print("=" * 50)
    
    for i, doc_file in enumerate(doc_files):
        print(f"📄 Converting {i+1}/{len(doc_files)}: {doc_file.name}")
        
        # Try LibreOffice first
        pdf_path = None
        if has_libreoffice:
            pdf_path = convert_with_libreoffice(doc_file, CONVERTED_DIR)
        
        # Fallback to Python if LibreOffice fails
        if not pdf_path:
            pdf_path = convert_with_python_libs(doc_file, CONVERTED_DIR)
        
        if pdf_path and pdf_path.exists():
            print(f"   ✅ Converted to: {pdf_path.name}")
            converted += 1
        else:
            print(f"   ❌ Failed to convert {doc_file.name}")
            failed += 1
        
        # Small delay to avoid overwhelming the system
        time.sleep(0.5)
    
    print(f"\n" + "=" * 50)
    print("🎉 CONVERSION COMPLETE!")
    print("=" * 50)
    print(f"✅ Successfully converted: {converted} files")
    print(f"❌ Failed conversions: {failed} files")
    print(f"📁 Converted PDFs saved to: {CONVERTED_DIR}")
    
    if converted > 0:
        print(f"\n💡 Next steps:")
        print(f"1. Run: python visible_ingest.py")
        print(f"2. The converted PDFs will be processed automatically")
        print(f"3. Check coverage with: python analyze_coverage_gaps.py")

if __name__ == "__main__":
    main()
