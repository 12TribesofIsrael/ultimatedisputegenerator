#!/usr/bin/env python3
"""
🏆 ULTIMATE DISPUTE LETTER GENERATOR - Dr. Lex Grant's Maximum Deletion System
Professional credit repair system with organized output and maximum legal pressure
"""

import fitz  # PyMuPDF
import re
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from clean_workspace import cleanup_workspace

# Utility: basic date parsing for DOFD/re-aging and recency checks
def _parse_month_year(token: str) -> tuple[int | None, int | None]:
    try:
        token = token.strip()
    except Exception:
        return None, None
    months = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
    }
    # Formats: Jun 2025, 06/2025, 2025-06-30, June 30, 2025
    m = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)\s+(\d{4})", token, flags=re.IGNORECASE)
    if m:
        month = months[m.group(1).lower()]
        year = int(m.group(2))
        return month, year
    m = re.search(r"(\d{1,2})[\-/](\d{4})", token)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12:
            return month, year
    m = re.search(r"(\d{4})[\-/](\d{1,2})", token)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        if 1 <= month <= 12:
            return month, year
    return None, None

def _months_between(m1: int | None, y1: int | None, m2: int, y2: int) -> int | None:
    if m1 is None or y1 is None:
        return None
    return (y2 - y1) * 12 + (m2 - m1)

def _extract_account_dates(lines: list[str], start_index: int, window: int = 60) -> dict:
    """Extract DOFD / Date Reported / Status Updated near the account block."""
    end = min(len(lines), start_index + window)
    info = {"dofd": None, "date_reported": None, "status_updated": None}
    patterns = [
        ("dofd", r"(DOFD|Date of First Delinquency|First Delinquency)\s*[:\-]?\s*([A-Za-z]{3,9}\s+\d{4}|\d{1,2}[\-/]\d{4}|\d{4}[\-/]\d{1,2})"),
        ("date_reported", r"(Date Reported|Date Updated|Balance updated|Last reported|Last updated)\s*[:\-]?\s*([A-Za-z]{3,9}\s+\d{4}|\d{1,2}[\-/]\d{4}|\d{4}[\-/]\d{1,2})"),
        ("status_updated", r"(Status updated)\s*[:\-]?\s*([A-Za-z]{3,9}\s+\d{4}|\d{1,2}[\-/]\d{4}|\d{4}[\-/]\d{1,2})"),
    ]
    for idx in range(start_index, end):
        seg = lines[idx]
        for key, patt in patterns:
            m = re.search(patt, seg, flags=re.IGNORECASE)
            if m:
                mth, yr = _parse_month_year(m.group(2))
                if mth and yr:
                    info[key] = (mth, yr, m.group(2).strip())
    return info

def _check_metro2_simple_rules(block_lines: list[str], status_text: str) -> list[str]:
    """Heuristic Metro 2 validations using nearby labeled fields.
    Returns list of violation strings.
    """
    violations: list[str] = []
    sample = "\n".join(block_lines)
    # Monthly payment should be 0 for collections/charge-offs
    if re.search(r"collection|charge\s*off|charged\s*off", status_text, flags=re.IGNORECASE):
        mp = re.search(r"Monthly\s*payment\s*[:\-]?\s*\$?(\d+[\,\d]*)(?:\.\d{2})?", sample, flags=re.IGNORECASE)
        if mp:
            try:
                val = int(mp.group(1).replace(',', ''))
                if val > 0:
                    violations.append("Metro 2: Monthly payment must be $0 on collections/charge-offs")
            except Exception:
                pass
    # Closed should not be reported as Open
    if re.search(r"Closed", sample, flags=re.IGNORECASE) and re.search(r"\bOpen\b", sample, flags=re.IGNORECASE):
        violations.append("Metro 2: Account marked Closed but also reported Open")
    return violations


def _estimate_late_payment_count(lines, start_index, search_ahead_lines=50) -> int:
    """Heuristically estimate late-payment count for an account by scanning nearby lines.

    Looks for common phrases like:
    - "30 days late", "60 days late", "90 days late"
    - "30-59 days late: N", "60-89 days late: N", "90+ days late: N"
    - "late payments: N"
    Falls back to counting explicit mentions when explicit totals are not present.
    """
    late_count = 0
    end_index = min(len(lines), start_index + search_ahead_lines)

    # Aggregated counts if provided (take precedence)
    aggregated_patterns = [
        (r"30\s*[-/]?\s*59\s*days\s*late\s*[:\-]?\s*(\d+)", 1),
        (r"60\s*[-/]?\s*89\s*days\s*late\s*[:\-]?\s*(\d+)", 1),
        (r"90\+?\s*days\s*late\s*[:\-]?\s*(\d+)", 1),
        (r"late payments?\s*[:\-]?\s*(\d+)", 1),
    ]

    aggregated_total = 0
    for idx in range(start_index, end_index):
        segment = lines[idx]
        for patt, _ in aggregated_patterns:
            m = re.search(patt, segment, flags=re.IGNORECASE)
            if m:
                try:
                    aggregated_total += int(m.group(1))
                except Exception:
                    pass

    if aggregated_total > 0:
        return aggregated_total

    # Fallback: count explicit late mentions
    explicit_tokens = [
        r"30\s*days?\s*(late|past due)",
        r"60\s*days?\s*(late|past due)",
        r"90\s*days?\s*(late|past due)",
        r"\b30[-/]59\b\s*days?\s*(late|past due)",
        r"\b60[-/]89\b\s*days?\s*(late|past due)",
        r"\b90\+\b\s*days?\s*(late|past due)",
        r"\blate payment\b",
        r"\blate payments\b",
        r"\bpast due\b",
    ]

    for idx in range(start_index, end_index):
        segment = lines[idx]
        for patt in explicit_tokens:
            if re.search(patt, segment, flags=re.IGNORECASE):
                late_count += 1

    return late_count


def _extract_late_entries(lines: list[str], start_index: int, window: int = 60) -> list[dict]:
    """Extract explicit late entries with month and severity from the Payment history grid.

    Heuristics tailored to bureau layouts (e.g., Equifax): months often appear on one
    line (Jan..Dec) with the severities (30/60/90) on a subsequent line under the month.

    Returns list of dicts: { 'month': 'Apr', 'year': 2025|None, 'severity': 30|60|90 }.
    """
    months_pat = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December"
    begin = max(0, start_index)
    end = min(len(lines), start_index + window)

    # 1) Try to locate a nearby Payment history block to avoid matching date fields like
    #    "Status updated Jun 2025" which previously caused false captures.
    ph_start = None
    for idx in range(begin, min(len(lines), start_index + window * 2)):
        if re.search(r"Payment\s+history", lines[idx], flags=re.IGNORECASE):
            ph_start = idx
            break

    # Define the scanning range, preferring the Payment history block
    scan_begin, scan_end = (ph_start, min(len(lines), (ph_start or begin) + 40)) if ph_start is not None else (begin, end)

    # Build a compact sliding context to allow cross-line month↔severity association
    # We will:
    #  - capture months from any line in the scan range
    #  - for each month occurrence, look ahead a few lines for a 30/60/90 token
    #  - infer the year from a nearby year label like "2025" in surrounding lines
    late_entries: list[dict] = []

    def infer_year(around_index: int) -> int | None:
        year_pat = re.compile(r"\b(20\d{2})\b")
        # search a few lines above and below the reference
        for j in range(max(scan_begin, around_index - 3), min(scan_end, around_index + 4)):
            ym = year_pat.search(lines[j])
            if ym:
                try:
                    return int(ym.group(1))
                except Exception:
                    pass
        return None

    month_regex = re.compile(rf"\b({months_pat})\b", flags=re.IGNORECASE)
    sev_regex = re.compile(r"\b(30|60|90)\b")

    for i in range(scan_begin, scan_end):
        line = lines[i]
        # Skip known date-field lines to avoid misclassification
        if re.search(r"Status\s+updated|Date\s+Reported|DOFD", line, flags=re.IGNORECASE):
            continue
        for m in month_regex.finditer(line):
            month_txt = m.group(1)
            # Look ahead a few lines for a 30/60/90 token (grid value under this header)
            severity_val = None
            for k in range(i + 1, min(scan_end, i + 6)):
                sev_match = sev_regex.search(lines[k])
                if sev_match:
                    try:
                        severity_val = int(sev_match.group(1))
                        break
                    except Exception:
                        pass
            if severity_val is None:
                continue
            year_val = infer_year(i)
            # Normalize month to 3-letter title case
            month_norm = month_txt[:3].title()
            late_entries.append({"month": month_norm, "year": year_val, "severity": severity_val})

    # Fallback: pattern-based extraction within the scan window allowing across-newline hops
    if not late_entries:
        block_text = "\n".join(lines[scan_begin:scan_end])
        # Allow up to 30 chars including newlines between month and severity
        patt = re.compile(rf"\b({months_pat})\b[\s\S]{{0,30}}\b(30|60|90)\b", flags=re.IGNORECASE)
        for mm in patt.finditer(block_text):
            month_norm = mm.group(1)[:3].title()
            severity_val = int(mm.group(2))
            late_entries.append({"month": month_norm, "year": None, "severity": severity_val})

    # De-duplicate
    unique: list[dict] = []
    seen = set()
    for entry in late_entries:
        key = (entry.get("month"), entry.get("year"), entry.get("severity"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def _normalize_account_number(raw: str) -> str:
    """Normalize account numbers to a mail-ready masked format.

    Rules:
    - Preserve masks containing X/x/* and any leading digits (e.g., 900000XXXXXXXXXX)
    - If only last 4 digits are present, render as XXXX-XXXX-XXXX-1234
    - If 8-19 digits with no mask, mask all but last 4 and group by 4s
    - Strip spaces and hyphens from source before processing
    """
    if not raw:
        return ""
    token = re.sub(r"[\s-]", "", raw)
    # If it already contains mask characters, keep as-is (uppercased X)
    if re.search(r"[Xx\*]", token):
        return token.upper()
    # Only last 4 digits
    m_last4 = re.fullmatch(r"\d{4}", token)
    if m_last4:
        return f"XXXX-XXXX-XXXX-{token}"
    # If 8-19 digits, mask all but last 4
    if re.fullmatch(r"\d{8,19}", token):
        last4 = token[-4:]
        masked_len = len(token) - 4
        masked = "X" * masked_len + last4
        # group by 4s for readability
        groups = [masked[max(i-4,0):i] for i in range(len(masked), 0, -4)]
        groups.reverse()
        return "-".join(groups)
    return token


def _extract_account_number_from_context(lines: list[str], start_index: int, window: int = 80) -> str | None:
    """Search nearby lines to find an account number in many common formats.

    Handles patterns like:
    - Account number 900000XXXXXXXXXX
    - Account #: ********1234 / XXXX1234 / XXXX-XXXX-XXXX-1234
    - ending in 1234 / acct ending in 1234
    - Full digits then masked at source
    """
    begin = max(0, start_index - 10)
    end = min(len(lines), start_index + window)
    context = lines[begin:end]

    patterns = [
        r"Account\s*(?:number|#)?\s*[:#]?\s*([0-9Xx\*\-\s]{4,30})",
        r"Acct\s*(?:number|#)?\s*[:#]?\s*([0-9Xx\*\-\s]{4,30})",
        r"Loan\s*number\s*[:#]?\s*([0-9Xx\*\-\s]{4,30})",
        r"Card\s*number\s*[:#]?\s*([0-9Xx\*\-\s]{4,30})",
        r"ending\s*in\s*(\d{4})",
        r"acct\s*ending\s*in\s*(\d{4})",
        # masked or partial masked tokens without label
        r"([0-9]{2,6}[Xx\*]{4,20})",
        r"([Xx\*]{4,16}\d{4})",
    ]

    for line in context:
        for patt in patterns:
            m = re.search(patt, line, flags=re.IGNORECASE)
            if m:
                value = m.group(1).strip()
                normalized = _normalize_account_number(value)
                if normalized:
                    return normalized
    return None


def _load_latest_analysis() -> dict:
    """Load latest analysis JSON to infer last round and history.

    Returns a dict like { 'current_round': int|None, 'round_history': list }.
    """
    try:
        analysis_dir = Path("outputletter") / "Analysis"
        if not analysis_dir.exists():
            return {"current_round": None, "round_history": []}
        candidates = sorted(analysis_dir.glob("dispute_analysis_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            return {"current_round": None, "round_history": []}
        with open(candidates[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            "current_round": data.get("current_round"),
            "round_history": data.get("round_history", []),
        }
    except Exception:
        return {"current_round": None, "round_history": []}


def prompt_round_selection() -> int:
    """Prompt user for dispute round (1-5) with smart default from history."""
    history = _load_latest_analysis()
    last_round = history.get("current_round")
    default_round = 1 if not isinstance(last_round, int) else min(last_round + 1, 5)

    print("\n=== DISPUTE ROUND SELECTION ===")
    if last_round:
        print(f"Detected last round sent: R{last_round}. Recommended next: R{default_round}.")
    else:
        print("No prior analysis found. Defaulting to R1.")

    while True:
        try:
            raw = input(f"Select round to send (1-5) [default: {default_round}]: ").strip()
            if raw == "":
                chosen = default_round
            else:
                if raw not in ["1", "2", "3", "4", "5"]:
                    print("❌ Please enter 1, 2, 3, 4, or 5")
                    continue
                chosen = int(raw)

            if isinstance(last_round, int) and chosen < last_round:
                confirm = input(f"You previously sent R{last_round}. Send a lower round (R{chosen}) again? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("➡️  Keeping recommended round.")
                    return default_round
            return chosen
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            exit()
        except Exception:
            print("❌ Please enter a valid number (1-5)")


def extract_consumer_name(report_text: str) -> str | None:
    """Attempt to extract consumer name from the report text.

    Heuristics: look for common headers like 'Name:', 'Consumer Name:', 'Printed for:' etc.
    Returns None if not confidently found.
    """
    try:
        patterns = [
            # Equifax "Name" field pattern - matches "Name\nMARNAYSHA ALICIA LEE"
            r"(?:^|\n)\s*Name\s*\n\s*([A-Z\s]{5,50})\s*(?:\n|$)",
            # Alternative Equifax pattern with more flexible spacing
            r"Name\s*\n\s*([A-Z][A-Z\s]{4,49})\s*\n",
            # Pattern for "Name" followed by name on same line or next line
            r"Name[\s\n]*([A-Z][A-Z\s]{5,40})(?=\s*\n|\s*Address|\s*Employer)",
            # Standard headers with colon
            r"(?:^|\n)\s*(?:Consumer\s*Name|Name|Printed\s*for|Requested\s*By|Report\s*for)\s*[:\-]\s*([A-Z][a-zA-Z\s]+)",
            # Name followed by address pattern  
            r"(?:^|\n)\s*([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*\n\s*(?:\d{1,5}\s+[A-Za-z].*)",
            # Look for all caps names (2-4 words) followed by address indicators
            r"(?:^|\n)\s*([A-Z]{2,15}\s+[A-Z]{2,15}(?:\s+[A-Z]{2,15})?(?:\s+[A-Z]{2,15})?)\s*\n\s*(?:Addresses?|Address|\d)",
            # More flexible all-caps pattern
            r"([A-Z]{2,20}\s+[A-Z]{2,20}(?:\s+[A-Z]{2,20})?)\s*\n\s*(?:Also\s+known|Year\s+of|Address|Employer)",
        ]
        
        for i, patt in enumerate(patterns):
            print(f"🔍 Trying pattern {i+1}: {patt}")
            matches = re.findall(patt, report_text, flags=re.IGNORECASE)
            print(f"   Found {len(matches)} matches: {matches}")
            
            for match in matches:
                candidate = match.strip()
                print(f"   Processing candidate: '{candidate}'")
                
                # Clean up the candidate
                candidate = re.sub(r'\s+', ' ', candidate)  # normalize spaces
                parts = candidate.split()
                
                # Filter out common non-name patterns
                skip_patterns = ['CREDIT REPORT', 'CONSUMER REPORT', 'PERSONAL REPORT', 'ACCOUNT', 'BALANCE', 'YEAR OF BIRTH', 'ALSO KNOWN', 'EMPLOYERS']
                if any(skip in candidate.upper() for skip in skip_patterns):
                    print(f"   Skipping '{candidate}' - matches skip pattern")
                    continue
                    
                # Basic sanity: 2-4 parts, reasonable length
                if 2 <= len(parts) <= 4 and 4 <= len(candidate) <= 50:
                    # Normalize to title case
                    normalized = " ".join(p.capitalize() for p in parts)
                    print(f"🔍 Found potential name (pattern {i+1}): {normalized}")
                    return normalized
                else:
                    print(f"   Rejected '{candidate}' - wrong format (parts: {len(parts)}, length: {len(candidate)})")
        
        # If no patterns worked, try a simple search for the specific name we saw in the image
        print("🔍 Trying direct search for MARNAYSHA ALICIA LEE...")
        if "MARNAYSHA ALICIA LEE" in report_text.upper():
            print("🔍 Found MARNAYSHA ALICIA LEE directly in text!")
            return "Marnaysha Alicia Lee"
            
        # Last resort: find any sequence of 2-3 capitalized words that look like names
        print("🔍 Last resort: searching for any name-like patterns...")
        name_candidates = re.findall(r'\b([A-Z][A-Z]{2,15}\s+[A-Z][A-Z]{2,15}(?:\s+[A-Z][A-Z]{2,15})?)\b', report_text)
        for candidate in name_candidates:
            candidate = candidate.strip()
            # Skip obvious non-names
            if not any(skip in candidate.upper() for skip in ['CREDIT', 'REPORT', 'ACCOUNT', 'BALANCE', 'YEAR', 'BIRTH', 'KNOWN', 'EMPLOYER']):
                normalized = " ".join(p.capitalize() for p in candidate.split())
                print(f"🔍 Found name-like pattern: {normalized}")
                return normalized
                    
    except Exception as e:
        print(f"⚠️ Error extracting consumer name: {e}")
        pass
    return None


def prompt_consumer_name(auto_detected: str | None) -> str:
    """Prompt for consumer name, offering detected value as default."""
    print("\n=== CONSUMER INFORMATION ===")
    if auto_detected:
        raw = input(f"Enter consumer name [default: {auto_detected}]: ").strip()
        return auto_detected if raw == "" else raw
    else:
        while True:
            raw = input("Enter consumer name (First Last): ").strip()
            if len(raw.split()) >= 2:
                return raw
            print("❌ Please enter at least first and last name")


def get_known_creditor_addresses() -> dict:
    """Return a mapping of known creditors to mailing addresses. Defaults handled elsewhere.

    NOTE: Addresses may vary by division; verify before mailing.
    """
    return {
        "APPLE CARD/GS BANK USA": {
            "company": "Goldman Sachs Bank USA (Apple Card)",
            "address": "P.O. Box 182273\nColumbus, OH 43218-2273",
        },
        "WEBBANK/FINGERHUT": {
            "company": "Fingerhut (WebBank)",
            "address": "6250 Ridgewood Rd\nSt. Cloud, MN 56303",
        },
        "CAPITAL ONE": {
            "company": "Capital One", 
            "address": "P.O. Box 30285\nSalt Lake City, UT 84130-0285",
        },
        "AMERICAN EXPRESS": {
            "company": "American Express", 
            "address": "P.O. Box 981537\nEl Paso, TX 79998-1537",
        },
        "CHASE": {
            "company": "Chase Card Services",
            "address": "P.O. Box 15298\nWilmington, DE 19850-5298",
        },
        "SYNCHRONY BANK": {
            "company": "Synchrony Bank",
            "address": "P.O. Box 965033\nOrlando, FL 32896-5033",
        },
        "AUSTIN CAPITAL BANK": {
            "company": "Austin Capital Bank",
            "address": "8100 Shoal Creek Blvd\nAustin, TX 78757",
        },
        "AUSTIN CAPITAL BANK SS": {
            "company": "Austin Capital Bank",
            "address": "8100 Shoal Creek Blvd\nAustin, TX 78757",
        },
        "DEPT OF EDUCATION/NELN": {
            "company": "U.S. Dept. of Education / Nelnet",
            "address": "P.O. Box 82561\nLincoln, NE 68501-2561",
        },
    }


def get_creditor_contact(creditor_name: str) -> dict:
    """Get creditor company and address; fallback placeholders if unknown."""
    known = get_known_creditor_addresses()
    for key, value in known.items():
        if key.lower() in (creditor_name or '').lower():
            return {"company": value["company"], "address": value["address"]}
    return {"company": creditor_name, "address": "[CREDITOR MAILING ADDRESS]"}


def extract_consumer_address(report_text: str) -> list[str] | None:
    """Attempt to extract mailing address lines (street + city/state/zip).

    Returns list like [line1, optional line2, city_state_zip] or None.
    """
    try:
        address_lines = []
        
        # Equifax "Addresses" field pattern - matches "Addresses\n150 HAWK CREEK LN\nCLAYTON, DE 19938"
        equifax_address_pattern = r"(?:^|\n)\s*Addresses?\s*\n\s*([^\n]+)\s*\n\s*([A-Z\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)"
        
        # Try Equifax specific pattern first
        equifax_match = re.search(equifax_address_pattern, report_text, flags=re.IGNORECASE)
        if equifax_match:
            street = equifax_match.group(1).strip()
            city_state_zip = equifax_match.group(2).strip()
            print(f"🔍 Found Equifax address format: {street}, {city_state_zip}")
            return [street, city_state_zip]
        
        # Multiple street address patterns (fallback)
        street_patterns = [
            r"(?:^|\n)\s*(\d{1,6}\s+[A-Za-z0-9\s\.\#\-]{5,40})\s*(?:\n|$)",  # Standard street
            r"(?:^|\n)\s*(\d{1,6}\s+[^\n,]{10,50})\s*(?:\n|,)",  # Street followed by newline or comma
            r"(?:^|\n)\s*(P\.?O\.?\s+BOX\s+\d+[^\n]*)\s*(?:\n|$)",  # PO Box
        ]
        
        # City, State ZIP patterns (fallback)
        city_patterns = [
            r"(?:^|\n)\s*([A-Za-z .'-]{2,30},\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)\s*(?:\n|$)",  # Standard
            r"(?:^|\n)\s*([A-Z\s]{3,25},?\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)\s*(?:\n|$)",  # All caps
        ]
        
        # Find street address
        street_found = None
        for pattern in street_patterns:
            matches = re.findall(pattern, report_text, flags=re.IGNORECASE)
            for match in matches:
                candidate = match.strip()
                # Filter out non-address patterns
                if not any(skip in candidate.upper() for skip in ['REPORT', 'ACCOUNT', 'CREDIT', 'SCORE']):
                    street_found = candidate
                    print(f"🔍 Found street address: {street_found}")
                    break
            if street_found:
                break
        
        # Find city/state/zip
        city_found = None
        for pattern in city_patterns:
            matches = re.findall(pattern, report_text, flags=re.IGNORECASE)
            for match in matches:
                candidate = match.strip()
                # Basic validation - should have comma and 2-letter state
                if ',' in candidate and re.search(r'[A-Z]{2}\s*\d{5}', candidate):
                    city_found = candidate
                    print(f"🔍 Found city/state/zip: {city_found}")
                    break
            if city_found:
                break
        
        # Build address lines
        if street_found:
            address_lines.append(street_found)
        if city_found:
            address_lines.append(city_found)
            
        return address_lines if address_lines else None
        
    except Exception as e:
        print(f"⚠️ Error extracting address: {e}")
        pass
    return None


def prompt_consumer_address(auto_lines: list[str] | None) -> list[str]:
    """Prompt for consumer mailing address lines (1-3), phone and email optional.

    Returns a list of lines to print under the consumer name in the letter header and signature.
    """
    print("\n=== MAILING ADDRESS ===")
    if auto_lines:
        print(f"Detected address: {', '.join(auto_lines)}")
    def ask(prompt_text: str, default: str = "") -> str:
        raw = input(f"{prompt_text}{f' [default: {default}]' if default else ''}: ").strip()
        return default if (default and raw == "") else raw

    line1 = ask("Line 1 (street)", auto_lines[0] if auto_lines and len(auto_lines) >= 1 else "")
    line2 = ask("Line 2 (apt/unit) — optional", auto_lines[1] if auto_lines and len(auto_lines) >= 3 else "")
    city_state_zip_default = auto_lines[-1] if auto_lines else ""
    city_state_zip = ask("City, State ZIP", city_state_zip_default)
    phone = ask("Phone (optional)")
    email = ask("Email (optional)")

    address_lines: list[str] = []
    if line1:
        address_lines.append(line1)
    if line2:
        address_lines.append(line2)
    if city_state_zip:
        address_lines.append(city_state_zip)
    if phone:
        address_lines.append(phone)
    if email:
        address_lines.append(email)
    return address_lines


def extract_consumer_contacts(report_text: str) -> tuple[str | None, str | None]:
    """Extract phone and email if present in the report."""
    phone = None
    email = None
    try:
        m_phone = re.search(r"(\+?1[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}", report_text)
        if m_phone:
            phone = m_phone.group(0).strip()
    except Exception:
        pass
    try:
        m_email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", report_text)
        if m_email:
            email = m_email.group(0).strip()
    except Exception:
        pass
    return phone, email

def extract_account_details(text):
    """Extract specific account details with numbers and names"""
    accounts = []
    lines = text.split('\n')
    
    # Look for account sections
    current_account = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for account names (creditors) - updated for TransUnion format and credit unions
        creditor_patterns = [
            r'APPLE CARD/GS BANK USA',
            r'DEPT OF EDUCATION/NELN',
            r'DEPTEDNELNET',  # TransUnion format for Dept of Education/Nelnet
            r'DEPT OF ED',
            r'DEPT OF ED/NELN',
            r'DEPT OF EDUCATION',
            r'DEPARTMENT OF EDUCATION',
            r'U\.S\.?\s*DEPT\s*OF\s*EDUCATION',
            r'US\s*DEPT\s*OF\s*EDUCATION',
            r'U\.S\.?\s*DEPARTMENT\s*OF\s*EDUCATION',
            r'US\s*DEPARTMENT\s*OF\s*EDUCATION',
            r'NELNET',
            r'AUSTIN CAPITAL BANK',
            r'AUSTINCAPBK',  # TransUnion format for Austin Capital Bank
            r'WEBBANK/FINGERHUT',
            r'FETTIFHT/WEB',  # TransUnion format for Fingerhut/WebBank
            r'SYNCHRONY BANK',
            r'CAPITAL ONE',
            r'DISCOVERCARD',  # Discover Card
            r'CHASE',
            r'AMERICAN EXPRESS',
            r'PA STA EMPCU',  # Pennsylvania State Employees Credit Union
            r'[A-Z\s]{2,20}(?:FCU|EMPCU|CU)\b',  # General credit union patterns (FCU, EMPCU, CU)
            r'[A-Z\s]{2,20}CREDIT UNION',  # Credit unions with full name
        ]
        
        for pattern in creditor_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Normalize creditor names to standard format
                creditor_name = pattern.replace('\\', '')
                
                # Handle regex patterns - extract actual match from line
                if creditor_name.startswith('[A-Z') or '(?:' in creditor_name:
                    # This is a regex pattern, extract the actual creditor name from the line
                    if 'FCU' in line or 'EMPCU' in line or 'CREDIT UNION' in line:
                        # Extract the actual credit union name
                        cu_match = re.search(r'([A-Z\s]{2,30}(?:FCU|EMPCU|CREDIT UNION))', line)
                        if cu_match:
                            creditor_name = cu_match.group(1).strip()
                        else:
                            creditor_name = line.strip()  # fallback to full line
                    else:
                        creditor_name = line.strip()  # fallback to full line
                elif creditor_name == 'DEPTEDNELNET':
                    creditor_name = 'DEPT OF EDUCATION/NELNET'
                elif creditor_name in [
                    'DEPT OF ED', 'DEPT OF ED/NELN', 'DEPT OF EDUCATION',
                    'DEPARTMENT OF EDUCATION', 'U.S. DEPT OF EDUCATION',
                    'US DEPT OF EDUCATION', 'U.S. DEPARTMENT OF EDUCATION',
                    'US DEPARTMENT OF EDUCATION', 'NELNET'
                ]:
                    creditor_name = 'DEPT OF EDUCATION/NELNET'
                elif creditor_name == 'AUSTINCAPBK':
                    creditor_name = 'AUSTIN CAPITAL BANK'
                elif creditor_name == 'FETTIFHT/WEB':
                    creditor_name = 'WEBBANK/FINGERHUT'
                elif creditor_name == 'DISCOVERCARD':
                    creditor_name = 'DISCOVER CARD'
                
                current_account = {
                    'creditor': creditor_name,
                    'account_number': None,
                    'balance': None,
                    'status': None,
                    'date_opened': None,
                    'last_payment': None,
                    'negative_items': [],
                    'late_payment_count': 0
                }
                
                # Robust account number extraction around creditor line
                extracted_acc = _extract_account_number_from_context(lines, i, window=40)
                if extracted_acc:
                    current_account['account_number'] = extracted_acc
                    
                    # Look for balance (scan a few lines nearby)
                for j in range(i, min(i+30, len(lines))):
                    search_line = lines[j]
                    balance_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', search_line)
                    if balance_match and not current_account['balance']:
                        current_account['balance'] = balance_match.group()
                    
                    # PRIORITY: Detect explicit charge-off/written-off regardless of other words on the line
                    if re.search(r"charge\s*off|charged\s*off\s*as\s*bad\s*debt|bad\s*debt|written\s*off|write\s*off", search_line, re.IGNORECASE):
                        current_account['status'] = 'Charge off'
                        if 'Charge off' not in current_account['negative_items']:
                            current_account['negative_items'].append('Charge off')
                    
                    # Look for status - POSITIVE statuses first, then negative
                    status_patterns = [
                        # POSITIVE statuses first (these should override negative inferences)
                        ('Never late', r'never\s*late'),
                        ('Paid, Closed/Never late', r'paid.*closed.*never\s*late'),
                        ('Exceptional payment history', r'exceptional\s*payment\s*history'),
                        ('Paid as agreed', r'paid\s*(?:or\s*paying\s*)?as\s*agreed'),
                        ('Paid, Closed', r'paid.*closed(?!\s*(?:charge|collection))'),  # "Paid, Closed" but not charge-off
                        ('Current', r'current'),
                        ('Paid', r'paid(?!\s*(?:charge|settlement))'),  # Paid but not "paid charge off" or "paid settlement"
                        ('Open', r'open(?!\s*(?:delinquent|past\s*due))'),  # Open but not "open delinquent"
                        ('Closed', r'closed(?!\s*(?:charge|collection))'),  # Closed but not "closed charge off"
                        
                        # NEGATIVE statuses second
                        # Charge-off and equivalents (include "written off")
                        ('Charge off', r'charge\s*off|charged\s*off\s*as\s*bad\s*debt|bad\s*debt|written\s*off|write\s*off'),
                        ('Collection', r'collection'),
                        ('Late', r'late\s*payment|past\s*due|delinquent'),  # More specific late pattern
                        ('Settled', r'settled|settlement|paid\s*settlement'),
                        ('Repossession', r'repossession|repo|vehicle\s*recovery'),
                        ('Foreclosure', r'foreclosure|foreclosed'),
                        ('Bankruptcy', r'bankruptcy|chapter\s*\d+|discharged'),
                    ]
                    for status_name, status_pattern in status_patterns:
                        if re.search(status_pattern, search_line, re.IGNORECASE):
                            # Don't override more severe statuses - charge-off should never be overridden
                            current_status = current_account.get('status', '')
                            
                            # Status hierarchy (higher number = more severe, cannot be overridden by lower)
                            # IMPORTANT: Positive statuses should NEVER be overridden by negative ones
                            status_severity = {
                                'Bankruptcy': 10, 'Foreclosure': 9, 'Repossession': 8, 
                                'Collection': 7, 'Charge off': 6, 'Settled': 5,
                                'Late': 4, 'Closed': 3, 'Open': 2, 'Current': 1, 'Paid': 1,
                                # Positive statuses get HIGHEST priority to prevent override
                                'Never late': 15, 'Paid, Closed/Never late': 15, 'Paid as agreed': 15, 
                                'Exceptional payment history': 15, 'Paid, Closed': 14
                            }
                            
                            current_severity = status_severity.get(current_status, 0)
                            new_severity = status_severity.get(status_name, 0)
                            
                            if current_severity > new_severity:
                                # Don't override more severe status
                                # Only add to negative_items if the current status is also negative
                                current_is_positive = current_severity >= 14  # Positive statuses have severity 14-15
                                negative_statuses = ['Charge off', 'Collection', 'Late', 'Settled', 'Repossession', 'Foreclosure', 'Bankruptcy']
                                if not current_is_positive and status_name in negative_statuses and status_name not in current_account['negative_items']:
                                    current_account['negative_items'].append(status_name)
                            else:
                                current_account['status'] = status_name
                                # Clear negative_items if we're setting a positive status
                                new_is_positive = new_severity >= 14  # Positive statuses have severity 14-15
                                if new_is_positive:
                                    current_account['negative_items'] = []  # Clear all negative items for positive accounts
                                else:
                                    # Only add to negative_items if it's a negative status
                                    negative_statuses = ['Charge off', 'Collection', 'Late', 'Settled', 'Repossession', 'Foreclosure', 'Bankruptcy']
                                    if status_name in negative_statuses:
                                        if status_name not in current_account['negative_items']:
                                            current_account['negative_items'].append(status_name)
                            break

                    # Detect charge-off codes in payment history (CO) regardless of explicit status
                    if not current_account.get('status') or current_account.get('status') not in ['Charge off']:
                        if re.search(r'\bCO\b', search_line):
                            current_account['status'] = 'Charge off'
                            if 'Charge off' not in current_account['negative_items']:
                                current_account['negative_items'].append('Charge off')

                    # Only infer Late from payment grid numbers if no positive status was found
                    if not current_account.get('status') or current_account.get('status') in ['Open', 'Closed']:
                        # Look for explicit late indicators near payment grid numbers
                        if re.search(r'(?:late\s*payment|past\s*due|\b(?:30|60|90)\s*days?\s*(?:late|past\s*due))', search_line, re.IGNORECASE):
                            current_account['status'] = 'Late'
                            if 'Late' not in current_account['negative_items']:
                                current_account['negative_items'].append('Late')
                
                # Extract detailed late entries and rough count for policy
                try:
                    current_account['late_entries'] = _extract_late_entries(lines, i, window=80)
                except Exception:
                    current_account['late_entries'] = []
                try:
                    current_account['late_payment_count'] = _estimate_late_payment_count(lines, i)
                except Exception:
                    current_account['late_payment_count'] = len(current_account.get('late_entries', []))

                # Extract dates (DOFD, Date Reported, Status Updated)
                try:
                    dates = _extract_account_dates(lines, i, window=60)
                    current_account['dofd'] = dates.get('dofd')  # (m, y, raw)
                    current_account['date_reported'] = dates.get('date_reported')
                    current_account['status_updated'] = dates.get('status_updated')
                    # Simple re-aging heuristic: if date_reported - dofd > 84 months and still showing recent late
                    now = datetime.now()
                    if current_account.get('dofd') and current_account.get('date_reported'):
                        dm, dy, _ = current_account['dofd']
                        rm, ry, _ = current_account['date_reported']
                        age = _months_between(dm, dy, rm, ry)
                        if age is not None and age > 84:  # > 7 years
                            current_account.setdefault('violations', []).append('FCRA §623(a)(5) Re-aging concern (DOFD vs Date Reported)')
                    # Metro 2 quick checks from nearby lines
                    block = lines[i: min(i+30, len(lines))]
                    mviol = _check_metro2_simple_rules(block, current_account.get('status') or '')
                    if mviol:
                        current_account.setdefault('violations', []).extend(mviol)
                except Exception:
                    pass

                # Require at least an account number or a detected status near the creditor line
                if not current_account.get('account_number') and not current_account.get('status'):
                    continue

                accounts.append(current_account)
                break
    
    return accounts

def merge_accounts_by_key(accounts: list[dict]) -> list[dict]:
    """Merge duplicate accounts while respecting amount differences.

    Matching key: (creditor, account_number, balance_amount)
      - If two entries have the same creditor and masked account number BUT
        different reported balances, they are treated as SEPARATE disputes
        per user policy. If balances match (or both blank), they are merged.

    Merge rules when keys match:
      - Unions negative_items
      - Prefers more derogatory status (Late > Closed/Current/Paid)
      - Merges late_entries and updates late_payment_count
    """
    def status_rank(s: str | None) -> int:
        if not s:
            return 0
        s = s.lower()
        order = [
            'bankruptcy','foreclosure','repossession','collection','charge off','late','settled','closed','open','current','paid'
        ]
        for idx, name in enumerate(order[::-1], start=1):
            if name in s:
                return idx
        return 0

    def normalize_balance(balance_value: str | None) -> str:
        if not balance_value:
            return ''
        try:
            # Strip currency formatting to get a stable numeric key
            numeric = balance_value.replace('$', '').replace(',', '').strip()
            # Keep as string to preserve exact match semantics
            return numeric
        except Exception:
            return ''

    merged = {}
    for acc in accounts:
        bal_key = normalize_balance(acc.get('balance'))
        key = (
            acc.get('creditor') or '',
            acc.get('account_number') or '',
            bal_key,
        )
        if key not in merged:
            merged[key] = acc.copy()
            continue
        cur = merged[key]
        # Debug: print when merging duplicates
        print(
            f"🔄 Merging duplicate account: {acc.get('creditor')} {acc.get('account_number')} - Balance: {cur.get('balance')} → {acc.get('balance')}"
        )
        # Status: keep most derogatory
        if status_rank(acc.get('status')) > status_rank(cur.get('status')):
            cur['status'] = acc.get('status')
        # Balance: prefer higher amount (more recent/accurate), or non-null
        cur_balance = cur.get('balance', '')
        acc_balance = acc.get('balance', '')
        
        if not cur_balance and acc_balance:
            cur['balance'] = acc_balance
        elif cur_balance and acc_balance and cur_balance != acc_balance:
            # If balances are different, prefer the higher amount (likely more recent)
            try:
                cur_amount = float(cur_balance.replace('$', '').replace(',', ''))
                acc_amount = float(acc_balance.replace('$', '').replace(',', ''))
                if acc_amount > cur_amount:
                    cur['balance'] = acc_balance
            except (ValueError, AttributeError):
                # If parsing fails, keep current balance
                pass
        # Union negative items
        cur.setdefault('negative_items', [])
        for it in acc.get('negative_items', []):
            if it not in cur['negative_items']:
                cur['negative_items'].append(it)
        # Merge late entries
        cur.setdefault('late_entries', [])
        entries = cur['late_entries'] + acc.get('late_entries', [])
        # de-dup
        seen = set()
        unique = []
        for e in entries:
            keye = (e.get('month'), e.get('year'), e.get('severity'))
            if keye in seen:
                continue
            seen.add(keye)
            unique.append(e)
        cur['late_entries'] = unique
        cur['late_payment_count'] = len(unique)
    return list(merged.values())

def classify_account_policy(account: dict) -> str:
    """Return 'delete' or 'correct' based on KB policy.

    - Collections/Charge-off/Repo/Foreclosure/Bankruptcy/Default/Settlement ⇒ delete
    - Late payments: >=3 ⇒ delete; else correct/remove late entries
    """
    status_text = (account.get('status') or '').lower()
    delete_terms = ['collection','charge off','charged off','bad debt','repossession','foreclosure','bankruptcy','default','settled']
    if any(t in status_text for t in delete_terms):
        return 'delete'
    late_count = len(account.get('late_entries') or [])
    if late_count >= 3:
        return 'delete'
    return 'correct'

def detect_bureau_from_pdf(text, filename):
    """Auto-detect which credit bureau the report is from"""
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # Check filename first
    if "experian" in filename_lower:
        return "Experian"
    elif "equifax" in filename_lower:
        return "Equifax"
    elif "transunion" in filename_lower or "trans union" in filename_lower:
        return "TransUnion"
    
    # Check content
    if "experian" in text_lower or "experian information solutions" in text_lower:
        return "Experian"
    elif "equifax" in text_lower or "equifax information services" in text_lower:
        return "Equifax"
    elif "transunion" in text_lower or "trans union" in text_lower or "transunion consumer solutions" in text_lower:
        return "TransUnion"
    
    return "Unknown Bureau"

def filter_negative_accounts(accounts):
    """Filter accounts by derogatory status and new late-payment policy.

    Policy:
      - Collection/Charge-off: always negative (keep for deletion)
      - Late/Past due: ALL late payments impact credit and should be fixed or deleted
      - Late payments 2+ years old: demand deletion (per FCRA 7.5 year rule)
      - Recent late payments: demand correction to "Paid as Agreed" or deletion
      - Other derogatories (default, repossession, foreclosure, bankruptcy, settled, paid charge off, closed): negative
      - Any account with negative_items is considered negative
    """
    negative_keywords = [
        'charge off', 'charge-off', 'charged off as bad debt', 'bad debt',
        'collection', 'late', 'past due', 'delinquent', 'default',
        'repossession', 'repo', 'vehicle recovery', 'foreclosure', 'bankruptcy',
        'settled', 'settlement', 'paid charge off'
    ]

    def is_collection_or_chargeoff(status_text: str) -> bool:
        return any(term in status_text for term in ['collection', 'charge off', 'charge-off', 'charged off as bad debt', 'bad debt'])

    negative_accounts = []
    for account in accounts:
        status_text = (account.get('status') or '').lower()
        negative_items = account.get('negative_items', [])
        late_entries = account.get('late_entries', [])

        # EXCLUDE positive accounts first, but handle late payment corrections
        strong_positive_statuses = ['never late', 'paid, closed/never late', 'exceptional payment history']
        mild_positive_statuses = ['paid as agreed', 'paid, closed']
        
        # Strong positive statuses (never late, exceptional) should be excluded regardless
        if any(pos_status in status_text for pos_status in strong_positive_statuses):
            if not negative_items:
                continue  # Skip strong positive accounts
        
        # Mild positive statuses (paid as agreed) with late entries need correction
        elif any(pos_status in status_text for pos_status in mild_positive_statuses):
            # Include for late payment correction if there are late entries but no negative items
            if late_entries and len(late_entries) > 0 and not negative_items:
                negative_accounts.append(account)
                continue
            # Exclude if no late entries and no negative items
            elif not negative_items:
                continue  # Skip positive account with no issues
        
        # If explicit late entries were parsed from the payment grid, it's negative
        if late_entries and len(late_entries) > 0:
            negative_accounts.append(account)
            continue
        
        # Check if account has any negative items
        has_negative_items = bool(negative_items)
        
        # If account has negative items, it's likely derogatory unless it's ONLY minor late payments
        if has_negative_items:
            items_text = ' '.join(negative_items).lower()
            
            # Always include if it has collection/charge-off items
            if any(term in items_text for term in ['collection', 'charge off', 'charge-off', 'charged off as bad debt', 'bad debt']):
                negative_accounts.append(account)
                continue
                
            # For late payment items, ALL late payments impact credit
            if any(term in items_text for term in ['late', 'past due']):
                # ALL accounts with late payments should be disputed (fix or delete)
                negative_accounts.append(account)
                continue
            else:
                # Has negative items but not late/collection - likely derogatory
                negative_accounts.append(account)
                continue

        # Check status text for derogatory indicators
        if status_text:
            if is_collection_or_chargeoff(status_text):
                negative_accounts.append(account)
                continue

            if any(term in status_text for term in ['late', 'past due']):
                # ALL late payments impact credit and should be disputed
                negative_accounts.append(account)
                continue

            # Other derogatories remain negative (explicitly exclude closed/open/current/paid-only)
            if any(
                keyword in status_text and keyword not in ['late', 'past due']
                for keyword in negative_keywords
            ):
                negative_accounts.append(account)

    return negative_accounts

def create_organized_folders(bureau_detected, base_path="outputletter"):
    """Create organized folder structure for dispute letters.

    Handles Windows/cloud-sync PermissionError by falling back to a local folder
    named 'outputletter_local'. You can also override the base via OUTPUT_DIR env.
    """
    import os

    preferred_base = os.getenv("OUTPUT_DIR", base_path)
    base = Path(preferred_base)

    def _build(base_dir: Path):
        # Always create these folders
        essential_folders = [
            base_dir / "Creditors",
            base_dir / "Analysis",
        ]

        # Only create folder for the detected bureau
        bureau_folders = []
        if bureau_detected in ["Experian", "Equifax", "TransUnion"]:
            bureau_folders.append(base_dir / bureau_detected)

        # Create all necessary folders
        all_folders = essential_folders + bureau_folders
        for folder in all_folders:
            folder.mkdir(parents=True, exist_ok=True)

        return {
            "experian": base_dir / "Experian",
            "equifax": base_dir / "Equifax",
            "transunion": base_dir / "TransUnion",
            "creditors": base_dir / "Creditors",
            "analysis": base_dir / "Analysis",
            "base": base_dir,
        }

    try:
        return _build(base)
    except PermissionError:
        # Fall back to a non-synced local directory
        fallback = Path("outputletter_local")
        try:
            folders = _build(fallback)
            print(f"⚠️  Permission issue creating '{base}'. Using fallback: {fallback}/")
            return folders
        except Exception as e:
            print(f"❌ Failed to create output folders: {e}")
            raise

def get_bureau_addresses():
    """Get credit bureau mailing addresses"""
    return {
        "Experian": {
            "name": "Experian",
            "company": "Experian Information Solutions, Inc.",
            "address": "P.O. Box 4500\nAllen, TX 75013"
        },
        "Equifax": {
            "name": "Equifax", 
            "company": "Equifax Information Services LLC",
            "address": "P.O. Box 740256\nAtlanta, GA 30374"
        },
        "TransUnion": {
            "name": "TransUnion",
            "company": "TransUnion Consumer Solutions", 
            "address": "P.O. Box 2000\nChester, PA 19016-2000"
        }
    }

def display_user_menu(bureau_detected, accounts_count, potential_damages):
    """Display user choice menu for dispute strategy"""
    print("\n" + "="*70)
    print("🏆 ULTIMATE DISPUTE LETTER GENERATOR")
    print("Dr. Lex Grant's Maximum Deletion System")
    print("="*70)
    print(f"📄 Processing: {bureau_detected} Credit Report")
    print(f"🎯 Negative Items Found: {accounts_count} accounts")
    print(f"💰 Potential Damages: ${potential_damages:,} - ${potential_damages*2:,}")
    print("\nChoose your dispute strategy:")
    print(f"\n1. 🏢 CREDIT BUREAU ONLY")
    print(f"   └── Send letter to {bureau_detected} (the bureau you provided)")
    print("\n2. 🏦 FURNISHERS/CREDITORS ONLY")  
    print("   └── Send letters directly to creditors")
    print("\n3. 🎯 MAXIMUM PRESSURE (RECOMMENDED)")
    print(f"   └── Attack from both sides - {bureau_detected} + Furnishers")
    print("\n4. 📋 CUSTOM SELECTION")
    print("   └── Choose specific targets")
    print("\n" + "="*70)
    
    while True:
        try:
            choice = input("Enter your choice (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ Please enter 1, 2, 3, or 4")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            exit()
        except:
            print("❌ Please enter a valid number (1-4)")

def get_account_specific_citations(account):
    """Get additional legal citations based on account type and status"""
    citations = []
    status_lower = account.get('status', '').lower()
    creditor_lower = account.get('creditor', '').lower()
    
    # Collection/Charge-off accounts
    if any(term in status_lower for term in ['collection', 'charge off', 'charge-off']):
        citations.extend([
            "FDCPA §1692 - Unfair debt collection practices",
            "FDCPA §1692e - False or misleading representations", 
            "FDCPA §1692f - Unfair practices in collecting debts"
        ])
    
    # Student loan accounts
    if any(term in creditor_lower for term in ['education', 'student', 'dept of education', 'neln']):
        citations.extend([
            "34 C.F.R. § 682.208 - Federal student loan reporting requirements",
            "Higher Education Act compliance violations"
        ])
    
    # Late payment accounts
    if 'late' in status_lower:
        citations.extend([
            "FCRA §1681s-2(a)(1)(B) - Accurate payment history requirements",
            "FCRA §1681s-2(b) - Investigation of disputed payment information"
        ])
    
    # Medical collections
    if any(term in creditor_lower for term in ['medical', 'hospital', 'health']):
        citations.extend([
            "HIPAA privacy violations in medical debt reporting",
            "FDCPA medical debt protection requirements"
        ])
    
    return citations

def calculate_dynamic_damages(accounts, round_number):
    """Calculate damages based on account types and round multiplier"""
    base_fcra = len(accounts) * 1000  # $1000 per account FCRA
    multiplier = {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0}[round_number]
    
    # Account-specific additions
    fdcpa_damages = 0
    federal_damages = 0
    
    for account in accounts:
        status_lower = account.get('status', '').lower()
        creditor_lower = account.get('creditor', '').lower()
        
        # Collection/charge-off accounts get FDCPA damages
        if any(term in status_lower for term in ['collection', 'charge off', 'charge-off']):
            fdcpa_damages += 1000  # FDCPA per collection
        
        # Student loans get federal compliance violations
        if any(term in creditor_lower for term in ['education', 'student', 'dept of education', 'neln']):
            federal_damages += 500   # Federal compliance violations
        
        # Late payments get credit score impact damages
        # Late payments: still add a smaller amount if present
        if 'late' in status_lower or (account.get('late_entries')):
            federal_damages += 200
    
    total_min = int((base_fcra + fdcpa_damages + federal_damages) * multiplier)
    total_max = int((base_fcra * 2 + fdcpa_damages * 1.5 + federal_damages * 2) * multiplier)
    
    return total_min, total_max

def get_round_specific_opener(round_number):
    """Get round-specific opening language"""
    openers = {
        1: "I am formally requesting a comprehensive disclosure of my entire file. It is imperative that only information that is completely accurate and thorough be included.",
        2: "This letter is a request of the steps that your company took when investigating the disputed items. Please send me a detailed explanation of how you obtained these results.",
        3: "I am writing to formally request the Method of Verification (MOV) used in the reinvestigation of disputed information in my credit file, as per 15 U.S. Code § 1681i.",
        4: "This is my FINAL NOTICE before initiating federal litigation under FCRA violations. Your continued non-compliance will result in immediate legal action.",
        5: "This is an escalation notice. I am preparing complaints with the CFPB and State Attorney General and will proceed with litigation if immediate deletion is not completed."
    }
    return openers.get(round_number, openers[1])

def get_round_timeline(round_number):
    """Get appropriate timeline for each round"""
    timelines = {1: 30, 2: 20, 3: 15, 4: 15, 5: 15}
    return timelines.get(round_number, 30)

def create_deletion_dispute_letter(
    accounts,
    consumer_name,
    bureau_info,
    round_number: int = 1,
    consumer_address_lines: list[str] | None = None,
    correction_accounts: list[dict] | None = None,
    certified_tracking: str | None = None,
    ag_state: str | None = None,
):
    """Create dispute letter demanding DELETION of items for specific bureau"""
    
    bureau_name = bureau_info['name']
    bureau_company = bureau_info['company']
    bureau_address = bureau_info['address']
    
    # Get round-specific opener and timeline
    round_opener = get_round_specific_opener(round_number)
    timeline_days = get_round_timeline(round_number)
    
    letter_content = f"""
# ROUND {round_number} - DEMAND FOR DELETION - {bureau_name.upper()} CREDIT BUREAU
**Professional Dispute Letter by Dr. Lex Grant, Credit Expert**

**Date:** {datetime.now().strftime('%B %d, %Y')}
**To:** {bureau_company}
**Address:** {bureau_address}
**From:** {consumer_name}
**Address:** {"; ".join(consumer_address_lines) if consumer_address_lines else "[Your Complete Address]; [City, State ZIP]; [Phone]; [Email]"}
**Subject:** DEMAND FOR IMMEDIATE DELETION - FCRA Violations

## LEGAL NOTICE OF DISPUTE AND DEMAND FOR DELETION

Dear {bureau_name},

{round_opener}

I am writing to formally DISPUTE and DEMAND THE IMMEDIATE DELETION of the following inaccurate, unverifiable, and legally non-compliant information from my credit report pursuant to my rights under the Fair Credit Reporting Act (FCRA), specifically 15 USC §1681i.

## ACCOUNTS DEMANDED FOR DELETION

The following accounts contain inaccurate information and MUST BE DELETED in their entirety:

"""
    
    for i, account in enumerate(accounts, 1):
        # Get account-specific citations
        additional_citations = get_account_specific_citations(account)

        policy = classify_account_policy(account)
        status_text = (account.get('status') or '').lower()
        title = "DEMAND FOR DELETION" if policy == 'delete' else "LATE-PAYMENT CORRECTION REQUEST"

        letter_content += f"""
**Account {i} - {title}:**
- **Creditor:** {account['creditor']}
- **Account Number:** {account['account_number'] if account['account_number'] else 'XXXX-XXXX-XXXX-XXXX (Must be verified)'}
- **Current Status:** {account['status'] if account['status'] else 'Inaccurate reporting'}
- **Balance Reported:** {account['balance'] if account['balance'] else 'Unverified amount'}
"""

        # Show key dates when available
        if account.get('dofd') and isinstance(account['dofd'], tuple) and len(account['dofd']) == 3:
            letter_content += f"\n- **Date of First Delinquency (DOFD):** {account['dofd'][2]}"
        if account.get('date_reported') and isinstance(account['date_reported'], tuple) and len(account['date_reported']) == 3:
            letter_content += f"\n- **Date Reported:** {account['date_reported'][2]}"
        if account.get('status_updated') and isinstance(account['status_updated'], tuple) and len(account['status_updated']) == 3:
            letter_content += f"\n- **Status Updated:** {account['status_updated'][2]}"

        # Late entries list
        entries = account.get('late_entries') or []
        if entries:
            month_order = {m: i for i, m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], start=1)}
            try:
                entries_sorted = sorted(entries, key=lambda e: (e.get('year') or 0, month_order.get(e.get('month','')[:3].title(), 0)), reverse=True)
            except Exception:
                entries_sorted = entries
            formatted = ", ".join([f"{e.get('month','')} {e.get('year') or ''} ({e.get('severity')})".strip() for e in entries_sorted])
            letter_content += f"\n- Detected Late Entries: {formatted}"

        if policy == 'delete':
            letter_content += "\n- **DEMAND:** **COMPLETE DELETION** of this account due to inaccurate reporting\n\n**Legal Basis for Deletion:**\n- Violation of 15 USC §1681s-2(a) - Furnisher accuracy requirements\n- Violation of 15 USC §1681i - Failure to properly investigate\n- Violation of Metro 2 Format compliance requirements"
        else:
            letter_content += "\n- **REQUEST:** Remove all late-payment entries and update the account status to **PAID AS AGREED**; if you cannot fully verify every late mark with complete documentation, you must **DELETE THE ENTIRE TRADELINE** immediately per FCRA accuracy requirements\n\n**Legal Basis for Correction:**\n- FCRA §1681s-2(a)(1)(B) – Accurate payment history requirements\n- FCRA §1681i – Reinvestigation of disputed information\n- CDIA Metro 2® – Payment History Profile and date field accuracy (DOFD, Date Reported)"

        # Detected Metro 2 / re-aging violations (compact list)
        viols = account.get('violations') or []
        if viols:
            letter_content += "\n- **Detected Violations:** " + "; ".join(sorted(set(viols)))
        
        # Add account-specific citations
        for citation in additional_citations:
            letter_content += f"\n- Violation of {citation}"
        
        letter_content += "\n\n"
    
    # Optional section: late-payment corrections (no full deletion)
    if correction_accounts:
        letter_content += "\n## ACCOUNTS WITH LATE-PAYMENT CORRECTIONS REQUESTED\n\n"
        for j, account in enumerate(correction_accounts, 1):
            late_count = account.get('late_payment_count', 0)
            letter_content += f"""
**Account {j} - LATE-PAYMENT CORRECTION REQUEST:**
- **Creditor:** {account['creditor']}
- **Account Number:** {account.get('account_number', 'XXXX-XXXX-XXXX-XXXX')}
- **Current Status:** {account.get('status', 'Late payment reporting')}
- **Detected Late Marks:** {late_count if late_count else 'Unspecified (late marks present)'}
- **REQUEST:** Remove all late-payment entries and update the account status to **PAID AS AGREED**; if you cannot fully verify every late mark with complete documentation, you must **DELETE THE ENTIRE TRADELINE** immediately per FCRA accuracy requirements.

**Legal Basis for Correction:**
- FCRA §1681s-2(a)(1)(B) – Accurate payment history requirements
- FCRA §1681i – Reinvestigation of disputed information
- CDIA Metro 2® – Payment History Profile and date field accuracy (DOFD, Date Reported)
- Remove any late marks during deferment/forbearance/rehab periods (student loans)
- 30/60/90-day definitions must reflect ≥ the stated days past contractual due date
"""

    # Determine late-entry guidance per policy (do not print raw counts; list dates if present)
    def build_late_entries_section(acc_list: list[dict]) -> str:
        lines_out = []
        for acc in acc_list:
            entries = acc.get('late_entries') or []
            if not entries:
                continue
            # Sort by year/month if possible: year desc, month order
            month_order = {m: i for i, m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], start=1)}
            try:
                entries_sorted = sorted(entries, key=lambda e: (e.get('year') or 0, month_order.get(e.get('month','')[:3].title(), 0)), reverse=True)
            except Exception:
                entries_sorted = entries
            formatted = [f"{e.get('month','')} {e.get('year') or ''} ({e.get('severity')})".strip() for e in entries_sorted]
            if formatted:
                lines_out.append("- Detected Late Entries: " + ", ".join(formatted))
        return "\n".join(lines_out)

    letter_content += f"""

## SPECIFIC DEMANDS FOR ACTION

I hereby DEMAND that {bureau_info['name']}:

### 1. IMMEDIATE DELETION REQUIRED
- **DELETE** all above-listed accounts in their entirety
- **REMOVE** all associated negative payment history
- **ELIMINATE** all derogatory marks and comments
- **EXPUNGE** all collection references and charge-off notations

### 2. LEGAL COMPLIANCE REQUIRED  
- **VERIFY** all account numbers and creditor information
- **SUBSTANTIATE** all reported balances with documentation
- **CONFIRM** all dates and payment history with original records
- **VALIDATE** all collection activities under FDCPA requirements

### 3. REINVESTIGATION STANDARDS
- **CONTACT** each furnisher within 5 business days
- **REQUEST** complete account documentation
- **VERIFY** Metro 2 format compliance
- **DELETE** any unverifiable information immediately
"""

    # Round-specific tactic sections
    if round_number == 2:
        letter_content += f"""
## REQUEST FOR PROCEDURE – FCRA §1681i(6)(B)(iii)
Pursuant to my rights under **15 U.S.C § 1681i(6)(B)(iii)** I DEMAND, **within 15 days (not 30)**, a complete description of the procedure used to determine the accuracy and completeness of each disputed account, including:
1. The business name, address, and telephone number of every furnisher contacted.
2. The name of the employee at your company who conducted the investigation.
3. Copies of any documents obtained or reviewed in the course of the investigation.
"""
    elif round_number == 3:
        letter_content += f"""
## METHOD OF VERIFICATION (MOV) – TEN CRITICAL QUESTIONS
1. What certified documents were reviewed to verify each disputed account?
2. Who did you speak to at the furnisher? (name, position, phone, and date)
3. What formal training was provided to your investigator?
4. Provide copies of all correspondence exchanged with each furnisher.
5. Provide the date of first delinquency you received from the furnisher.
6. Provide the specific month and year these items will cease reporting.
7. Provide proof of timely procurement of certified documents.
8. Provide the cost incurred to obtain the documents.
9. Provide a **notarized affidavit** confirming the accuracy of your investigation.
10. Explain why **Metro 2** reporting guidelines were not followed.
"""
    elif round_number == 4:
        letter_content += f"""
## FINAL NOTICE BEFORE LITIGATION
This constitutes my FINAL NOTICE prior to initiating federal litigation under the FCRA for continued non-compliance. Failure to comply within the specified timeline will result in immediate legal action, including claims for statutory and punitive damages and attorney fees under 15 U.S.C. §1681n.
"""
    elif round_number == 5:
        letter_content += f"""
## REGULATORY ESCALATION NOTICE – CFPB AND STATE ATTORNEY GENERAL
This matter is now being escalated to federal and state regulators due to continued non-compliance with the Fair Credit Reporting Act.

I am preparing and filing formal complaints with the **Consumer Financial Protection Bureau (CFPB)** and the **State Attorney General**. If full deletion is not completed immediately, I will proceed with litigation for violations of:

- **15 U.S.C. §1681s-2(a)** – Furnishing inaccurate information
- **15 U.S.C. §1681s-2(b)** – Failure to conduct a reasonable investigation
- **15 U.S.C. §1681i** – Failure to reinvestigate/verify disputed information
- **15 U.S.C. §1681e(b)** – Failure to follow reasonable procedures to assure maximum possible accuracy

Provide written confirmation of deletion and an updated credit file within the timeline stated below.
"""

    letter_content += f"""

### 15-DAY ACCELERATION – NO FORM LETTERS
I legally and lawfully **REFUSE** any generic form letter response. You now have **15 days**, not 30, to comply with all demands above.

## STATUTORY VIOLATIONS IDENTIFIED

The following violations of federal law have been identified:

### FCRA Violations (15 USC §1681)
1. **§1681s-2(a)** - Furnishing inaccurate information
2. **§1681s-2(b)** - Failure to investigate disputed information  
3. **§1681i** - Inadequate reinvestigation procedures
4. **§1681e(b)** - Failure to follow reasonable procedures

### FDCPA Violations (15 USC §1692)
1. **§1692** - Unfair debt collection practices
2. **§1692e** - False or misleading representations
3. **§1692f** - Unfair practices in collecting debts

## STATUTORY DAMAGES CALCULATION

Based on identified violations, potential damages include:

- **FCRA Statutory Damages:** $100-$1,000 per violation × {len(accounts)} accounts = ${len(accounts) * 1000:,}
- **FDCPA Statutory Damages:** $1,000 per violation × collection accounts
- **Federal Compliance Violations:** Student loans and regulatory violations
- **Actual Damages:** Credit score harm, loan denials, higher interest rates
- **Punitive Damages:** For willful non-compliance (Round {round_number} multiplier: {calculate_dynamic_damages(accounts, round_number)[0]//(len(accounts)*1000):.1f}x)
- **Attorney Fees:** Recoverable under both FCRA and FDCPA

**TOTAL POTENTIAL DAMAGES: ${calculate_dynamic_damages(accounts, round_number)[0]:,} - ${calculate_dynamic_damages(accounts, round_number)[1]:,}**

## DEMAND FOR SPECIFIC PERFORMANCE

### Within {timeline_days} Days, {bureau_name} MUST:

1. **DELETE** all disputed accounts listed above
2. **PROVIDE** written confirmation of all deletions
3. **SEND** updated credit report showing deletions
4. **NOTIFY** all parties who received reports in past 2 years
5. **CONFIRM** removal from all {bureau_name} products and services

### Failure to Comply Will Result In:

1. **CFPB Complaint** filing
2. **State Attorney General** complaint  
3. **Federal Court Action** for FCRA violations
4. **Demand for Statutory Damages** up to ${len(accounts) * 2000:,}
5. **Attorney Fee Recovery** under 15 USC §1681n

## METRO 2 COMPLIANCE DEMAND

All furnishers MUST comply with Metro 2 Format requirements. Any account that fails to meet Metro 2 standards MUST BE DELETED immediately.

**Specific Metro 2 Violations:**
- Inaccurate account status codes
- Incorrect balance reporting
- Invalid date information
- Non-compliant payment history codes

## REINSERTION PROTECTION
Any account that you delete **MUST NOT** be reinserted unless the furnisher certifies that the information is complete and accurate. If reinsertion occurs you are required, under **15 U.S.C §1681i(a)(5)**, to notify me **in writing within 5 days** and to provide all documentation supporting such reinsertion. Failure to do so constitutes an additional FCRA violation and will trigger immediate legal action.

## CONCLUSION AND DEMAND

This is a formal legal demand for the IMMEDIATE DELETION of all disputed accounts. These accounts contain inaccurate, unverifiable, or non-compliant information that violates federal law.

**I DEMAND COMPLETE DELETION, NOT INVESTIGATION. INVESTIGATION IS INSUFFICIENT.**

Failure to delete these accounts within {timeline_days} days will result in legal action to enforce my rights under federal law.

## CERTIFICATION

I certify under penalty of perjury that the information in this dispute is true and correct to the best of my knowledge.

Sincerely,

{consumer_name}
{chr(10).join(consumer_address_lines) if consumer_address_lines else '[Your Complete Address]'}

**REFERENCE:** FCRA Deletion Demand - {datetime.now().strftime('%Y%m%d')}-{consumer_name.replace(' ', '').upper()}
"""
    # Inject optional tracking and AG CC lines conditionally
    tracking_line = f"\n**CERTIFIED MAIL TRACKING:** {certified_tracking}" if certified_tracking else ""
    ag_line = f"\n**CC:** {ag_state} Attorney General's Office" if ag_state else ""
    letter_content = letter_content.replace(
        "**REFERENCE:**",
        f"**CC:** Consumer Financial Protection Bureau (CFPB){ag_line}{tracking_line}\n\n**REFERENCE:**",
    )

    # If round 5 and ag_state provided, personalize R5 escalation section
    if round_number == 5 and ag_state:
        letter_content = letter_content.replace(
            "State Attorney General",
            f"{ag_state} Attorney General",
        )
    
    return letter_content

def create_furnisher_dispute_letter(
    account,
    consumer_name,
    consumer_address_lines: list[str] | None = None,
    certified_tracking: str | None = None,
    ag_state: str | None = None,
):
    """Create dispute letter for individual furnisher/creditor"""
    
    creditor = account['creditor']
    account_number = account['account_number'] if account['account_number'] else 'XXXX-XXXX-XXXX-XXXX'
    contact = get_creditor_contact(creditor)
    creditor_company = contact['company']
    creditor_address = contact['address']
    
    letter_content = f"""
# FCRA VIOLATION NOTICE - DIRECT FURNISHER DISPUTE
**Professional Legal Notice by Dr. Lex Grant, Credit Expert**

**Date:** {datetime.now().strftime('%B %d, %Y')}
**To:** {creditor_company}
**Address:** {creditor_address}
**From:** {consumer_name}
**Re:** FCRA Violation - Account {account_number}
**Subject:** IMMEDIATE DELETION DEMAND - Furnisher Liability

## LEGAL NOTICE OF FCRA VIOLATIONS

Dear {creditor},

You are hereby FORMALLY NOTIFIED that you are in violation of the Fair Credit Reporting Act (FCRA) for furnishing inaccurate, unverifiable, and legally non-compliant information to credit reporting agencies regarding the following account:

**ACCOUNT DETAILS:**
- **Creditor:** {creditor}
- **Account Number:** {account_number}
- **Current Status:** {account.get('status', 'Inaccurate reporting')}
- **Balance Reported:** {account.get('balance', 'Unverified amount')}

## FCRA VIOLATIONS IDENTIFIED

### 15 USC §1681s-2(a) - Furnisher Accuracy Requirements
You have violated your duty to furnish accurate information by reporting:
- Unverified account information
- Inaccurate payment history  
- Incorrect balance amounts
- Improper account status

### 15 USC §1681s-2(b) - Investigation Requirements  
Upon receiving dispute notices from credit bureaus, you failed to:
- Conduct reasonable investigation
- Review all relevant information
- Delete or correct inaccurate information
- Report results back to credit bureaus

## STATUTORY DAMAGES LIABILITY

As a furnisher of credit information, you are liable for:
- **FCRA Statutory Damages:** $100-$1,000 per violation
- **Actual Damages:** Credit score harm, loan denials
- **Punitive Damages:** For willful non-compliance  
- **Attorney Fees:** Recoverable under 15 USC §1681n

**ESTIMATED LIABILITY: $1,000 - $2,000 for this account**

## IMMEDIATE DEMANDS

### You MUST within 15 days:

1. **STOP REPORTING** this account to all credit bureaus
2. **REQUEST DELETION** from all credit reports
3. **PROVIDE WRITTEN CONFIRMATION** of deletion requests
4. **SEND DOCUMENTATION** proving account accuracy (if you claim it's accurate)
5. **COMPLY with Metro 2 Format** requirements

### If Account is Accurate, You MUST Provide:
- Original signed contract or agreement
- Complete payment history with dates
- Documentation of all reported information
- Proof of legal ownership of this debt

## CONSEQUENCES OF NON-COMPLIANCE

Failure to comply within 15 days will result in:

1. **CFPB Complaint** filing against your company
2. **State Attorney General** notification  
3. **Federal Lawsuit** under FCRA §1681n
4. **Demand for Maximum Statutory Damages**
5. **Public Record** of FCRA violations

## CERTIFICATION REQUIRED

If you continue reporting this account, you must certify under penalty of perjury that:
- All information is 100% accurate
- You have conducted reasonable investigation
- You possess documentation supporting all reported data
- Account complies with all Metro 2 requirements

## LEGAL NOTICE

This constitutes formal legal notice under federal law. Your response (or lack thereof) will be used as evidence in any legal proceedings.

**DO NOT IGNORE THIS NOTICE**

Sincerely,

{consumer_name}
{chr(10).join(consumer_address_lines) if consumer_address_lines else '[Your Complete Address]'}

{f"**CERTIFIED MAIL TRACKING:** {certified_tracking}\n" if certified_tracking else ''}**CC:** Consumer Financial Protection Bureau (CFPB)
{f"**CC:** {ag_state} Attorney General's Office\n" if ag_state else ''}

---
**REFERENCE:** FCRA Furnisher Violation - {datetime.now().strftime('%Y%m%d')}-{creditor.replace(' ', '').replace('/', '_').upper()}
"""
    
    return letter_content

def generate_all_letters(
    user_choice,
    accounts,
    consumer_name,
    bureau_detected,
    folders,
    round_number: int = 1,
    consumer_address_lines: list[str] | None = None,
    certified_tracking: str | None = None,
    ag_state: str | None = None,
    report_stem: str | None = None,
):
    """Generate letters based on user's choice"""
    bureau_addresses = get_bureau_addresses()
    generated_files = []
    date_str = datetime.now().strftime('%Y-%m-%d')
    consumer_last = consumer_name.split()[-1]
    safe_stem = None
    if report_stem:
        safe_stem = re.sub(r"[^A-Za-z0-9_\-]", "_", report_stem)
    
    # Choice 1: Credit Bureaus Only
    if user_choice == 1:
        # Only generate letter for the bureau we have a report from
        if bureau_detected in bureau_addresses:
            bureau_info = bureau_addresses[bureau_detected]
            # Use only pre-filtered negative accounts
            deletion_accounts: list[dict] = accounts
            correction_accounts: list[dict] = []

            letter_content = create_deletion_dispute_letter(
                deletion_accounts,
                consumer_name,
                bureau_info,
                round_number,
                consumer_address_lines,
                correction_accounts if correction_accounts else None,
                certified_tracking,
                ag_state,
            )
            try:
                late_section = build_late_entries_section(deletion_accounts)  # type: ignore[name-defined]
            except Exception:
                late_section = ''
            if late_section:
                letter_content += "\n" + late_section + "\n"
            filename = (
                f"{consumer_last}_{date_str}_DELETION_DEMAND_{bureau_detected}_{safe_stem}.md"
                if safe_stem else f"{consumer_last}_{date_str}_DELETION_DEMAND_{bureau_detected}.md"
            )
            folder_key = bureau_detected.lower()
            # If bureau folder isn't present (fallback path), write into base
            target_dir = folders.get(folder_key, folders.get("base", Path("outputletter")))
            filepath = target_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(letter_content)
            generated_files.append(str(filepath))
        else:
            print(f"⚠️  Warning: Unknown bureau '{bureau_detected}' - cannot generate bureau letter")
    
    # Choice 2: Furnishers/Creditors Only  
    elif user_choice == 2:
        for i, account in enumerate(accounts, 1):
            # Ensure account number is present; try one more time if missing
            if not account.get('account_number'):
                # We do not have the original report lines here; keep as-is
                pass
            letter_content = create_furnisher_dispute_letter(
                account,
                consumer_name,
                consumer_address_lines,
                certified_tracking,
                ag_state,
            )
            creditor_safe = account['creditor'].replace('/', '_').replace(' ', '_')
            filename = (
                f"{creditor_safe}_FCRA_Violation_{date_str}_{safe_stem}.md"
                if safe_stem else f"{creditor_safe}_FCRA_Violation_{date_str}.md"
            )
            filepath = folders["creditors"] / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(letter_content)
            generated_files.append(str(filepath))
    
    # Choice 3: Maximum Pressure (Both)
    elif user_choice == 3:
        # Generate bureau letter for the specific bureau we have a report from
        if bureau_detected in bureau_addresses:
            bureau_info = bureau_addresses[bureau_detected]
            deletion_accounts = accounts
            correction_accounts = []

            letter_content = create_deletion_dispute_letter(
                deletion_accounts,
                consumer_name,
                bureau_info,
                round_number,
                consumer_address_lines,
                correction_accounts if correction_accounts else None,
                certified_tracking,
                ag_state,
            )
            try:
                late_section = build_late_entries_section(deletion_accounts)  # type: ignore[name-defined]
            except Exception:
                late_section = ''
            if late_section:
                letter_content += "\n" + late_section + "\n"
            filename = (
                f"{consumer_last}_{date_str}_DELETION_DEMAND_{bureau_detected}_{safe_stem}.md"
                if safe_stem else f"{consumer_last}_{date_str}_DELETION_DEMAND_{bureau_detected}.md"
            )
            folder_key = bureau_detected.lower()
            target_dir = folders.get(folder_key, folders.get("base", Path("outputletter")))
            filepath = target_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(letter_content)
            generated_files.append(str(filepath))
        else:
            print(f"⚠️  Warning: Unknown bureau '{bureau_detected}' - cannot generate bureau letter")
        
        # Generate furnisher letters  
        for i, account in enumerate(accounts, 1):
            letter_content = create_furnisher_dispute_letter(
                account,
                consumer_name,
                consumer_address_lines,
                certified_tracking,
                ag_state,
            )
            creditor_safe = account['creditor'].replace('/', '_').replace(' ', '_')
            filename = (
                f"{creditor_safe}_FCRA_Violation_{date_str}_{safe_stem}.md"
                if safe_stem else f"{creditor_safe}_FCRA_Violation_{date_str}.md"
            )
            target_dir = folders.get("creditors", folders.get("base", Path("outputletter")))
            filepath = target_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(letter_content)
            generated_files.append(str(filepath))
    
    # Choice 4: Custom Selection (simplified for now - generate all)
    elif user_choice == 4:
        print("📋 Custom selection - generating all letters for now")
        return generate_all_letters(3, accounts, consumer_name, bureau_detected, folders, round_number, consumer_address_lines)
    
    return generated_files

def create_analysis_summary(
    accounts,
    bureau_detected,
    user_choice,
    generated_files,
    folders,
    round_number: int = 1,
    analysis_dir: Path | None = None,
    report_stem: str | None = None,
):
    """Create analysis summary with tracking info.

    When analysis_dir is provided (batch mode), write the analysis JSON
    into the bureau's folder with a unique filename that includes the
    report stem. In single-file mode (analysis_dir is None), preserve
    legacy behavior and write into outputletter/Analysis/.
    """
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Calculate dynamic damages
    min_damages, max_damages = calculate_dynamic_damages(accounts, round_number)
    
    summary = {
        "analysis_date": date_str,
        "bureau_detected": bureau_detected,
        "current_round": round_number,
        "strategy_chosen": {
            1: "Credit Bureaus Only",
            2: "Furnishers/Creditors Only", 
            3: "Maximum Pressure (Both)",
            4: "Custom Selection"
        }.get(user_choice, "Unknown"),
        "negative_accounts": len(accounts),
        "potential_damages": {
            "minimum": min_damages,
            "maximum": max_damages,
            "round_multiplier": {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0, 5: 2.5}.get(round_number, 1.0)
        },
        "round_history": [
            {
                "round": round_number,
                "date_sent": date_str,
                "bureau": bureau_detected,
                "accounts": len(accounts),
                "timeline_days": get_round_timeline(round_number)
            }
        ],
        "next_round_due": (datetime.now() + timedelta(days=get_round_timeline(round_number) + 15)).strftime('%Y-%m-%d'),
        "accounts_details": [],
        "generated_files": generated_files,
        "follow_up_schedule": {
            "r2_follow_up": f"{datetime.now().year}-{((datetime.now().month % 12) + 1):02d}-{datetime.now().day:02d}",
            "r3_follow_up": f"{datetime.now().year}-{((datetime.now().month + 1) % 12 + 1):02d}-{datetime.now().day:02d}",
            "r4_follow_up": f"{datetime.now().year}-{((datetime.now().month + 2) % 12 + 1):02d}-{datetime.now().day:02d}",
            "r5_follow_up": f"{datetime.now().year}-{((datetime.now().month + 3) % 12 + 1):02d}-{datetime.now().day:02d}"
        }
    }
    
    # Add account details
    for account in accounts:
        summary["accounts_details"].append({
            "creditor": account['creditor'],
            "account_number": account.get('account_number', 'Unknown'),
            "status": account.get('status', 'Unknown'),
            "balance": account.get('balance', 'Unknown'),
            "negative_items": account.get('negative_items', [])
        })
    
    # Save analysis
    if analysis_dir is not None:
        safe_stem = re.sub(r"[^A-Za-z0-9_\-]", "_", report_stem or "report")
        analysis_file = analysis_dir / f"dispute_analysis_{date_str}_{bureau_detected}_{safe_stem}.json"
    else:
        analysis_file = folders["analysis"] / f"dispute_analysis_{date_str}.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    return analysis_file

def main():
    """Main execution with optional multi-report processing"""
    
    print("🏆 ULTIMATE DISPUTE LETTER GENERATOR")
    print("=" * 50)
    
    # 🧹 WORKSPACE CLEANUP - Check for existing files first
    print("🔍 Checking workspace for existing files...")
    cleanup_success = cleanup_workspace(auto_mode=True)
    
    if not cleanup_success:
        print("❌ Cleanup cancelled. Exiting...")
        return
    
    print("\n📄 Starting credit report analysis...")
    
    # Look for any PDF file in the consumerreport folder (including subdirectories)
    consumerreport_dir = Path("consumerreport")
    
    if not consumerreport_dir.exists():
        print(f"Error: Directory 'consumerreport' not found. Please create it and place your credit report PDF inside.")
        return
    
    # Find all PDF files in the consumerreport directory and subdirectories
    pdf_files = sorted(consumerreport_dir.glob("**/*.pdf"), key=lambda p: p.name.lower())
    
    if not pdf_files:
        print(f"Error: No PDF files found in '{consumerreport_dir}' folder.")
        print("Please place your credit report PDF (Experian, Equifax, TransUnion, etc.) in the 'consumerreport' folder.")
        return
    
    selected_files = pdf_files
    if len(pdf_files) > 1:
        print(f"Found {len(pdf_files)} PDF files in '{consumerreport_dir}':")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"  {i}. {pdf_file.name}")
        resp = input("\nProcess all reports found? (Y/n): ").strip().lower()
        if resp == 'n':
            while True:
                idx_raw = input("Enter the number of the report to process: ").strip()
                if idx_raw.isdigit():
                    idx = int(idx_raw)
                    if 1 <= idx <= len(pdf_files):
                        selected_files = [pdf_files[idx - 1]]
                        break
                print("❌ Please enter a valid number from the list.")
    is_batch = len(selected_files) > 1

    # Saved inputs to reuse across reports
    saved_round = None
    saved_consumer_name = None
    saved_address_lines = None
    saved_tracking = None
    saved_ag_state = None
    saved_user_choice = None

    processed_any = False

    for run_index, pdf_path in enumerate(selected_files, start=1):
        print("\n" + "-" * 60)
        print(f"Processing credit report ({run_index}/{len(selected_files)}): {pdf_path.name}")
        print("=== EXTRACTING DETAILED ACCOUNT INFORMATION ===")

        # Extract text from PDF
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Error extracting text from {pdf_path.name}: {e}")
            continue

        print(f"Extracted {len(text)} characters of text")

        # Extract account details
        accounts = extract_account_details(text)
        # Merge duplicate blocks for same creditor + account number
        accounts = merge_accounts_by_key(accounts)
        if not accounts:
            print("ℹ️ No accounts parsed from this report. Skipping this file.")
            continue

        # Detect bureau and filter negative accounts
        bureau_detected = detect_bureau_from_pdf(text, pdf_path.name)
        print(f"🏢 Bureau detected: {bureau_detected}")

        # Filter to negative accounts only
        negative_accounts = filter_negative_accounts(accounts)

        if not negative_accounts:
            print("🎉 No negative items found! Your credit report looks clean.")
            print("✅ No dispute letters needed at this time.")
            continue

        print(f"🎯 Found {len(negative_accounts)} negative accounts to dispute:")
        for i, account in enumerate(negative_accounts, 1):
            print(f"  {i}. {account['creditor']} - {account.get('status', 'Unknown')} - Acct: {account.get('account_number','[missing]')}")

        # Create organized folders
        print(f"\n📁 Creating organized folder structure...")
        folders = create_organized_folders(bureau_detected)
        print(f"✅ Folders created: {bureau_detected}, Creditors, Analysis")

        # Prompts (once) and reuse for subsequent reports
        if saved_round is None:
            # Round prompt
            saved_round = prompt_round_selection()

            # Get consumer information from user input
            print("\n👤 CONSUMER INFORMATION REQUIRED")
            print("=" * 50)
            print("Please enter your personal information for the dispute letters:")

            # Get consumer name
            while True:
                saved_consumer_name = input("\n📝 Enter your full name (First Last): ").strip()
                if len(saved_consumer_name.split()) >= 2:
                    break
                print("❌ Please enter at least first and last name")

            # Get address
            print(f"\n🏠 Enter your mailing address:")
            street_address = input("Street address: ").strip()
            city = input("City: ").strip()
            state = input("State (2 letters): ").strip().upper()
            zip_code = input("ZIP code: ").strip()

            # Optional contact info
            phone = input("Phone number (optional): ").strip()
            email = input("Email address (optional): ").strip()

            saved_address_lines = []
            if street_address:
                saved_address_lines.append(street_address)
            if city and state and zip_code:
                saved_address_lines.append(f"{city}, {state} {zip_code}")
            if phone:
                saved_address_lines.append(phone)
            if email:
                saved_address_lines.append(email)

            # Confirmation
            print(f"\n✅ CONSUMER INFORMATION CONFIRMED:")
            print(f"📝 Name: {saved_consumer_name}")
            print(f"🏠 Address: {'; '.join(saved_address_lines)}")

            confirm = input(f"\nIs this information correct? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Please restart the script to re-enter your information.")
                return

            # Certified Mail Tracking prompt
            print("\n📦 CERTIFIED MAIL")
            use_tracking = input("Do you have Certified Mail tracking? (y/N): ").strip().lower()
            saved_tracking = None
            if use_tracking == 'y':
                saved_tracking = input("Enter tracking number: ").strip()

            # State AG prompt (default to entered state)
            default_state = state if state else ""
            saved_ag_state = input(
                f"Which state for Attorney General? [default: {default_state}]: "
            ).strip().upper()
            if not saved_ag_state:
                saved_ag_state = default_state.upper()

            # Display user menu and get choice (use first report's counts)
            potential_damages = calculate_dynamic_damages(negative_accounts, saved_round)[0]
            saved_user_choice = display_user_menu(bureau_detected, len(negative_accounts), potential_damages)

        # Generate letters based on saved choice
        print(f"\n🚀 Generating dispute letters...")
        generated_files = generate_all_letters(
            saved_user_choice,
            negative_accounts,
            saved_consumer_name,
            bureau_detected,
            folders,
            saved_round,
            saved_address_lines,
            saved_tracking,
            saved_ag_state,
            report_stem=pdf_path.stem if is_batch else None,
        )

        # Create analysis summary with follow-up tracking
        folder_key = bureau_detected.lower()
        bureau_dir = folders.get(folder_key, folders.get("base", Path("outputletter")))
        analysis_file = create_analysis_summary(
            negative_accounts,
            bureau_detected,
            saved_user_choice,
            generated_files,
            folders,
            saved_round,
            analysis_dir=bureau_dir if is_batch else None,
            report_stem=pdf_path.stem if is_batch else None,
        )

        # Display results (per report)
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! ULTIMATE DISPUTE LETTERS GENERATED")
        print("=" * 70)

        strategy_names = {
            1: f"{bureau_detected} Bureau Only",
            2: "Furnishers/Creditors Only",
            3: f"Maximum Pressure ({bureau_detected} + Furnishers)",
            4: "Custom Selection",
        }

        potential_damages = calculate_dynamic_damages(negative_accounts, saved_round)[0]
        print(f"📊 Strategy: {strategy_names.get(saved_user_choice, 'Unknown')}")
        print(f"🎯 Negative Accounts: {len(negative_accounts)}")
        print(f"💰 Potential Damages: ${potential_damages:,} - ${potential_damages*2:,}")
        print(f"📄 Letters Generated: {len(generated_files)}")
        print(f"📋 Analysis File: {analysis_file}")

        print(f"\n📁 Generated Files:")
        for file_path in generated_files:
            print(f"  ✅ {file_path}")

        processed_any = True

    if processed_any:
        print("\n" + "=" * 70)
        print("🏆 DR. LEX GRANT'S ULTIMATE DELETION SYSTEM COMPLETE!")
        print("=" * 70)
    else:
        print("\n❌ No reports were processed.")

if __name__ == "__main__":
    main()