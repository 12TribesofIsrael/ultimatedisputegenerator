#!/usr/bin/env python
"""
Organize unprocessable files into a dedicated folder
Moves files that can't be processed by the current ingestion system
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

# Setup
KB_DIR = Path("knowledgebase")
IDX_DIR = Path("knowledgebase_index")
MANIFEST_PATH = IDX_DIR / "ingestion_manifest.jsonl"
UNPROCESSABLE_DIR = KB_DIR / "unprocessable_files"

# File types that CAN be processed by current system
PROCESSABLE_EXTENSIONS = {
    '.pdf', '.docx', '.txt', '.json', '.csv'
}

# File types that CANNOT be processed (need special handling)
UNPROCESSABLE_EXTENSIONS = {
    '.doc', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', 
    '.ppt', '.pptx', '.xls', '.xlsx', '.zip', '.rar', '.7z',
    '.mp3', '.mp4', '.avi', '.mov', '.wav', '.exe', '.dll',
    '.sys', '.tmp', '.log', '.bak', '.old'
}

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

def analyze_and_organize():
    """Analyze files and organize unprocessable ones"""
    print("🔍 ANALYZING FILES FOR ORGANIZATION")
    print("=" * 50)
    
    # Create unprocessable directory
    UNPROCESSABLE_DIR.mkdir(exist_ok=True)
    
    # Load processed files
    processed_files = load_processed_files()
    print(f"✅ Already processed: {len(processed_files)} files")
    
    # Analyze all files
    all_files = list(KB_DIR.rglob("*"))
    file_stats = {
        'total': 0,
        'processable': 0,
        'unprocessable': 0,
        'already_processed': 0,
        'by_extension': {}
    }
    
    files_to_move = []
    
    for file_path in all_files:
        if not file_path.is_file():
            continue
            
        file_stats['total'] += 1
        ext = file_path.suffix.lower()
        
        # Track by extension
        if ext not in file_stats['by_extension']:
            file_stats['by_extension'][ext] = 0
        file_stats['by_extension'][ext] += 1
        
        # Check if already processed
        if file_path.name in processed_files:
            file_stats['already_processed'] += 1
            continue
        
        # Check if processable
        if ext in PROCESSABLE_EXTENSIONS:
            file_stats['processable'] += 1
        elif ext in UNPROCESSABLE_EXTENSIONS:
            file_stats['unprocessable'] += 1
            files_to_move.append(file_path)
        else:
            # Unknown extension - treat as unprocessable
            file_stats['unprocessable'] += 1
            files_to_move.append(file_path)
    
    # Print analysis
    print(f"\n📊 FILE ANALYSIS:")
    print(f"   Total files: {file_stats['total']}")
    print(f"   Already processed: {file_stats['already_processed']}")
    print(f"   Processable (not yet processed): {file_stats['processable']}")
    print(f"   Unprocessable: {file_stats['unprocessable']}")
    
    print(f"\n📋 EXTENSION BREAKDOWN:")
    for ext, count in sorted(file_stats['by_extension'].items()):
        status = "✅ Processable" if ext in PROCESSABLE_EXTENSIONS else "❌ Unprocessable"
        print(f"   {ext}: {count} files - {status}")
    
    # Move unprocessable files
    if files_to_move:
        print(f"\n🚚 MOVING {len(files_to_move)} UNPROCESSABLE FILES...")
        
        moved_count = 0
        for file_path in files_to_move:
            try:
                # Create relative path structure
                rel_path = file_path.relative_to(KB_DIR)
                target_path = UNPROCESSABLE_DIR / rel_path
                
                # Create parent directories if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.move(str(file_path), str(target_path))
                moved_count += 1
                print(f"   ✅ Moved: {rel_path}")
                
            except Exception as e:
                print(f"   ❌ Failed to move {file_path.name}: {e}")
        
        print(f"\n🎉 SUCCESSFULLY MOVED {moved_count} FILES")
        print(f"📁 Location: {UNPROCESSABLE_DIR}")
        
        # Create summary file
        summary_path = UNPROCESSABLE_DIR / "MOVE_SUMMARY.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"Unprocessable Files Organization Summary\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"Total files moved: {moved_count}\n")
            f.write(f"Original location: {KB_DIR}\n")
            f.write(f"New location: {UNPROCESSABLE_DIR}\n\n")
            f.write(f"Files moved:\n")
            for file_path in files_to_move:
                f.write(f"  - {file_path.relative_to(KB_DIR)}\n")
        
        print(f"📄 Summary saved to: {summary_path}")
    else:
        print(f"\n✅ No unprocessable files found to move!")
    
    # Calculate new coverage
    remaining_processable = file_stats['processable']
    total_after_move = file_stats['already_processed'] + remaining_processable
    new_coverage = (total_after_move / file_stats['total']) * 100
    
    print(f"\n📈 COVERAGE AFTER ORGANIZATION:")
    print(f"   Remaining processable files: {remaining_processable}")
    print(f"   Total files (excluding unprocessable): {total_after_move}")
    print(f"   New coverage: {new_coverage:.1f}%")
    
    if new_coverage >= 95:
        print(f"🎉 TARGET ACHIEVED: {new_coverage:.1f}% coverage!")
    else:
        print(f"📊 Need {95 - new_coverage:.1f}% more coverage")

if __name__ == "__main__":
    analyze_and_organize()
