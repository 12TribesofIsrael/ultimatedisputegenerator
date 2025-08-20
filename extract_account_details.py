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
from typing import Any, Dict, List, Optional, Tuple
try:
    import faiss  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    faiss = None  # type: ignore
    SentenceTransformer = None  # type: ignore
from debug.clean_workspace import cleanup_workspace
from utils.inquiries import extract_inquiries_from_text
from utils.inquiry_disputes import save_inquiry_analysis
KB_INDEX_DIR = Path("knowledgebase_index")
KB_MODEL_NAME = "all-MiniLM-L6-v2"
_KB = {"index": None, "meta": None, "model": None}

def _kb_latest_files() -> tuple[Path | None, Path | None]:
    try:
        faiss_files = sorted(KB_INDEX_DIR.glob("index_v*.faiss"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not faiss_files:
            return None, None
        base = faiss_files[0].with_suffix("")
        pkl = base.with_suffix(".pkl")
        return faiss_files[0], pkl if pkl.exists() else None
    except Exception:
        return None, None

def kb_load() -> bool:
    if _KB["index"] is not None:
        return True
    if faiss is None or SentenceTransformer is None:
        return False
    faiss_path, meta_path = _kb_latest_files()
    if not faiss_path or not meta_path:
        return False
    try:
        index = faiss.read_index(str(faiss_path))  # type: ignore
        with open(str(meta_path), "r", encoding="utf-8") as f:
            meta = json.load(f)
        model = SentenceTransformer(KB_MODEL_NAME, device="cpu")
        _KB["index"] = index
        _KB["meta"] = meta
        _KB["model"] = model
        return True
    except Exception:
        return False

def kb_search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Search knowledgebase. Falls back to filename keyword search if FAISS is unavailable.

    Returns list of {file_name, score}.
    """
    def _fallback_filesystem_search(q: str, limit: int) -> list[dict[str, Any]]:
        kb_dir = Path("knowledgebase")
        if not kb_dir.exists():
            return []
        text = (q or "").lower()
        # Expand synonyms for derogatory terms
        synonyms: dict[str, list[str]] = {
            "charge off": ["charge off", "charged off", "charge-off", "profit and loss", "written off", "write off", "bad debt"],
            "collection": ["collection", "collections", "collection account"],
            "repossession": ["repossession", "repo", "vehicle recovery", "repossessed"],
            "foreclosure": ["foreclosure", "foreclosed"],
            "bankruptcy": ["bankruptcy", "chapter 7", "chapter 13"],
            "late": ["late", "past due", "delinquent"],
            "settlement": ["settled", "settlement"],
            "default": ["default"],
        }
        expanded_tokens: list[str] = []
        for key, alts in synonyms.items():
            if key in text:
                expanded_tokens.extend(alts)
        if not expanded_tokens:
            expanded_tokens = [t for t in re.split(r"[^a-z0-9]+", text) if t]
        scored: list[tuple[float, str]] = []
        for p in kb_dir.rglob("*"):
            if not p.is_file():
                continue
            name = p.name.lower()
            score = 0.0
            for tok in expanded_tokens:
                if tok.lower() in name:
                    score += 1.0
            if score > 0.0:
                # Prefer closer path depth and markdown/txt
                if p.suffix.lower() in {".md", ".txt"}:
                    score += 0.25
                scored.append((score, str(p.relative_to(kb_dir))))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"file_name": fn, "score": float(sc)} for sc, fn in scored[:limit]]

    # Try FAISS-backed search first
    if kb_load():
        try:
            model = _KB["model"]
            index = _KB["index"]
            meta = _KB["meta"] or []
            if model and index:
                emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
                D, I = index.search(emb.astype("float32"), top_k)
                results: list[dict[str, Any]] = []
                seen: set[str] = set()
                for rank, idx in enumerate(I[0]):
                    if idx < 0 or idx >= len(meta):
                        continue
                    fn = meta[idx].get("file_name", "")
                    if fn and fn not in seen:
                        seen.add(fn)
                        results.append({"file_name": fn, "score": float(D[0][rank])})
                if results:
                    return results
        except Exception:
            pass

    # Fallback if FAISS not available or returned nothing
    return _fallback_filesystem_search(query, top_k)

def build_kb_references_for_account(account: dict, max_refs: int = 5, round_number: int = 1) -> list[str]:
    """
    Enhanced knowledgebase reference builder with comprehensive search capabilities.
    
    Now includes:
    - Template letter integration with actual content extraction
    - Creditor-specific strategies with targeted approaches
    - Case law and legal precedents with specific citations
    - Round-based escalation tactics
    - Multi-dimensional query patterns
    - Success probability calculation
    - Template content adaptation
    """
    
    # Import enhanced knowledgebase functions
    try:
        from utils.knowledgebase_enhanced import (
            build_comprehensive_kb_references, 
            generate_enhanced_citations,
            classify_creditor_type,
            get_creditor_specific_queries,
            calculate_success_probability,
            estimate_dispute_timeline
        )
        from utils.template_integration import (
            extract_template_content,
            adapt_template_to_account,
            merge_template_content,
            generate_enhanced_dispute_letter
        )
    except ImportError as e:
        print(f"Warning: Enhanced modules not available, using fallback: {e}")
        return _build_kb_references_fallback(account, max_refs)
    
    # Classify creditor type for targeted approach
    creditor_type = classify_creditor_type(account.get('creditor', ''))
    
    # Build comprehensive references using enhanced module
    comprehensive_refs = build_comprehensive_kb_references(account, round_number, max_refs_per_type=3)
    
    # Generate enhanced citations
    enhanced_citations = generate_enhanced_citations(account, comprehensive_refs)
    
    # Calculate success probability
    success_prob = calculate_success_probability(account, comprehensive_refs)
    
    # Estimate timeline
    timeline = estimate_dispute_timeline(round_number, account)
    
    # Combine all references with enhanced categorization
    all_refs = []
    seen_files = set()
    
    # Add template letters with content extraction
    for template in comprehensive_refs.get('template_letters', []):
        file_name = template.get('file_name', '')
        if file_name and file_name not in seen_files:
            seen_files.add(file_name)
            all_refs.append(f"Template: {file_name}")
            
            # Extract and adapt template content
            try:
                template_content = extract_template_content(file_name)
                if template_content:
                    adapted_content = adapt_template_to_account(template_content, account, round_number)
                    if adapted_content:
                        all_refs.append(f"Adapted Content: {file_name}")
            except Exception as e:
                print(f"Template content extraction failed for {file_name}: {e}")
    
    # Add case law with specific precedents
    for case in comprehensive_refs.get('case_law', []):
        file_name = case.get('file_name', '')
        if file_name and file_name not in seen_files:
            seen_files.add(file_name)
            all_refs.append(f"Case Law: {file_name}")
    
    # Add creditor strategies with targeted approaches
    for strategy in comprehensive_refs.get('creditor_strategies', []):
        file_name = strategy.get('file_name', '')
        if file_name and file_name not in seen_files:
            seen_files.add(file_name)
            all_refs.append(f"Strategy: {file_name}")
    
    # Add strategy documents with advanced tactics
    for doc in comprehensive_refs.get('strategy_documents', []):
        file_name = doc.get('file_name', '')
        if file_name and file_name not in seen_files:
            seen_files.add(file_name)
            all_refs.append(f"Guide: {file_name}")
    
    # Add creditor-specific queries
    creditor_queries = get_creditor_specific_queries(account.get('creditor', ''), account.get('status', ''))
    for query in creditor_queries[:2]:  # Limit to 2 creditor-specific queries
        all_refs.append(f"Creditor-Specific: {query}")
    
    # Add enhanced citations
    for citation in enhanced_citations:
        if citation not in all_refs:
            all_refs.append(citation)
    
    # Add success probability and timeline information
    if success_prob > 0.6:
        all_refs.append(f"High Success Probability: {success_prob:.1%}")
    if timeline:
        all_refs.append(f"Estimated Timeline: {timeline} days")
    
    # Add round-based strategy information
    if round_number > 1:
        all_refs.append(f"Round {round_number} Escalation Strategy")
    
    # Limit to max_refs but prioritize high-value references
    prioritized_refs = []
    
    # Priority 1: Template content and adapted content
    for ref in all_refs:
        if "Adapted Content:" in ref or "Template:" in ref:
            prioritized_refs.append(ref)
    
    # Priority 2: Case law and strategies
    for ref in all_refs:
        if "Case Law:" in ref or "Strategy:" in ref:
            prioritized_refs.append(ref)
    
    # Priority 3: Creditor-specific and guides
    for ref in all_refs:
        if "Creditor-Specific:" in ref or "Guide:" in ref:
            prioritized_refs.append(ref)
    
    # Priority 4: Everything else
    for ref in all_refs:
        if ref not in prioritized_refs:
            prioritized_refs.append(ref)
    
    return prioritized_refs[:max_refs]

def _build_kb_references_fallback(account: dict, max_refs: int = 5) -> list[str]:
    """Fallback implementation using original logic."""
    status = (account.get("status") or "").lower()
    creditor = account.get("creditor") or ""
    queries: list[str] = []
    if "charge off" in status or "charged off" in status or "bad debt" in status:
        queries = [
            "FCRA 1681s-2(a) furnisher accuracy charge-off",
            "CDIA Metro 2 charge-off reporting requirements",
        ]
    elif "collection" in status:
        queries = [
            "FCRA 1681i reinvestigation collection account",
            "FDCPA 1692 validation of debts reporting",
        ]
    elif "repossession" in status or "repo" in status:
        queries = [
            "Repossession credit reporting Metro 2",
            "FCRA accuracy repossession status reporting",
        ]
    elif "foreclosure" in status:
        queries = [
            "Foreclosure credit reporting Metro 2",
            "FCRA accuracy foreclosure status",
        ]
    elif "late" in status or account.get("late_entries"):
        queries = [
            "Metro 2 payment history profile late reporting",
            "FCRA 1681s-2(a) accurate payment history",
        ]
    else:
        queries = [
            f"{creditor} credit reporting Metro 2 compliance",
            "FCRA accuracy requirements furnisher",
        ]
    refs: list[str] = []
    seen: set[str] = set()
    for q in queries:
        for r in kb_search(q, top_k=5):
            fn = r.get("file_name")
            if fn and fn not in seen:
                seen.add(fn)
                refs.append(fn)
            if len(refs) >= max_refs:
                break
        if len(refs) >= max_refs:
            break
    return refs

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
    """Enhanced Metro 2 validations using nearby labeled fields.
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
    
    # Credit limit should be 0 for closed accounts
    if re.search(r"Closed", sample, flags=re.IGNORECASE):
        cl = re.search(r"Credit\s*limit\s*[:\-]?\s*\$?(\d+[\,\d]*)(?:\.\d{2})?", sample, flags=re.IGNORECASE)
        if cl:
            try:
                val = int(cl.group(1).replace(',', ''))
                if val > 0:
                    violations.append("Metro 2: Credit limit should be $0 on closed accounts")
            except Exception:
                pass
    
    # Past due amount should be 0 for paid accounts
    if re.search(r"paid|paid\s*as\s*agreed|never\s*late", status_text, flags=re.IGNORECASE):
        pd = re.search(r"Past\s*due\s*amount\s*[:\-]?\s*\$?(\d+[\,\d]*)(?:\.\d{2})?", sample, flags=re.IGNORECASE)
        if pd:
            try:
                val = int(pd.group(1).replace(',', ''))
                if val > 0:
                    violations.append("Metro 2: Past due amount should be $0 on paid accounts")
            except Exception:
                pass
    
    # Balance should be 0 for charge-offs unless sold
    if re.search(r"charge\s*off|charged\s*off", status_text, flags=re.IGNORECASE):
        bal = re.search(r"Balance\s*[:\-]?\s*\$?(\d+[\,\d]*)(?:\.\d{2})?", sample, flags=re.IGNORECASE)
        if bal:
            try:
                val = int(bal.group(1).replace(',', ''))
                if val > 0 and not re.search(r"sold|transferred|assigned", sample, flags=re.IGNORECASE):
                    violations.append("Metro 2: Balance should be $0 on charge-offs unless sold")
            except Exception:
                pass
    
    # Account type mismatch checks
    if re.search(r"revolving|credit\s*card", sample, flags=re.IGNORECASE):
        if re.search(r"installment|loan", sample, flags=re.IGNORECASE):
            violations.append("Metro 2: Account type mismatch - revolving vs installment")
    
    # Date consistency checks
    dofd_match = re.search(r"DOFD|Date\s*of\s*First\s*Delinquency\s*[:\-]?\s*([A-Za-z]{3,9}\s+\d{4})", sample, flags=re.IGNORECASE)
    reported_match = re.search(r"Date\s*Reported\s*[:\-]?\s*([A-Za-z]{3,9}\s+\d{4})", sample, flags=re.IGNORECASE)
    if dofd_match and reported_match:
        dofd_date = dofd_match.group(1)
        reported_date = reported_match.group(1)
        if dofd_date == reported_date and re.search(r"collection|charge\s*off", status_text, flags=re.IGNORECASE):
            violations.append("Metro 2: DOFD and Date Reported should not be identical for collections")
    
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
        # Major Credit Card Issuers
        "APPLE CARD/GS BANK USA": {
            "company": "Goldman Sachs Bank USA (Apple Card)",
            "address": "P.O. Box 182273\nColumbus, OH 43218-2273",
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
        "DISCOVER": {
            "company": "Discover Bank",
            "address": "P.O. Box 30417\nSalt Lake City, UT 84130-0417",
        },
        "CITIBANK": {
            "company": "Citibank",
            "address": "P.O. Box 6000\nSioux Falls, SD 57117-6000",
        },
        "BANK OF AMERICA": {
            "company": "Bank of America",
            "address": "P.O. Box 15019\nWilmington, DE 19850-5019",
        },
        "WELLS FARGO": {
            "company": "Wells Fargo Bank",
            "address": "P.O. Box 10335\nDes Moines, IA 50306-0335",
        },
        
        # Store/Retail Cards
        "WEBBANK/FINGERHUT": {
            "company": "Fingerhut (WebBank)",
            "address": "6250 Ridgewood Rd\nSt. Cloud, MN 56303",
        },
        "SYNCHRONY BANK": {
            "company": "Synchrony Bank",
            "address": "P.O. Box 965033\nOrlando, FL 32896-5033",
        },
        "COMENITY": {
            "company": "Comenity Bank",
            "address": "P.O. Box 183003\nColumbus, OH 43218-3003",
        },
        "COMENITY BANK": {
            "company": "Comenity Bank",
            "address": "P.O. Box 183003\nColumbus, OH 43218-3003",
        },
        "COMENITYCB": {
            "company": "Comenity Bank",
            "address": "P.O. Box 183003\nColumbus, OH 43218-3003",
        },
        
        # Auto/Installment Lenders
        "AUSTIN CAPITAL BANK": {
            "company": "Austin Capital Bank",
            "address": "8100 Shoal Creek Blvd\nAustin, TX 78757",
        },
        "AUSTIN CAPITAL BANK SS": {
            "company": "Austin Capital Bank",
            "address": "8100 Shoal Creek Blvd\nAustin, TX 78757",
        },
        "ALLY BANK": {
            "company": "Ally Bank",
            "address": "P.O. Box 13625\nGreenville, SC 29610-3625",
        },
        "SANTANDER": {
            "company": "Santander Consumer USA",
            "address": "P.O. Box 650489\nDallas, TX 75265-0489",
        },
        "TOYOTA MOTOR CREDIT": {
            "company": "Toyota Motor Credit Corporation",
            "address": "P.O. Box 2991\nTorrance, CA 90509-2991",
        },
        "HONDA FINANCIAL": {
            "company": "American Honda Finance Corporation",
            "address": "P.O. Box 53190\nPhoenix, AZ 85072-3190",
        },
        
        # Student Loans
        "DEPT OF EDUCATION/NELN": {
            "company": "U.S. Dept. of Education / Nelnet",
            "address": "P.O. Box 82561\nLincoln, NE 68501-2561",
        },
        "NAVIENT": {
            "company": "Navient",
            "address": "P.O. Box 9635\nWilkes-Barre, PA 18773-9635",
        },
        "MOHELA": {
            "company": "MOHELA",
            "address": "633 Spirit Drive\nChesterfield, MO 63005-1243",
        },
        
        # Credit Unions
        "NAVY FCU": {
            "company": "Navy Federal Credit Union",
            "address": "P.O. Box 3000\nMerrifield, VA 22119-3000",
        },
        "NAVY FEDERAL": {
            "company": "Navy Federal Credit Union",
            "address": "P.O. Box 3000\nMerrifield, VA 22119-3000",
        },
        "PENFED": {
            "company": "Pentagon Federal Credit Union",
            "address": "P.O. Box 247021\nOmaha, NE 68124-7021",
        },
        
        # Collection Agencies
        "IC SYSTEM": {
            "company": "IC System",
            "address": "444 Highway 96 East\nSt. Paul, MN 55127-2557",
        },
        "PORTFOLIO RECOVERY": {
            "company": "Portfolio Recovery Associates",
            "address": "P.O. Box 12914\nNorfolk, VA 23502-0914",
        },
        "ENHANCED RECOVERY": {
            "company": "Enhanced Recovery Company",
            "address": "P.O. Box 105685\nAtlanta, GA 30348-5685",
        },
        "CONCORD SERVICING": {
            "company": "Concord Servicing LLC",
            "address": "P.O. Box 2900\nPhoenix, AZ 85062-2900",
        },
        
        # Medical Collections
        "MEDICAL COLLECTION": {
            "company": "Medical Collection Agency",
            "address": "[VERIFY SPECIFIC AGENCY ADDRESS]",
        },
        "HOSPITAL": {
            "company": "Hospital Billing Department",
            "address": "[VERIFY SPECIFIC HOSPITAL ADDRESS]",
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
    # Allow passing either raw text or a path to a text file
    try:
        if isinstance(text, str):
            import os
            if os.path.isfile(text):
                with open(text, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
    except Exception:
        pass
    lines = text.split('\n')
    
    # Look for account sections
    current_account = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Fallback: capture creditor from explicit report field labels (e.g., "Account name CONCORD SERVICING LLC")
        # IMPORTANT: Do NOT use "Original creditor" to populate the current creditor field.
        if re.match(r'^(account\s*name|creditor\s*name)\b', line, re.IGNORECASE):
            # Extract value on the same line if present; otherwise, peek next non-empty line
            value_part = re.sub(r'^(account\s*name|creditor\s*name)\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            if not value_part or value_part in {'-', '—'}:
                # Look ahead up to 2 lines
                for k in range(1, 3):
                    if i + k < len(lines):
                        probe = lines[i + k].strip()
                        # Skip if the next line is another label (e.g., "Company sold", "Account type")
                        if not probe or probe in {'-', '—'}:
                            continue
                        if re.match(r'^(original\s*creditor|company\s*sold|account\s*type|open/closed|status|balance|terms|responsibility|date\s*(?:opened|updated|last|reported)|past\s*due|payment\s*history)\b', probe, re.IGNORECASE):
                            continue
                        # Not a label: treat as the creditor value
                        value_part = probe
                        break
            if value_part:
                current_account = {
                    'creditor': value_part.strip(),
                    'raw_creditor': value_part.strip(),
                    'display_creditor': value_part.strip(),
                    'account_number': None,
                    'balance': None,
                    'status': None,
                    'status_raw': None,
                    'account_type': None,
                    'date_opened': None,
                    'last_payment': None,
                    'negative_items': [],
                    'late_payment_count': 0
                }

                # Robust account number extraction around this position
                extracted_acc = _extract_account_number_from_context(lines, i, window=40)
                if extracted_acc:
                    current_account['account_number'] = extracted_acc

                # Continue scanning the local block for balance and status cues
                for j in range(i, min(i + 60, len(lines))):
                    search_line = lines[j]
                    # Stop scanning when the next account section begins
                    if j > i and re.match(r'^account\s*name\b', search_line.strip(), re.IGNORECASE):
                        break
                    balance_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', search_line)
                    if balance_match and not current_account['balance']:
                        current_account['balance'] = balance_match.group()

                    # Capture account type for product grouping and display fidelity
                    m_acc_type = re.match(r'^account\s*type\s*[:\-]?\s*(.+)\s*$', search_line.strip(), re.IGNORECASE)
                    if m_acc_type and not current_account.get('account_type'):
                        current_account['account_type'] = m_acc_type.group(1).strip()

                    # Avoid matching legend/guide rows (e.g., "CO Charge Off" in 24-month history keys)
                    if (re.search(r"charge\s*off|charged\s*off\s*as\s*bad\s*debt|bad\s*debt|written\s*off|write\s*off|charged\s*to\s*profit\s*and\s*loss", search_line, re.IGNORECASE)
                        and not re.search(r"24\s*month\s*history|narrative\s*code|days\s*past\s*due|paid\s*on\s*time|\bCO\b\s*charge\s*off", search_line, re.IGNORECASE)):
                        current_account['status'] = 'Charge off'
                        if 'Charge off' not in current_account['negative_items']:
                            current_account['negative_items'].append('Charge off')

                    status_patterns = [
                        ('Never late', r'never\s*late'),
                        ('Paid, Closed/Never late', r'paid.*closed.*never\s*late'),
                        ('Exceptional payment history', r'exceptional\s*payment\s*history'),
                        ('Paid as agreed', r'(?:paid|pays|paying)\s*(?:account\s*)?as\s*agreed'),
                        ('Not more than two payments past due', r'not\s*more\s*than\s*two\s*payments?\s*past\s*due'),
                        ('Paid, Closed', r'paid.*closed(?!\s*(?:charge|collection))'),
                        ('Current', r'current'),
                        ('Paid', r'paid(?!\s*(?:charge|settlement))'),
                        ('Open', r'open(?!\s*(?:delinquent|past\s*due))'),
                        ('Closed', r'closed(?!\s*(?:charge|collection))'),
                        # Critical derogatories: include repo/foreclosure and common synonyms
                        ('Charge off', r'charge\s*[-–—]?\s*off|charged\s*[-–—]?\s*off\s*as\s*bad\s*debt|bad\s*debt|written\s*off|write\s*off|charged\s*to\s*profit\s*and\s*loss'),
                        ('Collection', r'collection|placed\s*for\s*collection|in\s*collections?'),
                        ('Late', r'late\s*payment|past\s*due(?!\s*amount)|delinquent'),
                        ('Settled', r'settled|settlement|paid\s*settlement'),
                        ('Repossession', r'\brepossession\b|\brepo\b(?!rt|rted|rting)|vehicle\s*recovery|repossessed'),
                        ('Foreclosure', r'foreclosure|foreclosed|foreclosed\s*upon'),
                        ('Bankruptcy', r'bankruptcy|chapter\s*\d+|discharged'),
                    ]
                    # Status precedence map to prevent negatives from overriding positives unless on explicit Status line
                    status_severity = {
                        'Never late': 15,
                        'Paid, Closed/Never late': 15,
                        'Paid as agreed': 15,
                        'Exceptional payment history': 15,
                        'Not more than two payments past due': 15,
                        'Paid, Closed': 14,
                        'Current': 13,
                        'Paid': 12,
                        'Open': 11,
                        'Bankruptcy': 10,
                        'Foreclosure': 9,
                        'Repossession': 8,
                        'Collection': 7,
                        'Charge off': 6,
                        'Settled': 5,
                        'Late': 4,
                        'Closed': 3,
                    }

                    for status_name, status_pattern in status_patterns:
                        if re.search(status_pattern, search_line, re.IGNORECASE):
                            # Prefer explicit Status lines and avoid confusing labels like "Account type: Collection"
                            is_status_line = re.match(r'^(status|current\s*status)\b', search_line.strip(), re.IGNORECASE) is not None
                            # Preserve exact status line value as reported (after the label)
                            if is_status_line and not current_account.get('status_raw'):
                                try:
                                    raw_val = re.sub(r'^(status|current\s*status)\s*[:\-]?\s*', '', search_line.strip(), flags=re.IGNORECASE)
                                    current_account['status_raw'] = re.sub(r'\s+', ' ', raw_val).strip()
                                except Exception:
                                    pass
                            if status_name == 'Collection' and re.search(r'account\s*type', search_line, re.IGNORECASE):
                                continue
                            # Skip legend/guide/key lines for severe derogatories unless explicit Status line
                            if (not is_status_line and status_name in {'Foreclosure','Repossession','Collection','Charge off'} and 
                                re.search(r'legend|key\s*:|status\s*codes?|codes?\s*:\s*|narrative\s*code|24\s*month\s*history|payment\s*history|paid\s*on\s*time|how\s*to\s*read|abbreviations|definitions', search_line, re.IGNORECASE)):
                                continue
                            # Foreclosure should only apply to mortgage/real-estate accounts
                            if status_name == 'Foreclosure':
                                acct_text = (current_account.get('account_type') or '') + ' ' + (current_account.get('creditor') or '')
                                if not re.search(r'mortgage|real\s*estate|home|property|heloc|loan\s*servic', acct_text, re.IGNORECASE):
                                    continue
                            if status_name == 'Late' and re.search(r'past\s*due\s*amount', search_line, re.IGNORECASE):
                                continue
                            severe_derogatories = {'Charge off', 'Collection', 'Repossession', 'Foreclosure', 'Bankruptcy'}
                            positive_statuses = {'Never late', 'Paid, Closed/Never late', 'Paid as agreed', 'Exceptional payment history', 'Paid, Closed', 'Current', 'Paid', 'Open', 'Not more than two payments past due'}
                            current_status = current_account.get('status')
                            # Absolute: if positive is already detected anywhere in this block, do not add Late
                            if status_name == 'Late' and current_status in positive_statuses and not is_status_line:
                                continue
                            # Block positives from being overridden by lesser negatives unless it's an explicit status line
                            if current_status and not is_status_line:
                                cur_sev = status_severity.get(current_status, -1)
                                new_sev = status_severity.get(status_name, -1)
                                if new_sev < cur_sev:
                                    continue
                            # Skip generic section headers like "Collection accounts"
                            if status_name == 'Collection' and re.search(r'collection\s+accounts', search_line, re.IGNORECASE):
                                continue
                            # If on Status line, take it as authoritative
                            current_account['status'] = status_name
                            if status_name in severe_derogatories:
                                if status_name not in current_account['negative_items']:
                                    current_account['negative_items'].append(status_name)
                            elif status_name in {'Late', 'Settled'}:
                                if status_name not in current_account['negative_items']:
                                    current_account['negative_items'].append(status_name)
                                # For CAP ONE AUTO and similar installment auto accounts with explicit 30/60 in grid, keep Late even without explicit Status line
                                try:
                                    if status_name == 'Late':
                                        if re.search(r'CAP\s*ONE\s*AUTO', (current_account.get('creditor') or ''), re.IGNORECASE):
                                            pass
                                except Exception:
                                    pass
                                # Removed aggressive Late→Charge‑off auto-upgrade to avoid false positives
                                # (Charge‑off will be set only on explicit status lines or clearly scoped phrases within the account block.)
                            break

                try:
                    current_account['late_entries'] = _extract_late_entries(lines, i, window=80)
                except Exception:
                    current_account['late_entries'] = []
                try:
                    current_account['late_payment_count'] = _estimate_late_payment_count(lines, i)
                except Exception:
                    current_account['late_payment_count'] = len(current_account.get('late_entries', []))

                # Hard normalization for ANY creditor: only within this account block and only on explicit contexts
                try:
                    # Determine bounds of this account block to avoid picking up legend/guide text
                    block_end = min(i + 200, len(lines))
                    for k in range(i + 1, min(i + 200, len(lines))):
                        nxt = lines[k].strip()
                        if re.match(r'^(account\s*name|creditor\s*name)\b', nxt, re.IGNORECASE):
                            block_end = k
                            break
                    window_text = "\n".join(lines[i:block_end])
                    creditor_lower = (current_account.get('creditor') or '').lower()
                    chargeoff_patterns = (
                        r'charge\s*[-–—]?\s*off|charged\s*[-–—]?\s*off|'
                        r'charged\s*to\s*profit\s*&?\s*loss|'
                        r'written\s*off|write\s*off|'
                        r'charged\s*off\s*account|charge\s*[-–—]?\s*off\s*account|'
                        r'CHARGED\s*OFF\s*ACCOUNT|'
                        r'(?:payment\s*code|pymt\s*code|pay\s*code)\s*[:\-]?\s*CO\b'
                    )
                    # Tighten block-level charge-off detection to avoid legend/guide false positives
                    found_co = re.search(chargeoff_patterns, window_text, re.IGNORECASE)
                    legend_like = re.search(r'legend|key\s*:|24\s*month\s*history|narrative\s*code|days\s*past\s*due|payment\s*history', window_text, re.IGNORECASE)

                    # Additional robust detection: CO codes in payment grids (exclude legend/key lines only)
                    try:
                        non_legend_lines = [ln for ln in window_text.splitlines() if not re.search(r'legend|key\s*:|how\s*to\s*read|abbreviations|definitions', ln, re.IGNORECASE)]
                        grid_text = "\n".join(non_legend_lines)
                        co_token_count = len(re.findall(r'\bCO\b', grid_text, flags=re.IGNORECASE))
                        month_token_count = len(re.findall(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b', grid_text, flags=re.IGNORECASE))
                        grid_indicates_chargeoff = co_token_count >= 2 and month_token_count >= 2
                    except Exception:
                        grid_indicates_chargeoff = False

                    if (
                        current_account.get('status') == 'Charge off'
                        or 'Charge off' in current_account.get('negative_items', [])
                        or (found_co and not legend_like)
                        or grid_indicates_chargeoff
                    ):
                        current_account['status'] = 'Charge off'
                        if 'Charge off' not in current_account['negative_items']:
                            current_account['negative_items'].append('Charge off')
                    # Normalize creditor label artifacts from regex tokens (e.g., "s*" → space)
                    try:
                        raw_name = current_account.get('creditor') or ''
                        cleaned = re.sub(r's\*', ' ', raw_name, flags=re.IGNORECASE)
                        # Remove any stray asterisks that slipped through (e.g., "CAP* ONE")
                        cleaned = cleaned.replace('*', ' ')
                        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                        if cleaned and cleaned != raw_name:
                            current_account['creditor'] = cleaned
                            # keep display_creditor as original string
                    except Exception:
                        pass
                    # Fallback: extract account number from local window if missing
                    try:
                        if not current_account.get('account_number'):
                            m = re.search(r'(?:account\s*number|acct(?:\.|\s*#)?)\D*([0-9Xx]{5,20})', window_text, re.IGNORECASE)
                            if m:
                                current_account['account_number'] = m.group(1)
                    except Exception:
                        pass
                    # If within a 'Collection accounts' section, force Collection status regardless of incidental positives like 'Open account'
                    if re.search(r'collection\s+accounts', window_text, re.IGNORECASE):
                        current_account['status'] = 'Collection'
                        if 'Collection' not in current_account['negative_items']:
                            current_account['negative_items'].append('Collection')

                    # If an explicit Status line states Collection, take it as authoritative
                    if re.search(r'^(?:status|current\s*status)\s*[:\-]?\s*(?:collection\s*account|collection)\b', window_text, re.IGNORECASE | re.MULTILINE):
                        current_account['status'] = 'Collection'
                        if 'Collection' not in current_account['negative_items']:
                            current_account['negative_items'].append('Collection')
                except Exception:
                    pass

                if current_account.get('account_number') or current_account.get('status'):
                    accounts.append(current_account)
                    # Do not continue to creditor_patterns on the same line; move to next line
                    continue

        # Look for account names (creditors) - updated for TransUnion format and credit unions
        creditor_patterns = [
            r'CAP\s*ONE\s*AUTO',
            r'CAP\s*ONE\s*AUTO\s*FINANCE',
            r'CAP(?:ITAL)?\s*ONE\s*AUTO\s*FINANCE',
            r'CAP(?:ITAL)?\s*ONE\s*BANK\s*\(\s*USA\s*\)\s*,?\s*N\.?A\.?',
            r'CAP(?:ITAL)?\s*ONE\s*BANK\s*USA',
            r'THD/CBNA',
            r'CB/VICS?CRT',
            r'CCB/CHLDPLCE',
            r'MERIDIAN\s*FIN',
            r'COMENITYBANK/VICTORI',
            r'COMENITYCAPITAL/CHLD',
            r'CONCORD SERVICING',
            r'CONCORD SERVICING LLC',
            r'I\.C\.\s*SYSTEM',
            r'I\s*C\s*SYSTEM',
            r'IC\s*SYSTEMS?',
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
            r'MOHELA',
            r'AIDVANTAGE',
            r'GREAT\s*LAKES',
            r'NAVIENT',
            r'AES',
            r'AUSTIN CAPITAL BANK',
            r'AUSTINCAPBK',  # TransUnion format for Austin Capital Bank
            r'WEBBANK/FINGERHUT',
            r'FETTIFHT/WEB',  # TransUnion format for Fingerhut/WebBank
            r'SYNCHRONY BANK',
            r'SYNCB',  # Synchrony abbreviation
            r'AMZN/SYNCB',
            r'PAYPAL/SYNCB',
            r'CARE\s*?CREDIT/SYNCB|CARECREDIT/SYNCB',
            r'WALMART/SYNCB',
            r'KOHLS/CAPONE|KOHLS/ CAPONE',
            r'CAPITAL ONE',
            r'CAPITAL ONE NA',
            r'CAP\s*ONE',
            r'DISCOVERCARD',  # Discover Card
            r'DISCOVER BANK',
            r'DISCOVER',
            r'CHASE',
            r'JPMORGAN CHASE',
            r'JPMCB\s*CARD\s*SERVICES',
            r'JPMCB',
            r'AMERICAN EXPRESS',
            r'AMEX',
            r'BANK OF AMERICA',
            r'BOFA|BofA',
            r'WELLS FARGO',
            r'WF\s*BANK',
            r'CITIBANK',
            r'CBNA',  # Citibank abbreviation on reports
            r'CITI',
            r'BARCLAYS',
            r'BARCLAYS BANK DELAWARE',
            r'US BANK',
            r'\bALLY\b',
            r'COMENITY',
            r'COMENITYBANK',
            r'COMENITYCAPITAL',
            r'ELAN',
            r'FIRST PREMIER',
            r'MERRICK BANK',
            r'CFNA',  # Credit First NA
            r'TD BANK',
            r'TD AUTO',
            r'PNC',
            r'REGIONS',
            r'ALLY\s*FINANCIAL',
            r'TOYOTA\s*MOTOR\s*CREDIT|TOYOTA\s*FINANCIAL',
            r'AMERICAN\s*HONDA\s*FINANCE|AHFC',
            r'SANTANDER|SANTANDER\s*CONSUMER\s*USA|SCUSA',
            r'CREDIT\s*ONE\s*BANK',
            r'PREMIER\s*BANKCARD',
            r'PAYPAL CREDIT',
            # Common collection agencies
            r'PORTFOLIO\s*RECOVERY',
            r'MIDLAND\s*(FUNDING|CREDIT|MCM)',
            r'LVNV\s*FUNDING',
            r'ENHANCED\s*RECOVERY|\bERC\b',
            r'JEFFERSON\s*CAPITAL',
            r'CONVERGENT',
            r'PHOENIX\s*FINANCIAL',
            r'CREDIT\s*CONTROL',
            r'RECEIVABLES\s*PERFORMANCE|\bRPM\b',
            r'NATIONAL\s*CREDIT\s*SYSTEMS|\bNCS\b',
            r'NATIONAL\s*RECOVERY\s*AGENCY|\bNRA\b',
            r'AFNI',
            r'IQOR',
            r'SEQUIUM',
            r'SALLIE MAE',
            r'PORTFOLIO RECOVERY',
            r'LVNV',
            r'MIDLAND CREDIT',
            r'MIDLAND FUNDING',
            r'CAVALRY',
            r'CAVALRY SPV',
            r'PA STA EMPCU',  # Pennsylvania State Employees Credit Union
            r'NAVY\s*FEDERAL\s*CREDIT\s*UNION',
            r'NAVY\s*FEDERAL\s*CREDIT',
            r'[A-Z\s]{2,20}(?:FCU|EMPCU|CU)\b',  # General credit union patterns (FCU, EMPCU, CU)
            r'[A-Z\s]{2,20}CREDIT UNION',  # Credit unions with full name
        ]
        
        for pattern in creditor_patterns:
            if re.search(pattern, line, re.IGNORECASE) and not re.match(r'^(status|current\s*status|account\s*type|balance|monthly\s*payment|past\s*due|credit\s*(?:limit|usage)|terms|responsibility|your\s*statement)\b', line, re.IGNORECASE):
                # Normalize creditor names to standard format (canonical), but preserve exact report label for display
                canonical = pattern.replace('\\', '')
                # Extract matched text and attempt to expand to the full creditor label on the line before metadata tokens
                match_obj = re.search(pattern, line, re.IGNORECASE)
                matched_text = match_obj.group(0).strip() if match_obj else line.strip()
                full_label = line.strip()
                m_full = re.match(r'^\s*([A-Z0-9][A-Z0-9\s\/\-\.\(\),&]+?)(?=\s{2,}|[:#]|acct|account|bal|open|status|date|responsibility|terms|type|credit|limit|usage|monthly|past|payment|reported|history|remarks|\d)', line, re.IGNORECASE)
                if m_full:
                    full_label = re.sub(r'\s+', ' ', m_full.group(1)).strip()
                else:
                    full_label = re.sub(r'\s+', ' ', matched_text)
                
                creditor_name = canonical
                # Handle regex canonical forms → canonical names; display uses full_label
                if creditor_name == 'DEPTEDNELNET':
                    creditor_name = 'DEPT OF EDUCATION/NELNET'
                elif creditor_name in [
                    'DEPT OF ED', 'DEPT OF ED/NELN', 'DEPT OF EDUCATION', 'DEPT OF EDUCATION/NELN',
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
                elif re.search(r'NAVY\s*FEDERAL\s*CREDIT', line, re.IGNORECASE):
                    if re.search(r'UNION|FCU', line, re.IGNORECASE):
                        creditor_name = 'NAVY FEDERAL CREDIT UNION'
                    else:
                        creditor_name = 'NAVY FEDERAL CREDIT'
                elif re.search(r'JPMCB', line, re.IGNORECASE) or re.search(r'JPMORGAN\s*CHASE', line, re.IGNORECASE):
                    creditor_name = 'JPMCB CARD SERVICES'

                current_account = {
                    'creditor': creditor_name,
                    'raw_creditor': full_label,
                    'display_creditor': full_label,
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
                for j in range(i, min(i+60, len(lines))):
                    search_line = lines[j]
                    # Stop scanning when the next account section begins
                    if j > i and re.match(r'^account\s*name\b', search_line.strip(), re.IGNORECASE):
                        break
                    balance_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', search_line)
                    if balance_match and not current_account['balance']:
                        current_account['balance'] = balance_match.group()
                    
                    # Charge-off only from Status (line-start) or explicit payment-code/remark contexts
                    if re.search(r"^(?:status|current\s*status)\b.*?(charge\s*[-–—]?\s*off|charged\s*[-–—]?\s*off\s*as\s*bad\s*debt)", search_line, re.IGNORECASE):
                        current_account['status'] = 'Charge off'
                        if 'Charge off' not in current_account['negative_items']:
                            current_account['negative_items'].append('Charge off')
                    elif re.search(r"(?:payment\s*code|pymt\s*code|pay\s*code)\s*[:\-]?\s*CO\b|CHARGED\s*OFF\s*ACCOUNT", search_line, re.IGNORECASE):
                        current_account['status'] = 'Charge off'
                        if 'Charge off' not in current_account['negative_items']:
                            current_account['negative_items'].append('Charge off')
                    # Inline Status field (e.g., "... | Status: Charge Off")
                    elif re.search(r"\bstatus\s*:\s*(charge\s*[-–—]?\s*off|charged\s*[-–—]?\s*off\s*as\s*bad\s*debt)", search_line, re.IGNORECASE):
                        current_account['status'] = 'Charge off'
                        # capture raw status if present inline
                        mraw = re.search(r"\bstatus\s*:\s*([^|\n]+)", search_line, re.IGNORECASE)
                        if mraw and not current_account.get('status_raw'):
                            current_account['status_raw'] = re.sub(r"\s+", " ", mraw.group(1)).strip()
                        if 'Charge off' not in current_account['negative_items']:
                            current_account['negative_items'].append('Charge off')
                    
                    # Look for status - POSITIVE statuses first, then negative
                    status_patterns = [
                        # POSITIVE statuses first (these should override negative inferences)
                        ('Never late', r'never\s*late'),
                        ('Paid, Closed/Never late', r'paid.*closed.*never\s*late'),
                        ('Exceptional payment history', r'exceptional\s*payment\s*history'),
                        ('Paid as agreed', r'(?:paid|pays|paying)\s*(?:account\s*)?as\s*agreed'),
                        ('Not more than two payments past due', r'not\s*more\s*than\s*two\s*payments?\s*past\s*due'),
                        ('Paid, Closed', r'paid.*closed(?!\s*(?:charge|collection))'),  # "Paid, Closed" but not charge-off
                        ('Current', r'current'),
                        ('Paid', r'paid(?!\s*(?:charge|settlement))'),  # Paid but not "paid charge off" or "paid settlement"
                        ('Open', r'open(?!\s*(?:delinquent|past\s*due))'),  # Open but not "open delinquent"
                        ('Closed', r'closed(?!\s*(?:charge|collection))'),  # Closed but not "closed charge off"
                        
                        # NEGATIVE statuses second
                        # Charge-off and equivalents (include "written off")
                        ('Charge off', r'charge\s*[-–—]?\s*off|charged\s*[-–—]?\s*off\s*as\s*bad\s*debt|bad\s*debt|written\s*off|write\s*off'),
                        ('Collection', r'collection'),
                        ('Late', r'late\s*payment|past\s*due|delinquent'),  # More specific late pattern
                        ('Settled', r'settled|settlement|paid\s*settlement'),
                        ('Repossession', r'\brepossession\b|\brepo\b(?!rt|rted|rting)|vehicle\s*recovery|repossessed'),
                        ('Foreclosure', r'foreclosure|foreclosed'),
                        ('Bankruptcy', r'bankruptcy|chapter\s*\d+|discharged'),
                    ]
                    for status_name, status_pattern in status_patterns:
                        if re.search(status_pattern, search_line, re.IGNORECASE):
                            # Ignore "Account type: Collection" when deciding status
                            is_status_line = re.match(r'^(status|current\s*status)\b', search_line.strip(), re.IGNORECASE) is not None
                            if status_name == 'Collection' and re.search(r'account\s*type', search_line, re.IGNORECASE):
                                continue
                            # Skip legend/guide/key lines that list multiple codes (e.g., "90 Days Past Due F Foreclosure ...")
                            if (not is_status_line and status_name in {'Foreclosure','Repossession','Collection','Charge off'} and 
                                re.search(r'legend|key\s*:|status\s*codes?|codes?\s*:\s*|narrative\s*code|24\s*month\s*history|payment\s*history|how\s*to\s*read|abbreviations|definitions', search_line, re.IGNORECASE)):
                                continue
                            # Only allow Charge off when on explicit status line or explicit remark/payment-code contexts
                            if status_name == 'Charge off' and not is_status_line:
                                if not re.search(r'(?:payment\s*code|pymt\s*code|pay\s*code)\s*[:\-]?\s*CO\b|CHARGED\s*OFF\s*ACCOUNT', search_line, re.IGNORECASE):
                                    continue
                            # Foreclosure only for mortgage/real-estate
                            if status_name == 'Foreclosure':
                                acct_text = (current_account.get('account_type') or '') + ' ' + (current_account.get('creditor') or '')
                                if not re.search(r'mortgage|real\s*estate|home|property|heloc|loan\s*servic', acct_text, re.IGNORECASE):
                                    continue
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
                                'Exceptional payment history': 15, 'Not more than two payments past due': 15, 'Paid, Closed': 14
                            }
                            
                            current_severity = status_severity.get(current_status, 0)
                            new_severity = status_severity.get(status_name, 0)
                            
                            # On explicit Status lines, treat as authoritative by boosting severity virtually
                            if is_status_line:
                                new_severity += 20

                            # Absolute guard: once a severe derogatory is detected, never allow a positive to override it
                            severe_derogatories = {'Charge off', 'Collection', 'Repossession', 'Foreclosure', 'Bankruptcy'}
                            positive_statuses = {'Never late', 'Paid, Closed/Never late', 'Paid as agreed', 'Exceptional payment history', 'Not more than two payments past due', 'Paid, Closed', 'Current', 'Paid', 'Open'}
                            if current_status in severe_derogatories and status_name in positive_statuses:
                                # Skip override; also ensure the negative item is recorded
                                if current_status not in current_account['negative_items'] and current_status != 'Closed':
                                    current_account['negative_items'].append(current_status)
                                continue

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

                    # Removed standalone CO promotion; handled only in explicit contexts above

                    # Only infer Late from payment grid numbers if no positive status was found
                    if not current_account.get('status') or current_account.get('status') in ['Open', 'Closed']:
                        # Look for explicit late indicators near payment grid numbers
                        # IMPORTANT: Do not mark Late if a charge-off indicator exists in this account block
                        block_start = max(0, i - 10)
                        block_end_local = min(i + 120, len(lines))
                        local_block = "\n".join(lines[block_start:block_end_local])
                        co_present = re.search(r'charge\s*[-–—]?\s*off|charged\s*[-–—]?\s*off|\bCO\b|CHARGED\s*OFF\s*ACCOUNT', local_block, re.IGNORECASE) is not None
                        if not co_present and re.search(r'(?:late\s*payment|past\s*due|\b(?:30|60|90)\s*days?\s*(?:late|past\s*due))', search_line, re.IGNORECASE):
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
                    # Enhanced re-aging detection: check for multiple re-aging indicators
                    try:
                        dofd_data = current_account.get('dofd')
                        reported_data = current_account.get('date_reported')
                        status_updated = current_account.get('status_updated')
                        
                        if dofd_data and reported_data:
                            dm, dy, _ = dofd_data
                            rm, ry, _ = reported_data
                            age_months = _months_between(dm, dy, rm, ry)
                            
                            # Flag if DOFD is old but account still showing recent activity
                            if age_months is not None and age_months > 84:  # > 7 years
                                current_account.setdefault('violations', []).append('FCRA §623(a)(5) Re-aging concern (DOFD vs Date Reported)')
                            
                            # Additional re-aging checks
                            if age_months is not None and age_months > 60:  # > 5 years
                                # Check if status was recently updated
                                if status_updated:
                                    sm, sy, _ = status_updated
                                    status_age = _months_between(dm, dy, sm, sy)
                                    if status_age is not None and status_age > 60 and (sm, sy) != (rm, ry):
                                        current_account.setdefault('violations', []).append('FCRA §623(a)(5) Re-aging: Status updated on old DOFD account')
                            
                            # Check for balance changes on old accounts (potential re-aging)
                            if age_months is not None and age_months > 48:  # > 4 years
                                balance = current_account.get('balance')
                                if balance and balance != '$0':
                                    current_account.setdefault('violations', []).append('FCRA §623(a)(5) Re-aging: Non-zero balance on old DOFD account')
                    except Exception:
                        pass
                    # Metro 2 quick checks from nearby lines
                    block = lines[i: min(i+30, len(lines))]
                    mviol = _check_metro2_simple_rules(block, current_account.get('status') or '')
                    if mviol:
                        current_account.setdefault('violations', []).extend(mviol)
                    # Medical collection <$500 flag (CFPB/NCRA policy)
                    try:
                        balance_amount = _parse_balance_amount(current_account.get('balance'))
                        is_medical_like = False
                        cred = (current_account.get('creditor') or '').lower()
                        if any(term in cred for term in ['medical', 'hospital', 'health', 'clinic', 'radiology', 'dental', 'orthopedic']):
                            is_medical_like = True
                        if (current_account.get('status') and 'collection' in current_account['status'].lower()) or 'collection' in ' '.join(current_account.get('negative_items') or []).lower():
                            if is_medical_like and balance_amount is not None and balance_amount < 500:
                                current_account.setdefault('violations', []).append('Medical collection under $500 — should not be reported per NCRA policy (2023)')
                    except Exception:
                        pass
                except Exception:
                    pass

                # Require at least an account number or a detected status near the creditor line
                # If payment grid clearly shows CO codes with month tokens, accept as charge-off
                if not current_account.get('account_number') and not current_account.get('status'):
                    try:
                        window_text = "\n".join(lines[i: min(i+120, len(lines))])
                        non_legend_lines = [ln for ln in window_text.splitlines() if not re.search(r'legend|key\s*:|how\s*to\s*read|abbreviations|definitions', ln, re.IGNORECASE)]
                        grid_text = "\n".join(non_legend_lines)
                        co_token_count = len(re.findall(r'\bCO\b', grid_text, flags=re.IGNORECASE))
                        month_token_count = len(re.findall(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b', grid_text, flags=re.IGNORECASE))
                        if co_token_count >= 2 and month_token_count >= 2:
                            current_account['status'] = 'Charge off'
                            current_account.setdefault('negative_items', [])
                            if 'Charge off' not in current_account['negative_items']:
                                current_account['negative_items'].append('Charge off')
                    except Exception:
                        pass
                    if not current_account.get('status'):
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

    # New merging with heuristic keys (creditor + last4 + balance) and enrichment
    merged: dict[tuple[str, str, str], dict] = {}
    MULTI = object()
    by_cred_bal: dict[tuple[str, str], object] = {}

    def normalize_creditor(name: str) -> str:
        """Normalize creditor to a canonical family name for dedup.

        Rules:
          - Uppercase, remove extra spaces and punctuation
          - Drop corporate suffixes: LLC, INC, CO, CORP, CORPORATION, COMPANY
          - Collapse known aliases: JPMCB CARD SERVICES→JPMCB CARD, DISCOVERC→DISCOVER, etc.
          - Reduce any X/CBNA forms to CBNA
          - Normalize IC SYSTEM variants
        """
        try:
            n = (name or '').upper()
            # Replace non-alnum with spaces
            n = re.sub(r"[^A-Z0-9]+", " ", n)
            # Remove common corporate suffixes
            n = re.sub(r"\b(LLC|INC|CO|CORP|CORPORATION|COMPANY)\b", " ", n)
            n = re.sub(r"\s+", " ", n).strip()
            # Known alias collapses
            n = n.replace("JPMCB CARD SERVICES", "JPMCB CARD")
            n = n.replace("DISCOVERC", "DISCOVER")
            n = n.replace("DISCOVER CARD", "DISCOVER")
            n = n.replace("CONCORD SERVICING LLC", "CONCORD SERVICING")
            n = n.replace("NAVY FEDERAL CR UNION", "NAVY FCU")
            # Reduce any X/CBNA forms (MACYS/CBNA, THD/CBNA, etc.) to CBNA
            if "CBNA" in n:
                n = "CBNA"
            # COMENITY variants
            if n.startswith("COMENITYCB") or n.startswith("COMENITY BANK"):
                n = "COMENITY"
            if n.startswith("COMENITY "):
                n = "COMENITY"
            # IC SYSTEM variants (I C SYSTEM, I.C. SYSTEM, etc.)
            if re.search(r"\bI\s*C\s*SYSTEM\b", n):
                n = "IC SYSTEM"
            # CAPITAL ONE AUTO variants -> merge to CAPITAL ONE
            if re.search(r"\bCAP(?:S|ITAL)?\s+ONE(?:S)?\s+AUTO\b", n):
                n = "CAPITAL ONE"
            return n
        except Exception:
            return name or ''

    def extract_last4(num: str | None) -> str | None:
        if not num:
            return None
        digits = re.sub(r"[^0-9]", "", num)
        return digits[-4:] if len(digits) >= 4 else None

    def prefer_account_number(a: str | None, b: str | None) -> str | None:
        a_has = bool(re.search(r"\d", a or ''))
        b_has = bool(re.search(r"\d", b or ''))
        if b_has and not a_has:
            return b
        return a or b

    def merge_into(cur: dict, acc: dict) -> None:
        if status_rank(acc.get('status')) > status_rank(cur.get('status')):
            cur['status'] = acc.get('status')
        cur_balance = cur.get('balance', '')
        acc_balance = acc.get('balance', '')
        if not cur_balance and acc_balance:
            cur['balance'] = acc_balance
        elif cur_balance and acc_balance and cur_balance != acc_balance:
            try:
                cur_amt = float(cur_balance.replace('$', '').replace(',', ''))
                acc_amt = float(acc_balance.replace('$', '').replace(',', ''))
                if acc_amt > cur_amt:
                    cur['balance'] = acc_balance
            except Exception:
                pass
        cur['account_number'] = prefer_account_number(cur.get('account_number'), acc.get('account_number'))
        cur.setdefault('negative_items', [])
        for it in acc.get('negative_items', []):
            if it not in cur['negative_items']:
                cur['negative_items'].append(it)
        cur.setdefault('late_entries', [])
        entries = cur['late_entries'] + acc.get('late_entries', [])
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

    for acc in accounts:
        cred = normalize_creditor(acc.get('creditor') or '')
        bal_key = normalize_balance(acc.get('balance'))
        last4 = extract_last4(acc.get('account_number'))
        last4_key = last4 if last4 else 'UNK'
        # Keep installment auto products distinct from bank/cards when account type says Installment
        acc_type = (acc.get('account_type') or acc.get('type') or '').lower()
        product_group = 'AUTO' if 'installment' in acc_type or re.search(r'auto\b', (acc.get('raw_creditor') or ''), re.IGNORECASE) else 'GEN'
        comp_key = (cred, product_group, last4_key, bal_key)

        # If key exists, merge directly
        if comp_key in merged:
            merge_into(merged[comp_key], acc)
        else:
            # If unknown account number, try to merge into a unique creditor+balance entry
            cred_bal = (cred, bal_key)
            ref = by_cred_bal.get(cred_bal)
            if last4_key == 'UNK' and isinstance(ref, tuple) and ref in merged:
                merge_into(merged[ref], acc)
                comp_key = ref
            else:
                # Try fallback: same creditor and same last4 regardless of exact balance (if one side missing)
                matched = None
                if last4_key != 'UNK':
                    for k in merged.keys():
                        if k[0] == cred and k[2] == last4_key:
                            matched = k
                            break
                if matched:
                    merge_into(merged[matched], acc)
                    comp_key = matched
                else:
                    merged[comp_key] = acc.copy()

        # Track mapping uniqueness for creditor+balance
        marker = by_cred_bal.get((cred, bal_key))
        if marker is None:
            by_cred_bal[(cred, bal_key)] = comp_key
        elif marker is not MULTI and marker != comp_key:
            by_cred_bal[(cred, bal_key)] = MULTI

    return list(merged.values())

def _parse_balance_amount(balance_value: str | None) -> float | None:
    """Parse a currency string like "$1,234.56" to a float 1234.56.

    Returns None if parsing fails.
    """
    if not balance_value:
        return None
    try:
        numeric = re.sub(r"[^0-9.]", "", balance_value)
        if not numeric:
            return None
        return float(numeric)
    except Exception:
        return None

def classify_account_policy(account: dict) -> str:
    """Return 'delete' or 'correct' based on KB policy.

    - Collections/Charge-off/Repo/Foreclosure/Bankruptcy/Default/Settlement ⇒ delete
    - COMENITYBANK accounts ⇒ delete (specialty lender with aggressive collection)
    - Late payments policy (per user):
        • If account is OPEN: always correct (remove late marks), regardless of count
        • If account is CLOSED: delete only if late_count > 4; otherwise correct
    """
    status_text = (account.get('status') or '').lower()
    status_raw = (account.get('status_raw') or '').lower()
    creditor_text = (account.get('creditor') or '').lower()
    display_text = (account.get('display_creditor') or account.get('raw_creditor') or '').lower()
    account_type_text = (account.get('account_type') or '').lower()
    
    # Special case: COMENITYBANK accounts should always be deletion demands
    if 'comenity' in creditor_text:
        return 'delete'
    
    delete_terms = [
        'collection','placed for collection','in collection','in collections',
        'charge off','charged off','charged off as bad debt','bad debt','charged to profit and loss',
        'repossession','repo(?!rt|rted|rting)','vehicle recovery','repossessed',
        'foreclosure','foreclosed','foreclosed upon',
        'bankruptcy','default','settled','settlement'
    ]
    if any(t in status_text for t in delete_terms):
        return 'delete'
    
    # Late-payment policy (revised)
    late_count = len(account.get('late_entries') or [])
    has_late = ('late' in status_text) or ('past due' in status_text) or ('past due' in status_raw) or late_count > 0
    is_open = ('open' in status_text) or ('current' in status_text) or ('open' in status_raw) or ('current' in status_raw)
    is_closed = ('closed' in status_text) or ('paid, closed' in status_text) or ('closed' in status_raw) or ('paid, closed' in status_raw)

    if has_late:
        if is_open and not is_closed:
            return 'correct'
        if is_closed:
            return 'delete' if late_count > 4 else 'correct'
        # If indeterminate open/closed, be conservative and correct
        return 'correct'

    # Default: correct unless a delete term matched above
    return 'correct'

def normalize_creditor_for_filename(name: str) -> str:
    """Return a canonical, filesystem-safe creditor label for filenames.

    Applies similar aliasing rules as merging and strips punctuation/suffixes,
    then converts spaces to single underscores.
    """
    try:
        n = (name or '').upper()
        # Replace non-alphanumeric with spaces
        n = re.sub(r"[^A-Z0-9]+", " ", n)
        # Remove common corporate suffixes
        n = re.sub(r"\b(LLC|INC|CO|CORP|CORPORATION|COMPANY)\b", " ", n)
        n = re.sub(r"\s+", " ", n).strip()
        # Aliases
        n = n.replace("JPMCB CARD SERVICES", "JPMCB CARD")
        n = n.replace("DISCOVERC", "DISCOVER")
        if "CONCORD SERVICING LLC" in n:
            n = n.replace("CONCORD SERVICING LLC", "CONCORD SERVICING")
        if "NAVY FEDERAL CR UNION" in n:
            n = "NAVY FCU"
        if "CBNA" in n:
            n = "CBNA"
        if n.startswith("COMENITYCB") or n.startswith("COMENITY BANK") or n.startswith("COMENITY "):
            n = "COMENITY"
        if re.search(r"\bI\s*C\s*SYSTEM\b", n):
            n = "IC SYSTEM"
        # Final: to underscore form
        n = re.sub(r"\s+", "_", n)
        return n
    except Exception:
        return re.sub(r"\s+", "_", (name or ''))

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
        'repossession', 'repo(?!rt|rted|rting)', 'vehicle recovery', 'foreclosure', 'bankruptcy',
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
        strong_positive_statuses = ['never late', 'paid, closed/never late', 'exceptional payment history', 'paid as agreed', 'not more than two payments past due']
        mild_positive_statuses = ['pays account as agreed', 'paid, closed']
        
        # Strong positive statuses (never late, exceptional) should be excluded regardless
        if any(pos_status in status_text for pos_status in strong_positive_statuses):
            # Special case: "Not more than two payments past due" with late entries needs correction
            if 'not more than two payments past due' in status_text and late_entries and len(late_entries) > 0:
                negative_accounts.append(account)
                continue
            elif not negative_items:
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

    # Remove duplicate accounts before returning
    unique_negative_accounts = deduplicate_accounts(negative_accounts)
    
    if len(unique_negative_accounts) < len(negative_accounts):
        print(f"🔍 Removed {len(negative_accounts) - len(unique_negative_accounts)} duplicate accounts")
    
    return unique_negative_accounts

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
    is_medical_like = any(term in creditor_lower for term in ['medical', 'hospital', 'health', 'clinic', 'radiology', 'dental', 'orthopedic'])
    if is_medical_like:
        citations.extend([
            "HIPAA privacy violations in medical debt reporting",
            "FDCPA medical debt protection requirements"
        ])
        # Add NCRA/CFPB medical debt policy reference for <$500 where applicable
        try:
            amt = _parse_balance_amount(account.get('balance'))
        except Exception:
            amt = None
        status_lower = account.get('status', '').lower()
        if amt is not None and amt < 500 and ('collection' in status_lower or 'collection' in ' '.join(account.get('negative_items') or []).lower()):
            citations.append("NCRA policy (2023): Medical collections under $500 should not be reported")
    
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
        # Get account-specific citations and knowledgebase references
        additional_citations = get_account_specific_citations(account)
        kb_refs = build_kb_references_for_account(account, max_refs=5, round_number=round_number)

        # Enhanced template integration
        try:
            from utils.template_integration import generate_enhanced_dispute_letter
            enhanced_letter_data = generate_enhanced_dispute_letter(account, round_number)
            template_content = enhanced_letter_data.get('letter_content', '')
            success_probability = enhanced_letter_data.get('success_probability', 0)
            strategy_recommendations = enhanced_letter_data.get('recommended_approach', [])
        except ImportError:
            template_content = ''
            success_probability = 0
            strategy_recommendations = []

        policy = classify_account_policy(account)
        status_text = (account.get('status') or '').lower()
        title = "DEMAND FOR DELETION" if policy == 'delete' else "LATE-PAYMENT CORRECTION REQUEST"

        # Account number display: preserve report-masked or raw string exactly as captured
        acct_display = account.get('account_number') or 'XXXX-XXXX-XXXX-XXXX (Must be verified)'

        # Generate complete account content (without template content to avoid duplication)
        account_content = generate_complete_account_content(account, round_number, "")

        letter_content += f"""
**Account {i} - {title}:**
- **Creditor:** {account.get('display_creditor') or account.get('raw_creditor') or account['creditor']}
- **Account Number:** {acct_display}
- **Current Status:** {account.get('status_raw') or account.get('status') or 'Inaccurate reporting'}
- **Balance Reported:** {account.get('balance') or 'Unverified amount'}

{account_content}
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

        # Demand/correction language is produced in generate_demands within account_content

        # Detected Metro 2 / re-aging violations (compact list)
        viols = account.get('violations') or []
        if viols:
            letter_content += "\n- **Detected Violations:** " + "; ".join(sorted(set(viols)))
            
        # Re-aging summary if applicable
        reaging_viols = [v for v in viols if 're-aging' in v.lower()]
        if reaging_viols:
            letter_content += "\n- **Re-aging Violations:** This account shows signs of re-aging, which violates FCRA §623(a)(5). The furnisher must provide complete documentation proving the accuracy of all dates and status changes."

        # Medical collection < $500 explicit note
        try:
            amt = _parse_balance_amount(account.get('balance'))
            cred = (account.get('creditor') or '').lower()
            is_medical = any(term in cred for term in ['medical','hospital','health','clinic','radiology','dental','orthopedic'])
            status_lower = (account.get('status') or '').lower()
            if is_medical and amt is not None and amt < 500 and ('collection' in status_lower or 'collection' in ' '.join(account.get('negative_items') or []).lower()):
                letter_content += "\n- **Medical Collection Policy:** Under the 2023 NCRA policy and CFPB guidance, medical collections under $500 should not be reported and must be deleted."
        except Exception:
            pass
        
        # Add concise, account-specific citations (no "Violation of" prefix)
        for citation in additional_citations:
            letter_content += f"\n- {citation}"
        
        # Skip external template content to avoid system-looking text
        
        # Remove internal system markers - these should not appear in consumer letters
        # Success probability and strategy recommendations are for internal use only
        
        # Remove duplicate content that may have been created during template merging
        letter_content = remove_duplicate_content(letter_content)
        
        # Do not show internal knowledgebase references in user-facing letters
        
        letter_content += "\n\n"
    
    # Re-aging violations summary
    reaging_accounts = [acc for acc in accounts if any('re-aging' in v.lower() for v in acc.get('violations') or [])]
    if reaging_accounts:
        letter_content += "\n## RE-AGING VIOLATIONS SUMMARY\n\n"
        letter_content += "The following accounts show evidence of re-aging violations under FCRA §623(a)(5):\n\n"
        
        for i, account in enumerate(reaging_accounts, 1):
            dofd_display = account.get('dofd')[2] if account.get('dofd') and isinstance(account['dofd'], tuple) else 'Unknown'
            reported_display = account.get('date_reported')[2] if account.get('date_reported') and isinstance(account['date_reported'], tuple) else 'Unknown'
            
            letter_content += f"""
**Account {i} - Re-aging Violation:**
- **Creditor:** {account.get('display_creditor') or account.get('raw_creditor') or account['creditor']}
- **Account Number:** {account.get('account_number') or 'XXXX-XXXX-XXXX-XXXX'}
- **DOFD:** {dofd_display}
- **Date Reported:** {reported_display}
- **Violation:** FCRA §623(a)(5) - Furnisher must provide complete documentation proving accuracy of all dates and status changes
"""
        letter_content += "\n**All re-aging violations must be investigated and substantiated with certified documentation, or the accounts must be deleted.**\n"
    
    # Optional section: late-payment corrections (no full deletion)
    if correction_accounts:
        letter_content += "\n## ACCOUNTS WITH LATE-PAYMENT CORRECTIONS REQUESTED\n\n"
        for j, account in enumerate(correction_accounts, 1):
            late_count = account.get('late_payment_count', 0)
            acct_display = account.get('account_number', 'XXXX-XXXX-XXXX-XXXX')
            letter_content += f"""
**Account {j} - LATE-PAYMENT CORRECTION REQUEST:**
- **Creditor:** {account.get('display_creditor') or account.get('raw_creditor') or account['creditor']}
- **Account Number:** {acct_display}
- **Current Status:** {account.get('status_raw') or account.get('status', 'Late payment reporting')}
- **Detected Late Marks:** {late_count if late_count else 'Unspecified (late marks present)'}
- **REQUEST:** Remove all late-payment entries and update the account status to **PAID AS AGREED**; if you cannot fully verify every late mark with complete documentation, you must **DELETE THE ENTIRE TRADELINE** immediately per FCRA accuracy requirements.
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

    # Remove system-facing strategy headers; keep consumer voice minimal and specific to the account

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
        # Avoid redundant stem if it duplicates the bureau name (e.g., Equifax.pdf)
        if safe_stem and safe_stem.lower() == bureau_detected.lower():
            safe_stem = None
    
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
            creditor_safe = normalize_creditor_for_filename(account['creditor'])
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
            creditor_safe = normalize_creditor_for_filename(account['creditor'])
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

def auto_generate_next_round_letter(analysis_file_path: str, round_number: int) -> str:
    """Auto-generate next-round letter based on analysis results.
    
    Analyzes the previous round's results and creates a follow-up letter
    with appropriate escalation tactics.
    """
    try:
        with open(analysis_file_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # Extract key information from analysis
        accounts = analysis_data.get('accounts', [])
        bureau_name = analysis_data.get('bureau_detected', 'Unknown Bureau')
        total_accounts = len(accounts)
        
        # Count different types of violations
        reaging_violations = sum(1 for acc in accounts if any('re-aging' in v.lower() for v in acc.get('violations', [])))
        medical_violations = sum(1 for acc in accounts if any('medical' in v.lower() for v in acc.get('violations', [])))
        metro2_violations = sum(1 for acc in accounts if any('metro 2' in v.lower() for v in acc.get('violations', [])))
        
        # Determine escalation strategy based on violations
        if reaging_violations > 0:
            escalation_focus = "re-aging violations"
        elif medical_violations > 0:
            escalation_focus = "medical debt violations"
        elif metro2_violations > 0:
            escalation_focus = "Metro 2 compliance violations"
        else:
            escalation_focus = "general FCRA violations"
        
        # Generate round-specific content
        if round_number == 2:
            letter_content = f"""
# ROUND 2 - ESCALATION NOTICE - {bureau_name.upper()}
**Follow-up Dispute Letter by Dr. Lex Grant, Credit Expert**

**Date:** {datetime.now().strftime('%B %d, %Y')}
**Subject:** ESCALATION - {total_accounts} Accounts Still Not Deleted

## NOTICE OF NON-COMPLIANCE

Dear {bureau_name},

This letter serves as formal notice that you have FAILED to comply with my previous dispute letter dated [DATE OF PREVIOUS LETTER]. 

**CRITICAL FINDINGS:**
- **{total_accounts} accounts** remain on my credit report despite clear violations
- **{reaging_violations} re-aging violations** detected and documented
- **{medical_violations} medical debt violations** under NCRA policy
- **{metro2_violations} Metro 2 compliance violations** identified

## IMMEDIATE ACTION REQUIRED

You now have **15 days** (not 30) to:
1. **DELETE** all disputed accounts
2. **PROVIDE** complete documentation for any accounts you refuse to delete
3. **EXPLAIN** why Metro 2 compliance violations were not addressed

## ESCALATION NOTICE

Failure to comply within 15 days will result in:
- **CFPB complaint** filing
- **State Attorney General** complaint
- **Federal litigation** under FCRA §1681n

**This is your FINAL opportunity to resolve this matter before regulatory and legal action.**
"""
        elif round_number == 3:
            letter_content = f"""
# ROUND 3 - FINAL NOTICE BEFORE LITIGATION - {bureau_name.upper()}
**Final Dispute Letter by Dr. Lex Grant, Credit Expert**

**Date:** {datetime.now().strftime('%B %d, %Y')}
**Subject:** FINAL NOTICE - Immediate Deletion Required

## FINAL NOTICE OF NON-COMPLIANCE

Dear {bureau_name},

This constitutes my **FINAL NOTICE** before initiating federal litigation. You have repeatedly failed to comply with FCRA requirements.

**VIOLATIONS DOCUMENTED:**
- **{total_accounts} accounts** with confirmed violations
- **{reaging_violations} re-aging violations** (FCRA §623(a)(5))
- **{medical_violations} medical debt violations** (NCRA policy)
- **{metro2_violations} Metro 2 violations** (CDIA compliance)

## IMMEDIATE DELETION DEMAND

You have **10 days** to:
1. **DELETE ALL** disputed accounts
2. **PROVIDE** written confirmation of deletion
3. **SUBMIT** updated credit report

## LITIGATION NOTICE

If accounts are not deleted within 10 days, I will file:
- **Federal lawsuit** under FCRA §1681n
- **CFPB complaint** for regulatory violations
- **State Attorney General** complaint
- **Punitive damages** claim for willful non-compliance

**This is your LAST opportunity to avoid litigation.**
"""
        else:
            letter_content = f"""
# ROUND {round_number} - REGULATORY ESCALATION - {bureau_name.upper()}
**Regulatory Escalation Letter by Dr. Lex Grant, Credit Expert**

**Date:** {datetime.now().strftime('%B %d, %Y')}
**Subject:** REGULATORY ESCALATION - {total_accounts} Violations

## REGULATORY ESCALATION NOTICE

Dear {bureau_name},

Due to continued non-compliance, this matter is being escalated to federal and state regulators.

**VIOLATIONS SUMMARY:**
- **{total_accounts} accounts** with confirmed violations
- **{reaging_violations} re-aging violations**
- **{medical_violations} medical debt violations**
- **{metro2_violations} Metro 2 violations**

## REGULATORY ACTION

I am filing complaints with:
1. **Consumer Financial Protection Bureau (CFPB)**
2. **State Attorney General**
3. **Federal Trade Commission (FTC)**

## IMMEDIATE COMPLIANCE REQUIRED

You have **5 days** to delete all disputed accounts or face:
- **Regulatory enforcement action**
- **Federal litigation**
- **Maximum statutory damages**

**This matter is now in the hands of federal regulators.**
"""
        
        return letter_content
        
    except Exception as e:
        return f"Error generating next-round letter: {e}"

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
        kb_refs = build_kb_references_for_account(account, max_refs=5, round_number=round_number)
        summary["accounts_details"].append({
            "creditor": account['creditor'],
            "account_number": account.get('account_number', 'Unknown'),
            "status": account.get('status', 'Unknown'),
            "balance": account.get('balance', 'Unknown'),
            "negative_items": account.get('negative_items', []),
            "kb_references": kb_refs,
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
        # Unified selection: allow 1..N to pick a single report, or A/Y to process all (default all)
        while True:
            resp = input("\nSelect a report [1-" + str(len(pdf_files)) + "] or 'A' for All (default A): ").strip().lower()
            if resp in ('', 'a', 'all', 'y', 'yes'):  # default/all
                selected_files = pdf_files
                break
            if resp.isdigit():
                idx = int(resp)
                if 1 <= idx <= len(pdf_files):
                    selected_files = [pdf_files[idx - 1]]
                    break
            print("❌ Invalid selection. Enter a number from the list or 'A' for All.")
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

        # Extract text from PDF (with OCR fallback)
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Error extracting text from {pdf_path.name} (native parser): {e}")

        if len(text.strip()) < 100:
            print("ℹ️ Native PDF text extraction returned too little content. Attempting OCR fallback...")
            try:
                from utils.ocr_fallback import extract_text_via_ocr  # local util, optional deps
                ocr_text = extract_text_via_ocr(pdf_path)
                if len(ocr_text.strip()) >= 100:
                    text = ocr_text
                    print(f"✅ OCR fallback succeeded. Extracted {len(text)} characters of text.")
                else:
                    print("❌ OCR fallback produced insufficient text. Skipping this file.")
                    continue
            except Exception as e:
                print(f"❌ OCR fallback not available or failed: {e}")
                print("Skipping this file due to insufficient extractable text.")
                continue

        print(f"Extracted {len(text)} characters of text (after fallback if used)")

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

        # Also extract hard inquiries and save a simple JSON for reference
        try:
            inquiries = extract_inquiries_from_text(text)
            if inquiries:
                inquiries_path = (bureau_dir if is_batch else folders.get("Analysis", bureau_dir)) / f"inquiries_{pdf_path.stem}.json"
                with open(inquiries_path, "w", encoding="utf-8") as f_inq:
                    json.dump({"file": pdf_path.name, "inquiries": inquiries}, f_inq, indent=2)
                print(f"🧾 Inquiries extracted: {len(inquiries)} → {inquiries_path}")
                
                # Generate inquiry dispute analysis
                try:
                    inquiry_analysis_file, inquiry_dispute_file = save_inquiry_analysis(
                        inquiries, bureau_detected, f"inquiry_analysis_{pdf_path.stem}.json"
                    )
                    print(f"📋 Generated inquiry analysis: {inquiry_analysis_file}")
                    print(f"📄 Generated inquiry dispute letter: {inquiry_dispute_file}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not generate inquiry dispute analysis: {e}")
        except Exception as _e:
            print("(Note) Inquiries extraction skipped due to an error.")

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

def remove_duplicate_content(content: str) -> str:
    """Remove duplicate content sections from the letter."""
    if not content:
        return content
    
    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    unique_paragraphs = []
    seen_paragraphs = set()
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # Create a normalized version for comparison
        normalized = normalize_paragraph_for_dedup(paragraph)
        
        # Only add if we haven't seen this content before
        if normalized not in seen_paragraphs:
            unique_paragraphs.append(paragraph)
            seen_paragraphs.add(normalized)
    
    return '\n\n'.join(unique_paragraphs)

def normalize_paragraph_for_dedup(paragraph: str) -> str:
    """Normalize a paragraph for deduplication by removing variable content."""
    if not paragraph:
        return ""
    
    # Remove account-specific information
    normalized = re.sub(r'account \d+', 'ACCOUNT_PLACEHOLDER', paragraph, flags=re.IGNORECASE)
    normalized = re.sub(r'with [A-Z\s\*]+', 'with CREDITOR_PLACEHOLDER', normalized)
    normalized = re.sub(r'\d{10,}', 'ACCOUNT_NUMBER_PLACEHOLDER', normalized)
    
    # Remove specific creditor names
    normalized = re.sub(r'CAPs\*ONEs\*AUTO|CAPITAL ONE|DEPTEDNELNET|CB/VICS\?CRT|CB/VICSCRT|CCB/CHLDPLCE|CREDITONEBNK|DISCOVER CARD|DISCOVERCARD|JPMCB CARD SERVICES|CBNA|NAVY FCU|THD/CBNA|MERIDIAN FIN|MERIDIANs\*FIN', 'CREDITOR_PLACEHOLDER', normalized)
    
    # Remove specific amounts
    normalized = re.sub(r'\$\d{1,3}(?:,\d{3})*', 'AMOUNT_PLACEHOLDER', normalized)
    
    # Remove specific dates
    normalized = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b', 'DATE_PLACEHOLDER', normalized)
    
    # Normalize whitespace and case
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip().lower()

def deduplicate_accounts(accounts_data):
    """Remove duplicate accounts based on account numbers and creditor names."""
    if not accounts_data:
        return accounts_data
    
    unique_accounts = []
    seen_accounts = set()
    
    for account in accounts_data:
        account_number = account.get('account_number')
        if account_number is None:
            account_number = ''
        else:
            account_number = str(account_number).strip()
        
        creditor = account.get('creditor')
        if creditor is None:
            creditor = ''
        else:
            creditor = str(creditor).strip()
        
        # Create a unique identifier
        account_id = f"{creditor}_{account_number}"
        
        # Normalize account ID for better matching
        normalized_id = normalize_account_id(account_id)
        
        if normalized_id not in seen_accounts:
            unique_accounts.append(account)
            seen_accounts.add(normalized_id)
    
    return unique_accounts

def _format_reported_fields(account: Dict[str, Any]) -> str:
    """Build a dynamic 'Reported Fields' section from whatever was parsed off the credit report."""
    lines_out: list[str] = []
    def add(label: str, value) -> None:
        if value is None:
            return
        if isinstance(value, (list, tuple)):
            # handle (m, y, raw) tuples for dates
            if len(value) == 3 and all(v is not None for v in value):
                lines_out.append(f"- **{label}:** {value[2]}")
                return
        text = str(value).strip()
        if text:
            lines_out.append(f"- **{label}:** {text}")

    # Prefer on-report labels if present
    add("Creditor (as reported)", account.get('display_creditor') or account.get('raw_creditor') or account.get('creditor'))
    add("Account Number", account.get('account_number'))
    add("Account Type", account.get('account_type'))
    add("Responsibility", account.get('responsibility'))
    add("Terms", account.get('terms'))
    add("Current Status (as reported)", account.get('status_raw') or account.get('status'))
    add("Balance", account.get('balance'))
    add("Past Due", account.get('past_due'))
    add("Monthly Payment", account.get('monthly_payment'))
    add("Credit Limit", account.get('credit_limit'))
    add("High Credit", account.get('high_credit'))
    add("Date Opened", account.get('date_opened'))
    add("Date Reported", account.get('date_reported'))
    add("Status Updated", account.get('status_updated'))
    add("DOFD", account.get('dofd'))

    # Summarize late entries if available
    late_entries = account.get('late_entries') or []
    if late_entries:
        try:
            month_order = {m: i for i, m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], start=1)}
            entries_sorted = sorted(late_entries, key=lambda e: (e.get('year') or 0, month_order.get(e.get('month','')[:3].title(), 0)), reverse=True)
        except Exception:
            entries_sorted = late_entries
        formatted = ", ".join([f"{e.get('month','')} {e.get('year') or ''} ({e.get('severity')})".strip() for e in entries_sorted])
        if formatted:
            lines_out.append(f"- **Detected Late Entries:** {formatted}")

    return "\n".join(lines_out)

def generate_complete_account_content(account: Dict[str, Any], round_number: int, template_content: str) -> str:
    """Generate complete account content with all required sections."""
    # Reported (dynamic) fields from the credit report
    reported_fields = _format_reported_fields(account)

    # Generate legal basis
    legal_basis = generate_legal_basis(account, round_number)
    
    # Generate violations
    violations = generate_violations(account, round_number)
    
    # Generate demands
    demands = generate_demands(account, round_number)
    
    # Combine all content
    parts: list[str] = []
    if reported_fields:
        parts.append("### Reported Fields\n" + reported_fields)
    if template_content:
        parts.append(template_content)
    if legal_basis:
        parts.append(legal_basis)
    if violations:
        parts.append(violations)
    if demands:
        parts.append(demands)

    complete_content = "\n\n".join(parts)
    
    return complete_content.strip()

def generate_legal_basis(account: Dict[str, Any], round_number: int) -> str:
    """Generate legal basis dynamically based on detected issues and status."""
    status_text = (account.get('status') or '').lower()
    violations = [v.lower() for v in (account.get('violations') or [])]

    points: list[str] = []
    # Core citations mapped to detected problems
    if status_text:
        points.append("- 15 USC §1681i – Reinvestigation of disputed information")
        points.append("- 15 USC §1681s-2(a) – Furnisher accuracy requirements")
    if any('re-aging' in v for v in violations):
        points.append("- 15 USC §1681s-2(a)(5) – Proper DOFD reporting (no re-aging)")
    if 'collection' in status_text or any('collection' in v for v in violations):
        points.append("- 15 USC §1692g – FDCPA debt validation before reporting/collecting")
    if 'late' in status_text:
        points.append("- 15 USC §1681s-2(a)(1)(B) – Accurate payment history (late codes)")
    if 'charge off' in status_text:
        points.append("- 15 USC §1681e(b) – Reasonable procedures for maximum possible accuracy")
    if violations:
        points.append("- CDIA Metro 2 – Reporting format and field consistency")

    if not points:
        return ""
    return "**Legal Basis (derived from the reported data):**\n" + "\n".join(points)

def generate_violations(account: Dict[str, Any], round_number: int) -> str:
    """List specific violations detected for this tradeline (Metro 2/FCRA), no boilerplate."""
    detected = account.get('violations') or []
    if not detected:
        return ""
    unique_sorted = sorted(set(detected))
    bullets = "\n".join(f"- {v}" for v in unique_sorted)
    return "**Detected Issues (as parsed from the report):**\n" + bullets

def generate_demands(account: Dict[str, Any], round_number: int) -> str:
    """Generate demands based on the account's status and detected issues (no static boilerplate)."""
    status_text = (account.get('status') or '').lower()
    items = account.get('negative_items') or []
    lines: list[str] = []

    if 'collection' in status_text or 'collection' in " ".join(items).lower():
        lines.append("1. Provide full FDCPA validation (original contract, chain of custody, and authority to collect)")
        lines.append("2. Cease reporting until validation is completed")
        lines.append("3. Delete the tradeline if validation cannot be completed")
    if 'charge off' in status_text:
        lines.append("1. Correct all Metro 2 fields or delete if you cannot certify accuracy")
        lines.append("2. Provide documentation supporting charge-off status and amounts")
    if 'late' in status_text:
        lines.append("1. Remove all late codes and update status to PAID AS AGREED (or delete if unverifiable)")

    # If no status-specific lines, provide a minimal accuracy demand
    if not lines:
        lines.append("1. Provide certified documentation for all reported fields or delete the tradeline as unverifiable")

    return "**Requested Action (based on issues above):**\n" + "\n".join(f"- {l}" for l in lines)

def normalize_account_id(account_id: str) -> str:
    """Normalize account ID for better duplicate detection."""
    if not account_id:
        return ""
    
    # Remove common variations in creditor names
    normalized = account_id.upper()
    
    # Handle common creditor name variations
    normalized = re.sub(r'DISCOVER\s+CARD', 'DISCOVERCARD', normalized)
    normalized = re.sub(r'JPMCB\s+CARD\s+SERVICES', 'JPMCB', normalized)
    normalized = re.sub(r'CAPs\*ONEs\*AUTO', 'CAPITAL ONE AUTO', normalized)
    normalized = re.sub(r'CB/VICS\?CRT', 'CB/VICSCRT', normalized)
    normalized = re.sub(r'MERIDIANs\*FIN', 'MERIDIAN FIN', normalized)
    
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()

if __name__ == "__main__":
    main()