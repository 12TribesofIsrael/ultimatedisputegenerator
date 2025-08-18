#!/usr/bin/env python3
"""Debug script to examine APPLE CARD extraction in detail"""

import fitz
import re

def debug_apple_card_detailed():
    # Extract text from Experian PDF
    doc = fitz.open('consumerreport/input/Experian.pdf')
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    lines = text.split('\n')
    
    # Find APPLE CARD lines
    apple_lines = []
    for i, line in enumerate(lines):
        if 'APPLE CARD' in line.upper():
            apple_lines.append(i)
    
    print(f"Found APPLE CARD at lines: {apple_lines}")
    
    # Show extensive context around APPLE CARD
    for apple_idx in apple_lines:
        print(f"\n=== APPLE CARD CONTEXT (Line {apple_idx}) ===")
        start = max(0, apple_idx - 5)
        end = min(len(lines), apple_idx + 30)  # More lines to see full account
        
        for i in range(start, end):
            marker = ">>> " if i == apple_idx else "    "
            line_text = lines[i]
            
            # Highlight key patterns
            if re.search(r'written\s*off|write\s*off|charged?\s*off|bad\s*debt', line_text, re.IGNORECASE):
                marker = "!CO!"
            elif re.search(r'never\s*late|paid.*closed.*never\s*late|exceptional\s*payment|paid\s*as\s*agreed', line_text, re.IGNORECASE):
                marker = "+POS"
            elif re.search(r'\bCO\b', line_text):
                marker = "!CO!"
            elif re.search(r'late\s*payment|past\s*due|\b(?:30|60|90)\s*days?\s*(?:late|past\s*due)', line_text, re.IGNORECASE):
                marker = "LATE"
                
            print(f"{marker} Line {i:4d}: {line_text}")

if __name__ == "__main__":
    debug_apple_card_detailed()
