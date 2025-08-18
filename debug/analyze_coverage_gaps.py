#!/usr/bin/env python
"""
Analyze coverage gaps to reach 95% knowledgebase indexing
"""
import json
from pathlib import Path
from collections import defaultdict

def load_processed_files():
    """Load list of already processed files"""
    manifest_path = Path("knowledgebase_index/ingestion_manifest.jsonl")
    if not manifest_path.exists():
        return set()
    
    processed = set()
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                processed.add(entry["file_name"])
            except:
                continue
    return processed

def analyze_knowledgebase():
    """Analyze all files in knowledgebase and categorize them"""
    kb_dir = Path("knowledgebase")
    if not kb_dir.exists():
        print("❌ Knowledgebase directory not found")
        return
    
    # Get all files
    all_files = list(kb_dir.rglob("*"))
    files = [f for f in all_files if f.is_file()]
    
    # Categorize by extension
    by_extension = defaultdict(list)
    by_size = defaultdict(list)
    
    for file_path in files:
        ext = file_path.suffix.lower()
        size_mb = file_path.stat().st_size / 1024 / 1024
        
        by_extension[ext].append(file_path)
        by_size[ext].append(size_mb)
    
    return files, by_extension, by_size

def categorize_file_types():
    """Categorize file types by processing capability"""
    return {
        "fully_supported": ['.pdf', '.docx', '.txt', '.json', '.csv'],
        "enhanced_support": ['.doc', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'],
        "limited_support": ['.ppt', '.pptx', '.xls', '.xlsx'],
        "no_support": ['.zip', '.rar', '.7z', '.exe', '.dll', '.sys', '.tmp', '.log']
    }

def main():
    print("🔍 ANALYZING KNOWLEDGEBASE COVERAGE GAPS")
    print("=" * 60)
    
    # Load processed files
    processed_files = load_processed_files()
    print(f"📋 Currently processed: {len(processed_files)} files")
    
    # Analyze knowledgebase
    files, by_extension, by_size = analyze_knowledgebase()
    print(f"📁 Total files in knowledgebase: {len(files)}")
    
    # Categorize file types
    categories = categorize_file_types()
    
    print("\n📊 FILE TYPE ANALYSIS")
    print("-" * 60)
    
    total_processed = 0
    total_processable = 0
    total_enhanceable = 0
    
    for ext, file_list in by_extension.items():
        count = len(file_list)
        avg_size = sum(by_size[ext]) / len(by_size[ext]) if by_size[ext] else 0
        
        # Count processed files of this type
        processed_count = sum(1 for f in file_list if str(f.relative_to(Path("knowledgebase"))) in processed_files)
        
        if ext in categories["fully_supported"]:
            status = "✅ Fully Supported"
            total_processable += count
            total_processed += processed_count
        elif ext in categories["enhanced_support"]:
            status = "🔄 Enhanced Support"
            total_enhanceable += count
        elif ext in categories["limited_support"]:
            status = "⚠️  Limited Support"
        elif ext in categories["no_support"]:
            status = "❌ No Support"
        else:
            status = "❓ Unknown"
        
        print(f"{ext:>8}: {count:>4} files ({processed_count:>3} processed) - {status} - Avg: {avg_size:.1f}MB")
    
    print("\n🎯 COVERAGE ANALYSIS")
    print("-" * 60)
    
    current_coverage = (total_processed / len(files)) * 100 if files else 0
    potential_coverage = ((total_processed + total_enhanceable) / len(files)) * 100 if files else 0
    
    print(f"📈 Current coverage: {current_coverage:.1f}%")
    print(f"🎯 Potential coverage with enhancements: {potential_coverage:.1f}%")
    print(f"📊 Files to process for 95%: {int(len(files) * 0.95) - total_processed}")
    
    print("\n🚀 ENHANCEMENT OPPORTUNITIES")
    print("-" * 60)
    
    for ext in categories["enhanced_support"]:
        if ext in by_extension:
            count = len(by_extension[ext])
            processed_count = sum(1 for f in by_extension[ext] if str(f.relative_to(Path("knowledgebase"))) in processed_files)
            unprocessed = count - processed_count
            
            if unprocessed > 0:
                print(f"📄 {ext}: {unprocessed} files to process")
                
                # Show some examples
                examples = [f.name for f in by_extension[ext][:3] if str(f.relative_to(Path("knowledgebase"))) not in processed_files]
                if examples:
                    print(f"   Examples: {', '.join(examples)}")
    
    print("\n💡 RECOMMENDATIONS")
    print("-" * 60)
    
    if potential_coverage >= 95:
        print("✅ Run enhanced_ingest.py to reach 95% coverage")
        print("✅ Install additional dependencies if needed")
    else:
        print("⚠️  Additional file type support needed")
        print("💡 Consider adding support for:")
        for ext in categories["limited_support"]:
            if ext in by_extension and len(by_extension[ext]) > 0:
                print(f"   - {ext} files ({len(by_extension[ext])} files)")
    
    print(f"\n📋 Next steps:")
    print(f"1. Run: python install_enhanced_deps.py")
    print(f"2. Run: python enhanced_ingest.py")
    print(f"3. Monitor progress and check final coverage")

if __name__ == "__main__":
    main()
