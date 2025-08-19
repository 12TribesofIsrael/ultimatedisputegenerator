#!/usr/bin/env python3
"""
Simple test to verify deduplication fixes are working.
"""

import re

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
        normalized = normalize_content_for_dedup(paragraph)
        
        # Only add if we haven't seen this content before
        if normalized not in seen_paragraphs:
            unique_paragraphs.append(paragraph)
            seen_paragraphs.add(normalized)
    
    return '\n\n'.join(unique_paragraphs)

def test_deduplication():
    """Test the deduplication functionality."""
    print("🧪 Testing Deduplication Fix")
    print("=" * 40)
    
    # Test content with duplicates
    test_content = """
This account contains inaccurate information that violates federal law:

**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements

This account contains inaccurate information that violates federal law:

**LEGAL BASIS FOR DISPUTE:**
1. **FCRA Section 1681s-2(a)** - Furnisher accuracy requirements
2. **FCRA Section 1681i** - Reinvestigation requirements

**SPECIFIC VIOLATIONS:**
- Inaccurate account information
- Unverifiable payment history
"""
    
    # Apply deduplication
    cleaned_content = remove_duplicate_content(test_content)
    
    original_paragraphs = len([p for p in test_content.split('\n\n') if p.strip()])
    cleaned_paragraphs = len([p for p in cleaned_content.split('\n\n') if p.strip()])
    
    print(f"Original paragraphs: {original_paragraphs}")
    print(f"Cleaned paragraphs: {cleaned_paragraphs}")
    print(f"Duplicates removed: {original_paragraphs - cleaned_paragraphs}")
    
    # Check for duplicate phrases
    duplicate_phrase = 'This account contains inaccurate information that violates federal law:'
    original_count = test_content.count(duplicate_phrase)
    cleaned_count = cleaned_content.count(duplicate_phrase)
    
    print(f"'{duplicate_phrase}': {original_count} → {cleaned_count} occurrences")
    
    success = cleaned_paragraphs < original_paragraphs and cleaned_count < original_count
    print(f"✅ PASSED" if success else "❌ FAILED")
    
    return success

if __name__ == "__main__":
    test_deduplication()
