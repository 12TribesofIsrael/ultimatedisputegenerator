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
        return f"""Date: {datetime.now().strftime('%B %d, %Y')}
Subject: Dispute of Hard Inquiries

Dear {bureau_name},

I am writing to review recent hard inquiries on my credit report. No suspicious inquiries were identified at this time. This letter is provided to document my review and intent to monitor my report for accuracy under the Fair Credit Reporting Act (FCRA).

Sincerely,
"""
    
    # Generate detailed dispute letter
    letter_content = f"""Date: {datetime.now().strftime('%B %d, %Y')}
Subject: Dispute of Unauthorized Hard Inquiries (FCRA §1681b)

Dear {bureau_name},

I am writing to dispute the following hard inquiries on my credit report as unauthorized under the Fair Credit Reporting Act (FCRA) §1681b.

Unauthorized inquiries in dispute:
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

Legal basis for dispute (FCRA §1681b - permissible purpose required):
- A consumer reporting agency may furnish a consumer report only for specific, lawful purposes.
- The disputed inquiries were not authorized by me and do not meet the permissible purpose requirements.

Requested actions:
1. Remove all disputed inquiries within 30 days.
2. Provide written confirmation of removal and investigation results.
3. Prevent future unauthorized inquiries.

Certification:
- I did not authorize any of the disputed inquiries.
- I did not apply for credit with the furnishers listed.
- The information provided is accurate and complete to the best of my knowledge.

Sincerely,
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
