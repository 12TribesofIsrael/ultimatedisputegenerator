#!/usr/bin/env python3
"""
Monitored ingestion process that shows real-time progress.

This script runs the enhanced ingestion with live monitoring so you can
see exactly what's happening during the process.

Author: AI Assistant
Date: 2024
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

def run_ingestion():
    """Run the enhanced ingestion process."""
    print("🚀 Starting Enhanced Ingestion Process...")
    try:
        # Run enhanced ingestion
        result = subprocess.run(
            [sys.executable, "enhanced_ingest.py"],
            capture_output=False,  # Let output show in real-time
            text=True
        )
        return result.returncode
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        return 1

def run_monitor():
    """Run the progress monitor."""
    try:
        subprocess.run([sys.executable, "ingestion_monitor.py"])
    except Exception as e:
        print(f"❌ Monitor error: {e}")

def main():
    """Main entry point - runs ingestion with monitoring."""
    print("🔍 Enhanced Ingestion with Real-Time Monitoring")
    print("=" * 60)
    print("This will show you live progress as files are processed.")
    print("Press Ctrl+C to stop at any time.")
    print("=" * 60)
    
    # Start monitor in separate thread
    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()
    
    # Give monitor time to start
    time.sleep(2)
    
    # Run ingestion
    try:
        return_code = run_ingestion()
        
        print("\n🏁 Ingestion process completed!")
        print(f"Exit code: {return_code}")
        
        return return_code
        
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
