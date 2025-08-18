#!/usr/bin/env python3
"""
Monitored Knowledgebase Ingestion with Real-time Progress
Shows exactly what's happening during the ingestion process
"""
import os
import sys
import time
import subprocess
from pathlib import Path
import json
from datetime import datetime

def count_files_in_knowledgebase():
    """Count total files in knowledgebase directory"""
    kb_dir = Path("knowledgebase")
    count = 0
    for file_path in kb_dir.rglob("*"):
        if file_path.is_file():
            count += 1
    return count

def get_current_indexed_count():
    """Get current number of indexed files"""
    manifest_path = Path("knowledgebase_index/ingestion_manifest.jsonl")
    if not manifest_path.exists():
        return 0
    
    count = 0
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and line.strip().startswith('{'):
                    count += 1
    except:
        pass
    return count

def monitor_ingestion():
    """Monitor the ingestion process with real-time updates"""
    print("🔍 MONITORED KNOWLEDGEBASE INGESTION")
    print("=" * 50)
    
    # Initial counts
    total_files = count_files_in_knowledgebase()
    initial_indexed = get_current_indexed_count()
    
    print(f"📊 INITIAL STATUS:")
    print(f"   Total files in knowledgebase: {total_files}")
    print(f"   Currently indexed: {initial_indexed}")
    print(f"   Current coverage: {(initial_indexed/total_files)*100:.1f}%")
    print()
    
    print("🚀 STARTING INGESTION PROCESS...")
    print("⏱️  Monitoring progress every 10 seconds...")
    print()
    
    # Start the ingestion process
    start_time = time.time()
    
    try:
        # Run the ingestion script
        process = subprocess.Popen(
            [sys.executable, "debug/knowledgebase_ingest.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        last_count = initial_indexed
        check_count = 0
        
        while True:
            # Check if process is still running
            if process.poll() is not None:
                break
                
            # Wait 10 seconds
            time.sleep(10)
            check_count += 1
            
            # Get current indexed count
            current_count = get_current_indexed_count()
            elapsed = time.time() - start_time
            
            # Calculate progress
            new_files = current_count - last_count
            total_new = current_count - initial_indexed
            current_coverage = (current_count/total_files)*100 if total_files > 0 else 0
            
            print(f"⏰ Check #{check_count} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"   Elapsed time: {elapsed/60:.1f} minutes")
            print(f"   Files indexed: {current_count} (+{new_files} this check)")
            print(f"   Total new files: +{total_new}")
            print(f"   Coverage: {current_coverage:.1f}%")
            print(f"   Process status: {'Running' if process.poll() is None else 'Completed'}")
            print()
            
            last_count = current_count
            
            # If no progress for 3 checks, show warning
            if check_count >= 3 and total_new == 0:
                print("⚠️  WARNING: No new files indexed in last 30 seconds")
                print("   Process may be stuck or processing large files...")
                print()
    
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user")
        process.terminate()
        return
    
    # Get final results
    stdout, stderr = process.communicate()
    final_count = get_current_indexed_count()
    total_time = time.time() - start_time
    
    print("🎉 INGESTION COMPLETED!")
    print("=" * 50)
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"📊 Final results:")
    print(f"   Initial indexed: {initial_indexed}")
    print(f"   Final indexed: {final_count}")
    print(f"   New files indexed: +{final_count - initial_indexed}")
    print(f"   Final coverage: {(final_count/total_files)*100:.1f}%")
    
    if stderr:
        print(f"\n⚠️  Errors/Warnings:")
        print(stderr)
    
    print(f"\n✅ Process completed successfully!")

if __name__ == "__main__":
    monitor_ingestion()
