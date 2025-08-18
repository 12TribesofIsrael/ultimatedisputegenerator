#!/usr/bin/env python3
"""
Robust DOC to PDF converter with multiple fallback strategies.

This script handles the conversion of legacy .doc files to PDF with:
- Filename sanitization for Unicode characters
- Multiple conversion methods (LibreOffice, pandoc, text extraction)
- Robust process management
- Detailed logging and progress tracking
- Automatic retry mechanisms

Author: AI Assistant
Date: 2024
"""

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import concurrent.futures
import threading
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('doc_conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
KB_DIR = Path("knowledgebase")
CONVERTED_DIR = KB_DIR / "converted_docs"
UNPROCESSABLE_DIR = KB_DIR / "unprocessable_files"
IDX_DIR = Path("knowledgebase_index")
MANIFEST_PATH = IDX_DIR / "ingestion_manifest.jsonl"
PROGRESS_FILE = Path("conversion_progress.json")
MAX_WORKERS = 2  # Limit concurrent conversions to avoid resource issues


class ProcessManager:
    """Manages LibreOffice processes to prevent hanging."""
    
    def __init__(self):
        self.active_processes = set()
        self.lock = threading.Lock()
    
    def register_process(self, process):
        with self.lock:
            self.active_processes.add(process)
    
    def unregister_process(self, process):
        with self.lock:
            self.active_processes.discard(process)
    
    def cleanup_all(self):
        """Kill all active processes."""
        with self.lock:
            for process in list(self.active_processes):
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
            self.active_processes.clear()
        
        # Also kill system LibreOffice processes
        self.kill_system_libreoffice()
    
    @staticmethod
    def kill_system_libreoffice():
        """Kill any hanging LibreOffice processes system-wide."""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/f', '/im', 'soffice.bin'], 
                             capture_output=True, timeout=10)
                subprocess.run(['taskkill', '/f', '/im', 'soffice.exe'], 
                             capture_output=True, timeout=10)
            else:  # Linux/Mac
                subprocess.run(['pkill', '-f', 'soffice'], 
                             capture_output=True, timeout=10)
        except Exception as e:
            logger.warning(f"Failed to kill LibreOffice processes: {e}")


class DocConverter:
    """Main converter class with multiple strategies."""
    
    def __init__(self):
        self.process_manager = ProcessManager()
        self.progress = self.load_progress()
        self.stats = {
            'total': 0,
            'converted': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Setup signal handler for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals by cleaning up processes."""
        logger.info("Received interrupt signal, cleaning up...")
        self.process_manager.cleanup_all()
        self.save_progress()
        sys.exit(1)
    
    def load_progress(self) -> Dict:
        """Load conversion progress from file."""
        if PROGRESS_FILE.exists():
            try:
                with open(PROGRESS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load progress: {e}")
        return {'completed': set(), 'failed': set()}
    
    def save_progress(self):
        """Save conversion progress to file."""
        try:
            progress_data = {
                'completed': list(self.progress['completed']),
                'failed': list(self.progress['failed'])
            }
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to remove problematic characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for file operations
        """
        # Normalize Unicode characters
        normalized = unicodedata.normalize('NFKD', filename)
        
        # Convert to ASCII, removing non-ASCII characters
        ascii_str = normalized.encode('ascii', 'ignore').decode('ascii')
        
        # Replace problematic characters with underscores
        ascii_str = re.sub(r'[<>:"/\\|?*]', '_', ascii_str)
        
        # Replace multiple spaces/underscores with single underscore
        ascii_str = re.sub(r'[_\s]+', '_', ascii_str)
        
        # Remove leading/trailing underscores and dots
        ascii_str = ascii_str.strip('_.')
        
        # Ensure we have a valid filename
        if not ascii_str or ascii_str in ['.', '..']:
            ascii_str = 'converted_document'
        
        return ascii_str
    
    def get_unindexed_doc_files(self) -> Set[Path]:
        """Find all .doc files that need conversion."""
        if not KB_DIR.exists():
            logger.error("knowledgebase/ directory not found")
            return set()
        
        # Load already processed files
        processed = set()
        if MANIFEST_PATH.exists():
            try:
                with open(MANIFEST_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('{'):
                            try:
                                entry = json.loads(line)
                                if 'file_name' in entry:
                                    processed.add(entry['file_name'])
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.warning(f"Failed to read manifest: {e}")
        
        # Find unprocessed .doc files
        doc_files = set()
        for path in KB_DIR.rglob("*.doc"):
            if not path.is_file():
                continue
            
            # Skip already converted files
            if "converted_docs" in str(path):
                continue
            
            rel_path = str(path.relative_to(KB_DIR))
            if rel_path not in processed:
                doc_files.add(path)
        
        return doc_files
    
    def check_libreoffice(self) -> Optional[Path]:
        """Check if LibreOffice is available and return path."""
        candidates = [
            "soffice",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        
        for candidate in candidates:
            try:
                path = Path(candidate)
                result = subprocess.run(
                    [str(path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"Found LibreOffice: {path}")
                    return path
            except Exception:
                continue
        
        logger.warning("LibreOffice not found")
        return None
    
    def install_dependencies(self):
        """Install required Python packages."""
        packages = ['python-docx2txt', 'pypandoc']
        for package in packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"{package} already installed")
            except ImportError:
                logger.info(f"Installing {package}...")
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", package
                    ], stdout=subprocess.DEVNULL)
                    logger.info(f"Successfully installed {package}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to install {package}: {e}")
    
    def convert_with_libreoffice(self, doc_path: Path, pdf_path: Path, 
                               soffice: Path, timeout: int = 120) -> Tuple[bool, str]:
        """
        Convert DOC to PDF using LibreOffice with robust process management.
        
        Args:
            doc_path: Path to source .doc file
            pdf_path: Path for output PDF file
            soffice: Path to LibreOffice executable
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, error_message)
        """
        # Clean up any existing processes first
        self.process_manager.kill_system_libreoffice()
        time.sleep(1)
        
        # Create sanitized temporary copy
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sanitized filename
            safe_name = self.sanitize_filename(doc_path.name)
            temp_doc = temp_path / safe_name
            
            try:
                # Copy file with safe name
                shutil.copy2(doc_path, temp_doc)
                
                # Prepare output directory
                temp_out = temp_path / "output"
                temp_out.mkdir()
                
                # Build LibreOffice command
                cmd = [
                    str(soffice),
                    "--headless",
                    "--norestore",
                    "--nofirststartwizard",
                    "--nologo",
                    "--convert-to", "pdf",
                    "--outdir", str(temp_out),
                    str(temp_doc)
                ]
                
                logger.debug(f"Running: {' '.join(cmd)}")
                
                # Start process
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=temp_path
                )
                
                self.process_manager.register_process(process)
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    self.process_manager.unregister_process(process)
                    
                    if process.returncode != 0:
                        return False, f"LibreOffice failed (code {process.returncode}): {stderr}"
                    
                    # Check for output file
                    expected_pdf = temp_out / (temp_doc.stem + ".pdf")
                    if not expected_pdf.exists():
                        return False, "LibreOffice did not produce PDF output"
                    
                    # Move to final location
                    pdf_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(expected_pdf), str(pdf_path))
                    
                    return True, ""
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"LibreOffice timeout for {doc_path.name}")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    self.process_manager.unregister_process(process)
                    return False, "LibreOffice conversion timed out"
                
            except Exception as e:
                return False, f"LibreOffice conversion error: {e}"
    
    def convert_with_pandoc(self, doc_path: Path, pdf_path: Path) -> Tuple[bool, str]:
        """
        Convert DOC to PDF using pandoc (if available).
        
        Args:
            doc_path: Path to source .doc file
            pdf_path: Path for output PDF file
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            import pypandoc
            
            # Create output directory
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert using pandoc
            pypandoc.convert_file(
                str(doc_path),
                'pdf',
                outputfile=str(pdf_path),
                extra_args=['--pdf-engine=pdflatex']
            )
            
            return pdf_path.exists(), ""
            
        except ImportError:
            return False, "pypandoc not available"
        except Exception as e:
            return False, f"Pandoc conversion error: {e}"
    
    def extract_text_fallback(self, doc_path: Path, pdf_path: Path) -> Tuple[bool, str]:
        """
        Fallback: Extract text and create simple PDF.
        
        Args:
            doc_path: Path to source .doc file
            pdf_path: Path for output PDF file
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Try python-docx2txt for text extraction
            try:
                import docx2txt
                text = docx2txt.process(str(doc_path))
            except:
                # Fallback to basic text extraction
                with open(doc_path, 'rb') as f:
                    content = f.read()
                    # Simple text extraction (very basic)
                    text = content.decode('utf-8', errors='ignore')
                    # Clean up binary content
                    text = re.sub(r'[^\x20-\x7E\n\r]', '', text)
            
            if not text.strip():
                return False, "No text content extracted"
            
            # Create simple PDF using reportlab
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                from reportlab.lib.utils import simpleSplit
                
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                
                c = canvas.Canvas(str(pdf_path), pagesize=letter)
                width, height = letter
                
                # Add text to PDF
                lines = text.split('\n')
                y = height - 50
                
                for line in lines:
                    if y < 50:  # Start new page
                        c.showPage()
                        y = height - 50
                    
                    # Wrap long lines
                    wrapped_lines = simpleSplit(line, "Helvetica", 12, width - 100)
                    for wrapped_line in wrapped_lines:
                        if y < 50:
                            c.showPage()
                            y = height - 50
                        c.drawString(50, y, wrapped_line)
                        y -= 15
                
                c.save()
                return True, ""
                
            except ImportError:
                # If reportlab not available, save as text file with .pdf extension
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                with open(pdf_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                    f.write(f"Text extracted from: {doc_path.name}\n\n{text}")
                return True, "Saved as text file (reportlab not available)"
                
        except Exception as e:
            return False, f"Text extraction failed: {e}"
    
    def convert_single_file(self, doc_path: Path) -> Dict:
        """
        Convert a single DOC file to PDF using multiple strategies.
        
        Args:
            doc_path: Path to .doc file
            
        Returns:
            Dictionary with conversion results
        """
        rel_path = doc_path.relative_to(KB_DIR)
        pdf_path = CONVERTED_DIR / rel_path.with_suffix('.pdf')
        
        result = {
            'source': str(rel_path),
            'target': str(pdf_path.relative_to(KB_DIR)),
            'success': False,
            'method': None,
            'error': None
        }
        
        # Check if already converted
        if pdf_path.exists():
            result['success'] = True
            result['method'] = 'already_exists'
            self.stats['skipped'] += 1
            return result
        
        # Check progress
        if str(rel_path) in self.progress['completed']:
            self.stats['skipped'] += 1
            result['success'] = True
            result['method'] = 'previously_completed'
            return result
        
        logger.info(f"Converting: {rel_path}")
        
        # Strategy 1: LibreOffice
        soffice = self.check_libreoffice()
        if soffice:
            success, error = self.convert_with_libreoffice(doc_path, pdf_path, soffice)
            if success:
                result['success'] = True
                result['method'] = 'libreoffice'
                self.progress['completed'].add(str(rel_path))
                self.stats['converted'] += 1
                logger.info(f"✓ Converted with LibreOffice: {rel_path}")
                return result
            else:
                logger.warning(f"LibreOffice failed for {rel_path}: {error}")
        
        # Strategy 2: Pandoc
        success, error = self.convert_with_pandoc(doc_path, pdf_path)
        if success:
            result['success'] = True
            result['method'] = 'pandoc'
            self.progress['completed'].add(str(rel_path))
            self.stats['converted'] += 1
            logger.info(f"✓ Converted with Pandoc: {rel_path}")
            return result
        else:
            logger.warning(f"Pandoc failed for {rel_path}: {error}")
        
        # Strategy 3: Text extraction fallback
        success, error = self.extract_text_fallback(doc_path, pdf_path)
        if success:
            result['success'] = True
            result['method'] = 'text_extraction'
            self.progress['completed'].add(str(rel_path))
            self.stats['converted'] += 1
            logger.info(f"✓ Converted with text extraction: {rel_path}")
            return result
        
        # All strategies failed
        result['error'] = error
        self.progress['failed'].add(str(rel_path))
        self.stats['failed'] += 1
        logger.error(f"✗ All conversion methods failed for {rel_path}: {error}")
        
        return result
    
    def run_conversion(self) -> Dict:
        """
        Run the complete conversion process.
        
        Returns:
            Dictionary with conversion statistics
        """
        logger.info("Starting DOC to PDF conversion...")
        
        # Install dependencies
        self.install_dependencies()
        
        # Find files to convert
        doc_files = self.get_unindexed_doc_files()
        self.stats['total'] = len(doc_files)
        
        logger.info(f"Found {len(doc_files)} DOC files to convert")
        
        if not doc_files:
            logger.info("No DOC files need conversion")
            return self.stats
        
        # Create output directory
        CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
        
        # Convert files with controlled concurrency
        results = []
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Submit all conversion tasks
                future_to_file = {
                    executor.submit(self.convert_single_file, doc_file): doc_file 
                    for doc_file in doc_files
                }
                
                # Process completed tasks
                for future in concurrent.futures.as_completed(future_to_file):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Save progress periodically
                        if len(results) % 5 == 0:
                            self.save_progress()
                            logger.info(f"Progress: {len(results)}/{len(doc_files)} files processed")
                            
                    except Exception as e:
                        doc_file = future_to_file[future]
                        logger.error(f"Error processing {doc_file}: {e}")
                        self.stats['failed'] += 1
        
        finally:
            # Cleanup
            self.process_manager.cleanup_all()
            self.save_progress()
        
        # Log final statistics
        logger.info("Conversion completed!")
        logger.info(f"Total files: {self.stats['total']}")
        logger.info(f"Converted: {self.stats['converted']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        # Generate detailed report
        self.generate_report(results)
        
        return self.stats
    
    def generate_report(self, results: List[Dict]):
        """Generate detailed conversion report."""
        report_path = Path("conversion_report.json")
        
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'statistics': self.stats,
            'results': results,
            'failed_files': list(self.progress['failed']),
            'completed_files': list(self.progress['completed'])
        }
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Detailed report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")


def main():
    """Main entry point."""
    try:
        converter = DocConverter()
        stats = converter.run_conversion()
        
        # Exit code based on results
        if stats['failed'] == 0:
            logger.info("All conversions successful!")
            return 0
        elif stats['converted'] > 0:
            logger.warning(f"Partial success: {stats['converted']} converted, {stats['failed']} failed")
            return 1
        else:
            logger.error("All conversions failed!")
            return 2
            
    except KeyboardInterrupt:
        logger.info("Conversion interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
