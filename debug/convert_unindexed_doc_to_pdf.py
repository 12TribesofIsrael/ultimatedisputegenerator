#!/usr/bin/env python
"""
Convert unindexed legacy .doc files in knowledgebase/ into PDFs so they can be ingested.

Strategy:
- Identify NOT INDEXED files from knowledgebase_index/ingestion_manifest.jsonl
- Filter to .doc files under knowledgebase/ (excluding converted_docs/ and unprocessable_files/)
- Try Microsoft Word COM (pywin32) conversion first (fastest, most reliable on Windows)
- Fallback to LibreOffice headless (if installed)
- Preserve directory structure under knowledgebase/converted_docs/
- Write a summary report at the end
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Set, Tuple
import shutil
import tempfile
import unicodedata
import re
import argparse


KB_DIR = Path("knowledgebase")
CONVERTED_DIR = KB_DIR / "converted_docs"
IDX_DIR = Path("knowledgebase_index")
MANIFEST_PATH = IDX_DIR / "ingestion_manifest.jsonl"


def load_unindexed_doc_files() -> Set[Path]:
    if not KB_DIR.exists():
        print("ERROR: knowledgebase/ not found")
        return set()

    processed: Set[str] = set()
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("{"):
                    continue
                try:
                    entry = json.loads(line)
                    name = entry.get("file_name")
                    if isinstance(name, str) and name:
                        processed.add(name)
                except Exception:
                    continue

    to_convert: Set[Path] = set()
    # Walk all files and filter by suffix for case-insensitive .doc
    for p in KB_DIR.rglob("*"):
        if not p.is_file():
            continue
        # Skip previously generated PDFs
        if "\\converted_docs\\" in str(p):
            continue
        if p.suffix.lower() != ".doc":
            continue
        rel = str(p.relative_to(KB_DIR))
        if rel not in processed:
            to_convert.add(p)

    return to_convert


def kill_libreoffice_processes():
    """Kill any hanging LibreOffice processes"""
    try:
        if os.name == 'nt':  # Windows
            os.system('taskkill /f /im soffice.bin* /t')
            os.system('taskkill /f /im soffice.exe* /t')
        else:  # Linux/Mac
            os.system('pkill -f soffice')
    except Exception:
        pass


def ensure_pywin32_installed() -> bool:
    try:
        import win32com.client  # type: ignore
        return True
    except Exception:
        pass
    try:
        print("Installing pywin32/comtypes for Word automation if missing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32", "comtypes"], stdout=subprocess.DEVNULL)
        import win32com.client  # type: ignore
        return True
    except Exception as e:
        print(f"WARNING: Word automation unavailable: {e}")
        return False


def word_convert_to_pdf(doc_path: Path, out_pdf: Path) -> Tuple[bool, str]:
    try:
        import win32com.client  # type: ignore
    except Exception as e:
        return False, f"pywin32 not available: {e}"

    try:
        out_pdf.parent.mkdir(parents=True, exist_ok=True)

        # Use absolute Windows paths; Word COM may not resolve relative paths
        abs_doc = str(doc_path.resolve()).replace("/", "\\")
        abs_pdf = str(out_pdf.resolve()).replace("/", "\\")

        # First attempt: open original file directly
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        try:
            doc = word.Documents.Open(FileName=abs_doc, ReadOnly=True, AddToRecentFiles=False)
            # 17 = wdFormatPDF
            doc.SaveAs(abs_pdf, FileFormat=17)
            doc.Close(False)
            word.Quit()
            return out_pdf.exists(), ""
        except Exception as direct_err:
            try:
                word.Quit()
            except Exception:
                pass
            # Fallback: copy to temp with ASCII-safe short name to avoid path/encoding issues
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmpdir_path = Path(tmpdir)
                    safe_name = _slugify_filename(doc_path.name) or "file.doc"
                    # ensure reasonably short name
                    if len(safe_name) > 80:
                        parts = safe_name.rsplit('.', 1)
                        base = parts[0][:70]
                        ext = parts[1] if len(parts) > 1 else 'doc'
                        safe_name = f"{base}.{ext}"
                    tmp_src = tmpdir_path / safe_name
                    shutil.copy2(doc_path, tmp_src)

                    tmp_pdf = tmpdir_path / (tmp_src.stem + ".pdf")
                    abs_tmp_src = str(tmp_src.resolve()).replace("/", "\\")
                    abs_tmp_pdf = str(tmp_pdf.resolve()).replace("/", "\\")

                    word2 = win32com.client.DispatchEx("Word.Application")
                    word2.Visible = False
                    word2.DisplayAlerts = 0
                    try:
                        doc2 = word2.Documents.Open(FileName=abs_tmp_src, ReadOnly=True, AddToRecentFiles=False)
                        doc2.SaveAs(abs_tmp_pdf, FileFormat=17)
                        doc2.Close(False)
                        word2.Quit()

                        if not tmp_pdf.exists():
                            return False, "Word did not produce output (temp)"
                        out_pdf.parent.mkdir(parents=True, exist_ok=True)
                        if out_pdf.exists():
                            out_pdf.unlink()
                        shutil.move(str(tmp_pdf), str(out_pdf))
                        return True, ""
                    except Exception as tmp_err:
                        try:
                            word2.Quit()
                        except Exception:
                            pass
                        return False, f"Word conversion failed (temp): {tmp_err}"
            except Exception as fallback_err:
                return False, f"Word conversion failed: {direct_err} | Fallback error: {fallback_err}"
    except Exception as e:
        return False, f"Word automation error: {e}"


def libreoffice_available() -> Optional[Path]:
    candidates = [
        Path("soffice"),
        Path(r"C:\\Program Files\\LibreOffice\\program\\soffice.exe"),
        Path(r"C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe"),
    ]
    for c in candidates:
        try:
            result = subprocess.run([str(c), "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return c
        except Exception:
            continue
    return None


def _run_libreoffice_convert(soffice: Path, src_path: Path, out_dir: Path) -> Tuple[bool, str]:
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        # Kill any hanging processes first
        kill_libreoffice_processes()
        
        cmd = [
            str(soffice),
            "--headless",
            "--norestore",
            "--accept=pipe,name=instance,host=localhost",
            "--nofirststartwizard",
            "--convert-to", "pdf",
            "--outdir", str(out_dir.resolve()),
            str(src_path.resolve()),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env={"PATH": os.environ.get("PATH", "")})
        if result.returncode != 0:
            return False, f"LibreOffice failed: {result.stderr.strip()}"
        return True, ""
    except Exception as e:
        return False, f"LibreOffice conversion error: {e}"
    finally:
        # Cleanup any hanging processes
        kill_libreoffice_processes()


def _slugify_filename(name: str) -> str:
    # Normalize unicode and keep ASCII only
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = nfkd.encode('ascii', 'ignore').decode('ascii')
    ascii_str = re.sub(r"[^A-Za-z0-9_.-]", "_", ascii_str)
    # Avoid empty
    return ascii_str or "file.doc"


def libreoffice_convert_to_pdf(soffice: Path, doc_path: Path, out_pdf: Path) -> Tuple[bool, str]:
    # Direct attempt
    ok, err = _run_libreoffice_convert(soffice, doc_path, out_pdf.parent)
    produced = out_pdf.parent / (doc_path.stem + ".pdf")
    if ok and produced.exists():
        try:
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            if out_pdf.exists():
                out_pdf.unlink()
            produced.replace(out_pdf)
            return True, ""
        except Exception as move_err:
            return False, f"Move error after LO conversion: {move_err}"

    # Fallback: copy to temp with safe ASCII name, then convert
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            safe_name = _slugify_filename(doc_path.name)
            src_copy = tmpdir_path / safe_name
            shutil.copy2(doc_path, src_copy)

            tmp_out = tmpdir_path / "out"
            _ = tmp_out.mkdir(parents=True, exist_ok=True)
            ok2, err2 = _run_libreoffice_convert(soffice, src_copy, tmp_out)
            if not ok2:
                return False, err2

            produced2 = tmp_out / (src_copy.stem + ".pdf")
            if not produced2.exists():
                return False, "LibreOffice did not produce output (temp)"

            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            if out_pdf.exists():
                out_pdf.unlink()
            shutil.move(str(produced2), str(out_pdf))
            return True, ""
    except Exception as e:
        return False, f"LibreOffice robust conversion error: {e}"
    
    return False, err or "LibreOffice conversion failed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert legacy .doc files to PDF for ingestion")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PDFs if present")
    args = parser.parse_args()

    print("Finding unindexed .doc files...")
    to_convert = load_unindexed_doc_files()
    print(f".doc files to convert: {len(to_convert)}")

    if not to_convert:
        print("No .doc files need conversion.")
        return 0

    # Prepare converters
    have_pywin32 = ensure_pywin32_installed()
    soffice = libreoffice_available()

    converted = 0
    failed = 0
    skipped = 0

    for i, doc_path in enumerate(sorted(to_convert)):
        rel = doc_path.relative_to(KB_DIR)
        out_pdf = (CONVERTED_DIR / rel).with_suffix(".pdf")

        if out_pdf.exists() and not args.overwrite:
            print(f"SKIP {i+1}/{len(to_convert)} Already exists: {out_pdf.relative_to(KB_DIR)}")
            skipped += 1
            continue

        print(f"CONVERT {i+1}/{len(to_convert)}: {rel}")

        ok = False
        err = ""

        if have_pywin32:
            ok, err = word_convert_to_pdf(doc_path, out_pdf)
        if not ok and soffice is not None:
            ok, err = libreoffice_convert_to_pdf(soffice, doc_path, out_pdf)

        if ok and out_pdf.exists():
            print(f"   Saved: {out_pdf.relative_to(KB_DIR)}")
            converted += 1
        else:
            print(f"   FAILED: {rel}  {('('+err+')' if err else '')}")
            failed += 1

    print("\nConversion Summary")
    print(f"   Converted: {converted}")
    print(f"   Skipped (already existed): {skipped}")
    print(f"   Failed: {failed}")
    print(f"   Output dir: {CONVERTED_DIR}")

    # Hint for next steps
    if converted > 0:
        print("\nNext: run ingestion to index the new PDFs, e.g.")
        print("   python enhanced_ingest.py")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())