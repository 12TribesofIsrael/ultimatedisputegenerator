from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import os

import fitz  # PyMuPDF

from utils.ocr_fallback import extract_text_via_ocr
from utils.template_integration import clean_template_content_for_consumer

from extract_account_details import (
    extract_account_details,
    detect_bureau_from_pdf,
    filter_negative_accounts,
    create_organized_folders,
    generate_all_letters,
)


def _extract_text_with_ocr_fallback(pdf_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception:
        text = ""

    if len(text.strip()) < 100:
        try:
            text = extract_text_via_ocr(pdf_path)
        except Exception:
            pass

    return text or ""


def process_reports(
    input_dir: str,
    output_base_dir: str,
    full_name: str,
    address: str,
    round_number: int = 1,
) -> Dict[str, Any]:
    """Process PDFs and generate dispute letters, returning structured results.

    Args:
        input_dir: directory containing uploaded PDFs
        output_base_dir: base directory to write outputs into
        full_name: consumer's full name
        address: consumer address (single string, will be split by newlines)
        round_number: dispute round
    Returns:
        Dict with summary and generated letters
    """

    input_path = Path(input_dir)
    output_base = Path(output_base_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))
    letters: List[Dict[str, Any]] = []
    analyses: List[Dict[str, Any]] = []
    processed_files: List[str] = []

    forbidden_patterns = [
        r"Dr\.\s*Lex\s*Grant",
        r"Credit\s*Expert",
        r"Ultimate Dispute Letter Generator",
        r"AI( |-)?generated|automation|system( |-)?generated",
        r"^\s*CC:.*$",
        r"^\s*\*\*CC:\*\*.*$",
    ]

    for pdf in pdf_files:
        processed_files.append(pdf.name)
        text = _extract_text_with_ocr_fallback(str(pdf))
        if not text:
            continue

        accounts = extract_account_details(text)
        negative_accounts = filter_negative_accounts(accounts)
        bureau_detected = detect_bureau_from_pdf(text, pdf.name)

        # Organize output folders under the temp output base
        folders = create_organized_folders(bureau_detected, base_path=str(output_base))

        consumer_address_lines = [line.strip() for line in address.splitlines() if line.strip()] if address else None

        # Strategy: generate bureau letter only (1) if bureau detected, otherwise max-pressure (3)
        user_choice = 1 if bureau_detected else 3
        generated_files = generate_all_letters(
            user_choice,
            negative_accounts,
            full_name,
            bureau_detected or "Unknown",
            folders,
            round_number,
            consumer_address_lines,
        )

        # Read and clean generated files
        for file_path in generated_files:
            try:
                p = Path(file_path)
                content = p.read_text(encoding="utf-8")
                cleaned = clean_template_content_for_consumer(content)
                # Final sanitize pass: hard-strip any forbidden markers
                for pat in forbidden_patterns:
                    try:
                        cleaned = __import__("re").sub(pat, "", cleaned, flags=__import__("re").IGNORECASE | __import__("re").MULTILINE)
                    except Exception:
                        pass
                letters.append(
                    {
                        "source_pdf": pdf.name,
                        "bureau": (p.parent.name.capitalize() if p.parent.name else bureau_detected) or "Unknown",
                        "filename": p.name,
                        "path": str(p),
                        "content": cleaned or content,
                    }
                )
            except Exception:
                continue

        analyses.append(
            {
                "source_pdf": pdf.name,
                "bureau_detected": bureau_detected,
                "accounts_total": len(accounts),
                "negative_accounts": len(negative_accounts),
            }
        )

    return {
        "status": "ok",
        "processed": processed_files,
        "letters": letters,
        "analysis": analyses,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "output_dir": str(output_base),
    }


