#!/usr/bin/env python
"""
List knowledgebase files that are indexed vs not indexed.
Outputs:
  - knowledgebase_index/indexed_list.txt
  - knowledgebase_index/not_indexed_list.txt
Also prints totals and a breakdown of NOT_INDEXED counts by extension.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


KB_DIR = Path("knowledgebase")
IDX_DIR = Path("knowledgebase_index")
MANIFEST_PATH = IDX_DIR / "ingestion_manifest.jsonl"


def load_processed_file_names(manifest_path: Path) -> set[str]:
    if not manifest_path.exists():
        return set()
    processed: set[str] = set()
    with manifest_path.open("r", encoding="utf-8", errors="ignore") as f:
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
                # skip malformed lines
                continue
    return processed


def iter_kb_files(base: Path):
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        # Exclude helper/output dirs under KB
        p_str = str(path)
        if "\\converted_docs\\" in p_str or "\\unprocessable_files\\" in p_str:
            continue
        yield path


def main() -> int:
    if not KB_DIR.exists():
        print("KB_MISSING")
        return 0

    processed_names = load_processed_file_names(MANIFEST_PATH)

    # Build canonical relative names exactly like manifest (OS-native separators)
    all_rel_names: set[str] = set()
    for f in iter_kb_files(KB_DIR):
        rel = str(f.relative_to(KB_DIR))
        all_rel_names.add(rel)

    indexed = sorted(n for n in all_rel_names if n in processed_names)
    not_indexed = sorted(n for n in all_rel_names if n not in processed_names)

    # Save lists
    IDX_DIR.mkdir(exist_ok=True)
    (IDX_DIR / "indexed_list.txt").write_text("\n".join(indexed), encoding="utf-8")
    (IDX_DIR / "not_indexed_list.txt").write_text("\n".join(not_indexed), encoding="utf-8")

    # Breakdown by extension for not-indexed
    ext_counts = Counter()
    for n in not_indexed:
        dot = n.rfind(".")
        ext = n[dot:].lower() if dot != -1 else ""
        ext_counts[ext] += 1

    print(f"TOTAL={len(all_rel_names)}")
    print(f"INDEXED={len(indexed)}")
    print(f"NOT_INDEXED={len(not_indexed)}")
    for ext, cnt in sorted(ext_counts.items()):
        print(f"EXT {ext or '(noext)'}={cnt}")
    print("LIST_SAVED=index: knowledgebase_index/indexed_list.txt; not_index: knowledgebase_index/not_indexed_list.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())


