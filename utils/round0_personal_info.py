#!/usr/bin/env python3
"""
Round 0 (Personal Information Cleanup) utilities.

Parses personal identifiers from a credit report, compares them to user-entered
information, and generates a Round 0 letter requesting deletion of inaccurate
identifiers per FCRA §1681e(b), §611/§1681i, and §1681i(a)(5)(B).
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_name(name: str) -> str:
    name = _normalize_whitespace(name)
    return name.lower()


def _normalize_address(address: str) -> str:
    # Basic normalization: remove punctuation, collapse spaces, lowercase
    cleaned = re.sub(r"[.,]", " ", address)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower()


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    # Keep last 10 where possible
    return digits[-10:]


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def parse_report_personal_identifiers(report_text: str) -> Dict[str, List[str]]:
    """Extract lists of personal identifiers from the report text.

    Returns a dict with keys: names, addresses, employers, phones, emails.
    Extraction uses tolerant regex patterns for common bureau formats.
    """
    text = report_text or ""

    # Candidates containers
    names: List[str] = []
    addresses: List[str] = []
    employers: List[str] = []
    phones: List[str] = []
    emails: List[str] = []

    # Names
    # Capture in sections like "Also Known As", "Other Names", "Former Name"
    name_section_patterns = [
        r"(?:Also\s+Known\s+As|Other\s+Names|Former\s+Name\(s\)|Name\s+Variations)[:\s]*([\s\S]{0,300})",
    ]
    for patt in name_section_patterns:
        for m in re.finditer(patt, text, flags=re.IGNORECASE):
            block = m.group(1)
            for line in block.splitlines():
                candidate = _normalize_whitespace(line)
                if 4 <= len(candidate) <= 60 and not re.search(r"\d", candidate):
                    names.append(candidate)

    # Often the primary name appears near a Name label
    for m in re.finditer(r"(?:^|\n)\s*Name\s*[:\n]\s*([A-Z][A-Za-z\s]{3,60})", text):
        names.append(_normalize_whitespace(m.group(1)))

    # Addresses
    # Look for Address sections; collect lines that look like street + city/state/zip
    address_block_patterns = [
        r"(?:Addresses?|Address\s+History)[:\s]*([\s\S]{0,600})",
        r"(?:Former\s+Address(?:es)?|Previous\s+Address(?:es)?)[:\s]*([\s\S]{0,400})",
    ]
    for patt in address_block_patterns:
        for m in re.finditer(patt, text, flags=re.IGNORECASE):
            block = m.group(1)
            for line in block.splitlines():
                candidate = _normalize_whitespace(line)
                if re.search(r"^\d{1,6}\s+[A-Za-z]", candidate):
                    addresses.append(candidate)
                # City, ST ZIP on next line
                elif re.search(r"[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?", candidate):
                    addresses.append(candidate)

    # Employers
    for m in re.finditer(r"(?:Employer|Employment\s+History)[:\s]*([\s\S]{0,300})", text, flags=re.IGNORECASE):
        block = m.group(1)
        for line in block.splitlines():
            candidate = _normalize_whitespace(line)
            if 2 <= len(candidate) <= 60 and not re.search(r"\d{3,}", candidate):
                employers.append(candidate)

    # Phones
    for m in re.finditer(r"(?:(?:Phone|Tel)[:\s]*)?(\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4})", text, flags=re.IGNORECASE):
        phones.append(_normalize_whitespace(m.group(1)))

    # Emails
    for m in re.finditer(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        emails.append(_normalize_whitespace(m.group(0)))

    # Deduplicate while preserving order
    def _dedup(seq: List[str]) -> List[str]:
        seen = set()
        out = []
        for item in seq:
            key = item.lower()
            if key not in seen:
                out.append(item)
                seen.add(key)
        return out

    return {
        "names": _dedup(names),
        "addresses": _dedup(addresses),
        "employers": _dedup(employers),
        "phones": _dedup(phones),
        "emails": _dedup(emails),
    }


def compare_identifiers(
    user_name: str,
    user_address_lines: List[str],
    user_phone: Optional[str],
    user_email: Optional[str],
    report_ids: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """Return which report identifiers must be deleted (do not match user-entered)."""

    # Build canonical current address (street + city/state zip lines only)
    user_street = next((l for l in user_address_lines if re.search(r"^\d{1,6}\s+", l)), "")
    user_city_state_zip = next((l for l in user_address_lines if re.search(r",\s*[A-Z]{2}\s*\d{5}", l)), "")
    user_address_canonical = _normalize_address("; ".join([p for p in [user_street, user_city_state_zip] if p]))

    # Normalized user fields
    user_name_norm = _normalize_name(user_name)
    user_phone_norm = _normalize_phone(user_phone) if user_phone else None
    user_email_norm = _normalize_email(user_email) if user_email else None

    to_delete = {
        "names": [],
        "addresses": [],
        "employers": [],
        "phones": [],
        "emails": [],
    }

    # Names: delete any name not equal to user's name
    for n in report_ids.get("names", []):
        if _normalize_name(n) != user_name_norm:
            to_delete["names"].append(n)

    # Addresses: delete any address whose canonical form != user's canonical
    for a in report_ids.get("addresses", []):
        if user_address_canonical:
            if _normalize_address(a) != user_address_canonical:
                to_delete["addresses"].append(a)
        else:
            # If we don't have a canonical user address, skip deletions
            pass

    # Employers: policy is to remove all employers that are not current
    # Since we do not capture current employer from user, request deletion of all employer entries.
    for e in report_ids.get("employers", []):
        to_delete["employers"].append(e)

    # Phones
    for p in report_ids.get("phones", []):
        if user_phone_norm:
            if _normalize_phone(p) != user_phone_norm:
                to_delete["phones"].append(p)
        else:
            to_delete["phones"].append(p)

    # Emails
    for em in report_ids.get("emails", []):
        if user_email_norm:
            if _normalize_email(em) != user_email_norm:
                to_delete["emails"].append(em)
        else:
            to_delete["emails"].append(em)

    return to_delete


def build_round0_letter_content(
    consumer_name: str,
    consumer_address_lines: List[str],
    bureau_detected: str,
    user_phone: Optional[str],
    user_email: Optional[str],
    to_delete: Dict[str, List[str]],
) -> str:
    """Create a Round 0 letter body in Markdown."""

    today = datetime.now().strftime("%B %d, %Y")
    consumer_address_block = "\n".join([consumer_name] + [l for l in consumer_address_lines if l])

    # Bureau address block (minimal; mirrors existing style)
    bureau = (bureau_detected or "Bureau").strip()
    bureau_addr = {
        "Equifax": "Equifax Information Services LLC\nP.O. Box 740256\nAtlanta, GA 30374",
        "Experian": "Experian\nP.O. Box 4500\nAllen, TX 75013",
        "TransUnion": "TransUnion LLC\nP.O. Box 2000\nChester, PA 19016",
    }.get(bureau, f"{bureau}\n[Address]")

    # Sections for deletions
    def _bullets(values: List[str]) -> str:
        if not values:
            return ""
        return "\n".join([f"- {v}" for v in values])

    names_block = _bullets(to_delete.get("names", []))
    addresses_block = _bullets(to_delete.get("addresses", []))
    employers_block = _bullets(to_delete.get("employers", []))
    phones_block = _bullets(to_delete.get("phones", []))
    emails_block = _bullets(to_delete.get("emails", []))

    parts: List[str] = []
    parts.append(f"# ROUND 0 - PERSONAL INFORMATION CLEANUP - {bureau.upper()} CREDIT BUREAU")
    parts.append("**Consumer-Generated Identifier Correction and Purge Request**")
    parts.append("")
    parts.append(f"**Date:** {today}")
    parts.append(f"**To:** {bureau_addr}")
    parts.append(f"**From:** {consumer_address_block}")
    parts.append("")
    parts.append("## PURPOSE")
    parts.append(
        "I am requesting immediate deletion of all personal identifiers in my file that do not exactly match my current, correct information provided below."
    )
    parts.append("")
    parts.append("## MY CORRECT IDENTIFIERS")
    parts.append(f"- Name: {consumer_name}")
    # Display only the first two address lines for clarity
    addr_lines = [l for l in consumer_address_lines if l][:2]
    if addr_lines:
        parts.append(f"- Address: {'; '.join(addr_lines)}")
    if user_phone:
        parts.append(f"- Phone: {user_phone}")
    if user_email:
        parts.append(f"- Email: {user_email}")
    parts.append("")
    parts.append("## DELETE THE FOLLOWING INACCURATE IDENTIFIERS")
    if names_block:
        parts.append("### Names")
        parts.append(names_block)
    if addresses_block:
        parts.append("### Addresses")
        parts.append(addresses_block)
    if employers_block:
        parts.append("### Employers")
        parts.append(employers_block)
    if phones_block:
        parts.append("### Phone Numbers")
        parts.append(phones_block)
    if emails_block:
        parts.append("### Email Addresses")
        parts.append(emails_block)
    if not any([names_block, addresses_block, employers_block, phones_block, emails_block]):
        parts.append("(No mismatched identifiers were detected in the copy of my report you provided. Please confirm my correct identifiers above and purge any prior variants not reflected here.)")

    parts.append("")
    parts.append("## LEGAL BASIS")
    parts.append("- FCRA §1681e(b): reasonable procedures to assure maximum possible accuracy")
    parts.append("- FCRA §611 / §1681i: reinvestigation and deletion of inaccurate information")
    parts.append("- FCRA §1681i(a)(5)(B): no reinsertions without certification and notice")
    parts.append("- FCRA §1681g: full file disclosure confirming corrections")
    parts.append("")
    parts.append("## REQUIRED ACTIONS (WITHIN 30 DAYS)")
    parts.append("1. Delete all non-matching identifiers listed above.")
    parts.append("2. Confirm in writing the identifiers that remain in my file (the correct set above).")
    parts.append("3. Provide an updated copy of my file showing these corrections.")
    parts.append("4. Certify that no deleted identifiers will be reinserted absent proper certification and notice.")
    parts.append("")
    parts.append("## ATTACHMENTS")
    parts.append("- Government ID")
    parts.append("- Proof of current address (utility/lease/bank)")
    parts.append("- SSN document (W‑2/SSA/tax page – last 4 only)")
    parts.append("")
    parts.append("Sincerely,")
    parts.append(consumer_name)

    return "\n".join(parts) + "\n"


def write_round0_letter(
    consumer_name: str,
    consumer_address_lines: List[str],
    bureau_detected: str,
    user_phone: Optional[str],
    user_email: Optional[str],
    to_delete: Dict[str, List[str]],
    target_dir: Path,
    report_stem: Optional[str] = None,
) -> str:
    """Render and write the Round 0 letter to the bureau folder. Returns file path."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    consumer_last = consumer_name.split()[-1] if consumer_name.strip() else "consumer"
    safe_stem = None
    if report_stem:
        safe_stem = re.sub(r"[^A-Za-z0-9_\-]", "_", report_stem)

    filename = (
        f"{consumer_last}_{date_str}_R0_PERSONAL_INFO_CLEANUP_{bureau_detected}_{safe_stem}.md"
        if safe_stem
        else f"{consumer_last}_{date_str}_R0_PERSONAL_INFO_CLEANUP_{bureau_detected}.md"
    )

    content = build_round0_letter_content(
        consumer_name,
        consumer_address_lines,
        bureau_detected,
        user_phone,
        user_email,
        to_delete,
    )

    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return str(filepath)




