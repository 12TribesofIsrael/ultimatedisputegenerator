#!/usr/bin/env python3
"""Generate next-round dispute letters based on analysis results."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extract_account_details import auto_generate_next_round_letter
import json
import argparse


def main():
    parser = argparse.ArgumentParser(description='Generate next-round dispute letters')
    parser.add_argument('analysis_file', help='Path to analysis JSON file')
    parser.add_argument('round_number', type=int, help='Round number (2, 3, 4, etc.)')
    parser.add_argument('--output', '-o', help='Output file path (default: next_round_{round}.md)')
    
    args = parser.parse_args()
    
    # Validate analysis file exists
    analysis_path = Path(args.analysis_file)
    if not analysis_path.exists():
        print(f"❌ Analysis file not found: {analysis_path}")
        return 1
    
    # Validate round number
    if args.round_number < 2:
        print("❌ Round number must be 2 or higher")
        return 1
    
    # Generate the letter
    try:
        letter_content = auto_generate_next_round_letter(str(analysis_path), args.round_number)
        
        # Determine output file
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path(f"next_round_{args.round_number}.md")
        
        # Write the letter
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(letter_content)
        
        print(f"✅ Next-round letter generated: {output_path}")
        print(f"📄 Round {args.round_number} letter ready for {analysis_path.stem}")
        
        # Show summary
        try:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            accounts = data.get('accounts', [])
            bureau = data.get('bureau_detected', 'Unknown')
            print(f"📊 Summary: {len(accounts)} accounts for {bureau}")
        except Exception:
            pass
            
    except Exception as e:
        print(f"❌ Error generating letter: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
