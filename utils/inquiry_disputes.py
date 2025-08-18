#!/usr/bin/env python3
"""Hard inquiry dispute letter generation module."""

import json
from datetime import datetime
from typing import List, Dict, Any


def generate_hard_inquiry_dispute_letter(inquiries_data: List[Dict[str, Any]], bureau_name: str) -> str:
    """Generate a dispute letter for unauthorized hard inquiries.
    
    Args:
        inquiries_data: List of inquiry dictionaries from utils.inquiries
        bureau_name: Name of the credit bureau (Experian, Equifax, TransUnion)
    
    Returns:
        Formatted dispute letter content
    """
    
    # Filter for inquiries that might be unauthorized
    unauthorized_indicators = [
        'collection', 'debt', 'credit repair', 'credit counseling',
        'loan', 'mortgage', 'auto', 'student', 'personal loan',
        'credit card', 'store card', 'retail', 'utility'
    ]
    
    suspicious_inquiries = []
    for inquiry in inquiries_data:
        furnisher = inquiry.get('furnisher', '').lower()
        # Check if inquiry might be unauthorized
        if any(indicator in furnisher for indicator in unauthorized_indicators):
            suspicious_inquiries.append(inquiry)
    
    if not suspicious_inquiries:
        return f"""# HARD INQUIRY DISPUTE LETTER - {bureau_name.upper()}
**Dispute Letter by Dr. Lex Grant, Credit Expert**

**Date:** {datetime.now().strftime('%B %d, %Y')}
**Subject:** Dispute of Unauthorized Hard Inquiries

Dear {bureau_name},

I am writing to dispute the following hard inquiries on my credit report as unauthorized:

## DISPUTED INQUIRIES

**No suspicious inquiries detected in the analysis.**

All inquiries appear to be legitimate and authorized. No action required.

Sincerely,
Dr. Lex Grant
Credit Expert
"""
    
    # Generate detailed dispute letter
    letter_content = f"""# HARD INQUIRY DISPUTE LETTER - {bureau_name.upper()}
**Dispute Letter by Dr. Lex Grant, Credit Expert**

**Date:** {datetime.now().strftime('%B %d, %Y')}
**Subject:** DISPUTE OF UNAUTHORIZED HARD INQUIRIES - FCRA §1681b

Dear {bureau_name},

I am writing to dispute the following hard inquiries on my credit report as unauthorized under the Fair Credit Reporting Act (FCRA) §1681b.

## UNAUTHORIZED INQUIRIES DISPUTED

The following inquiries were made without my express written authorization:

"""
    
    for i, inquiry in enumerate(suspicious_inquiries, 1):
        furnisher = inquiry.get('furnisher', 'Unknown')
        date = inquiry.get('date', 'Unknown Date')
        
        letter_content += f"""
**Inquiry {i}:**
- **Furnisher:** {furnisher}
- **Date:** {date}
- **Dispute Reason:** Unauthorized access to credit report
- **FCRA Violation:** §1681b - Permissible purpose required
"""
    
    letter_content += f"""

## LEGAL BASIS FOR DISPUTE

**FCRA §1681b - Permissible Purpose Required:**
A consumer reporting agency may furnish a consumer report only under the following circumstances:
1. In response to a court order
2. In accordance with the written instructions of the consumer
3. To a person which it has reason to believe intends to use the information for a credit transaction
4. For employment purposes with written authorization
5. For insurance purposes with written authorization
6. For government licensing or benefits
7. For legitimate business need in connection with a business transaction

**None of the above conditions apply to the disputed inquiries.**

## SPECIFIC DEMANDS FOR ACTION

1. **IMMEDIATE REMOVAL:** Remove all disputed inquiries from my credit report within 30 days
2. **INVESTIGATION:** Conduct a thorough investigation of each disputed inquiry
3. **DOCUMENTATION:** Provide written confirmation of removal and investigation results
4. **NOTIFICATION:** Notify all furnishers of the disputed inquiries of the removal
5. **PREVENTION:** Implement measures to prevent future unauthorized inquiries

## STATUTORY DAMAGES

Under FCRA §1681n, I am entitled to:
- **Actual damages** for any harm caused by unauthorized inquiries
- **Statutory damages** of $1,000 per violation
- **Punitive damages** for willful non-compliance
- **Attorney's fees** and court costs

**Total potential damages: ${len(suspicious_inquiries) * 1000:,}**

## TIMELINE FOR COMPLIANCE

You have **30 days** from receipt of this letter to:
1. Remove all disputed inquiries
2. Provide written confirmation of removal
3. Submit updated credit report

## ESCALATION NOTICE

Failure to comply within 30 days will result in:
- **CFPB complaint** filing
- **State Attorney General** complaint  
- **Federal litigation** under FCRA §1681n
- **Maximum statutory damages** claim

## CERTIFICATION

I certify that:
- I did not authorize any of the disputed inquiries
- I did not apply for credit with any of the furnishers listed
- I did not provide written authorization for credit checks
- All information in this dispute is accurate and complete

## CONTACT INFORMATION

**Dr. Lex Grant**
Credit Expert
[YOUR ADDRESS]
[YOUR PHONE]
[YOUR EMAIL]

**SEND ALL CORRESPONDENCE TO THE ABOVE ADDRESS**

---

**This dispute is filed under FCRA §1681i and must be investigated within 30 days.**

Sincerely,

Dr. Lex Grant
Credit Expert

**CC:** Consumer Financial Protection Bureau (CFPB)
**CC:** State Attorney General
**CC:** Federal Trade Commission (FTC)
"""
    
    return letter_content


def analyze_inquiry_patterns(inquiries_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze inquiry patterns for potential violations.
    
    Args:
        inquiries_data: List of inquiry dictionaries
    
    Returns:
        Analysis results with violation indicators
    """
    analysis = {
        'total_inquiries': len(inquiries_data),
        'suspicious_inquiries': [],
        'violations': [],
        'risk_score': 0
    }
    
    # Check for multiple inquiries from same furnisher
    furnisher_counts = {}
    for inquiry in inquiries_data:
        furnisher = inquiry.get('furnisher', 'Unknown')
        furnisher_counts[furnisher] = furnisher_counts.get(furnisher, 0) + 1
    
    # Flag multiple inquiries from same source
    for furnisher, count in furnisher_counts.items():
        if count > 1:
            analysis['violations'].append(f"Multiple inquiries from {furnisher} ({count} times)")
            analysis['risk_score'] += 10
    
    # Check for suspicious furnishers
    suspicious_keywords = [
        'collection', 'debt', 'credit repair', 'credit counseling',
        'loan', 'mortgage', 'auto', 'student', 'personal loan'
    ]
    
    for inquiry in inquiries_data:
        furnisher = inquiry.get('furnisher', '').lower()
        if any(keyword in furnisher for keyword in suspicious_keywords):
            analysis['suspicious_inquiries'].append(inquiry)
            analysis['risk_score'] += 5
    
    # Check for recent inquiry patterns
    recent_inquiries = [inq for inq in inquiries_data if inq.get('date')]
    if len(recent_inquiries) > 5:
        analysis['violations'].append(f"High volume of recent inquiries ({len(recent_inquiries)})")
        analysis['risk_score'] += 15
    
    return analysis


def save_inquiry_analysis(inquiries_data: List[Dict[str, Any]], bureau_name: str, output_file: str = None):
    """Save inquiry analysis and generate dispute letter.
    
    Args:
        inquiries_data: List of inquiry dictionaries
        bureau_name: Name of the credit bureau
        output_file: Optional output file path
    """
    # Analyze patterns
    analysis = analyze_inquiry_patterns(inquiries_data)
    
    # Generate dispute letter
    dispute_letter = generate_hard_inquiry_dispute_letter(inquiries_data, bureau_name)
    
    # Prepare output data
    output_data = {
        'bureau': bureau_name,
        'analysis_date': datetime.now().isoformat(),
        'inquiry_analysis': analysis,
        'dispute_letter': dispute_letter,
        'total_inquiries': len(inquiries_data),
        'suspicious_count': len(analysis['suspicious_inquiries']),
        'risk_score': analysis['risk_score']
    }
    
    # Save to file
    if output_file is None:
        output_file = f"inquiry_analysis_{bureau_name.lower()}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Save dispute letter separately
    letter_file = f"inquiry_dispute_{bureau_name.lower()}.md"
    with open(letter_file, 'w', encoding='utf-8') as f:
        f.write(dispute_letter)
    
    return output_file, letter_file
