#!/usr/bin/env python3
"""
Install all dependencies required for robust DOC to PDF conversion.

This script installs:
- Python packages for document processing
- Checks for LibreOffice installation
- Provides guidance for missing components

Author: AI Assistant
Date: 2024
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path


def install_python_packages():
    """Install required Python packages."""
    packages = [
        'docx2txt',         # Text extraction from DOC files
        'pypandoc',         # Universal document converter
        'reportlab',        # PDF generation
        'concurrent.futures', # Parallel processing (usually built-in)
    ]
    
    print("🔧 Installing Python packages...")
    
    for package in packages:
        try:
            # Check if already installed
            if package == 'concurrent.futures':
                import concurrent.futures
                print(f"✓ {package} (built-in)")
                continue
                
            __import__(package.replace('-', '_'))
            print(f"✓ {package} (already installed)")
        except ImportError:
            print(f"📦 Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package
                ])
                print(f"✓ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
                return False
    
    return True


def check_libreoffice():
    """Check if LibreOffice is installed."""
    print("\n🔍 Checking LibreOffice installation...")
    
    candidates = [
        "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    
    for candidate in candidates:
        if shutil.which(candidate) or Path(candidate).exists():
            try:
                result = subprocess.run(
                    [candidate, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"✓ LibreOffice found: {version}")
                    return True
            except Exception:
                continue
    
    print("❌ LibreOffice not found!")
    print("📋 To install LibreOffice:")
    print("   Option 1: Download from https://www.libreoffice.org/download/")
    print("   Option 2: Use winget: winget install TheDocumentFoundation.LibreOffice")
    print("   Option 3: Use chocolatey: choco install libreoffice")
    return False


def check_pandoc():
    """Check if pandoc is installed."""
    print("\n🔍 Checking pandoc installation...")
    
    if shutil.which("pandoc"):
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✓ Pandoc found: {version_line}")
                return True
        except Exception:
            pass
    
    print("⚠️  Pandoc not found (optional but recommended)")
    print("📋 To install pandoc:")
    print("   Option 1: Download from https://pandoc.org/installing.html")
    print("   Option 2: Use winget: winget install JohnMacFarlane.Pandoc")
    print("   Option 3: Use chocolatey: choco install pandoc")
    return False


def check_system_requirements():
    """Check system requirements and environment."""
    print("\n🖥️  Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 6):
        print(f"❌ Python {sys.version} is too old. Requires Python 3.6+")
        return False
    else:
        print(f"✓ Python {sys.version}")
    
    # Check available disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free // (1024**3)
        if free_gb < 1:
            print(f"⚠️  Low disk space: {free_gb}GB available")
        else:
            print(f"✓ Disk space: {free_gb}GB available")
    except Exception:
        print("⚠️  Could not check disk space")
    
    return True


def setup_directories():
    """Setup required directories."""
    print("\n📁 Setting up directories...")
    
    directories = [
        Path("knowledgebase/converted_docs"),
        Path("knowledgebase_index"),
    ]
    
    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ {dir_path}")
        except Exception as e:
            print(f"❌ Failed to create {dir_path}: {e}")
            return False
    
    return True


def main():
    """Main installation process."""
    print("🚀 DOC Converter Dependencies Installation")
    print("=" * 50)
    
    success = True
    
    # Check system requirements
    if not check_system_requirements():
        success = False
    
    # Install Python packages
    if not install_python_packages():
        success = False
    
    # Check external tools
    libreoffice_ok = check_libreoffice()
    pandoc_ok = check_pandoc()
    
    # Setup directories
    if not setup_directories():
        success = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Installation Summary:")
    print(f"✓ Python packages: {'OK' if success else 'FAILED'}")
    print(f"{'✓' if libreoffice_ok else '❌'} LibreOffice: {'OK' if libreoffice_ok else 'MISSING'}")
    print(f"{'✓' if pandoc_ok else '⚠️ '} Pandoc: {'OK' if pandoc_ok else 'MISSING (optional)'}")
    
    if success and libreoffice_ok:
        print("\n🎉 All required dependencies installed!")
        print("💡 You can now run: python robust_doc_converter.py")
    elif success:
        print("\n⚠️  Core dependencies installed, but LibreOffice is missing.")
        print("💡 The converter will work with limited functionality.")
        print("💡 Install LibreOffice for best results.")
    else:
        print("\n❌ Some dependencies failed to install.")
        print("💡 Please resolve the issues above and try again.")
    
    return 0 if (success and libreoffice_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
