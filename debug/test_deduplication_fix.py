#!/usr/bin/env python3
"""
Test script to verify deduplication fixes for repetitive content.

This script tests:
1. Content deduplication in template merging
2. Account deduplication
3. Paragraph deduplication
4. Overall letter quality improvement
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.template_integration import (
    merge_template_content, 
    normalize_content_for_dedup,
    merge_content_sections_intelligently,
    remove_duplicate_content
)
from extract_account_details import deduplicate_accounts, normalize_account_id

def test_content_deduplication():
    """Test content deduplication functionality."""
    print("=== Testing Content Deduplication ===")
    
    # Create test templates with duplicate content
    test_templates = [
        {
            'file_name': 'template1.txt',
            'content': """This account contains inaccurate information that violates federal law:
**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements

**SPECIFIC VIOLATIONS:**
- Inaccurate account information
- Unverifiable payment history""",
            'score': 0.8,
            'priority': 'high'
        },
        {
            'file_name': 'template2.txt',
            'content': """This account contains inaccurate information that violates federal law:
**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements

**SPECIFIC VIOLATIONS:**
- Inaccurate account information
- Unverifiable payment history""",
            'score': 0.7,
            'priority': 'medium'
        },
        {
            'file_name': 'template3.txt',
            'content': """This account contains inaccurate information that violates federal law:
**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements

**SPECIFIC VIOLATIONS:**
- Inaccurate account information
- Unverifiable payment history""",
            'score': 0.6,
            'priority': 'low'
        }
    ]
    
    test_account = {
        'creditor': 'TEST BANK',
        'account_number': '1234567890',
        'status': 'charge off',
        'balance': '$5000'
    }
    
    # Test template merging with deduplication
    merged_content = merge_template_content(test_templates, test_account, 1)
    
    print(f"Original templates: {len(test_templates)}")
    print(f"Merged content length: {len(merged_content)} characters")
    print(f"Content contains duplicates: {'No' if len(merged_content.split('This account contains')) == 1 else 'Yes'}")
    
    # Test content normalization
    normalized1 = normalize_content_for_dedup(test_templates[0]['content'])
    normalized2 = normalize_content_for_dedup(test_templates[1]['content'])
    
    print(f"Normalized content identical: {normalized1 == normalized2}")
    
    return len(merged_content.split('This account contains')) == 1

def test_account_deduplication():
    """Test account deduplication functionality."""
    print("\n=== Testing Account Deduplication ===")
    
    # Create test accounts with duplicates
    test_accounts = [
        {
            'creditor': 'DISCOVER CARD',
            'account_number': '6011011234567890',
            'status': 'charge off',
            'balance': '$4946'
        },
        {
            'creditor': 'DISCOVERCARD',
            'account_number': '6011011234567890',
            'status': 'charge off',
            'balance': '$4946'
        },
        {
            'creditor': 'JPMCB CARD SERVICES',
            'account_number': '4147201234567890',
            'status': 'charge off',
            'balance': '$9666'
        },
        {
            'creditor': 'JPMCB',
            'account_number': '4147201234567890',
            'status': 'charge off',
            'balance': '$9666'
        }
    ]
    
    # Test account deduplication
    unique_accounts = deduplicate_accounts(test_accounts)
    
    print(f"Original accounts: {len(test_accounts)}")
    print(f"Unique accounts: {len(unique_accounts)}")
    print(f"Duplicates removed: {len(test_accounts) - len(unique_accounts)}")
    
    # Test account ID normalization
    id1 = normalize_account_id("DISCOVER CARD_6011011234567890")
    id2 = normalize_account_id("DISCOVERCARD_6011011234567890")
    
    print(f"Normalized IDs identical: {id1 == id2}")
    
    return len(unique_accounts) < len(test_accounts)

def test_paragraph_deduplication():
    """Test paragraph deduplication functionality."""
    print("\n=== Testing Paragraph Deduplication ===")
    
    # Create test content with duplicate paragraphs
    test_content = """
This account contains inaccurate information that violates federal law.

**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements

This account contains inaccurate information that violates federal law.

**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements

**SPECIFIC VIOLATIONS:**
- Inaccurate account information
- Unverifiable payment history
"""
    
    # Test paragraph deduplication
    deduplicated_content = remove_duplicate_content(test_content)
    
    original_paragraphs = len([p for p in test_content.split('\n\n') if p.strip()])
    deduplicated_paragraphs = len([p for p in deduplicated_content.split('\n\n') if p.strip()])
    
    print(f"Original paragraphs: {original_paragraphs}")
    print(f"Deduplicated paragraphs: {deduplicated_paragraphs}")
    print(f"Duplicate paragraphs removed: {original_paragraphs - deduplicated_paragraphs}")
    
    return deduplicated_paragraphs < original_paragraphs

def test_letter_quality_improvement():
    """Test overall letter quality improvement."""
    print("\n=== Testing Letter Quality Improvement ===")
    
    # Simulate the repetitive content from the original letter
    repetitive_content = """
To: CAPs*ONEs*AUTO

Subject: Dispute of Account: 620734XXXXXXXXXXX

I am writing to dispute the following information in my credit report regarding account 620734XXXXXXXXXXX with CAPs*ONEs*AUTO.

This account contains inaccurate information that violates federal law:
This account contains inaccurate, unverifiable, and legally non-compliant information that violates federal law:
**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements
3. **FCRA Section 1681e(b)** - Reasonable procedures for accuracy
4. **Metro 2 Compliance** - Reporting format requirements

This account contains inaccurate information that violates federal law:
This account contains inaccurate, unverifiable, and legally non-compliant information that violates federal law:
**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements
3. **FCRA Section 1681e(b)** - Reasonable procedures for accuracy
4. **Metro 2 Compliance** - Reporting format requirements

This account contains inaccurate information that violates federal law:
This account contains inaccurate, unverifiable, and legally non-compliant information that violates federal law:
**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements
3. **FCRA Section 1681e(b)** - Reasonable procedures for accuracy
4. **Metro 2 Compliance** - Reporting format requirements
"""
    
    # Apply deduplication
    cleaned_content = remove_duplicate_content(repetitive_content)
    
    original_length = len(repetitive_content)
    cleaned_length = len(cleaned_content)
    
    print(f"Original content length: {original_length} characters")
    print(f"Cleaned content length: {cleaned_length} characters")
    print(f"Content reduction: {((original_length - cleaned_length) / original_length * 100):.1f}%")
    
    # Check for duplicate phrases
    duplicate_phrases = [
        'This account contains inaccurate information that violates federal law:',
        '**LEGAL BASIS FOR DISPUTE:**',
        '**FCRA Section 1681s-2(a)** - Furnisher accuracy requirements'
    ]
    
    for phrase in duplicate_phrases:
        original_count = repetitive_content.count(phrase)
        cleaned_count = cleaned_content.count(phrase)
        print(f"'{phrase}': {original_count} → {cleaned_count} occurrences")
    
    return cleaned_length < original_length

def main():
    """Run all deduplication tests."""
    print("🧪 Testing Deduplication Fixes")
    print("=" * 50)
    
    tests = [
        test_content_deduplication,
        test_account_deduplication,
        test_paragraph_deduplication,
        test_letter_quality_improvement
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED")
            else:
                print("❌ FAILED")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All deduplication fixes are working correctly!")
    else:
        print("⚠️ Some deduplication fixes need attention.")
    
    return passed == total

if __name__ == "__main__":
    main()
