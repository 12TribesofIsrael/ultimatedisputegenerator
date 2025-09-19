# Dispute Letter Style Guide (Authoring + PDF Output)

Source of truth: Example PDF at `__pycache__/Example/41603_68a3e4df19515_Experian.pdf`. Match look and feel.

1) Tone and Voice
- Consumer-authored. No system/branding/automation markers.
- Clear, firm language ("I DEMAND" not "I request").

2) Header Block
- Lines: Name, Address, Phone, Email (optional), masked SSN (XXX-XX-1234), DOB (MM/DD/YYYY), Date.
- Minimal labels; "SSN:" and "DOB:" allowed.

3) Salutation/Subject
- "Dear <Bureau>," then a blank line before body.
- Subject kept in body; no page-top banners.

4) Section Structure (no bullets or numbered lists)
- Use plain paragraphs. Strip bullets (•, -, *) and enumerators (1., 2), (3)).
- Ensure a blank line between account sections.
- Account header format: "Account N - DEMAND FOR DELETION" or "Account N - LATE-PAYMENT CORRECTION REQUEST".
- Follow header with reported fields, legal basis, detected issues, and requests as paragraphs.

5) Knowledgebase Integration
- Keep dynamic legal citations inline as sentences (FCRA/FDCPA/Metro 2).
- No template/system labels or internal references in user-facing output.

6) PDF Formatting Rules
- No bullet or numbered lists. Render as paragraphs only.
- Normalize Unicode to PDF-safe ASCII (quotes/dashes/spaces).
- Margins: ~1.1in left/right/top; ~1.06in bottom (current defaults).

7) Spacing
- One blank line between logical sections.
- Extra blank line before each new account header.

8) Classification
- "Collection" only when the tradeline Status line explicitly states it.

9) Regeneration Checklist
- Compare spacing and paragraph flow to the Example PDF.
- If list markers reappear, adjust `convert_to_professional_pdf.py` normalization.
