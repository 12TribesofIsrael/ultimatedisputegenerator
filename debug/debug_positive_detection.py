#!/usr/bin/env python3
"""Debug script to examine why positive status detection is failing"""

import fitz
import re

def debug_positive_detection():
    # Extract text from TransUnion PDF
    doc = fitz.open('consumerreport/input/transunion.pdf')
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    lines = text.split('\n')
    
    # Test positive status patterns
    positive_patterns = [
        ('Never late', r'never\s*late'),
        ('Paid, Closed/Never late', r'paid.*closed.*never\s*late'),
        ('Paid as agreed', r'paid\s*(?:or\s*paying\s*)?as\s*agreed'),
        ('Exceptional payment history', r'exceptional\s*payment\s*history'),
        ('Paid, Closed', r'paid.*closed(?!\s*(?:charge|collection))'),
        ('Current', r'current'),
        ('Paid', r'paid(?!\s*(?:charge|settlement))'),
        ('Open', r'open(?!\s*(?:delinquent|past\s*due))'),
        ('Closed', r'closed(?!\s*(?:charge|collection))'),
    ]
    
    print("=== TESTING POSITIVE STATUS PATTERNS ===")
    
    # Find lines with "Exceptional payment history"
    exceptional_lines = []
    for i, line in enumerate(lines):
        if 'exceptional payment history' in line.lower():
            exceptional_lines.append(i)
    
    print(f"Found 'Exceptional payment history' at lines: {exceptional_lines}")
    
    # Test each pattern on these lines
    for line_idx in exceptional_lines:
        line_text = lines[line_idx]
        print(f"\nLine {line_idx}: '{line_text}'")
        
        for status_name, pattern in positive_patterns:
            if re.search(pattern, line_text, re.IGNORECASE):
                print(f"  ✅ Matches '{status_name}' pattern: {pattern}")
            else:
                print(f"  ❌ No match for '{status_name}' pattern: {pattern}")
    
    # Also check what the extraction actually finds
    print(f"\n=== SIMULATING EXTRACTION LOGIC ===")
    
    # Find CAPITAL ONE context
    capital_lines = []
    for i, line in enumerate(lines):
        if 'CAPITAL ONE' in line.upper():
            capital_lines.append(i)
    
    print(f"Found CAPITAL ONE at lines: {capital_lines}")
    
    for capital_idx in capital_lines:
        print(f"\n--- CAPITAL ONE at line {capital_idx} ---")
        # Simulate the search window (30 lines)
        start = capital_idx
        end = min(len(lines), capital_idx + 30)
        
        found_positive = False
        found_negative = False
        
        for j in range(start, end):
            search_line = lines[j]
            print(f"  Line {j:4d}: {search_line}")
            
            # Test positive patterns
            for status_name, pattern in positive_patterns:
                if re.search(pattern, search_line, re.IGNORECASE):
                    print(f"    ✅ POSITIVE: {status_name}")
                    found_positive = True
            
            # Test negative patterns  
            if re.search(r'late\s*payment|past\s*due|delinquent', search_line, re.IGNORECASE):
                print(f"    ❌ NEGATIVE: Late")
                found_negative = True
        
        print(f"  Summary: Positive={found_positive}, Negative={found_negative}")

if __name__ == "__main__":
    debug_positive_detection()
