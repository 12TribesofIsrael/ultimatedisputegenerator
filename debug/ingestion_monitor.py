#!/usr/bin/env python3
"""
Real-time ingestion monitor with progress display.

This script provides live monitoring of the ingestion process with:
- Real-time progress updates
- Current file being processed
- Speed metrics
- ETA calculations
- Visual progress bar

Author: AI Assistant
Date: 2024
"""

import json
import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
import argparse
from typing import Dict, List, Optional

class IngestionMonitor:
    """Real-time monitor for ingestion progress."""
    
    def __init__(self, use_ascii: bool = False, interval: float = 2.0, duration: float = 0.0):
        self.manifest_path = Path("knowledgebase_index/ingestion_manifest.jsonl")
        self.log_path = Path("ingestion_monitor.log")
        self.initial_count = 0
        self.start_time = None
        self.running = False
        self.use_ascii = use_ascii
        self.interval = max(0.25, float(interval))
        self.duration = max(0.0, float(duration))
        
    def get_indexed_count(self) -> int:
        """Count currently indexed files."""
        if not self.manifest_path.exists():
            return 0
        
        count = 0
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        count += 1
        except Exception:
            pass
        return count
    
    def get_total_files_to_process(self) -> int:
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
    
    def format_time(self, seconds: float) -> str:
        """Format seconds into readable time."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def create_progress_bar(self, current: int, total: int, width: int = 50) -> str:
        """Create a visual progress bar."""
        if total == 0:
            percent = 0
        else:
            percent = current / total
        
        filled = int(width * percent)
        if self.use_ascii:
            bar = "=" * filled + "-" * (width - filled)
        else:
            bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percent*100:.1f}%"
    
    def log_status(self, message: str):
        """Log status to file and print."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"{timestamp} - {message}"
        
        print(f"\r{log_msg}")
        
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_msg + "\n")
        except Exception:
            pass
    
    def monitor_loop(self):
        """Main monitoring loop."""
        print("Starting Ingestion Monitor...")
        print("=" * 80)
        
        # Get initial state
        self.initial_count = self.get_indexed_count()
        total_files = self.get_total_files_to_process()
        self.start_time = time.time()
        
        print("Initial Status:")
        print(f"   - Files already indexed: {self.initial_count}")
        print(f"   - Total files to process: {total_files}")
        print(f"   - Files remaining: {total_files - self.initial_count}")
        print()
        
        last_count = self.initial_count
        last_update_time = time.time()
        no_change_duration = 0
        
        while self.running:
            try:
                current_count = self.get_indexed_count()
                current_time = time.time()
                elapsed_time = current_time - self.start_time
                
                # Calculate progress
                files_processed = current_count - self.initial_count
                files_remaining = total_files - current_count
                
                # Calculate speed
                if current_count > last_count:
                    last_update_time = current_time
                    no_change_duration = 0
                else:
                    no_change_duration = current_time - last_update_time
                
                # Calculate processing speed
                if elapsed_time > 0:
                    files_per_second = files_processed / elapsed_time
                    files_per_minute = files_per_second * 60
                else:
                    files_per_second = 0
                    files_per_minute = 0
                
                # Calculate ETA
                if files_per_second > 0 and files_remaining > 0:
                    eta_seconds = files_remaining / files_per_second
                    eta_str = self.format_time(eta_seconds)
                else:
                    eta_str = "calculating..."
                
                # Create progress display
                progress_bar = self.create_progress_bar(current_count, total_files)
                
                # Clear line and print status
                print(f"\r{' ' * 120}", end='')  # Clear line
                status_line = (
                    f"\rProgress: {current_count}/{total_files} files | "
                    f"{progress_bar} | "
                    f"Speed: {files_per_minute:.1f}/min | "
                    f"ETA: {eta_str} | "
                    f"Runtime: {self.format_time(elapsed_time)}"
                )
                
                # Add warning if no progress
                if no_change_duration > 30:
                    status_line += f"  WARNING: No progress for {self.format_time(no_change_duration)}"
                
                print(status_line, end='', flush=True)
                
                last_count = current_count
                
                # Check if completed
                if current_count >= total_files:
                    print("\nIngestion completed!")
                    break

                # Stop after requested duration
                if self.duration and (elapsed_time >= self.duration):
                    print("\nStopping monitor after requested duration.")
                    break

                time.sleep(self.interval)  # Update periodically
                
            except KeyboardInterrupt:
                print("\nMonitor stopped by user")
                break
            except Exception as e:
                print(f"\nMonitor error: {e}")
                time.sleep(5)
        
        # Final status
        final_count = self.get_indexed_count()
        final_processed = final_count - self.initial_count
        final_elapsed = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("Final Results:")
        print(f"   - Files processed this session: {final_processed}")
        print(f"   - Total files indexed: {final_count}/{total_files}")
        print(f"   - Total runtime: {self.format_time(final_elapsed)}")
        if final_processed > 0 and final_elapsed > 0:
            avg_speed = final_processed / final_elapsed * 60
            print(f"   - Average speed: {avg_speed:.1f} files/minute")
        print("=" * 80)
    
    def start(self):
        """Start monitoring."""
        self.running = True
        self.monitor_loop()
    
    def stop(self):
        """Stop monitoring."""
        self.running = False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Real-time ingestion monitor")
    parser.add_argument("--ascii", action="store_true", help="Use ASCII-only output (Windows-safe)")
    parser.add_argument("--interval", type=float, default=2.0, help="Refresh interval in seconds")
    parser.add_argument("--duration", type=float, default=0.0, help="Stop after N seconds (0 = run until done)")
    args = parser.parse_args()

    monitor = IngestionMonitor(use_ascii=args.ascii, interval=args.interval, duration=args.duration)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\nMonitor interrupted")
        monitor.stop()
    except Exception as e:
        print(f"\nMonitor error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
