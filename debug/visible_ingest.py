#!/usr/bin/env python
"""
Visible ingestion with frequent progress updates
"""
import json
import logging
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
logger = logging.getLogger("visible_ingest")

# Import required libraries
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import faiss
    import fitz  # PyMuPDF
    from docx import Document
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
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def extract_text(file_path):
    """Fast text extraction with size limits"""
    try:
        size_mb = file_path.stat().st_size / 1024 / 1024
        
        if file_path.suffix.lower() == '.pdf':
            if size_mb > 20:  # Skip very large PDFs
                print(f"   ⚠️  Skipping large PDF {file_path.name} ({size_mb:.1f}MB)")
                return ""
            
            with fitz.open(str(file_path)) as doc:
                max_pages = min(len(doc), 200)
                text = "\n".join(doc[i].get_text() for i in range(max_pages))
                return text[:500000]
                
        elif file_path.suffix.lower() == '.docx':
            doc = Document(str(file_path))
            text = "\n".join(p.text for p in doc.paragraphs)
            return text[:100000]
            
        elif file_path.suffix.lower() in ['.txt', '.json']:
            if size_mb > 5:  # Skip very large text files
                print(f"   ⚠️  Skipping large text file {file_path.name} ({size_mb:.1f}MB)")
                return ""
            text = file_path.read_text(encoding='utf-8', errors='ignore')
            return text[:100000]
            
    except Exception as e:
        print(f"   ❌ Failed to extract from {file_path.name}: {e}")
        return ""
    
    return ""

def chunk_text(text, size=1000, overlap=200):
    """Simple chunking"""
    if not text.strip():
        return []
    
    chunks = []
    step = size - overlap
    for i in range(0, len(text), step):
        chunk = text[i:i+size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks

def main():
    print("🚀 VISIBLE KNOWLEDGEBASE INGESTION")
    print("=" * 60)
    
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
    
    # Find all files
    all_files = []
    for ext in ['.pdf', '.docx', '.txt', '.json']:
        all_files.extend(KB_DIR.rglob(f"*{ext}"))
    
    print(f"📁 Found {len(all_files)} total files")
    
    # Find unprocessed files
    unprocessed = []
    for file_path in all_files:
        try:
            file_hash = compute_sha256(file_path)
            if file_hash not in existing_hashes:
                unprocessed.append(file_path)
        except:
            unprocessed.append(file_path)
    
    print(f"🔄 Need to process: {len(unprocessed)} files")
    
    if len(unprocessed) == 0:
        print("🎉 All files already processed!")
        return
    
    print("\n" + "=" * 60)
    print("🚀 STARTING PROCESSING WITH LIVE UPDATES")
    print("=" * 60)
    
    # Process files with frequent updates
    processed = 0
    total_chunks = len(metadata)
    version = datetime.utcnow().strftime("%Y%m%d_%H%M")
    
    for i, file_path in enumerate(unprocessed):
        start_time = time.time()
        
        print(f"\n📄 [{i+1:3d}/{len(unprocessed):3d}] Processing: {file_path.name}")
        
        try:
            # Skip if already processed (double-check)
            file_hash = compute_sha256(file_path)
            if file_hash in existing_hashes:
                print("   ✅ Already processed (skipping)")
                continue
            
            # Extract and chunk text
            text = extract_text(file_path)
            if not text:
                print("   ⚠️  No text extracted")
                continue
                
            chunks = chunk_text(text)
            if not chunks:
                print("   ⚠️  No chunks generated")
                continue
            
            print(f"   📝 Generated {len(chunks)} chunks")
            
            # Create embeddings in small batches for progress
            embeddings = []
            batch_size = 16  # Smaller batches for more frequent updates
            
            for j in range(0, len(chunks), batch_size):
                batch = chunks[j:j+batch_size]
                embs = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
                embeddings.append(embs.astype('float32'))
                
                # Show embedding progress
                progress = min(len(chunks), j + batch_size)
                print(f"   🧠 Embedded {progress}/{len(chunks)} chunks", end='\r')
            
            print()  # New line after progress
            
            if embeddings:
                vectors = np.concatenate(embeddings)
                index.add(vectors)
                
                # Add metadata
                timestamp = datetime.utcnow().isoformat()
                for idx in range(len(chunks)):
                    metadata.append({
                        "file_name": str(file_path.relative_to(KB_DIR)),
                        "file_sha256": file_hash,
                        "chunk_index": idx,
                        "ingest_timestamp": timestamp,
                    })
                
                total_chunks += len(chunks)
                processed += 1
                
                # Update manifest
                with open(MANIFEST_PATH, 'a', encoding='utf-8') as f:
                    entry = {
                        "file_name": str(file_path.relative_to(KB_DIR)),
                        "file_sha256": file_hash,
                        "chunk_count": len(chunks),
                        "ingest_timestamp": timestamp,
                        "model_name": "all-MiniLM-L6-v2",
                        "index_version": version,
                    }
                    f.write(json.dumps(entry) + "\n")
                
                # Save index frequently (every 5 files)
                if processed % 5 == 0:
                    faiss_path = IDX_DIR / f"index_v{version}.faiss"
                    pkl_path = IDX_DIR / f"index_v{version}.pkl"
                    
                    faiss.write_index(index, str(faiss_path))
                    with open(pkl_path, 'w') as f:
                        json.dump(metadata, f)
                    
                    print(f"   💾 Saved checkpoint: {processed} files processed")
                
                # Show progress
                elapsed = time.time() - start_time
                remaining = len(unprocessed) - (i + 1)
                current_total = len(all_files) - remaining
                success_rate = (current_total / len(all_files)) * 100
                
                print(f"   ✅ Success! ({elapsed:.1f}s) | Progress: {current_total}/{len(all_files)} ({success_rate:.1f}%) | Remaining: {remaining}")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            continue
    
    # Final save
    faiss_path = IDX_DIR / f"index_v{version}.faiss"
    pkl_path = IDX_DIR / f"index_v{version}.pkl"
    
    faiss.write_index(index, str(faiss_path))
    with open(pkl_path, 'w') as f:
        json.dump(metadata, f)
    
    print("\n" + "=" * 60)
    print("🎉 PROCESSING COMPLETE!")
    print(f"✅ Processed: {processed} new files")
    print(f"🧮 Total chunks: {total_chunks}")
    print(f"📁 Index file: {faiss_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()