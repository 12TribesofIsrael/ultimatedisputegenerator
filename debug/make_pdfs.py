#!/usr/bin/env python3
"""
Force-generate PDFs for all Markdown letters under outputletter/.

Uses convert_to_professional_pdf.write_pdf to create PDFs alongside .md files.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure project root is first on sys.path so we import the root module,
# not debug/convert_to_professional_pdf.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import convert_to_professional_pdf as conv


def main() -> int:
    base = Path("outputletter")
    if not base.exists():
        print("No outputletter/ directory found.")
        return 1

    md_files = list(base.rglob("*.md"))
    if not md_files:
        print("No .md letters found under outputletter/.")
        return 0

    made = 0
    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8")
            pdf_path = conv.write_pdf(md, content)
            print(f"✅ {md} -> {pdf_path}")
            made += 1
        except Exception as e:
            print(f"❌ Failed {md}: {e}")

    print(f"Done. Wrote {made} PDF(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


