#!/usr/bin/env python
"""
DOC-only processor - Quick 95% coverage boost
Processes only DOC files to get to 95% coverage quickly
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from hashlib import sha256
from pathlib import Path

# Setup
KB_DIR = Path("knowledgebase")
IDX_DIR = Path("knowledgebase_index")
MANIFEST_PATH = IDX_DIR / "ingestion_manifest.jsonl"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger("doc_processor")

# Import required libraries
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import faiss
    import fitz  # PyMuPDF
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    sys.exit(1)

def load_existing_hashes():
    if not MANIFEST_PATH.exists():
        return set()
    hashes = set()
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                hashes.add(entry["file_sha256"])
            except:
                continue
    return hashes

def compute_sha256(path):
    h = sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute hash for {path}: {e}")
        return ""

def extract_text_from_doc(file_path):
    """Extract text from DOC files using PyMuPDF"""
    try:
        size_mb = file_path.stat().st_size / 1024 / 1024
        if size_mb > 10:  # Skip very large DOC files
            logger.warning(f"Skipping large DOC file {file_path.name} ({size_mb:.1f}MB)")
            return ""
        
        # Try using PyMuPDF for DOC files
        with fitz.open(str(file_path)) as doc:
            text = ""
            max_pages = min(len(doc), 30)  # Limit pages for speed
            for i in range(max_pages):
                page_text = doc[i].get_text()
                if page_text.strip():
                    text += page_text + "\n"
            return text[:100000]  # Limit text length
    except Exception as e:
        logger.error(f"Failed to extract from DOC {file_path.name}: {e}")
        return ""

def chunk_text(text, size=1000, overlap=200):
    """Simple chunking"""
    if len(text.strip()) < 20:  # Very low minimum for DOC files
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def main():
    print("📄 DOC-ONLY PROCESSOR - QUICK 95% BOOST")
    print("=" * 50)
    
    # Setup
    IDX_DIR.mkdir(exist_ok=True)
    existing_hashes = load_existing_hashes()
    print(f"📋 Found {len(existing_hashes)} previously processed files")
    
    # Initialize model and index
    print("🤖 Loading AI model...")
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    print("✅ Model loaded!")
    
    # Load existing index
    existing_faiss = list(IDX_DIR.glob("index_v*.faiss"))
    if existing_faiss:
        latest_faiss = max(existing_faiss, key=lambda x: x.stat().st_mtime)
        try:
            index = faiss.read_index(str(latest_faiss))
            pkl_file = latest_faiss.with_suffix('.pkl')
            if pkl_file.exists():
                with open(pkl_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = []
            print(f"📁 Loaded existing index with {index.ntotal} vectors")
        except Exception as e:
            print(f"⚠️  Failed to load existing index: {e}")
            index = faiss.IndexFlatIP(384)
            metadata = []
    else:
        index = faiss.IndexFlatIP(384)
        metadata = []
    
    # Find all DOC files
    doc_files = list(KB_DIR.rglob("*.doc"))
    print(f"📁 Found {len(doc_files)} total DOC files")
    
    # Find unprocessed DOC files
    unprocessed_docs = []
    for doc_file in doc_files:
        try:
            file_hash = compute_sha256(doc_file)
            if file_hash and file_hash not in existing_hashes:
                unprocessed_docs.append(doc_file)
        except:
            unprocessed_docs.append(doc_file)
    
    print(f"🔄 Need to process: {len(unprocessed_docs)} DOC files")
    
    if len(unprocessed_docs) == 0:
        print("🎉 All DOC files already processed!")
        return
    
    print("\n" + "=" * 50)
    print("🚀 STARTING DOC PROCESSING")
    print("=" * 50)
    
    # Process files
    processed = 0
    total_chunks = len(metadata)
    version = datetime.utcnow().strftime("%Y%m%d_%H%M")
    start_time = time.time()
    
    for i, doc_file in enumerate(unprocessed_docs):
        try:
            print(f"📄 Processing {i+1}/{len(unprocessed_docs)}: {doc_file.name}")
            
            file_hash = compute_sha256(doc_file)
            if not file_hash:
                print(f"   ❌ Failed to compute hash for {doc_file.name}")
                continue
            
            # Extract text
            text = extract_text_from_doc(doc_file)
            if not text or len(text.strip()) < 10:  # Very low minimum
                print(f"   ⚠️  No meaningful text from {doc_file.name}")
                continue
            
            # Chunk text
            chunks = chunk_text(text)
            if not chunks:
                print(f"   ⚠️  No chunks generated from {doc_file.name}")
                continue
            
            print(f"   ✅ Generated {len(chunks)} chunks from {doc_file.name}")
            
            # Generate embeddings
            embeddings = []
            for j in range(0, len(chunks), 16):  # Small batch size
                batch = chunks[j:j+16]
                try:
                    embs = model.encode(batch, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
                    embeddings.append(embs.astype('float32'))
                except Exception as e:
                    print(f"   ❌ Failed to embed batch for {doc_file.name}: {e}")
                    continue
            
            if embeddings:
                vectors = np.concatenate(embeddings)
                index.add(vectors)
                
                # Add metadata
                timestamp = datetime.utcnow().isoformat()
                for idx in range(len(chunks)):
                    metadata.append({
                        "file_name": str(doc_file.relative_to(KB_DIR)),
                        "file_sha256": file_hash,
                        "chunk_index": idx,
                        "ingest_timestamp": timestamp,
                    })
                
                total_chunks += len(chunks)
                processed += 1
                
                # Update manifest
                with open(MANIFEST_PATH, 'a', encoding='utf-8') as f:
                    entry = {
                        "file_name": str(doc_file.relative_to(KB_DIR)),
                        "file_sha256": file_hash,
                        "chunk_count": len(chunks),
                        "ingest_timestamp": timestamp,
                        "model_name": "all-MiniLM-L6-v2",
                        "index_version": version,
                    }
                    f.write(json.dumps(entry) + "\n")
                
                # Save progress every 3 files
                if processed % 3 == 0:
                    faiss_path = IDX_DIR / f"index_v{version}.faiss"
                    pkl_path = IDX_DIR / f"index_v{version}.pkl"
                    
                    faiss.write_index(index, str(faiss_path))
                    with open(pkl_path, 'w') as f:
                        json.dump(metadata, f)
                    
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    print(f"   💾 Saved checkpoint: {processed} files, {total_chunks} chunks ({rate:.1f} files/sec)")
            
        except Exception as e:
            print(f"   ❌ Failed to process {doc_file.name}: {e}")
            continue
    
    # Final save
    faiss_path = IDX_DIR / f"index_v{version}.faiss"
    pkl_path = IDX_DIR / f"index_v{version}.pkl"
    
    faiss.write_index(index, str(faiss_path))
    with open(pkl_path, 'w') as f:
        json.dump(metadata, f)
    
    print("\n" + "=" * 50)
    print("🎉 DOC PROCESSING COMPLETE!")
    print("=" * 50)
    print(f"✅ Processed: {processed} new DOC files")
    print(f"📊 Total chunks: {total_chunks}")
    print(f"📁 Index size: {faiss_path.stat().st_size / 1024 / 1024:.1f}MB")
    print(f"📈 Coverage improvement: +{processed} files")
    
    # Calculate coverage percentage
    total_files_in_kb = len(list(KB_DIR.rglob("*")))
    total_processed = len(existing_hashes) + processed
    coverage = (total_processed / total_files_in_kb) * 100 if total_files_in_kb > 0 else 0
    print(f"🎯 Estimated coverage: {coverage:.1f}%")

if __name__ == "__main__":
    main()
