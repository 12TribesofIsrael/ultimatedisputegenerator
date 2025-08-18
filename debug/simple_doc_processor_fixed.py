#!/usr/bin/env python
"""
Simple DOC processor - Direct text extraction
Uses PyMuPDF to extract text from DOC files directly
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from hashlib import sha256

# Setup
KB_DIR = Path("knowledgebase")
IDX_DIR = Path("knowledgebase_index")
MANIFEST_PATH = IDX_DIR / "ingestion_manifest.jsonl"

def load_processed_files():
    """Load list of already processed files"""
    if not MANIFEST_PATH.exists():
        return set()
    
    processed = set()
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                processed.add(entry["file_name"])
            except:
                continue
    return processed

def extract_text_from_doc(file_path):
    """Extract text from DOC files using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        
        size_mb = file_path.stat().st_size / 1024 / 1024
        if size_mb > 5:  # Skip very large files
            print(f"   ⚠️  Skipping large file {file_path.name} ({size_mb:.1f}MB)")
            return ""
        
        # Try to open with PyMuPDF
        with fitz.open(str(file_path)) as doc:
            text = ""
            max_pages = min(len(doc), 20)  # Limit pages for speed
            
            for i in range(max_pages):
                try:
                    page_text = doc[i].get_text()
                    if page_text.strip():
                        text += page_text + "\n"
                except:
                    continue
            
            return text[:50000]  # Limit text length
            
    except Exception as e:
        print(f"   ❌ Failed to extract from {file_path.name}: {e}")
        return ""

def main():
    print("📄 SIMPLE DOC PROCESSOR - DIRECT EXTRACTION")
    print("=" * 50)
    
    # Find all DOC files
    doc_files = list(KB_DIR.rglob("*.doc"))
    print(f"📁 Found {len(doc_files)} DOC files")
    
    # Find unprocessed DOC files
    processed_files = load_processed_files()
    unprocessed_docs = []
    
    for doc_file in doc_files:
        relative_path = str(doc_file.relative_to(KB_DIR))
        if relative_path not in processed_files:
            unprocessed_docs.append(doc_file)
    
    print(f"🔄 Need to process: {len(unprocessed_docs)} DOC files")
    
    if len(unprocessed_docs) == 0:
        print("✅ All DOC files already processed!")
        return
    
    # Test extraction on first few files
    print(f"\n🧪 TESTING TEXT EXTRACTION")
    print("=" * 50)
    
    successful_extractions = 0
    total_tested = min(5, len(unprocessed_docs))
    
    for i, doc_file in enumerate(unprocessed_docs[:total_tested]):
        print(f"📄 Testing {i+1}/{total_tested}: {doc_file.name}")
        
        text = extract_text_from_doc(doc_file)
        if text and len(text.strip()) > 20:
            print(f"   ✅ Success! Extracted {len(text)} characters")
            successful_extractions += 1
        else:
            print(f"   ❌ Failed or no meaningful text")
    
    success_rate = (successful_extractions / total_tested) * 100
    print(f"\n📊 EXTRACTION TEST RESULTS:")
    print(f"   Success rate: {success_rate:.1f}% ({successful_extractions}/{total_tested})")
    
    if success_rate >= 50:
        print(f"✅ Good success rate! Ready to process all DOC files.")
        print(f"💡 Run: python doc_only_processor.py")
    else:
        print(f"⚠️  Low success rate. DOC files may be in unsupported format.")
        print(f"💡 Alternative: Try converting DOC files to DOCX first")

if __name__ == "__main__":
    main()
