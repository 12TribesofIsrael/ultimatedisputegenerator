#!/usr/bin/env python
"""
Simple DOC processor - Quick 95% coverage boost
Just processes remaining DOC files to get to 95%
"""
import json
import sys
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

def main():
    print("📄 SIMPLE DOC PROCESSOR - QUICK 95% BOOST")
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
    
    # Show what we'll process
    print("\n📋 DOC files to process:")
    for i, doc_file in enumerate(unprocessed_docs[:10]):  # Show first 10
        print(f"   {i+1}. {doc_file.name}")
    
    if len(unprocessed_docs) > 10:
        print(f"   ... and {len(unprocessed_docs) - 10} more")
    
    # Calculate potential coverage
    total_files = len(list(KB_DIR.rglob("*")))
    current_processed = len(processed_files)
    potential_processed = current_processed + len(unprocessed_docs)
    potential_coverage = (potential_processed / total_files) * 100
    
    print(f"\n📊 COVERAGE PROJECTION:")
    print(f"   Current: {current_processed} files")
    print(f"   After DOC processing: {potential_processed} files")
    print(f"   Coverage: {potential_coverage:.1f}%")
    
    if potential_coverage >= 95:
        print("🎯 This will get us to 95% coverage!")
    else:
        print(f"⚠️  Still need {95 - potential_coverage:.1f}% more coverage")
    
    print(f"\n💡 To process these files, run:")
    print(f"   python quick_enhance_ingest.py")
    print(f"   or")
    print(f"   python visible_ingest.py")

if __name__ == "__main__":
    main()
