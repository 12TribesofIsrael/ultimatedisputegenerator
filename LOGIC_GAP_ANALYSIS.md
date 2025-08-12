# Logic vs. Knowledge-Base Alignment Report (Expanded)

*Generated August 11 2025*

---

## 1 · Current Pipeline Overview
1. **Input discovery** – batch processing of all PDFs in `consumerreport/`.
2. **Text extraction** – PyMuPDF; *OCR fallback TODO*.
3. **Parsing**  
   • Creditor & account-number capture (±40 lines) with Equifax/TransUnion variants.  
   • Late-entry extractor parses payment grids & headers, stores month / year / 30-60-90.  
   • Accounts merged by `(creditor, acct#)`; negative-item union.
4. **Policy classification**  
   • Collection / charge-off / repossession / foreclosure / bankruptcy / default / settlement ⇒ **delete**.  
   • Late payments: ≥3 ⇒ **delete**; 1-2 ⇒ **correct / remove late entries** (wording adjusts for >24 months).
5. **Letter generation**  
   • Bureau letter per report; furnisher letters optional.  
   • Bullet lists include late months & severities.  
   • Round-specific sections (MOV, Request-for-Procedure, Litigation, CFPB escalation).
6. **Manual flow** – MD → editable TXT → professional PDF remains unchanged.

---

## 2 · Alignment with *Maximum Negative Deletion* SOP

| SOP Requirement | Status | Comment |
| --- | --- | --- |
| Detect and dispute collections / charge-offs | ✅ | Implemented |
| Detect late payments & list dates | ✅ | Late-entry extractor & list builder |
| ≥3 lates → Deletion | ✅ | `classify_account_policy` |
| ≤2 lates → Removal / correction | ✅ | Policy wording present |
| 24-month impact rule considered | ✅ | Wording reflects recency |
| Metro 2 payment profile violations | ✅ | Mentioned in legal basis |
| Request-for-Procedure (R2) | ✅ | Round-specific template |
| MOV (R3) | ✅ | Round-specific template |
| Litigation / CFPB escalation (R4/R5) | ✅ | Included |
| DOFD/re-aging flag | ❌ | *GAP* |
| Duplicate tradeline detection | ❌ | *GAP* |
| Hard-inquiry disputes | ❌ | *GAP* |
| Medical-debt < $500 handling | ❌ | *GAP* |
| Image-only PDF OCR | ❌ | *GAP* |

---

## 3 · Negative-Item Taxonomy (KB vs. Code)

**Covered** ✅  
Collections / Charge-offs / Defaults / Settlements / Repossessions / Foreclosures / Bankruptcies / Late-payments.

**Not yet parsed** 🆕  
* Duplicate tradelines.  
* DOFD / re-aging inconsistencies.  
* High-balance, past-due mismatch.  
* Identity-theft blocks (FCRA §605B).  
* Medical debt < $500 (CFPB 2023).  
* Hard inquiries >2 years or unauthorized.  
* Public-record age-off (7/10-yr).  
* Student-loan rehab mis-reporting.

---

## 4 · Metro 2 / CDIA Violations Checklist

1. Payment History codes (30/60/90) – **implemented**.  
2. High-balance > charged-off balance – 🆕.  
3. Balance not 0 on repossession / collection – 🆕.  
4. Closed Date present but Status ≠ Closed – 🆕.  
5. ECOA code mismatch (Joint vs Individual) – 🆕.  
6. Missing Consumer-Information Indicator (“D” for ID-theft) – 🆕.

---

## 5 · Regulatory / Statutory Angles to Add

* FACTA §609(e) – ID-theft docs.  
* CFPB 2023 medical-debt bulletin (< $500).  
* CARES Act §4021 – COVID accommodation late marks.  
* State mini-FCRA references (e.g., California CC §1785.25).  
* DOFD re-aging (FCRA §623(a)(5)).

---

## 6 · Outstanding Gaps & Priority

| Gap | Priority | Implementation Note |
| --- | --- | --- |
| OCR fallback for image PDFs | High | `pdf2image`+`pytesseract` if extracted text <100 chars |
| DOFD / re-aging detection | High | Compare DOFD vs Date Reported & account age |
| Duplicate tradeline merge across bureaus | Med | Group by acct# & creditor across all reports |
| Hard-inquiry extractor | Med | Parse “Inquiries” sections; list date & furnisher |
| Medical < $500 flag | Med | Detect medical creditor + balance <500 |
| Metro 2 field mismatch validation | Med | Rule set vs parsed fields |
| Creditor address DB expansion | Low | Harvest from KB letters, store JSON |
| Damage calc per violation | Low | Weight late-removal vs full deletion |

---

## 7 · Recommended Roadmap

1. **OCR fallback implementation** (unlock any scan-only PDFs).  
2. **DOFD / re-aging detector** and add template wording.  
3. **Inquiry parsing** & unauthorized inquiry letter section.  
4. **Duplicate-tradeline merge across bureaus** to avoid double damages.  
5. **Metro 2 field checker** module with rules table.  
6. **Creditor-address registry** grown from KB.  
7. **Auto-generate next-round letters** from analysis JSON.

---

*End of expanded logic gap analysis*
