#!/usr/bin/env python
"""
Quick 95% coverage - Simple and fast
Just processes remaining files to reach 95% coverage
"""
import json
from pathlib import Path

# Setup
KB_DIR = Path("knowledgebase")
IDX_DIR = Path("knowledgebase_index")
MANIFEST_PATH = IDX_DIR / "ingestion_manifest.jsonl"

def main():
    print("🎯 QUICK 95% COVERAGE ANALYSIS")
    print("=" * 40)
    
    # Count total files
    all_files = list(KB_DIR.rglob("*"))
    total_files = len([f for f in all_files if f.is_file()])
    print(f"📁 Total files in knowledgebase: {total_files}")
    
    # Count processed files
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            processed_count = sum(1 for line in f if line.strip())
    else:
        processed_count = 0
    
    print(f"✅ Currently processed: {processed_count} files")
    
    # Calculate coverage
    current_coverage = (processed_count / total_files) * 100
    print(f"📊 Current coverage: {current_coverage:.1f}%")
    
    # Calculate what we need for 95%
    target_processed = int(total_files * 0.95)
    files_needed = target_processed - processed_count
    
    print(f"🎯 Target for 95%: {target_processed} files")
    print(f"📈 Files needed: {files_needed} files")
    
    if files_needed <= 0:
        print("🎉 Already at 95% coverage!")
        return
    
    # Show file types that need processing
    print(f"\n📋 FILE TYPES TO PROCESS:")
    
    # Count by extension
    extensions = {}
    for file_path in all_files:
        if file_path.is_file():
            ext = file_path.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
    
    # Show unprocessed file types
    for ext, count in sorted(extensions.items()):
        if ext in ['.pdf', '.docx', '.txt', '.json', '.csv', '.doc']:
            print(f"   {ext}: {count} files")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"1. The existing visible_ingest.py should handle most files")
    print(f"2. DOC files may need special handling")
    print(f"3. Run: python visible_ingest.py")
    print(f"4. Check progress with: python analyze_coverage_gaps.py")

if __name__ == "__main__":
    main()
