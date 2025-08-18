# 🏆 Ultimate Dispute Letter Generator
AI-powered system that analyzes credit reports and generates professional dispute letters.

## 🎯 Overview
**Dr. Lex Grant's Ultimate Dispute Letter Generator** is an AI-powered credit repair system that:

- **Analyzes credit reports** to identify FCRA violations (re-aging, Metro 2 compliance, unauthorized inquiries)
- **Calculates potential statutory damages** ($1,000+ per violation under FCRA §1681n)
- **Generates professional dispute letters** with legal citations and escalating pressure tactics
- **Handles medical debt** under $500 with NCRA policy compliance
- **Creates multi-round escalation strategies** for maximum effectiveness

**Goal**: Help consumers clean their credit AND potentially earn thousands in statutory damages through FCRA violations.

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Prepare Your Credit Reports**
Place your credit report PDF(s) from Experian, Equifax, or TransUnion in:
```
consumerreport/input/
```
The system auto-detects all PDFs in any subfolder.

### 3. **Run the Analysis**
```bash
python extract_account_details.py
```

### 4. **Follow the Prompts**
- Enter your name and address (once per session)
- Choose dispute strategy (Bureau Only, Furnishers Only, or Maximum Pressure)
- Select round number (1st, 2nd, 3rd, etc.)

### 5. **Review Generated Files**
- **Dispute letters** in `outputletter/` folders
- **Analysis summaries** with violation details
- **Inquiry disputes** for unauthorized credit pulls
- **Professional PDFs** ready for certified mail

## 🔄 Workflow
1) **Analyze credit reports** - Extract accounts, identify violations, calculate potential damages
2) **Enter personal information** - Name, address, certified mail tracking (once per session)
3) **Choose dispute strategy** - Bureau only, furnishers only, or maximum pressure approach
4) **Generate dispute letters** - Professional letters with legal citations and violation details
5) **Review and mail** - Send via certified mail with tracking for maximum effectiveness

## 📄 Convert to PDF
```
python debug/convert_to_professional_pdf.py          # create editable text version
python debug/convert_to_professional_pdf.py pdf      # generate professional PDF
```

## 🧹 Cleanup
```
python debug/clean_workspace.py
```
For non-interactive runs, set `CLEAN_CHOICE=2` for Smart Clean.

## 📚 Documentation
- `docs/INSTALLATION.md` – system setup and OCR prerequisites
- `docs/USAGE.md` – usage and automation tips
- `docs/DEVELOPMENT.md` – development notes and contribution
- `docs/README_FULL.md` – archived full-length README

## 💰 **Potential Financial Benefits**
- **Statutory damages**: $1,000 per FCRA violation
- **Re-aging violations**: FCRA §623(a)(5) - $1,000 per account
- **Unauthorized inquiries**: FCRA §1681b - $1,000 per inquiry
- **Medical debt violations**: NCRA policy compliance
- **Metro 2 violations**: CDIA compliance standards

## ⚠️ Important Notes
- **OCR fallback** is attempted automatically if native text extraction is insufficient
- **Knowledgebase features** require FAISS and sentence-transformers (optional)
- **Certified mail tracking** is recommended for all dispute letters
- **Multiple rounds** may be necessary for stubborn creditors/bureaus
- **Legal compliance** - All letters include proper FCRA citations and statutory damage calculations


