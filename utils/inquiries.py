"""Inquiries extraction utility.

Parses a credit report text for a likely "Inquiries" section and extracts
simple entries containing the furnisher name and date.
"""

from __future__ import annotations

import re
from typing import List, Dict, Tuple, Optional


_MONTHS = {
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


def _parse_month_year(token: str) -> Tuple[Optional[int], Optional[int]]:
	"""Return (month, year) if token looks like a month-year, else (None, None)."""
	if not token:
		return None, None
	t = token.strip()
	# Formats: Jun 2025, June 2025
	m = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", t, flags=re.IGNORECASE)
	if m:
		month = _MONTHS[m.group(1).lower()]
		year = int(m.group(2))
		return month, year
	# Formats: 06/2025 or 2025/06
	m = re.search(r"(\d{1,2})[\-/](\d{4})", t)
	if m:
		month = int(m.group(1))
		year = int(m.group(2))
		if 1 <= month <= 12:
			return month, year
	m = re.search(r"(\d{4})[\-/](\d{1,2})", t)
	if m:
		year = int(m.group(1))
		month = int(m.group(2))
		if 1 <= month <= 12:
			return month, year
	return None, None


def extract_inquiries_from_text(report_text: str) -> List[Dict]:
	"""Extract a simple list of inquiries from the report text.

	Heuristics:
	- Find a line containing "Inquiries" (hard/regular) and scan forward
	- For each subsequent non-empty line until a new section, attempt to capture
	  a furnisher name and a date token.
	"""
	lines = report_text.split("\n")
	# Locate an inquiries section header
	start_idx = None
	for idx, line in enumerate(lines):
		if re.search(r"\b(hard\s+inquiries|inquiries\s*(?:last\s*2\s*years)?)\b", line, flags=re.IGNORECASE):
			start_idx = idx + 1
			break
	if start_idx is None:
		return []

	results: List[Dict] = []
	for j in range(start_idx, min(len(lines), start_idx + 300)):
		row = lines[j].strip()
		if not row:
			# End of the block most likely
			if results:
				break
			else:
				continue
		# Stop if we appear to hit another major section
		if re.search(r"\b(Accounts|Collections|Public\s*records|Payment\s*history|Credit\s*utilization|Personal\s*information)\b", row, flags=re.IGNORECASE):
			break

		# Try to find a date token in the line
		date_match = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{1,2}[\-/]\d{4}|\d{4}[\-/]\d{1,2}", row, flags=re.IGNORECASE)
		month, year = (None, None)
		if date_match:
			month, year = _parse_month_year(date_match.group(0))

		# Furnisher: take the alpha words excluding the date token; prefer uppercase blocks
		furn = re.sub(re.escape(date_match.group(0)) if date_match else "", "", row).strip()
		# Clean separators
		furn = re.sub(r"^[\-:\u2013\u2014\s]+|[\-:\u2013\u2014\s]+$", "", furn)
		# Trim to a reasonable label
		furn = re.sub(r"\s{2,}", " ", furn)

		entry = {
			"furnisher": furn or None,
			"date": f"{year:04d}-{month:02d}" if (month and year) else None,
			"raw": row,
		}
		# Only include if either furnisher or date present
		if entry["furnisher"] or entry["date"]:
			results.append(entry)

	return results


