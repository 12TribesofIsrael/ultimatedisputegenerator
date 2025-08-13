#!/usr/bin/env python3
"""
🧹 WORKSPACE CLEANUP SYSTEM
Smart cleanup utility for Ultimate Dispute Letter Generator
Prevents file conflicts and keeps workspace organized
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import json

def check_existing_files():
    """Check if outputletter directory has existing files"""
    outputletter_path = Path("outputletter")
    
    if not outputletter_path.exists():
        return False, []
    
    existing_files = []
    bureau_folders = ["Experian", "Equifax", "TransUnion", "Creditors", "Analysis"]
    
    for folder in bureau_folders:
        folder_path = outputletter_path / folder
        try:
            if folder_path.exists():
                files = list(folder_path.glob("*"))
                if files:
                    existing_files.extend([(folder, len(files))])
        except PermissionError:
            # Skip folders we can't stat due to sync locks (OneDrive/Drive)
            continue
    
    return len(existing_files) > 0, existing_files

def display_cleanup_menu(existing_files):
    """Display cleanup options to user"""
    print("\n" + "="*60)
    print("🧹 WORKSPACE CLEANUP - EXISTING FILES DETECTED")
    print("="*60)
    
    print("\n📁 Current files found:")
    for folder, count in existing_files:
        print(f"   • {folder}/: {count} files")
    
    print(f"\n🎯 CLEANUP OPTIONS:")
    print("1. 🗑️  Clean All (delete all outputletter/ contents)")
    print("2. 🎯 Smart Clean (keep only latest per bureau) [RECOMMENDED]")
    print("3. 📅 Date Clean (remove files older than 7 days)")
    print("4. ❌ Keep All (continue without cleaning)")
    print("5. 🚪 Exit (stop processing)")
    
    while True:
        try:
            choice = input(f"\n🤔 Choose option (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return int(choice)
            else:
                print("❌ Please enter a number between 1-5")
        except KeyboardInterrupt:
            print("\n\n🚪 User cancelled. Exiting...")
            return 5

def clean_all():
    """Option 1: Delete entire outputletter directory"""
    outputletter_path = Path("outputletter")
    
    if outputletter_path.exists():
        # On Windows/Cloud drives, files may be locked. ignore_errors avoids EPERM.
        shutil.rmtree(outputletter_path, ignore_errors=True)
        print("✅ All files deleted from outputletter/")
    else:
        print("ℹ️  No outputletter/ directory found")
    
    return True

def smart_clean():
    """Option 2: Keep only the most recent file set per bureau"""
    outputletter_path = Path("outputletter")
    
    if not outputletter_path.exists():
        print("ℹ️  No outputletter/ directory found")
        return True
    
    bureau_folders = ["Experian", "Equifax", "TransUnion"]
    files_removed = 0
    
    for bureau in bureau_folders:
        bureau_path = outputletter_path / bureau
        if not bureau_path.exists():
            continue
        
        # Find all markdown files (main dispute letters)
        md_files = list(bureau_path.glob("*_DELETION_DEMAND_*.md"))
        
        if len(md_files) <= 1:
            continue  # Keep if only one or no files
        
        # Sort by creation time, keep newest
        def safe_mtime(p: Path) -> float:
            try:
                return p.stat().st_mtime
            except Exception:
                return 0.0
        md_files.sort(key=safe_mtime, reverse=True)
        newest_md = md_files[0]
        
        # Extract date from newest file for matching related files
        newest_date = None
        for part in newest_md.stem.split('_'):
            if len(part) == 10 and part.count('-') == 2:  # YYYY-MM-DD format
                newest_date = part
                break
        
        # Remove older files
        for old_md in md_files[1:]:
            try:
                old_md.unlink()
                files_removed += 1
                print(f"🗑️  Removed old file: {old_md.name}")
                
                # Remove related files (editable txt, pdf) with same date
                old_date = None
                for part in old_md.stem.split('_'):
                    if len(part) == 10 and part.count('-') == 2:
                        old_date = part
                        break
                
                if old_date:
                    # Remove related editable and PDF files
                    for related_file in bureau_path.glob(f"*{old_date}*"):
                        try:
                            if related_file != old_md and related_file.exists():
                                related_file.unlink()
                                files_removed += 1
                                print(f"🗑️  Removed related: {related_file.name}")
                        except Exception as e:
                            print(f"❌ Error removing related {related_file.name}: {e}")
                            
            except Exception as e:
                print(f"❌ Error removing {old_md.name}: {e}")
    
    # Clean empty bureau folders
    for bureau in bureau_folders:
        bureau_path = outputletter_path / bureau
        try:
            if bureau_path.exists() and not any(bureau_path.iterdir()):
                bureau_path.rmdir()
                print(f"📁 Removed empty folder: {bureau}/")
        except Exception:
            pass
    
    if files_removed > 0:
        print(f"✅ Smart clean complete: {files_removed} old files removed")
    else:
        print("ℹ️  No old files found to remove")
    
    return True

def date_clean(days=7):
    """Option 3: Remove files older than specified days"""
    outputletter_path = Path("outputletter")
    
    if not outputletter_path.exists():
        print("ℹ️  No outputletter/ directory found")
        return True
    
    cutoff_date = datetime.now() - timedelta(days=days)
    files_removed = 0
    
    # Check all subdirectories
    for item in outputletter_path.rglob("*"):
        if item.is_file():
            try:
                file_time = datetime.fromtimestamp(item.stat().st_mtime)
                if file_time < cutoff_date:
                    item.unlink()
                    files_removed += 1
                    print(f"🗑️  Removed old file: {item.relative_to(outputletter_path)}")
            except Exception as e:
                print(f"❌ Error removing {item.name}: {e}")
    
    # Clean empty directories
    for item in outputletter_path.rglob("*"):
        if item.is_dir() and not any(item.iterdir()):
            try:
                item.rmdir()
                print(f"📁 Removed empty folder: {item.relative_to(outputletter_path)}")
            except:
                pass
    
    if files_removed > 0:
        print(f"✅ Date clean complete: {files_removed} files older than {days} days removed")
    else:
        print(f"ℹ️  No files older than {days} days found")
    
    return True

def keep_all():
    """Option 4: Keep all files (no cleaning)"""
    print("ℹ️  Keeping all existing files. Processing will continue...")
    print("⚠️  Warning: Multiple files may cause confusion in PDF conversion")
    return True

def cleanup_workspace(auto_mode=False):
    """Main cleanup function"""
    
    # Check for existing files
    has_files, existing_files = check_existing_files()
    
    if not has_files:
        if not auto_mode:
            print("✅ Workspace is clean - no existing files found")
        return True
    
    # Determine non-interactive choice via environment override (useful for CI/automation)
    try:
        env_choice = os.environ.get('CLEAN_CHOICE')
        if env_choice and env_choice.strip() in {'1','2','3','4','5'}:
            choice = int(env_choice.strip())
        else:
            # In auto mode, still allow interactive prompt unless overridden by env
            choice = display_cleanup_menu(existing_files)
    except Exception:
        choice = display_cleanup_menu(existing_files)
    
    # Execute chosen action
    if choice == 1:
        return clean_all()
    elif choice == 2:
        return smart_clean()
    elif choice == 3:
        return date_clean()
    elif choice == 4:
        return keep_all()
    elif choice == 5:
        print("🚪 Cleanup cancelled. Exiting...")
        return False
    
    return True

def main():
    """Run cleanup as standalone script"""
    print("🧹 ULTIMATE DISPUTE LETTER GENERATOR - WORKSPACE CLEANUP")
    print("=" * 60)
    
    success = cleanup_workspace(auto_mode=False)
    
    if success:
        print("\n✅ Cleanup completed successfully!")
    else:
        print("\n❌ Cleanup cancelled or failed")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()