#!/usr/bin/env python3
"""Simple test harness for PDF parsing and OCR functionality."""

import fitz
from pathlib import Path
from utils.ocr_fallback import ocr_pdf
from extract_account_details import extract_account_details
from utils.inquiries import extract_inquiries_from_text
import json


def test_pdf_parsing(pdf_path: str) -> dict:
    """Test PDF text extraction and OCR fallback on a single file."""
    results = {
        "file": pdf_path,
        "text_extraction": {"success": False, "char_count": 0, "error": None},
        "ocr_fallback": {"success": False, "char_count": 0, "error": None},
        "account_extraction": {"success": False, "count": 0, "error": None},
        "inquiries_extraction": {"success": False, "count": 0, "error": None},
    }
    
    # Test standard text extraction
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        results["text_extraction"]["success"] = True
        results["text_extraction"]["char_count"] = len(text.strip())
        
        # Test OCR if text extraction yields little content
        if len(text.strip()) < 100:
            print(f"⚠️  Low text content ({len(text.strip())} chars), testing OCR...")
            try:
                ocr_text = ocr_pdf(pdf_path)
                results["ocr_fallback"]["success"] = True
                results["ocr_fallback"]["char_count"] = len(ocr_text.strip())
                if len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
                    print(f"✅ OCR improved text extraction: {len(text.strip())} chars")
                else:
                    print(f"⚠️  OCR didn't improve text extraction")
            except Exception as e:
                results["ocr_fallback"]["error"] = str(e)
                print(f"❌ OCR failed: {e}")
        
        # Test account extraction
        try:
            accounts = extract_account_details(text)
            results["account_extraction"]["success"] = True
            results["account_extraction"]["count"] = len(accounts)
            print(f"📊 Extracted {len(accounts)} accounts")
        except Exception as e:
            results["account_extraction"]["error"] = str(e)
            print(f"❌ Account extraction failed: {e}")
        
        # Test inquiries extraction
        try:
            inquiries = extract_inquiries_from_text(text)
            results["inquiries_extraction"]["success"] = True
            results["inquiries_extraction"]["count"] = len(inquiries)
            print(f"🔍 Extracted {len(inquiries)} inquiries")
        except Exception as e:
            results["inquiries_extraction"]["error"] = str(e)
            print(f"❌ Inquiries extraction failed: {e}")
            
    except Exception as e:
        results["text_extraction"]["error"] = str(e)
        print(f"❌ Text extraction failed: {e}")
    
    return results


def main():
    """Run tests on PDF files in consumerreport/input/"""
    input_dir = Path("consumerreport/input")
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {input_dir}")
        return
    
    print(f"🧪 Testing {len(pdf_files)} PDF files...")
    print("=" * 60)
    
    all_results = []
    for pdf_file in pdf_files:
        print(f"\n📄 Testing: {pdf_file.name}")
        print("-" * 40)
        
        result = test_pdf_parsing(str(pdf_file))
        all_results.append(result)
        
        # Print summary
        if result["text_extraction"]["success"]:
            print(f"✅ Text extraction: {result['text_extraction']['char_count']} chars")
        else:
            print(f"❌ Text extraction failed: {result['text_extraction']['error']}")
        
        if result["account_extraction"]["success"]:
            print(f"✅ Account extraction: {result['account_extraction']['count']} accounts")
        else:
            print(f"❌ Account extraction failed: {result['account_extraction']['error']}")
        
        if result["inquiries_extraction"]["success"]:
            print(f"✅ Inquiries extraction: {result['inquiries_extraction']['count']} inquiries")
        else:
            print(f"❌ Inquiries extraction failed: {result['inquiries_extraction']['error']}")
    
    # Save results
    output_file = Path("test_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📊 Test results saved to: {output_file}")
    
    # Summary
    successful_text = sum(1 for r in all_results if r["text_extraction"]["success"])
    successful_accounts = sum(1 for r in all_results if r["account_extraction"]["success"])
    successful_inquiries = sum(1 for r in all_results if r["inquiries_extraction"]["success"])
    
    print(f"\n📈 Summary:")
    print(f"  Text extraction: {successful_text}/{len(pdf_files)} successful")
    print(f"  Account extraction: {successful_accounts}/{len(pdf_files)} successful")
    print(f"  Inquiries extraction: {successful_inquiries}/{len(pdf_files)} successful")


if __name__ == "__main__":
    main()
