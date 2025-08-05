#!/usr/bin/env python
"""
knowledgebase_ingest.py

Offline pipeline to ingest, chunk, embed, and index every file in /knowledgebase.
Produces:
    • /knowledgebase_index/index_vYYYYMMDD_HHMM.faiss
    • /knowledgebase_index/index_vYYYYMMDD_HHMM.pkl   (chunk-level metadata)
    • /knowledgebase_index/ingestion_manifest.jsonl   (file-level log)
    • /knowledgebase_index/ingestion_errors.log       (errors)

Requirements (install via pip if missing):
    sentence_transformers, faiss-cpu, PyMuPDF, python-docx, pdfminer.six,
    pytesseract, pdf2image, tqdm
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Generator, List

# ---------- CONFIG ---------- #
KB_DIR = Path("knowledgebase").expanduser()
IDX_DIR = Path("knowledgebase_index").expanduser()
MANIFEST_PATH = IDX_DIR / "ingestion_manifest.jsonl"
ERROR_LOG_PATH = IDX_DIR / "ingestion_errors.log"

CHUNK_SIZE = 1000          # characters
CHUNK_OVERLAP = 200        # characters
EMBED_BATCH = 64
MODEL_NAME = "all-MiniLM-L6-v2"
DISK_THRESHOLD_GB = 5

# ---------- LOGGING ---------- #
IDX_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ERROR_LOG_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("ingest")

# ---------- OPTIONAL IMPORTS ---------- #
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logger.warning("PyMuPDF not available - PDF text extraction will be limited")

try:
    from docx import Document
except ImportError:
    Document = None
    logger.warning("python-docx not available - DOCX files will be skipped")

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
except ImportError:
    pdfminer_extract = None
    logger.warning("pdfminer.six not available - fallback PDF extraction disabled")

try:
    import pytesseract
    from pdf2image import convert_from_path
except ImportError:
    pytesseract = None
    logger.warning("pytesseract/pdf2image not available - OCR disabled")

try:
    import psutil
except ImportError:
    psutil = None
    logger.warning("psutil not available - disk space monitoring disabled")

# ---------- EMBEDDING MODEL & FAISS ---------- #
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError as e:
    logger.error("sentence_transformers not installed. Install with `pip install sentence_transformers`.")
    raise e

try:
    import faiss
except ImportError as e:
    logger.error("faiss-cpu not installed. Install with `pip install faiss-cpu`.")
    raise e

# ---------- UTILS ---------- #
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def disk_free_gb(path: Path) -> float:
    if psutil:
        usage = psutil.disk_usage(str(path))
        return usage.free / 1_073_741_824  # bytes→GiB
    else:
        total, used, free = shutil.disk_usage(path)
        return free / 1_073_741_824  # bytes→GiB


def ensure_disk_space() -> None:
    try:
        free_gb = disk_free_gb(IDX_DIR)
        if free_gb < DISK_THRESHOLD_GB:
            logger.error("Aborting: only %.2f GB free (minimum %.0f GB required).", free_gb, DISK_THRESHOLD_GB)
            sys.exit(1)
    except Exception as e:
        logger.warning("Could not check disk space: %s", e)


def compute_sha256(path: Path) -> str:
    h = sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error("Failed to compute SHA256 for %s: %s", path, e)
        return ""


def text_from_pdf(path: Path) -> str:
    """Extract text from PDF; fall back to OCR if no text."""
    text = ""
    
    # Skip very large PDFs to avoid hanging
    if path.stat().st_size > 50 * 1024 * 1024:  # 50MB limit
        logger.warning("Skipping very large PDF %s (%.1f MB)", path.name, path.stat().st_size / 1024 / 1024)
        return ""
    
    # Try PyMuPDF first
    if fitz:
        try:
            with fitz.open(str(path)) as doc:
                # Limit to first 1000 pages for very large documents
                max_pages = min(len(doc), 1000)
                text = "\n".join(doc[i].get_text() for i in range(max_pages))
                if max_pages < len(doc):
                    logger.info("Limited %s to first %d pages", path.name, max_pages)
        except Exception as e:
            logger.debug("PyMuPDF failed for %s: %s", path, e)

    # Try pdfminer as fallback (but skip for large files)
    if len(text.strip()) < 100 and pdfminer_extract and path.stat().st_size < 10 * 1024 * 1024:
        try:
            text = pdfminer_extract(str(path))
        except Exception as e:
            logger.debug("pdfminer failed for %s: %s", path, e)

    # Skip OCR for large files
    if len(text.strip()) < 100 and pytesseract and path.stat().st_size < 5 * 1024 * 1024:
        try:
            pages = convert_from_path(str(path))
            ocr_text = []
            # Limit OCR to first 10 pages
            for img in pages[:10]:
                ocr_text.append(pytesseract.image_to_string(img))
            text = "\n".join(ocr_text)
        except Exception as e:
            logger.error("OCR failed for %s – %s", path, e)

    return text


def text_from_docx(path: Path) -> str:
    if not Document:
        return ""
    try:
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.error("Failed to extract from DOCX %s: %s", path, e)
        return ""


def text_from_txt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.error("Failed to read TXT %s: %s", path, e)
        return ""


def text_from_csv(path: Path) -> str:
    try:
        import pandas as pd  # local import to avoid mandatory dependency if csvs absent
        df = pd.read_csv(str(path), dtype=str, low_memory=False)
        return df.to_string(index=False)
    except Exception as e:
        logger.error("Failed to read CSV %s: %s", path, e)
        return ""


def text_from_json(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            obj = json.load(f)
        return json.dumps(obj, separators=(",", ":"))
    except Exception as e:
        logger.error("Failed to read JSON %s: %s", path, e)
        return ""


EXT_HANDLERS = {
    ".pdf": text_from_pdf,
    ".docx": text_from_docx,
    ".txt": text_from_txt,
    ".csv": text_from_csv,
    ".json": text_from_json,
}


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch >= " " or ch == "\n")
    text = SSN_REGEX.sub("***-**-****", text)
    return text


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> Generator[str, None, None]:
    if not text.strip():
        return
    step = size - overlap
    for start in range(0, len(text), step):
        chunk = text[start : start + size].strip()
        if chunk:
            yield chunk


# ---------- MANIFEST ---------- #
def load_existing_hashes(manifest_path: Path) -> set[str]:
    if not manifest_path.exists():
        return set()
    hashes: set[str] = set()
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if "file_sha256" in entry:
                        hashes.add(entry["file_sha256"])
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error("Failed to load manifest: %s", e)
    return hashes


def append_manifest(entry: dict) -> None:
    try:
        with MANIFEST_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error("Failed to append to manifest: %s", e)


# ---------- INDEX ---------- #
def latest_index_files() -> tuple[Path | None, Path | None]:
    try:
        faiss_files = sorted(IDX_DIR.glob("index_v*.faiss"), key=os.path.getmtime, reverse=True)
        if not faiss_files:
            return None, None
        base = faiss_files[0].with_suffix("")  # strip .faiss
        pkl = base.with_suffix(".pkl")
        return faiss_files[0], pkl if pkl.exists() else None
    except Exception:
        return None, None


def atomic_write(src_path: Path, dest_path: Path) -> None:
    try:
        # On Windows, remove destination file first if it exists
        if dest_path.exists():
            dest_path.unlink()
        tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
        if tmp_path.exists():
            tmp_path.unlink()
        shutil.move(str(src_path), str(tmp_path))
        tmp_path.rename(dest_path)
    except Exception as e:
        logger.error("Failed atomic write from %s to %s: %s", src_path, dest_path, e)


# ---------- MAIN ---------- #
def main() -> None:
    if not KB_DIR.exists():
        logger.error("Knowledgebase directory %s not found.", KB_DIR)
        sys.exit(1)
    
    logger.info("Starting knowledgebase ingestion pipeline...")
    logger.info("Source: %s", KB_DIR.absolute())
    logger.info("Target: %s", IDX_DIR.absolute())
    
    ensure_disk_space()

    existing_hashes = load_existing_hashes(MANIFEST_PATH)
    logger.info("Loaded %d previously ingested file hashes.", len(existing_hashes))

    index_path, meta_path = latest_index_files()
    if index_path and meta_path:
        try:
            index = faiss.read_index(str(index_path))
            with open(str(meta_path), 'r', encoding='utf-8') as f:
                meta = json.load(f)
            logger.info("Loaded existing index with %d vectors.", index.ntotal)
        except Exception as e:
            logger.warning("Failed to load existing index: %s. Starting fresh.", e)
            dim = 384
            index = faiss.IndexFlatIP(dim)
            meta: List[dict] = []
    else:
        dim = 384
        index = faiss.IndexFlatIP(dim)
        meta: List[dict] = []
        logger.info("Initialized new index.")

    try:
        model = SentenceTransformer(MODEL_NAME, device="cpu")
        logger.info("Loaded embedding model: %s", MODEL_NAME)
    except Exception as e:
        logger.error("Failed to load embedding model: %s", e)
        sys.exit(1)

    index_version = datetime.utcnow().strftime("%Y%m%d_%H%M")
    total_chunks = 0
    total_files = 0
    processed_files = 0
    start_time = datetime.utcnow()

    # Count total files for progress tracking
    all_files = []
    for file_path in KB_DIR.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in EXT_HANDLERS:
            all_files.append(file_path)
    
    logger.info("Found %d files to process", len(all_files))

    for file_path in all_files:
        try:
            processed_files += 1
            logger.info("Processing file %d/%d: %s", processed_files, len(all_files), file_path.name)
            
            sha_hex = compute_sha256(file_path)
            if not sha_hex:
                continue
                
            if sha_hex in existing_hashes:
                logger.debug("Skipping duplicate file: %s", file_path.name)
                continue

            handler = EXT_HANDLERS.get(file_path.suffix.lower())
            if not handler:
                continue  # unsupported

            text = handler(file_path)
            if not text or len(text.strip()) < 50:
                logger.warning("No meaningful text extracted from %s", file_path.name)
                continue

            text = normalize(text)
            chunks = list(chunk_text(text))
            if not chunks:
                logger.warning("No chunks generated from %s", file_path.name)
                continue

            logger.info("Generated %d chunks from %s", len(chunks), file_path.name)

            # Batch embed
            embeddings = []
            for i in range(0, len(chunks), EMBED_BATCH):
                batch = chunks[i : i + EMBED_BATCH]
                try:
                    embs = model.encode(batch, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
                    embeddings.append(embs.astype("float32"))
                except Exception as e:
                    logger.error("Failed to embed batch for %s: %s", file_path.name, e)
                    continue
            
            if not embeddings:
                logger.warning("No embeddings generated for %s", file_path.name)
                continue
                
            vectors = np.concatenate(embeddings)
            index.add(vectors)

            # Metadata for each chunk
            ts = datetime.utcnow().isoformat()
            chunk_meta = []
            for idx in range(len(chunks)):
                chunk_meta.append({
                    "file_name": str(file_path.relative_to(KB_DIR)),
                    "file_sha256": sha_hex,
                    "chunk_index": idx,
                    "ingest_timestamp": ts,
                })
            meta.extend(chunk_meta)

            # Persist after each file (atomic)
            try:
                tmp_fd, tmp_faiss_path = tempfile.mkstemp(suffix=".faiss", dir=str(IDX_DIR))
                os.close(tmp_fd)
                faiss.write_index(index, tmp_faiss_path)
                atomic_write(Path(tmp_faiss_path), IDX_DIR / f"index_v{index_version}.faiss")

                tmp_meta_path = IDX_DIR / f"index_v{index_version}.pkl.tmp"
                with open(str(tmp_meta_path), 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=None, separators=(',', ':'))
                atomic_write(tmp_meta_path, IDX_DIR / f"index_v{index_version}.pkl")
            except Exception as e:
                logger.error("Failed to persist index after processing %s: %s", file_path.name, e)
                continue

            # Manifest entry
            append_manifest(
                dict(
                    file_name=str(file_path.relative_to(KB_DIR)),
                    file_sha256=sha_hex,
                    chunk_count=len(chunks),
                    ingest_timestamp=ts,
                    model_name=MODEL_NAME,
                    index_version=index_version,
                )
            )

            total_chunks += len(chunks)
            total_files += 1
            
            # Progress every 10 files or every 1000 chunks
            if total_files % 10 == 0 or total_chunks % 1000 < len(chunks) or total_chunks < 1000:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                rate = total_files / elapsed if elapsed > 0 else 0
                logger.info("Progress: %d/%d files (%.1f%%), %d chunks, %.1f files/sec", 
                           total_files, len(all_files), 100 * total_files / len(all_files), total_chunks, rate)

            ensure_disk_space()

        except Exception as e:
            logger.error("Failed to process file %s: %s", file_path, e)
            continue

    elapsed = (datetime.utcnow() - start_time).total_seconds()
    logger.info("=== INGESTION COMPLETE ===")
    logger.info("Files processed: %d", total_files)
    logger.info("Total chunks indexed: %d", total_chunks)
    logger.info("Time elapsed: %.1f seconds", elapsed)
    logger.info("Final index file: index_v%s.faiss", index_version)
    logger.info("Final metadata file: index_v%s.pkl", index_version)
    
    if total_chunks > 0:
        logger.info("Average chunks per file: %.1f", total_chunks / total_files if total_files > 0 else 0)
        logger.info("Processing rate: %.1f chunks/second", total_chunks / elapsed if elapsed > 0 else 0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user – exiting.")
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)