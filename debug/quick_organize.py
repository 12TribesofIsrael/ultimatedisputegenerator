#!/usr/bin/env python
"""
Quick organize unprocessable files
Simple and fast organization without complex analysis
"""
import shutil
from pathlib import Path

# Setup
KB_DIR = Path("knowledgebase")
UNPROCESSABLE_DIR = KB_DIR / "unprocessable_files"

# File types that CAN be processed
PROCESSABLE = {'.pdf', '.docx', '.txt', '.json', '.csv'}

def main():
    print("🚚 QUICK FILE ORGANIZATION")
    print("=" * 30)
    
    # Create unprocessable directory
    UNPROCESSABLE_DIR.mkdir(exist_ok=True)
    
    # Find all files
    all_files = list(KB_DIR.rglob("*"))
    files_to_move = []
    
    for file_path in all_files:
        if not file_path.is_file():
            continue
        
        # Skip if already in unprocessable directory
        if "unprocessable_files" in str(file_path):
            continue
            
        ext = file_path.suffix.lower()
        
        # Move if not processable
        if ext not in PROCESSABLE:
            files_to_move.append(file_path)
    
    print(f"📁 Found {len(files_to_move)} unprocessable files")
    
    # Move files
    moved_count = 0
    for file_path in files_to_move:
        try:
            # Create target path
            rel_path = file_path.relative_to(KB_DIR)
            target_path = UNPROCESSABLE_DIR / rel_path
            
            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(file_path), str(target_path))
            moved_count += 1
            
        except Exception as e:
            print(f"❌ Failed to move {file_path.name}: {e}")
    
    print(f"✅ Moved {moved_count} files to {UNPROCESSABLE_DIR}")
    
    # Count remaining processable files
    remaining = list(KB_DIR.rglob("*"))
    processable_count = len([f for f in remaining if f.is_file() and f.suffix.lower() in PROCESSABLE])
    
    print(f"📊 Remaining processable files: {processable_count}")

if __name__ == "__main__":
    main()
