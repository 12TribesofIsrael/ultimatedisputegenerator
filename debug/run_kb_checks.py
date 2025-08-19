#!/usr/bin/env python3
"""
Quick KB diagnostics: verifies index load and returns top files for key derogatory queries.
"""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    try:
        from extract_account_details import kb_load, kb_search, _kb_latest_files  # type: ignore
    except Exception as e:
        print("❌ Cannot import KB search from extract_account_details:", e)
        return

    faiss_path, meta_path = _kb_latest_files()
    print("KB index files:")
    print(" - FAISS:", str(faiss_path) if faiss_path else "<not found>")
    print(" - META :", str(meta_path) if meta_path else "<not found>")

    ok = kb_load()
    print("kb_load():", "OK" if ok else "FAIL")
    if not ok:
        print("⚠️  KB index not loaded. You may need to ingest with `python debug/visible_ingest.py`.\n")
        return

    queries = [
        "FCRA charge-off reporting requirements",
        "Metro 2 collection account status reporting",
        "Repossession credit reporting guidance",
        "Foreclosure Metro 2 status codes",
        "Bankruptcy reporting accuracy 1681",
        "Late payment Metro 2 payment history profile",
        "Settlement credit reporting requirements",
        "Default account Metro 2",
    ]

    for q in queries:
        try:
            res = kb_search(q, top_k=5) or []
            print(f"\nQ: {q}")
            if not res:
                print(" - No results")
                continue
            for r in res:
                print(" -", r.get("file_name"), f"score={r.get('score')}")
        except Exception as e:
            print(" - KB query error:", e)


if __name__ == "__main__":
    main()


