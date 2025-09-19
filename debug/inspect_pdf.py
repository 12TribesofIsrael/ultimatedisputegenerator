#!/usr/bin/env python3
"""
Inspect a PDF's typography and layout using PyMuPDF (fitz).

Reports:
- Page size (points and inches)
- Approximate text margins (min distances from edges)
- Font names and size histogram
- Bullet/list indentation (if bullets found)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Tuple

import fitz  # PyMuPDF


def inches(points: float) -> float:
    return round(points / 72.0, 3)


def analyze_pdf(pdf_path: Path) -> None:
    doc = fitz.open(str(pdf_path))
    print(f"Pages: {len(doc)}")

    all_font_sizes: Dict[float, int] = {}
    all_fonts: Dict[str, int] = {}
    left_margin = top_margin = right_margin = bottom_margin = None
    bullet_indent_points = []

    for page_index, page in enumerate(doc):
        w, h = page.rect.width, page.rect.height
        if page_index == 0:
            print(f"Page 1 size: {w:.1f} x {h:.1f} pt ({inches(w)} x {inches(h)} in)")

        d = page.get_text("dict")
        for b in d.get("blocks", []):
            if b.get("type", 0) != 0:
                continue
            x0, y0, x1, y1 = b.get("bbox", (0, 0, 0, 0))
            lm = x0
            tm = y0
            rm = w - x1
            bm = h - y1
            left_margin = lm if left_margin is None else min(left_margin, lm)
            top_margin = tm if top_margin is None else min(top_margin, tm)
            right_margin = rm if right_margin is None else min(right_margin, rm)
            bottom_margin = bm if bottom_margin is None else min(bottom_margin, bm)

            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    size = round(span.get("size", 0.0), 1)
                    text = span.get("text", "")
                    font = span.get("font", "")
                    all_font_sizes[size] = all_font_sizes.get(size, 0) + len(text)
                    all_fonts[font] = all_fonts.get(font, 0) + len(text)
                    if text.strip().startswith("•") or text.strip().startswith("-"):
                        # approximate indent by the block's left x0
                        bullet_indent_points.append(x0)

    print("Approx margins (min from edges):")
    print(
        f"  left: {left_margin:.1f} pt ({inches(left_margin)} in), "
        f"right: {right_margin:.1f} pt ({inches(right_margin)} in), "
        f"top: {top_margin:.1f} pt ({inches(top_margin)} in), "
        f"bottom: {bottom_margin:.1f} pt ({inches(bottom_margin)} in)"
    )

    print("Font sizes (pt -> chars):")
    for size, count in sorted(all_font_sizes.items()):
        print(f"  {size:>4}: {count}")

    print("Fonts (name -> chars):")
    for font, count in sorted(all_fonts.items(), key=lambda x: (-x[1], x[0]))[:6]:
        print(f"  {font}: {count}")

    if bullet_indent_points:
        avg_indent = sum(bullet_indent_points) / len(bullet_indent_points)
        print(
            f"Bullet indent approx: {avg_indent:.1f} pt ({inches(avg_indent)} in) from left edge"
        )
    else:
        print("No bullets detected (by • or - prefix)")


def main(argv: list[str]) -> int:
    target = Path(argv[1]) if len(argv) > 1 else Path("__pycache__/Example/41603_68a3e4df19515_Experian.pdf")
    if not target.exists():
        print(f"File not found: {target}")
        return 1
    analyze_pdf(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


