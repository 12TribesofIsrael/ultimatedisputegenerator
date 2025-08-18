#!/usr/bin/env python
"""
Enhanced dependency installer for 95% knowledgebase coverage
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("🔧 INSTALLING ENHANCED DEPENDENCIES FOR 95% COVERAGE")
    print("=" * 60)
    
    # Core packages for existing functionality
    core_packages = [
        "sentence-transformers>=2.2.0",
        "faiss-cpu>=1.7.0", 
        "PyMuPDF>=1.20.0",
        "python-docx>=0.8.11",
        "numpy>=1.21.0",
        "tqdm>=4.64.0"
    ]
    
    # Enhanced packages for additional file types
    enhanced_packages = [
        "Pillow>=9.0.0",           # Image processing
        "pytesseract>=0.3.10",     # OCR for images
        "pandas>=1.5.0",           # CSV processing
        "pdf2image>=1.16.0",       # PDF to image conversion
        "psutil>=5.9.0",           # System monitoring
        "markdown>=3.4.0"          # Markdown processing
    ]
    
    print("📦 Installing core packages...")
    core_success = 0
    for package in core_packages:
        if install_package(package):
            core_success += 1
    
    print(f"\n📦 Installing enhanced packages...")
    enhanced_success = 0
    for package in enhanced_packages:
        if install_package(package):
            enhanced_success += 1
    
    print("\n" + "=" * 60)
    print("📊 INSTALLATION SUMMARY")
    print("=" * 60)
    print(f"✅ Core packages: {core_success}/{len(core_packages)}")
    print(f"✅ Enhanced packages: {enhanced_success}/{len(enhanced_packages)}")
    print(f"📈 Total success rate: {(core_success + enhanced_success)}/{(len(core_packages) + len(enhanced_packages))}")
    
    if core_success == len(core_packages) and enhanced_success >= len(enhanced_packages) - 2:
        print("\n🎉 Ready for 95% coverage ingestion!")
        print("💡 Run: python enhanced_ingest.py")
    else:
        print("\n⚠️  Some packages failed to install")
        print("💡 Check your internet connection and try again")
    
    # Check for Tesseract OCR
    print("\n🔍 Checking OCR availability...")
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR is available")
    except Exception as e:
        print("⚠️  Tesseract OCR not found")
        print("💡 Install Tesseract OCR for image processing:")
        print("   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Linux: sudo apt-get install tesseract-ocr")
        print("   macOS: brew install tesseract")

if __name__ == "__main__":
    main()
