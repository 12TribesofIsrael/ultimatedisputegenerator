#!/usr/bin/env python3
"""
Convert generated letters under outputletter/ from Markdown to:
- TXT (default): creates .txt alongside .md
- PDF (if arg 'pdf'): creates .pdf alongside .md

Usage:
  python convert_to_professional_pdf.py       # generate .txt versions
  python convert_to_professional_pdf.py pdf   # generate .pdf versions
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from utils.template_integration import clean_template_content_for_consumer
import re


def find_markdown_letters(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []
    return base.rglob("*.md")


def md_to_text(md: str) -> str:
    # Minimal markdown cleanup for plain text output (more robust)
    text = md.replace("\r\n", "\n")
    out_lines: list[str] = []
    for raw in text.split("\n"):
        line = raw.lstrip()
        # Remove markdown heading markers
        if line.startswith("#"):
            line = line.lstrip("# ")
        # Convert bold field labels like **Date:** to Date:
        line = re.sub(r"^\s*\*\*(.+?)\*\*:\s*", r"\1: ", line)
        # Convert any remaining bold/italic to plain
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"\*(.+?)\*", r"\1", line)
        # Bullets → remove marker, keep text
        if line.startswith("- "):
            line = line[2:]
        if line.startswith("* "):
            line = line[2:]
        # Strip simple enumerator prefixes (1., 2), (3) or "4 " at start; keep content
        line = re.sub(r"^\s*(?:[1-9]|10)[\.)]\s+", "", line)
        line = re.sub(r"^\s*(?:[1-9]|10)\s+(?=[A-Za-z§(0-9])", "", line)
        out_lines.append(line)
    return "\n".join(out_lines).strip()


def normalize_for_pdf(text: str) -> str:
    """Replace problematic Unicode with PDF-safe ASCII for Type1 fonts.

    - Smart quotes → straight quotes
    - En/em dashes and minus → hyphen
    - Bullet → hyphen
    - NBSP → space
    """
    replacements = {
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201C": '"',  # left double quote
        "\u201D": '"',  # right double quote
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2212": "-",  # minus sign
        "\u2022": "-",  # bullet
        "\u00A0": " ",  # nbsp
        "\u2009": " ",  # thin space
        "\u200A": " ",
        "\u200B": "",    # zero-width space
        "\u202F": " ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # Final safeguard: replace any remaining non-ASCII (outside printable range)
    # with spaces to avoid garbled glyphs in base Type1 fonts
    text = "".join(
        (ch if (ch in "\n\r\t" or 32 <= ord(ch) <= 126) else " ")
        for ch in text
    )
    return text

def sanitize_letter_content(content: str) -> str:
    # Base cleaning from template integration
    cleaned = clean_template_content_for_consumer(content)

    # Remove reference and round/system headings and any branding
    patterns = [
        r"(?im)^\s*\*\*?reference:?\*\*?.*$",
        r"(?im)^\s*(#|\*\*)?\s*round\s*\d+.*$",
        r"(?im)^.*Professional Dispute Letter.*$",
        r"(?im)^\s*CC:.*$",
        r"(?im)^\s*\*\*CC:\*\*.*$",
        r"(?im)Dr\.\s*Lex\s*Grant.*$",
        r"(?im)Credit\s*Expert.*$",
        r"(?im)Ultimate Dispute Letter Generator.*$",
        r"(?im)AI( |-)?generated|automation|system( |-)?generated",
    ]
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned)

    # Drop banner-like headings in the first few lines
    lines = cleaned.splitlines()
    pruned: list[str] = []
    banner_tokens = (
        "ROUND",
        "DEMAND FOR DELETION",
        "DELETION DEMAND",
        "CREDIT BUREAU",
        "PROFESSIONAL DISPUTE LETTER",
    )
    for idx, ln in enumerate(lines):
        if idx < 6:
            up = ln.strip().upper()
            if any(tok in up for tok in banner_tokens):
                continue
            # Drop lines that are mostly uppercase symbols/words
            if up and up == up.upper() and len(up) <= 80 and any(c.isalpha() for c in up):
                continue
        pruned.append(ln)
    cleaned = "\n".join(pruned)

    # Address formatting: split semicolon-separated street and city/state on Address lines
    def _split_address_semicolon(match: re.Match[str]) -> str:
        label = match.group(1) or "Address:"
        street = match.group(2).strip()
        citystate = match.group(3).strip()
        return f"{label} {street}\n{citystate}"

    cleaned = re.sub(
        r"(?im)^\s*(\*\*?Address:?\*\*?|Address:)\s*(.+?);\s*(.+)$",
        _split_address_semicolon,
        cleaned,
    )

    # Demote shouty/legalistic headings to more natural phrasing (allow optional markdown tokens)
    md_prefix = r"(?:[#*_`>\-]+\s*)?"
    heading_replacements: list[tuple[str, str]] = [
        (fr"(?im)^\s*{md_prefix}ACCOUNTS DEMANDED FOR DELETION\s*$", "What I’m disputing"),
        (fr"(?im)^\s*{md_prefix}REQUEST FOR PROCEDURE.*$", "How you determined accuracy"),
        (fr"(?im)^\s*{md_prefix}15-?DAY ACCELERATION.*$", "Please respond within 15 days"),
        (fr"(?im)^\s*{md_prefix}STATUTORY VIOLATIONS IDENTIFIED\s*$", "What the law says"),
        (fr"(?im)^\s*{md_prefix}FCRA Violations.*$", "FCRA notes"),
        (fr"(?im)^\s*{md_prefix}FDCPA Violations.*$", "FDCPA notes"),
        (fr"(?im)^\s*{md_prefix}STATUTORY DAMAGES CALCULATION\s*$", "Potential impact"),
        (fr"(?im)^\s*{md_prefix}DEMAND FOR SPECIFIC PERFORMANCE\s*$", "What I need from you"),
        (fr"(?im)^\s*{md_prefix}Failure to Comply Will Result In\s*$", "If I don’t hear back"),
        (fr"(?im)^\s*{md_prefix}METRO 2 COMPLIANCE DEMAND\s*$", "Metro 2 reporting issues"),
        (fr"(?im)^\s*{md_prefix}Specific Metro 2 Violations\s*$", "Examples of Metro 2 issues"),
        (fr"(?im)^\s*{md_prefix}REINSERTION PROTECTION\s*$", "If something gets added back later"),
        (fr"(?im)^\s*{md_prefix}CONCLUSION AND DEMAND\s*$", "In closing"),
        (fr"(?im)^\s*{md_prefix}TOTAL POTENTIAL DAMAGES:.*$", ""),
        (fr"(?im)^\s*{md_prefix}LEGAL NOTICE OF DISPUTE AND DEMAND FOR DELETION\s*$", "About my dispute"),
        (fr"(?im)^\s*{md_prefix}Subject:\s*.*$", ""),
    ]
    for pat, repl in heading_replacements:
        cleaned = re.sub(pat, repl, cleaned)

    # Ensure paragraph breaks before common section headers
    hdr_tokens = (
        "Date:",
        "Subject:",
        "Dear ",
        "What I’m disputing",
        "How you determined accuracy",
        "Please respond within 15 days",
        "What the law says",
        "Potential impact",
        "What I need from you",
        "Metro 2 reporting issues",
        "Examples of Metro 2 issues",
        "If something gets added back later",
        "In closing",
        "Certification:",
        "Certification",
        "Sincerely,",
    )
    lines2: list[str] = []
    prev_nonempty = False
    for ln in cleaned.splitlines():
        ln_stripped = ln.strip()
        is_header = any(ln_stripped.lower().startswith(t.lower()) for t in hdr_tokens)
        if is_header and prev_nonempty:
            # Insert a blank line before header to force a new paragraph
            lines2.append("")
        lines2.append(ln)
        prev_nonempty = bool(ln_stripped)
    cleaned = "\n".join(lines2)

    # Ensure gentle blank lines after greeting and before signature
    cleaned = re.sub(r"(?im)^(Dear\s+[^,]+,)$", r"\1\n", cleaned)
    cleaned = re.sub(r"(?im)^(Sincerely,)\s*$", r"\1\n", cleaned)

    # Collapse extra blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def write_txt(md_path: Path, content: str) -> Path:
    out_path = md_path.with_suffix(".txt")
    out_path.write_text(md_to_text(sanitize_letter_content(content)), encoding="utf-8")
    return out_path


def write_pdf(md_path: Path, content: str) -> Path:
    # Lazy import reportlab
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, KeepTogether
    from reportlab.lib.units import inch
    from reportlab.lib import fonts
    from reportlab.lib.enums import TA_LEFT

    out_path = md_path.with_suffix(".pdf")

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        # Match example approx margins: left/right ~78pt, top ~80.4pt, bottom ~76.6pt
        leftMargin=(78.0 / 72.0) * inch,
        rightMargin=(78.0 / 72.0) * inch,
        topMargin=(80.4 / 72.0) * inch,
        bottomMargin=(76.6 / 72.0) * inch,
        title=md_path.stem,
        author="Personal Letter",
    )

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        name="LetterBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        spaceAfter=10,
        spaceBefore=0,
    )
    story = []

    # --- Extract consumer header info from original Markdown ---
    # We want: Name, Address lines, SSN, DOB, Date (top-right)
    import re as _re
    raw_md = content or ""

    def _find_field(label: str) -> str | None:
        m = _re.search(rf"(?im)^\s*\*\*?{_re.escape(label)}:??\*\*?\s*(.+)$", raw_md)
        return m.group(1).strip() if m else None

    def _find_consumer_address() -> str | None:
        # Prefer the Address line that appears AFTER the From line
        lines = raw_md.splitlines()
        from_idx = None
        for i, ln in enumerate(lines):
            if _re.search(r"(?im)^\s*\*\*?From:?\*\*?\s+", ln):
                from_idx = i
                break
        if from_idx is not None:
            for j in range(from_idx + 1, min(from_idx + 6, len(lines))):
                m = _re.search(r"(?im)^\s*\*\*?Address:?\*\*?\s*(.+)$", lines[j])
                if m:
                    return m.group(1).strip()
        # Fallbacks: choose Address line containing SSN/DOB tokens, else the last Address line
        addr_matches = _re.findall(r"(?im)^\s*\*\*?Address:?\*\*?\s*(.+)$", raw_md)
        if addr_matches:
            for a in addr_matches:
                if ("SSN" in a) or ("DOB" in a):
                    return a.strip()
            return addr_matches[-1].strip()
        return None

    header_name = _find_field("From")
    header_date = _find_field("Date")
    header_addr_raw = _find_consumer_address()

    header_ssn = None
    header_dob = None
    address_lines: list[str] = []
    if header_addr_raw:
        # Split by semicolons to capture street, city/state zip, and any SSN/DOB tokens
        parts = [p.strip() for p in header_addr_raw.split(";") if p.strip()]
        for p in parts:
            if p.upper().startswith("SSN"):
                # Normalize to "SSN: xxx"
                header_ssn = p if ":" in p else f"SSN: {p.split()[-1]}"
            elif p.upper().startswith("DOB"):
                header_dob = p if ":" in p else f"DOB: {p.split()[-1]}"
            else:
                address_lines.append(p)

    # Build right-aligned header block if we have at least a name or address
    header_lines: list[str] = []
    if header_name:
        header_lines.append(header_name)
    header_lines.extend(address_lines[:2])  # keep to two lines max for compact header
    if header_ssn:
        header_lines.append(header_ssn)
    if header_dob:
        header_lines.append(header_dob)
    if header_date:
        header_lines.append(f"Date: {header_date}")

    if header_lines:
        header_style = ParagraphStyle(
            name="ConsumerHeader",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=16,
        )
        header_html = "<br/>".join(
            ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") or " "
            for ln in header_lines
        )
        story.append(Paragraph(header_html, header_style))

    # Build paragraphs with soft line breaks, to improve spacing
    sanitized = md_to_text(sanitize_letter_content(content))
    sanitized = normalize_for_pdf(sanitized)
    # Remove any lingering bullet markers at start of lines
    sanitized = re.sub(r"^\s*[•\-*]\s+", "", sanitized, flags=re.MULTILINE)
    # Remove duplicate label headings when the following lines already list fields
    sanitized = re.sub(r"(?im)^\s*Reported\s*Fields\s*$\n", "", sanitized)
    sanitized = re.sub(r"(?im)^\s*Legal\s*Basis\s*\(derived.*?\):\s*$\n?", "", sanitized)
    sanitized = re.sub(r"(?im)^\s*Detected\s*Issues\s*\(as\s*parsed.*?\):\s*$\n?", "", sanitized)
    sanitized = re.sub(r"(?im)^\s*Requested\s*Action\s*\(based.*?\):\s*$\n?", "", sanitized)

    # Remove header fields from body to avoid duplication (placed in top header)
    # Only remove the first Date: line, and only the specific consumer From/Address line
    sanitized = re.sub(r"(?im)^\s*Date:\s*.*$\n?", "", sanitized, count=1)
    if header_name:
        sanitized = re.sub(rf"(?m)^\s*From:\s*{re.escape(header_name)}\s*$\n?", "", sanitized, count=1)
    if header_addr_raw:
        sanitized = re.sub(rf"(?m)^\s*Address:\s*{re.escape(header_addr_raw)}\s*$\n?", "", sanitized, count=1)
    # Remove any one-line personal info summary lines that repeat SSN/DOB/email
    sanitized = re.sub(r"(?im)^\s*(?:[A-Za-z].*?,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?.*?(?:SSN:|DOB:).*)$\n?", "", sanitized)
    sanitized = re.sub(r"(?im)^\s*[^\s@]+@[^\s@]+\.[A-Za-z]{2,}.*$\n?", "", sanitized)
    # Also clean any leftover consumer header lines in the very top block (first ~20 lines)
    top_lines = sanitized.splitlines()
    cleaned_top: list[str] = []
    for i, ln in enumerate(top_lines):
        if i < 20:
            if _re.search(r"^(From:|Address:|SSN:|DOB:)\s*", ln, flags=_re.IGNORECASE):
                continue
        cleaned_top.append(ln)
    sanitized = "\n".join(cleaned_top)
    # Deduplicate accidental repeated LEGAL headings like "LEGAL LEGAL NOTICE..."
    sanitized = re.sub(r"(?im)\bLEGAL\s+LEGAL\b", "LEGAL", sanitized)
    blocks = [b.strip() for b in re.split(r"\n\s*\n", sanitized) if b.strip()]

    def _paragraph_from_block(text_block: str) -> Paragraph:
        lines = [
            (ln.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;") or " ")
            for ln in text_block.splitlines()
        ]
        html = "<br/>".join(lines)
        return Paragraph(html, body_style)

    for idx, block in enumerate(blocks):
        raw_lines = [ln for ln in block.splitlines() if ln.strip()]

        def is_bullet(ln: str) -> bool:
            return False

        def is_numbered(ln: str) -> bool:
            return bool(re.match(r"^\s*\d+\.[\s\S]*$", ln))

        bullet_lines = [ln for ln in raw_lines if is_bullet(ln)]
        numbered_lines = [ln for ln in raw_lines if is_numbered(ln)]

        # Address/greeting/signature blocks should stay together
        keep_together = any(
            token in block for token in ("Date:", "To:", "From:", "Sincerely,")
        )

        # Disable bullet rendering completely (render as paragraphs)
        if False:
            # Preface: consecutive non-bullet lines at the start
            preface: list[str] = []
            i = 0
            while i < len(raw_lines) and not is_bullet(raw_lines[i]):
                preface.append(raw_lines[i])
                i += 1
            trailing: list[str] = [ln for ln in raw_lines[i:] if not is_bullet(ln)]

            if preface:
                para = _paragraph_from_block("\n".join(preface))
                story.append(KeepTogether(para) if keep_together else para)

            items: list[ListItem] = []
            for bl in raw_lines:
                if not is_bullet(bl):
                    continue
                text = bl.strip()[2:].lstrip()  # strip leading bullet marker and following space
                para = _paragraph_from_block(text)
                items.append(ListItem(para))
            if items:
                list_flow = ListFlowable(
                    items,
                    bulletType="bullet",
                    leftIndent=0,
                    bulletIndent=12,
                    bulletFontName="Helvetica",
                    bulletFontSize=11,
                    bulletChar="-",
                )
                story.append(KeepTogether(list_flow) if keep_together else list_flow)

            if trailing:
                para = _paragraph_from_block("\n".join(trailing))
                story.append(KeepTogether(para) if keep_together else para)
        # If block is predominantly numbered items, render as numbered list.
        elif len(numbered_lines) >= 2 and len(numbered_lines) >= len(raw_lines) * 0.6:
            preface: list[str] = []
            i = 0
            while i < len(raw_lines) and not is_numbered(raw_lines[i]):
                preface.append(raw_lines[i])
                i += 1
            trailing: list[str] = [ln for ln in raw_lines[i:] if not is_numbered(ln)]

            if preface:
                para = _paragraph_from_block("\n".join(preface))
                story.append(KeepTogether(para) if keep_together else para)

            items: list[ListItem] = []
            start_num = None
            for nl in raw_lines:
                if not is_numbered(nl):
                    continue
                m = re.match(r"^\s*(\d+)\.\s*(.*)$", nl)
                num = int(m.group(1)) if m else None
                text = m.group(2) if m else nl
                if start_num is None and num is not None:
                    start_num = num
                para = _paragraph_from_block(text)
                items.append(ListItem(para))
            if items:
                list_flow = ListFlowable(
                    items,
                    bulletType="1",
                    start=start_num or 1,
                    leftIndent=0,
                    bulletIndent=12,
                    bulletFontName="Helvetica",
                    bulletFontSize=11,
                )
                story.append(KeepTogether(list_flow) if keep_together else list_flow)

            if trailing:
                para = _paragraph_from_block("\n".join(trailing))
                story.append(KeepTogether(para) if keep_together else para)
        else:
            para = _paragraph_from_block(block)
            story.append(KeepTogether(para) if keep_together else para)

    doc.build(story)
    return out_path


def main() -> int:
    mode = (sys.argv[1].lower() if len(sys.argv) > 1 else "txt").strip()
    base = Path("outputletter")
    if not base.exists():
        print(f"❌ No outputletter directory found at: {base}")
        return 1

    md_files = list(find_markdown_letters(base))
    if not md_files:
        print("❌ No .md letters found under outputletter/.")
        return 1

    print(f"🔄 Converting {len(md_files)} letter(s) to {mode.upper()}...")
    converted = 0

    for md_path in md_files:
        try:
            content = md_path.read_text(encoding="utf-8")
            if mode == "pdf":
                out_path = write_pdf(md_path, content)
            else:
                out_path = write_txt(md_path, content)
            print(f"✅ {md_path.name} -> {out_path.name}")
            converted += 1
        except Exception as e:
            print(f"❌ Failed to convert {md_path}: {e}")

    print(f"\n🎉 Done. Converted {converted} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


