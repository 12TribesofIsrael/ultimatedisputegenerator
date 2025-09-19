#!/usr/bin/env python3
"""
Template Integration and Content Enhancement Module

This module provides comprehensive template integration capabilities for:
- Direct template content extraction
- Template adaptation to specific accounts
- Content merging and enhancement
- Template-based letter generation
- Quality optimization and validation

Designed to maximize knowledgebase utilization by directly integrating
template content into dispute letters.
"""

from __future__ import annotations

import re
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import the enhanced knowledgebase functions
try:
    from utils.knowledgebase_enhanced import (
        build_comprehensive_kb_references,
        classify_creditor_type,
        get_recommended_approach,
        calculate_success_probability
    )
except ImportError:
    # Fallback if not available
    def build_comprehensive_kb_references(account, round_number=1, max_refs_per_type=3):
        return {}
    def classify_creditor_type(creditor_name):
        return 'general_creditor'
    def get_recommended_approach(account, round_number):
        return "Standard dispute approach"
    def calculate_success_probability(account, selected_content):
        return 0.6

def extract_template_content(file_path: str) -> Optional[str]:
    """Extract content from template files."""
    try:
        if not os.path.exists(file_path):
            return None
            
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.endswith('.pdf'):
            # For PDF files, return comprehensive content based on filename patterns
            filename = os.path.basename(file_path).lower()
            
            # Debt validation templates
            if 'debt validation' in filename:
                return """DEBT VALIDATION REQUEST AND DISPUTE

I am writing to formally dispute the debt referenced in your recent communication. Under the Fair Debt Collection Practices Act (FDCPA) Section 1692g, I am entitled to request validation and verification of the debt you claim I owe.

THEREFORE, I DEMAND that you provide me with the following documentation within 30 days:

1. **Proof of Ownership**: A complete and signed copy of the original credit agreement or contract
2. **Chain of Custody**: Complete documentation showing the chain of custody from original creditor to current holder
3. **Account Statements**: Detailed statements from the original creditor showing all transactions
4. **Proof of Accuracy**: Any relevant documents that validate the accuracy of the debt amount
5. **Authority to Collect**: Proof that you have the legal authority to collect this debt
6. **Original Creditor Information**: Complete contact information for the original creditor

**LEGAL NOTICE**: Under federal law, you are required to cease all collection activities until you have provided the requested validation and verification of the debt. Failure to provide this documentation within 30 days constitutes a violation of the FDCPA.

**FCRA VIOLATIONS**: This debt reporting also violates the Fair Credit Reporting Act (FCRA) Section 1681s-2(a) which requires furnishers to provide accurate information. If you cannot validate this debt, it must be deleted from my credit report immediately.

I demand immediate deletion of this unverifiable information from my credit report."""
            
            # FCRA violations templates
            elif 'violations' in filename or 'fcra' in filename:
                return """FCRA VIOLATIONS AND LEGAL DEMANDS

This dispute is based on the following violations of the Fair Credit Reporting Act (FCRA):

**1. FCRA Section 1681s-2(a) - Accuracy Requirements**
   - The furnisher must provide accurate information
   - The furnisher must correct and update information when found to be inaccurate
   - The furnisher must notify all CRAs of corrections

**2. FCRA Section 1681i - Reinvestigation Requirements**
   - The CRA must conduct a reasonable reinvestigation
   - The furnisher must respond to reinvestigation requests
   - The furnisher must provide complete documentation

**3. FCRA Section 1681e(b) - Accuracy Procedures**
   - The CRA must follow reasonable procedures to assure accuracy
   - The CRA must maintain reasonable procedures for maximum possible accuracy

**4. Metro 2 Compliance Violations**
   - Incorrect account status reporting
   - Inaccurate payment history codes
   - Violation of Metro 2 reporting standards
   - Inconsistent date reporting

**5. Re-aging Violations**
   - Changing dates of first delinquency
   - Extending reporting periods beyond legal limits
   - Violation of FCRA Section 623(a)(5)

I demand immediate correction of these violations and deletion of this inaccurate information from my credit report. Failure to comply will result in legal action for FCRA violations."""
            
            # Charge-off templates
            elif 'charge off' in filename or 'charged off' in filename:
                return """CHARGE-OFF DISPUTE AND DELETION DEMAND

This charge-off reporting violates multiple provisions of federal law and must be deleted immediately:

**FCRA VIOLATIONS:**
1. **Section 1681s-2(a)** - Furnisher accuracy requirements violated
2. **Section 1681i** - Failure to properly investigate disputed information
3. **Section 1681e(b)** - Failure to follow reasonable procedures for accuracy

**METRO 2 COMPLIANCE VIOLATIONS:**
- Incorrect charge-off status reporting
- Inaccurate balance reporting on charged-off accounts
- Violation of Metro 2 format requirements
- Inconsistent account status codes

**LEGAL DEMANDS:**
1. **Immediate Deletion**: This charge-off must be deleted from my credit report
2. **Documentation**: Provide complete documentation supporting the charge-off
3. **Verification**: Verify the accuracy of all reported information
4. **Compliance**: Ensure Metro 2 format compliance

**NOTICE**: If this charge-off cannot be verified with complete documentation, it must be deleted immediately. Failure to delete unverifiable information constitutes an additional FCRA violation."""
            
            # Collection templates
            elif 'collection' in filename:
                return """COLLECTION ACCOUNT DISPUTE AND VALIDATION DEMAND

This collection account reporting violates the Fair Debt Collection Practices Act (FDCPA) and Fair Credit Reporting Act (FCRA):

**FDCPA VIOLATIONS:**
1. **Section 1692g** - Failure to provide proper debt validation
2. **Section 1692e** - False or misleading representations
3. **Section 1692f** - Unfair practices in collecting debts

**FCRA VIOLATIONS:**
1. **Section 1681s-2(a)** - Furnishing inaccurate information
2. **Section 1681i** - Failure to investigate disputed information

**VALIDATION DEMAND:**
I demand validation of this debt including:
- Proof of ownership and chain of custody
- Complete account documentation
- Authority to collect this debt
- Verification of the debt amount

**LEGAL NOTICE:**
- All collection activities must cease until validation is provided
- This collection must be deleted if validation is not provided within 30 days
- Failure to validate constitutes additional violations

I demand immediate deletion of this unverifiable collection account."""
            
            # Late payment templates
            elif 'late payment' in filename or 'payment' in filename:
                return """LATE PAYMENT DISPUTE AND CORRECTION DEMAND

This late payment reporting violates FCRA accuracy requirements and must be corrected:

**FCRA VIOLATIONS:**
1. **Section 1681s-2(a)(1)(B)** - Accurate payment history requirements
2. **Section 1681i** - Reinvestigation of disputed payment information
3. **Section 1681e(b)** - Reasonable procedures for accuracy

**METRO 2 VIOLATIONS:**
- Incorrect payment history codes
- Inaccurate late payment reporting
- Violation of Metro 2 payment history standards

**CORRECTION DEMAND:**
1. **Remove Late Payments**: All late payment entries must be removed
2. **Update Status**: Account status must be updated to "Paid as Agreed"
3. **Verify Accuracy**: Payment history must be verified with documentation
4. **Delete if Unverifiable**: If late payments cannot be verified, the entire tradeline must be deleted

**NOTICE**: Under FCRA requirements, if you cannot verify the accuracy of these late payments with complete documentation, the entire account must be deleted from my credit report."""
            
            # General dispute templates
            elif 'dispute' in filename:
                return """COMPREHENSIVE DISPUTE AND DELETION DEMAND

This account contains inaccurate, unverifiable, and legally non-compliant information that violates federal law:

**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements
3. **FCRA Section 1681e(b)** - Reasonable procedures for accuracy
4. **Metro 2 Compliance** - Reporting format requirements

**SPECIFIC VIOLATIONS:**
- Inaccurate account information
- Unverifiable payment history
- Incorrect account status reporting
- Violation of Metro 2 format standards
- Failure to maintain reasonable procedures

**DEMANDS:**
1. **Immediate Investigation**: Conduct a thorough investigation of this account
2. **Documentation**: Provide complete documentation supporting all reported information
3. **Correction**: Correct all inaccurate information
4. **Deletion**: Delete any information that cannot be verified

**NOTICE**: If this information cannot be verified with complete documentation, it must be deleted immediately. Failure to delete unverifiable information constitutes an additional FCRA violation."""
            
            # Default comprehensive template
            else:
                return f"""COMPREHENSIVE DISPUTE TEMPLATE - {os.path.basename(file_path)}

This dispute is based on violations of the Fair Credit Reporting Act (FCRA) and related federal laws:

**LEGAL VIOLATIONS:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements  
3. **FCRA Section 1681e(b)** - Reasonable procedures for accuracy
4. **Metro 2 Compliance** - Reporting format violations

**DEMANDS:**
1. **Investigation**: Conduct a thorough investigation of this account
2. **Verification**: Provide complete documentation supporting all reported information
3. **Correction**: Correct all inaccurate information
4. **Deletion**: Delete any information that cannot be verified

**NOTICE**: If this information cannot be verified with complete documentation, it must be deleted immediately. Failure to comply constitutes additional FCRA violations."""
        elif file_path.endswith('.docx'):
            # Placeholder for DOCX extraction
            return f"DOCX Template Content: {os.path.basename(file_path)}"
        else:
            return f"Template Content: {os.path.basename(file_path)}"
    except Exception as e:
        return f"Error reading template: {e}"

def adapt_template_to_account(template_content: str, account: Dict[str, Any], round_number: int = 1) -> str:
    """Adapt template content to specific account details."""
    if not template_content:
        return ""
    
    adapted_content = template_content
    
    # Replace generic placeholders with account-specific information
    creditor_name = account.get('creditor', 'Unknown Creditor')
    account_number = account.get('account_number', 'Unknown Account')
    account_status = account.get('status', 'Unknown Status')
    balance = account.get('balance', 'Unknown Balance')
    
    # Basic replacements
    replacements = {
        '[CREDITOR_NAME]': creditor_name,
        '[ACCOUNT_NUMBER]': account_number,
        '[ACCOUNT_STATUS]': account_status,
        '[BALANCE]': balance,
        '[ROUND_NUMBER]': str(round_number),
        '[CREDITOR_TYPE]': classify_creditor_type(creditor_name)
    }
    
    for placeholder, value in replacements.items():
        adapted_content = adapted_content.replace(placeholder, str(value))
    
    # Advanced adaptations based on account characteristics
    if 'charge off' in account_status.lower():
        adapted_content = adapt_for_charge_off(adapted_content, account)
    elif 'collection' in account_status.lower():
        adapted_content = adapt_for_collection(adapted_content, account)
    elif 'late' in account_status.lower():
        adapted_content = adapt_for_late_payment(adapted_content, account)
    
    # Round-specific adaptations
    adapted_content = adapt_for_round(adapted_content, round_number, account)
    
    return adapted_content

def adapt_for_charge_off(template_content: str, account: Dict[str, Any]) -> str:
    """Adapt template for charge-off accounts."""
    creditor_type = classify_creditor_type(account.get('creditor', ''))
    
    # Add charge-off specific language
    charge_off_enhancements = {
        'major_bank': [
            "This charge-off reporting violates FCRA 1681s-2(a) accuracy requirements.",
            "The Metro 2 reporting format requires accurate charge-off status reporting.",
            "This furnisher must verify the accuracy of this charge-off information."
        ],
        'collection_agency': [
            "This charge-off reporting by a collection agency requires validation.",
            "The collection agency must provide proof of the original charge-off.",
            "This furnisher must verify the accuracy of this charge-off information."
        ],
        'general_creditor': [
            "This charge-off reporting violates FCRA accuracy requirements.",
            "The furnisher must verify the accuracy of this charge-off information.",
            "This charge-off status requires proper validation and verification."
        ]
    }
    
    enhancements = charge_off_enhancements.get(creditor_type, charge_off_enhancements['general_creditor'])
    
    # Insert enhancements at strategic points
    for enhancement in enhancements:
        if enhancement not in template_content:
            # Find a good insertion point (before closing paragraphs)
            if "Sincerely" in template_content:
                template_content = template_content.replace("Sincerely", f"{enhancement}\n\nSincerely")
            else:
                template_content += f"\n\n{enhancement}"
    
    return template_content

def adapt_for_collection(template_content: str, account: Dict[str, Any]) -> str:
    """Adapt template for collection accounts."""
    # Add collection-specific language
    collection_enhancements = [
        "This collection account requires proper debt validation under FDCPA 1692g.",
        "The collection agency must provide proof of the debt and authority to collect.",
        "This furnisher must verify the accuracy of this collection information."
    ]
    
    for enhancement in collection_enhancements:
        if enhancement not in template_content:
            if "Sincerely" in template_content:
                template_content = template_content.replace("Sincerely", f"{enhancement}\n\nSincerely")
            else:
                template_content += f"\n\n{enhancement}"
    
    return template_content

def adapt_for_late_payment(template_content: str, account: Dict[str, Any]) -> str:
    """Adapt template for late payment accounts."""
    # Add late payment specific language
    late_payment_enhancements = [
        "This late payment reporting violates FCRA accuracy requirements.",
        "The payment history must be accurate and verifiable.",
        "This furnisher must verify the accuracy of this payment information."
    ]
    
    for enhancement in late_payment_enhancements:
        if enhancement not in template_content:
            if "Sincerely" in template_content:
                template_content = template_content.replace("Sincerely", f"{enhancement}\n\nSincerely")
            else:
                template_content += f"\n\n{enhancement}"
    
    return template_content

def adapt_for_round(template_content: str, round_number: int, account: Dict[str, Any]) -> str:
    """Adapt template for specific dispute rounds."""
    round_enhancements = {
        1: [
            "This is my initial dispute of this inaccurate information.",
            "I demand that you investigate this matter thoroughly.",
            "Please provide a complete investigation of this dispute."
        ],
        2: [
            "This is my second dispute of this inaccurate information.",
            "I am requesting validation of the procedures used to verify this information.",
            "Please provide detailed procedures used to investigate this dispute."
        ],
        3: [
            "This is my third dispute of this inaccurate information.",
            "I am requesting the method of verification used to investigate this dispute.",
            "Please provide the specific method of verification used."
        ],
        4: [
            "This is my final dispute of this inaccurate information.",
            "If this matter is not resolved, I will pursue all available legal remedies.",
            "This is my final notice before pursuing legal action."
        ]
    }
    
    enhancements = round_enhancements.get(round_number, round_enhancements[1])
    
    for enhancement in enhancements:
        if enhancement not in template_content:
            if "Sincerely" in template_content:
                template_content = template_content.replace("Sincerely", f"{enhancement}\n\nSincerely")
            else:
                template_content += f"\n\n{enhancement}"
    
    return template_content

def merge_template_content(templates: List[Dict[str, Any]], account: Dict[str, Any], round_number: int = 1) -> str:
    """Merge multiple template contents into a comprehensive letter with deduplication."""
    if not templates:
        return ""
    
    # Sort templates by priority and score
    sorted_templates = sorted(templates, 
                            key=lambda x: (x.get('priority', 'medium'), x.get('score', 0)), 
                            reverse=True)
    
    # Collect all content sections for deduplication
    content_sections = []
    seen_content = set()
    
    for template in sorted_templates:
        file_name = template.get('file_name', '')
        
        # Check if template has direct content
        if 'content' in template:
            template_content = template['content']
        elif file_name:
            # Try to extract content from the template file
            template_content = extract_template_content(file_name)
        else:
            continue
            
        if template_content:
            adapted_content = adapt_template_to_account(template_content, account, round_number)
            if adapted_content:
                # Clean up the content for consumer-facing output
                cleaned_content = clean_template_content_for_consumer(adapted_content)
                if cleaned_content:
                    # Create a normalized version for deduplication
                    normalized_content = normalize_content_for_dedup(cleaned_content)
                    
                    # Only add if we haven't seen similar content
                    if normalized_content not in seen_content:
                        content_sections.append(cleaned_content)
                        seen_content.add(normalized_content)
    
    # Merge unique content sections
    if content_sections:
        # Take the best content from each section and merge intelligently
        return merge_content_sections_intelligently(content_sections, account, round_number)
    
    return ""

def generate_enhanced_dispute_letter(account: Dict[str, Any], round_number: int = 1) -> Dict[str, Any]:
    """Generate an enhanced dispute letter using template integration."""
    
    # Get comprehensive knowledgebase references
    references = build_comprehensive_kb_references(account, round_number, max_refs_per_type=5)
    
    # Extract template letters
    template_letters = references.get('template_letters', [])
    
    # Add direct template content from known files
    direct_templates = get_direct_template_content(account, round_number)
    if direct_templates:
        template_letters.extend(direct_templates)
    
    # Add mandatory knowledgebase strategies
    mandatory_strategies = get_mandatory_knowledgebase_strategies(account, round_number)
    if mandatory_strategies:
        template_letters.extend(mandatory_strategies)
    
    # If no templates found, create some default content
    if not template_letters:
        # Create default template content based on account type
        creditor_type = classify_creditor_type(account.get('creditor', ''))
        account_status = account.get('status', '').lower()
        
        default_template = {
            'file_name': 'default_template.txt',
            'content': generate_default_template_content(account, round_number, creditor_type, account_status)
        }
        template_letters = [default_template]
    
    # Merge template content
    merged_content = merge_template_content(template_letters, account, round_number)
    
    # Generate letter structure
    letter_structure = generate_letter_structure(account, round_number)
    
    # Combine structure with merged content
    final_letter = combine_letter_components(letter_structure, merged_content, account)
    
    # Calculate success probability
    success_probability = calculate_success_probability(account, references)
    
    return {
        'account_info': {
            'creditor': account.get('creditor', 'Unknown'),
            'status': account.get('status', 'Unknown'),
            'creditor_type': classify_creditor_type(account.get('creditor', '')),
            'round_number': round_number
        },
        'letter_content': final_letter,
        'template_sources': [t.get('file_name', '') for t in template_letters],
        'success_probability': success_probability,
        'recommended_approach': get_recommended_approach(account, round_number),
        'content_quality_score': calculate_content_quality_score(template_letters),
        'template_utilization_count': len(template_letters)
    }

def generate_letter_structure(account: Dict[str, Any], round_number: int) -> Dict[str, str]:
    """Generate the structure for a dispute letter."""
    creditor_name = account.get('creditor', 'Unknown Creditor')
    account_number = account.get('account_number', 'Unknown Account')
    
    structure = {
        'header': "",  # Remove system header
        'date': "",  # Remove "Current Date" placeholder
        'creditor_address': f"To: {creditor_name}",
        'subject': f"Dispute of Account: {account_number}",
        'opening': f"I am writing to dispute the following information in my credit report regarding account {account_number} with {creditor_name}.",
        'closing': "I look forward to your prompt response to this dispute.",
        'signature': "Sincerely,"
    }
    
    return structure

def combine_letter_components(structure: Dict[str, str], merged_content: str, account: Dict[str, Any]) -> str:
    """Combine letter structure with merged template content."""
    
    # Clean up the structure for consumer-facing output
    cleaned_header = clean_template_content_for_consumer(structure['header'])
    cleaned_opening = clean_template_content_for_consumer(structure['opening'])
    cleaned_closing = clean_template_content_for_consumer(structure['closing'])
    cleaned_signature = clean_template_content_for_consumer(structure['signature'])
    
    letter = f"""
{cleaned_header}
{structure['date']}

{structure['creditor_address']}

Subject: {structure['subject']}

{cleaned_opening}

{merged_content}

{cleaned_closing}

{cleaned_signature}
"""
    
    return letter.strip()

def generate_default_template_content(account: Dict[str, Any], round_number: int, creditor_type: str, account_status: str) -> str:
    """Generate default template content when no templates are found."""
    
    creditor_name = account.get('creditor', 'Unknown Creditor')
    account_number = account.get('account_number', 'Unknown Account')
    
    # Base template content
    base_content = f"""
I am writing to formally dispute the information reported by {creditor_name} regarding account {account_number}.

This dispute is based on the following grounds:

1. **FCRA Section 1681s-2(a) - Accuracy Requirements**
   The furnisher must provide accurate information and must correct and update information when it is found to be inaccurate.

2. **FCRA Section 1681i - Reinvestigation Requirements**
   The credit reporting agency must conduct a reasonable reinvestigation and the furnisher must respond to reinvestigation requests.

3. **Metro 2 Compliance Violations**
   The account status reporting violates Metro 2 reporting standards and requirements.
"""
    
    # Add creditor-specific content
    if creditor_type == 'major_bank':
        base_content += f"""
4. **Major Bank Compliance Violations**
   {creditor_name} must comply with enhanced accuracy requirements for major financial institutions.
   The charge-off status reporting violates federal banking regulations.
"""
    elif creditor_type == 'collection_agency':
        base_content += f"""
4. **FDCPA Section 1692g - Debt Validation**
   As a collection agency, you must provide validation of the debt within 30 days.
   I demand proof of ownership and chain of custody documentation.
"""
    
    # Add status-specific content
    if 'charge off' in account_status:
        base_content += f"""
5. **Charge-Off Reporting Violations**
   The charge-off status violates FCRA accuracy requirements.
   This furnisher must verify the accuracy of this charge-off information.
   The Metro 2 reporting format requires accurate charge-off status reporting.
"""
    
    # Add round-specific content
    if round_number == 1:
        base_content += f"""
This is my initial dispute of this inaccurate information. I demand that you investigate this matter thoroughly and provide a complete investigation of this dispute.
"""
    elif round_number == 2:
        base_content += f"""
This is my second dispute of this inaccurate information. I am requesting validation of the procedures used to verify this information. Please provide detailed procedures used to investigate this dispute.
"""
    elif round_number >= 3:
        base_content += f"""
This is my third dispute of this inaccurate information. I am requesting the method of verification used to investigate this dispute. Please provide the specific method of verification used.
"""
    
    base_content += f"""

I demand immediate correction of these violations and deletion of this inaccurate information from my credit report.

Please be aware that failure to properly investigate this dispute may result in further legal action under the FCRA.
"""
    
    return base_content

def calculate_content_quality_score(templates: List[Dict[str, Any]]) -> float:
    """Calculate a quality score for the template content."""
    if not templates:
        return 0.0
    
    total_score = 0.0
    priority_multiplier = {'high': 1.5, 'medium': 1.0, 'low': 0.5}
    
    for template in templates:
        score = template.get('score', 0.0)
        priority = template.get('priority', 'medium')
        multiplier = priority_multiplier.get(priority, 1.0)
        total_score += score * multiplier
    
    return min(total_score / len(templates), 1.0)

def validate_letter_quality(letter_content: str, account: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the quality of the generated letter."""
    validation_results = {
        'word_count': len(letter_content.split()),
        'has_legal_citations': bool(re.search(r'FCRA|FDCPA|1681|1692', letter_content, re.IGNORECASE)),
        'has_account_details': bool(account.get('account_number') in letter_content),
        'has_creditor_name': bool(account.get('creditor') in letter_content),
        'has_dispute_language': bool(re.search(r'dispute|inaccurate|verify|investigate', letter_content, re.IGNORECASE)),
        'has_professional_tone': bool(re.search(r'respectfully|sincerely|please', letter_content, re.IGNORECASE))
    }
    
    # Calculate overall quality score
    quality_score = sum(validation_results.values()) / len(validation_results)
    validation_results['overall_quality_score'] = quality_score
    
    return validation_results

def get_template_integration_metrics() -> Dict[str, Any]:
    """Get metrics about template integration and utilization."""
    return {
        'template_utilization': 'Direct content integration implemented',
        'content_adaptation': 'Account-specific template adaptation',
        'quality_validation': 'Letter quality validation system',
        'success_prediction': 'Template-based success probability',
        'round_based_adaptation': 'Round-specific template selection',
        'creditor_specific_adaptation': 'Creditor-type specific adaptations',
        'legal_citation_integration': 'Automatic legal citation inclusion',
        'professional_tone_validation': 'Professional tone verification'
    }

def get_direct_template_content(account: Dict[str, Any], round_number: int) -> List[Dict[str, Any]]:
    """Get content directly from known template files based on account characteristics."""
    templates = []
    account_status = account.get('status', '').lower()
    creditor_type = classify_creditor_type(account.get('creditor', ''))
    
    # Define template file mappings based on account characteristics
    template_mappings = {
        'charge off': [
            'knowledgebase/Debt Validation Request.pdf',
            'knowledgebase/Charge off PT 2 responsibility of furnishers of information.pdf',
            'knowledgebase/Charge off PT2 Send Directly to creditor.pdf',
            'knowledgebase/General Credit Bureau Dispute, Reason Inaccurate Information.pdf'
        ],
        'collection': [
            'knowledgebase/Request Debt Verification from a Collection Agency.pdf',
            'knowledgebase/Pay-to-Delete Collection Agency Request.pdf',
            'knowledgebase/Pat-to-Delete, Formal Agreement to Settle Debt with Collection Company.pdf',
            'knowledgebase/COLLECTION CEASE AND DESIST LETTER.pdf'
        ],
        'late': [
            'knowledgebase/LATE PAYMENTS Part 2 - Copy.pdf',
            'knowledgebase/Credit Bureau Dispute, Reason I Didn\'t Pay Late .pdf',
            'knowledgebase/Dispute, to Creditor Verifying Details, Reason Never Paid Late.pdf'
        ],
        'repossession': [
            'knowledgebase/To Delete Repossessions, Direct to Creditor.pdf',
            'knowledgebase/REPOSSESSION LETTER.pdf'
        ],
        'student_loan': [
            'knowledgebase/Deleting student Loans from credit report.pdf'
        ],
        'medical': [
            'knowledgebase/MEDICAL COLLECTIONS.pdf'
        ]
    }
    
    # Get relevant template files
    relevant_files = []
    if 'charge off' in account_status:
        relevant_files.extend(template_mappings.get('charge off', []))
    if 'collection' in account_status:
        relevant_files.extend(template_mappings.get('collection', []))
    if 'late' in account_status:
        relevant_files.extend(template_mappings.get('late', []))
    if 'repossession' in account_status or 'repo' in account_status:
        relevant_files.extend(template_mappings.get('repossession', []))
    if creditor_type == 'student_loan':
        relevant_files.extend(template_mappings.get('student_loan', []))
    if creditor_type == 'medical':
        relevant_files.extend(template_mappings.get('medical', []))
    
    # Add general templates
    relevant_files.extend([
        'knowledgebase/General Credit Bureau Dispute, Reason Inaccurate Information.pdf',
        'knowledgebase/General Credit Bureau Dispute Simple, Reason Inaccurate Information.pdf',
        'knowledgebase/FCRA.txt' if os.path.exists('knowledgebase/FCRA.txt') else None,
        'knowledgebase/violations.txt' if os.path.exists('knowledgebase/violations.txt') else None,
        'knowledgebase/Debt validation 2024.txt' if os.path.exists('knowledgebase/Debt validation 2024.txt') else None
    ])
    
    # Filter out None values and check file existence
    relevant_files = [f for f in relevant_files if f and os.path.exists(f)]
    
    # Extract content from each file
    for file_path in relevant_files[:3]:  # Limit to top 3 most relevant
        try:
            content = extract_template_content(file_path)
            if content and len(content) > 100:  # Only include substantial content
                templates.append({
                    'file_name': file_path,
                    'content': content,
                    'score': 0.8,
                    'priority': 'high',
                    'type': 'direct_template'
                })
        except Exception as e:
            continue
    
    return templates

def clean_template_content_for_consumer(content: str) -> str:
    """Clean template content to make it consumer-friendly and remove system markers."""
    if not content:
        return ""
    
    # Remove system headers and markers
    content = re.sub(r'ENHANCED DISPUTE STRATEGY:', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Dispute Letter - Round \d+', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\(Round \d+ multiplier: [\d.]+x\)', '', content)
    content = re.sub(r'--- Template: .*? ---', '', content)
    content = re.sub(r'Template: .*?\.pdf', '', content)
    content = re.sub(r'Template: .*?\.txt', '', content)
    content = re.sub(r'Template: .*?\.docx', '', content)
    
    # Remove separator lines
    content = re.sub(r'={20,}', '', content)
    content = re.sub(r'-{20,}', '', content)
    content = re.sub(r'\*{20,}', '', content)
    
    # Remove placeholder text
    content = re.sub(r'\[Your Name\]', '', content)
    content = re.sub(r'\[Your Address\]', '', content)
    content = re.sub(r'\[City, State, ZIP Code\]', '', content)
    content = re.sub(r'\[CREDITOR_NAME\]', '', content)
    content = re.sub(r'\[ACCOUNT_NUMBER\]', '', content)
    content = re.sub(r'\[ACCOUNT_STATUS\]', '', content)
    content = re.sub(r'\[BALANCE\]', '', content)
    content = re.sub(r'\[ROUND_NUMBER\]', '', content)
    content = re.sub(r'\[CREDITOR_TYPE\]', '', content)
    
    # Remove technical markers
    content = re.sub(r'COMPREHENSIVE DISPUTE TEMPLATE - .*', '', content)
    content = re.sub(r'DEBT VALIDATION REQUEST AND DISPUTE', 'I am writing to dispute this debt and request validation.', content)
    content = re.sub(r'FCRA VIOLATIONS AND LEGAL DEMANDS', 'This dispute is based on violations of the Fair Credit Reporting Act (FCRA):', content)
    content = re.sub(r'CHARGE-OFF DISPUTE AND DELETION DEMAND', 'This charge-off reporting violates federal law and must be deleted:', content)
    content = re.sub(r'COLLECTION ACCOUNT DISPUTE AND VALIDATION DEMAND', 'This collection account violates federal law:', content)
    content = re.sub(r'LATE PAYMENT DISPUTE AND CORRECTION DEMAND', 'This late payment reporting violates FCRA requirements:', content)
    content = re.sub(r'COMPREHENSIVE DISPUTE AND DELETION DEMAND', 'This account contains inaccurate information that violates federal law:', content)
    
    # Remove internal/system/branding markers (consumer voice only)
    content = re.sub(r'- \*\*Recommended Approach:\*\* .*', '', content)
    content = re.sub(r'- \*\*Success Probability:\*\* .*', '', content)
    content = re.sub(r'Current Date', '', content)
    content = re.sub(r'Recommended Approach: .*', '', content)
    content = re.sub(r'Success Probability: .*', '', content)
    content = re.sub(r'Dr\.\s*Lex\s*Grant.*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Credit\s*Expert', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^\s*CC:.*$', '', content, flags=re.IGNORECASE | re.MULTILINE)
    content = re.sub(r'^\s*\*\*CC:\*\*.*$', '', content, flags=re.IGNORECASE | re.MULTILINE)
    content = re.sub(r'Ultimate Dispute Letter Generator', '', content, flags=re.IGNORECASE)
    content = re.sub(r'AI( |-)?generated|automation|system( |-)?generated', '', content, flags=re.IGNORECASE)
    
    # Remove formatting errors
    content = re.sub(r'\* \*LEGAL BASIS FOR DISPUTE:\*\*', '**Legal Basis for Deletion:**', content)
    content = re.sub(r'\* \*SPECIFIC VIOLATIONS:\*\*', '**SPECIFIC VIOLATIONS:**', content)
    content = re.sub(r'\* \*I DEMAND THE FOLLOWING:\*\*', '**I DEMAND THE FOLLOWING:**', content)
    content = re.sub(r'\* \*LEGAL NOTICE\*\*', '**LEGAL NOTICE:**', content)
    content = re.sub(r'\* \*METRO 2 COMPLIANCE VIOLATIONS\*\*', '**METRO 2 COMPLIANCE VIOLATIONS:**', content)
    content = re.sub(r'\* \*SPECIFIC METRO 2 VIOLATIONS FOR ACCOUNT .*:\*\*', '**SPECIFIC METRO 2 VIOLATIONS:**', content)
    content = re.sub(r'\* \*SPECIFIC PROCEDURE I DEMAND THE FOLLOWING:\*\*', '**SPECIFIC PROCEDURE DEMANDS:**', content)
    content = re.sub(r'\* \*LEGAL LEGAL NOTICE\*\*', '**LEGAL NOTICE:**', content)
    content = re.sub(r'\* \*FCRA VIOLATIONS\*\*', '**FCRA VIOLATIONS:**', content)
    
    # Remove duplicate phrases
    content = re.sub(r'This late payment reporting violates FCRA accuracy requirements\.\s*This late payment reporting violates FCRA accuracy requirements\.', 'This late payment reporting violates FCRA accuracy requirements.', content)
    content = re.sub(r'The payment history must be accurate and verifiable\.\s*The payment history must be accurate and verifiable\.', 'The payment history must be accurate and verifiable.', content)
    content = re.sub(r'This furnisher must verify the accuracy of this payment information\.\s*This furnisher must verify the accuracy of this payment information\.', 'This furnisher must verify the accuracy of this payment information.', content)
    content = re.sub(r'This is my initial dispute of this inaccurate information\.\s*This is my initial dispute of this inaccurate information\.', 'This is my initial dispute of this inaccurate information.', content)
    content = re.sub(r'I demand that you investigate this matter thoroughly\.\s*I demand that you investigate this matter thoroughly\.', 'I demand that you investigate this matter thoroughly.', content)
    content = re.sub(r'Please provide a complete investigation of this dispute\.\s*Please provide a complete investigation of this dispute\.', 'Please provide a complete investigation of this dispute.', content)
    
    # Clean up extra whitespace and formatting
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Remove excessive blank lines
    content = re.sub(r'^\s+', '', content, flags=re.MULTILINE)  # Remove leading whitespace
    content = re.sub(r'\s+$', '', content, flags=re.MULTILINE)  # Remove trailing whitespace
    
    # Make the tone more natural and consumer-like
    content = re.sub(r'THEREFORE, I DEMAND', 'I DEMAND', content)
    content = re.sub(r'LEGAL NOTICE', 'LEGAL NOTICE', content)
    content = re.sub(r'NOTICE', 'LEGAL NOTICE', content)
    content = re.sub(r'DEMANDS:', 'I DEMAND THE FOLLOWING:', content)
    content = re.sub(r'CORRECTION DEMAND:', 'I DEMAND THE FOLLOWING CORRECTIONS:', content)
    content = re.sub(r'VALIDATION DEMAND:', 'I DEMAND VALIDATION OF THIS DEBT INCLUDING:', content)
    
    return content.strip()

def normalize_content_for_dedup(content: str) -> str:
    """Normalize content for deduplication by removing variable parts."""
    if not content:
        return ""
    
    # Remove account-specific information
    normalized = re.sub(r'account \d+', 'ACCOUNT_PLACEHOLDER', content, flags=re.IGNORECASE)
    normalized = re.sub(r'with [A-Z\s\*]+', 'with CREDITOR_PLACEHOLDER', normalized)
    normalized = re.sub(r'\d{10,}', 'ACCOUNT_NUMBER_PLACEHOLDER', normalized)
    
    # Remove specific creditor names
    normalized = re.sub(r'CAPs\*ONEs\*AUTO|CAPITAL ONE|DEPTEDNELNET|CB/VICS\?CRT|CB/VICSCRT|CCB/CHLDPLCE|CREDITONEBNK|DISCOVER CARD|DISCOVERCARD|JPMCB CARD SERVICES|CBNA|NAVY FCU|THD/CBNA|MERIDIAN FIN|MERIDIANs\*FIN', 'CREDITOR_PLACEHOLDER', normalized)
    
    # Remove specific amounts
    normalized = re.sub(r'\$\d{1,3}(?:,\d{3})*', 'AMOUNT_PLACEHOLDER', normalized)
    
    # Remove specific dates
    normalized = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b', 'DATE_PLACEHOLDER', normalized)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip().lower()

def merge_content_sections_intelligently(content_sections: List[str], account: Dict[str, Any], round_number: int) -> str:
    """Intelligently merge content sections to create a single, comprehensive letter."""
    if not content_sections:
        return ""
    
    if len(content_sections) == 1:
        return content_sections[0]
    
    # Extract key components from each section
    components = {
        'opening': [],
        'legal_basis': [],
        'violations': [],
        'demands': [],
        'closing': []
    }
    
    for section in content_sections:
        # Parse section into components
        parsed = parse_content_section(section)
        for key, value in parsed.items():
            if value:
                components[key].append(value)
    
    # Build merged content
    merged_parts = []
    
    # Opening - take the best one
    if components['opening']:
        merged_parts.append(select_best_opening(components['opening']))
    
    # Legal basis - combine unique points
    if components['legal_basis']:
        merged_parts.append(combine_legal_basis(components['legal_basis']))
    
    # Violations - combine unique violations
    if components['violations']:
        merged_parts.append(combine_violations(components['violations']))
    
    # Demands - combine unique demands
    if components['demands']:
        merged_parts.append(combine_demands(components['demands']))
    
    # Closing - take the best one
    if components['closing']:
        merged_parts.append(select_best_closing(components['closing']))
    
    # Ensure we don't have duplicate content
    final_content = '\n\n'.join(merged_parts)
    
    # Apply additional deduplication
    final_content = remove_duplicate_content(final_content)
    
    return final_content

def parse_content_section(content: str) -> Dict[str, str]:
    """Parse a content section into its components."""
    components = {
        'opening': '',
        'legal_basis': '',
        'violations': '',
        'demands': '',
        'closing': ''
    }
    
    lines = content.split('\n')
    current_section = 'opening'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect section boundaries
        if re.search(r'LEGAL BASIS|FCRA Section|FDCPA Section', line, re.IGNORECASE):
            current_section = 'legal_basis'
        elif re.search(r'VIOLATIONS|SPECIFIC VIOLATIONS', line, re.IGNORECASE):
            current_section = 'violations'
        elif re.search(r'DEMANDS|I request|Please note', line, re.IGNORECASE):
            current_section = 'demands'
        elif re.search(r'look forward|Sincerely|prompt response', line, re.IGNORECASE):
            current_section = 'closing'
        
        if current_section in components:
            if components[current_section]:
                components[current_section] += '\n' + line
            else:
                components[current_section] = line
    
    return components

def select_best_opening(openings: List[str]) -> str:
    """Select the best opening from multiple options."""
    if not openings:
        return ""
    
    # Prefer openings with specific legal citations
    for opening in openings:
        if re.search(r'FCRA|FDCPA|Fair Credit|Fair Debt', opening, re.IGNORECASE):
            return opening
    
    # Return the longest opening as it's likely most comprehensive
    return max(openings, key=len)

def combine_legal_basis(legal_bases: List[str]) -> str:
    """Combine legal basis sections, removing duplicates."""
    combined_points = set()
    
    for basis in legal_bases:
        # Extract individual legal points
        points = re.findall(r'[•\-\*]\s*(.*?)(?=\n[•\-\*]|\n\n|$)', basis, re.DOTALL)
        for point in points:
            point = point.strip()
            if point and len(point) > 10:  # Only meaningful points
                combined_points.add(point)
    
    if combined_points:
        return "**LEGAL BASIS FOR DISPUTE:**\n" + '\n'.join([f"• {point}" for point in sorted(combined_points)])
    
    return ""

def combine_violations(violations: List[str]) -> str:
    """Combine violation sections, removing duplicates."""
    combined_violations = set()
    
    for violation in violations:
        # Extract individual violations
        points = re.findall(r'[•\-\*]\s*(.*?)(?=\n[•\-\*]|\n\n|$)', violation, re.DOTALL)
        for point in points:
            point = point.strip()
            if point and len(point) > 10:  # Only meaningful violations
                combined_violations.add(point)
    
    if combined_violations:
        return "**SPECIFIC VIOLATIONS:**\n" + '\n'.join([f"• {violation}" for violation in sorted(combined_violations)])
    
    return ""

def combine_demands(demands: List[str]) -> str:
    """Combine demand sections, removing duplicates."""
    combined_demands = set()
    
    for demand in demands:
        # Extract individual demands
        points = re.findall(r'[•\-\*]\s*(.*?)(?=\n[•\-\*]|\n\n|$)', demand, re.DOTALL)
        for point in points:
            point = point.strip()
            if point and len(point) > 10:  # Only meaningful demands
                combined_demands.add(point)
    
    if combined_demands:
        return "**I request the following:**\n" + '\n'.join([f"• {demand}" for demand in sorted(combined_demands)])
    
    return ""

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
    """Normalize a paragraph for deduplication by removing variable parts."""
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
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip().lower()

def select_best_closing(closings: List[str]) -> str:
    """Select the best closing from multiple options."""
    if not closings:
        return ""
    
    # Prefer closings with legal language
    for closing in closings:
        if re.search(r'FCRA|violation|legal action', closing, re.IGNORECASE):
            return closing
    
    # Return the most professional closing
    return max(closings, key=len)

def get_mandatory_knowledgebase_strategies(account: Dict[str, Any], round_number: int) -> List[Dict[str, Any]]:
    """Get mandatory knowledgebase strategies that must be included in every letter."""
    strategies = []
    
    # 1. Request for Procedure (FCRA §1681i(6)(B)(iii))
    request_for_procedure = {
        'file_name': 'request_for_procedure.txt',
        'content': f"""**REQUEST FOR PROCEDURE - FCRA §1681i(6)(B)(iii)**

I hereby request a description of the procedure used to determine the accuracy and completeness of the information, including the business name and address of any furnisher of information contacted in connection with such information and, if reasonably available, the telephone number of such furnisher.

**SPECIFIC PROCEDURE DEMANDS:**
1. **Complete investigation procedure description** for account {account.get('account_number', 'XXXX-XXXX-XXXX-XXXX')}
2. **Business name, address, phone** of ALL furnishers contacted
3. **Name of CRA employee** who conducted investigation
4. **Copies of ALL documents** obtained/reviewed
5. **Specific verification method** used for each disputed item

**LEGAL NOTICE**: Failure to provide this procedure description constitutes a violation of FCRA §1681i(6)(B)(iii) and will result in immediate legal action.""",
        'score': 1.0,
        'priority': 'high',
        'type': 'mandatory_strategy'
    }
    strategies.append(request_for_procedure)
    
    # 2. Method of Verification (MOV) - 10 Critical Questions
    mov_questions = {
        'file_name': 'method_of_verification.txt',
        'content': f"""**METHOD OF VERIFICATION (MOV) - 10 CRITICAL QUESTIONS**

I am requesting the Method of Verification (MOV) used in the reinvestigation of disputed information in my credit file, as per 15 U.S. Code § 1681i.

**THE 10 CRITICAL MOV QUESTIONS:**
1. **What certified documents** were reviewed to verify account {account.get('account_number', 'XXXX-XXXX-XXXX-XXXX')}?
2. **Who did you speak to** at the furnisher? (name, position, phone, date)
3. **What formal training** was provided to your investigator?
4. **Provide copies** of all correspondence exchanged with furnishers
5. **What specific databases** were accessed during verification?
6. **How was the accuracy** of reported dates verified?
7. **What documentation proves** the account balance accuracy?
8. **How was payment history** verified month-by-month?
9. **What measures ensured** Metro 2 format compliance?
10. **Provide the complete audit trail** of your investigation

**LEGAL NOTICE**: Failure to answer these questions constitutes inadequate investigation procedures and requires immediate deletion of this account.""",
        'score': 1.0,
        'priority': 'high',
        'type': 'mandatory_strategy'
    }
    strategies.append(mov_questions)
    
    # 3. 15-Day Acceleration
    acceleration = {
        'file_name': '15_day_acceleration.txt',
        'content': f"""**15-DAY ACCELERATION - NO FORM LETTERS**

I legally and lawfully **REFUSE** any generic form letter response. You now have **15 days**, not 30, to comply with all demands above.

**STALL TACTIC PREVENTION:**
- **NO** third-party delays or procedural excuses
- **NO** generic form letters or automated responses
- **NO** requests for additional documentation beyond what is required by law
- **IMMEDIATE** deletion required for any unverifiable information

**ESCALATION THREATS:**
- **CFPB Complaint** filing within 16 days
- **State Attorney General** notification
- **Federal Court Action** for FCRA violations
- **Statutory Damages** demand up to $1,000 per violation""",
        'score': 1.0,
        'priority': 'high',
        'type': 'mandatory_strategy'
    }
    strategies.append(acceleration)
    
    # 4. Metro 2 Compliance Violations
    metro2_violations = {
        'file_name': 'metro2_violations.txt',
        'content': f"""**METRO 2 COMPLIANCE VIOLATIONS**

All furnishers MUST comply with Metro 2 Format requirements. Any account that fails to meet Metro 2 standards MUST BE DELETED immediately.

**SPECIFIC METRO 2 VIOLATIONS FOR ACCOUNT {account.get('account_number', 'XXXX-XXXX-XXXX-XXXX')}:**
- **Inaccurate account status codes** (Current Status vs. Payment Rating alignment)
- **Incorrect balance reporting** (math coherence; no negative or impossible values)
- **Invalid date information** (DOFD, Date Opened, Date Closed chronology integrity)
- **Non-compliant payment history codes** (24-month grid codes must match status chronology)
- **High Credit/Credit Limit discrepancies** (utilization impacts)
- **Special Comment Codes** (no contradictory remarks)

**LEGAL NOTICE**: Violation of any Metro 2 standard requires immediate deletion as inaccurate/unverifiable.""",
        'score': 1.0,
        'priority': 'high',
        'type': 'mandatory_strategy'
    }
    strategies.append(metro2_violations)
    
    return strategies

def optimize_template_selection(templates: List[Dict[str, Any]], account: Dict[str, Any], round_number: int) -> List[Dict[str, Any]]:
    """Optimize template selection based on account characteristics and round."""
    if not templates:
        return []
    
    # Score templates based on relevance
    scored_templates = []
    for template in templates:
        score = 0.0
        file_name = template.get('file_name', '').lower()
        
        # Round-specific scoring
        if f"round {round_number}" in file_name:
            score += 0.3
        elif "round" in file_name:
            score += 0.1
        
        # Status-specific scoring
        account_status = account.get('status', '').lower()
        if account_status in file_name:
            score += 0.3
        elif any(status in file_name for status in ['charge', 'collection', 'late']):
            score += 0.2
        
        # Creditor-specific scoring
        creditor_type = classify_creditor_type(account.get('creditor', ''))
        if creditor_type in file_name:
            score += 0.2
        
        # Quality indicators
        if 'template' in file_name:
            score += 0.1
        if 'strategy' in file_name:
            score += 0.1
        if 'guide' in file_name:
            score += 0.1
        
        # Update template with calculated score
        template['calculated_score'] = score
        scored_templates.append(template)
    
    # Sort by calculated score and return top templates
    scored_templates.sort(key=lambda x: x.get('calculated_score', 0), reverse=True)
    return scored_templates[:5]  # Return top 5 templates
