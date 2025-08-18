#!/usr/bin/env python3
"""
Quick status checker for ingestion progress.

Run this anytime to see current indexing status without starting the full process.

Author: AI Assistant
Date: 2024
"""

import json
from pathlib import Path
from datetime import datetime

def get_indexed_count():
    """Count currently indexed files."""
    manifest_path = Path("knowledgebase_index/ingestion_manifest.jsonl")
    if not manifest_path.exists():
        return 0
    
    count = 0
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    count += 1
    except Exception:
        pass
    return count

def get_total_files():
    """Count total files that could be processed."""
    kb_dir = Path("knowledgebase")
    if not kb_dir.exists():
        return 0
    
    count = 0
    supported_extensions = {'.pdf', '.txt', '.docx', '.csv', '.json', '.png', '.jpg', '.jpeg'}
    
    for file_path in kb_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            count += 1
    
    return count

def check_converted_docs():
    """Check how many DOC files were converted."""
    converted_dir = Path("knowledgebase/converted_docs")
    if not converted_dir.exists():
        return 0
    
    count = 0
    for file_path in converted_dir.rglob("*.pdf"):
        if file_path.is_file():
            count += 1
    
    return count

def main():
    """Show current status."""
    print("📊 Current Knowledgebase Status")
    print("=" * 50)
    print(f"🕒 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get counts
    indexed_count = get_indexed_count()
    total_files = get_total_files()
    converted_docs = check_converted_docs()
    
    # Calculate progress
    if total_files > 0:
        progress_percent = (indexed_count / total_files) * 100
    else:
        progress_percent = 0
    
    # Display status
    print(f"📁 Files indexed: {indexed_count:,}")
    print(f"📁 Total files available: {total_files:,}")
    print(f"📄 DOC files converted to PDF: {converted_docs}")
    print(f"📈 Progress: {progress_percent:.1f}%")
    print()
    
    # Progress bar
    bar_width = 40
    filled = int(bar_width * (progress_percent / 100))
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"[{bar}] {progress_percent:.1f}%")
    print()
    
    # Status message
    if progress_percent >= 95:
        print("🎉 Knowledgebase is nearly complete!")
    elif progress_percent >= 80:
        print("🚀 Great progress! Almost there.")
    elif progress_percent >= 50:
        print("📈 Good progress so far.")
    elif progress_percent >= 20:
        print("🔄 Processing is underway.")
    else:
        print("🚀 Ready to start processing.")
    
    # Files remaining
    remaining = total_files - indexed_count
    if remaining > 0:
        print(f"📋 Files remaining to process: {remaining:,}")
    
    print("=" * 50)
    
    # Show recent activity
    manifest_path = Path("knowledgebase_index/ingestion_manifest.jsonl")
    if manifest_path.exists():
        try:
            # Get last few entries
            with open(manifest_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if lines:
                print("🕒 Recent Activity:")
                for line in lines[-3:]:  # Show last 3 entries
                    try:
                        entry = json.loads(line.strip())
                        file_name = entry.get('file_name', 'Unknown')
                        timestamp = entry.get('ingest_timestamp', '')
                        if timestamp:
                            # Parse timestamp and format nicely
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime('%H:%M:%S')
                        else:
                            time_str = 'Unknown time'
                        print(f"   {time_str} - {file_name}")
                    except:
                        continue
        except Exception:
            pass
    
    return 0

if __name__ == "__main__":
    main()
