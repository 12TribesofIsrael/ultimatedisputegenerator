"""
OCR fallback utilities for image-based PDFs.

Uses pdf2image to rasterize pages and pytesseract to recognize text.
All imports are done lazily to avoid hard failures when optional
dependencies or native binaries are not installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, List


def extract_text_via_ocr(
	pdf_path: Union[str, Path],
	dpi: int = 300,
	max_pages: Optional[int] = None,
) -> str:
	"""
	Attempt to OCR a PDF file page-by-page.

	Parameters
	- pdf_path: path to the PDF file
	- dpi: rasterization resolution; 300 dpi is a good balance of speed/accuracy
	- max_pages: limit number of pages to OCR for large files (None = all)

	Returns
	- Extracted text (possibly empty if OCR is unavailable or fails)
	"""
	try:
		from pdf2image import convert_from_path  # type: ignore
	except Exception:
		return ""

	try:
		import pytesseract  # type: ignore
	except Exception:
		return ""

	try:
		path = Path(pdf_path)
		if not path.exists():
			return ""

		# Convert pages to PIL images
		images = convert_from_path(str(path), dpi=dpi)
		if max_pages is not None:
			images = images[: max_pages]

		text_fragments: List[str] = []
		for img in images:
			try:
				# Use a readable config; users may tweak in DEVELOPMENT docs
				page_text = pytesseract.image_to_string(img)
				if page_text:
					text_fragments.append(page_text)
			except Exception:
				# Continue on single-page OCR failure
				continue

		return "\n\n".join(text_fragments).strip()
	except Exception:
		return ""


