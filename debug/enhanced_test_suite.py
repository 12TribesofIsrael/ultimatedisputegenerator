#!/usr/bin/env python3
"""Enhanced test suite with comprehensive edge case coverage."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
import traceback
from typing import Dict, List, Any
from extract_account_details import extract_account_details
from utils.ocr_fallback import extract_text_via_ocr
from utils.inquiries import extract_inquiries_from_text
from utils.inquiry_disputes import analyze_inquiry_patterns, generate_hard_inquiry_dispute_letter


class TestResult:
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.error = None
        self.duration = 0
        self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'success': self.success,
            'error': str(self.error) if self.error else None,
            'duration': self.duration,
            'details': self.details
        }


def test_pdf_text_extraction(pdf_path: Path) -> TestResult:
    """Test PDF text extraction with various methods."""
    result = TestResult(f"PDF Text Extraction - {pdf_path.name}")
    
    try:
        start_time = time.time()
        
        # Test standard text extraction
        import fitz
        doc = fitz.open(pdf_path)
        text_content = ""
        for page in doc:
            text_content += page.get_text()
        doc.close()
        
        # Test OCR fallback if text is insufficient
        if len(text_content.strip()) < 1000:
            print(f"⚠️ Low text content ({len(text_content)} chars), testing OCR...")
            ocr_text = extract_text_via_ocr(str(pdf_path))
            result.details['ocr_text_length'] = len(ocr_text)
            result.details['ocr_success'] = len(ocr_text) > len(text_content)
        
        result.details['text_length'] = len(text_content)
        result.details['has_content'] = len(text_content.strip()) > 0
        result.success = len(text_content.strip()) > 0
        result.duration = time.time() - start_time
        
    except Exception as e:
        result.error = e
        result.success = False
    
    return result


def test_account_extraction(pdf_path: Path) -> TestResult:
    """Test account extraction functionality."""
    result = TestResult(f"Account Extraction - {pdf_path.name}")
    
    try:
        start_time = time.time()
        
        # Extract text first
        import fitz
        doc = fitz.open(pdf_path)
        text_content = ""
        for page in doc:
            text_content += page.get_text()
        doc.close()
        
        # Use the account extraction logic from the main script
        from extract_account_details import extract_account_details
        # Create a temporary file to test with
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(text_content)
            temp_file = f.name
        
        try:
            accounts = extract_account_details(temp_file)
        finally:
            # Clean up temp file
            import os
            os.unlink(temp_file)
        
        result.details['total_accounts'] = len(accounts)
        result.details['negative_accounts'] = len([acc for acc in accounts if acc.get('is_negative', False)])
        result.details['positive_accounts'] = len([acc for acc in accounts if not acc.get('is_negative', True)])
        result.details['has_reaging_violations'] = any(
            any('re-aging' in v.lower() for v in acc.get('violations', [])) 
            for acc in accounts
        )
        result.details['has_medical_violations'] = any(
            any('medical' in v.lower() for v in acc.get('violations', [])) 
            for acc in accounts
        )
        result.details['has_metro2_violations'] = any(
            any('metro 2' in v.lower() for v in acc.get('violations', [])) 
            for acc in accounts
        )
        
        result.success = len(accounts) > 0
        result.duration = time.time() - start_time
        
    except Exception as e:
        result.error = e
        result.success = False
    
    return result


def test_inquiry_extraction(pdf_path: Path) -> TestResult:
    """Test inquiry extraction functionality."""
    result = TestResult(f"Inquiry Extraction - {pdf_path.name}")
    
    try:
        start_time = time.time()
        
        # Extract text first
        import fitz
        doc = fitz.open(pdf_path)
        text_content = ""
        for page in doc:
            text_content += page.get_text()
        doc.close()
        
        # Extract inquiries
        inquiries = extract_inquiries_from_text(text_content)
        
        result.details['total_inquiries'] = len(inquiries)
        result.details['unique_furnishers'] = len(set(inq.get('furnisher', '') for inq in inquiries))
        result.details['has_dates'] = any(inq.get('date') for inq in inquiries)
        
        # Test inquiry analysis
        if inquiries:
            analysis = analyze_inquiry_patterns(inquiries)
            result.details['risk_score'] = analysis['risk_score']
            result.details['suspicious_count'] = len(analysis['suspicious_inquiries'])
            result.details['violations'] = analysis['violations']
        
        result.success = True  # Inquiry extraction is optional
        result.duration = time.time() - start_time
        
    except Exception as e:
        result.error = e
        result.success = False
    
    return result


def test_edge_cases() -> List[TestResult]:
    """Test various edge cases and error conditions."""
    results = []
    
    # Test 1: Empty text
    result = TestResult("Edge Case - Empty Text")
    try:
        start_time = time.time()
        inquiries = extract_inquiries_from_text("")
        result.details['inquiries_found'] = len(inquiries)
        result.success = len(inquiries) == 0
        result.duration = time.time() - start_time
    except Exception as e:
        result.error = e
        result.success = False
    results.append(result)
    
    # Test 2: Very long text
    result = TestResult("Edge Case - Very Long Text")
    try:
        start_time = time.time()
        long_text = "This is a test inquiry from BANK OF AMERICA on 01/15/2024. " * 1000
        inquiries = extract_inquiries_from_text(long_text)
        result.details['inquiries_found'] = len(inquiries)
        result.success = True  # Should not crash
        result.duration = time.time() - start_time
    except Exception as e:
        result.error = e
        result.success = False
    results.append(result)
    
    # Test 3: Special characters
    result = TestResult("Edge Case - Special Characters")
    try:
        start_time = time.time()
        special_text = "Inquiry from BANK-OF-AMERICA (N.A.) on 01/15/2024"
        inquiries = extract_inquiries_from_text(special_text)
        result.details['inquiries_found'] = len(inquiries)
        result.success = True  # Should handle special chars
        result.duration = time.time() - start_time
    except Exception as e:
        result.error = e
        result.success = False
    results.append(result)
    
    # Test 4: Unicode characters
    result = TestResult("Edge Case - Unicode Characters")
    try:
        start_time = time.time()
        unicode_text = "Inquiry from BANCO DE AMÉRICA on 01/15/2024"
        inquiries = extract_inquiries_from_text(unicode_text)
        result.details['inquiries_found'] = len(inquiries)
        result.success = True  # Should handle unicode
        result.duration = time.time() - start_time
    except Exception as e:
        result.error = e
        result.success = False
    results.append(result)
    
    return results


def test_performance() -> List[TestResult]:
    """Test performance characteristics."""
    results = []
    
    # Test 1: Large text processing
    result = TestResult("Performance - Large Text Processing")
    try:
        start_time = time.time()
        large_text = "This is a test inquiry from BANK OF AMERICA on 01/15/2024. " * 10000
        inquiries = extract_inquiries_from_text(large_text)
        result.details['processing_time'] = time.time() - start_time
        result.details['text_length'] = len(large_text)
        result.details['inquiries_found'] = len(inquiries)
        result.success = result.details['processing_time'] < 5.0  # Should complete within 5 seconds
        result.duration = result.details['processing_time']
    except Exception as e:
        result.error = e
        result.success = False
    results.append(result)
    
    # Test 2: Multiple inquiry patterns
    result = TestResult("Performance - Multiple Inquiry Patterns")
    try:
        start_time = time.time()
        patterns_text = """
        Inquiry from BANK OF AMERICA on 01/15/2024
        Inquiry from CHASE BANK on 01/16/2024
        Inquiry from WELLS FARGO on 01/17/2024
        Inquiry from CITIBANK on 01/18/2024
        Inquiry from CAPITAL ONE on 01/19/2024
        """ * 1000  # Repeat 1000 times
        inquiries = extract_inquiries_from_text(patterns_text)
        result.details['processing_time'] = time.time() - start_time
        result.details['inquiries_found'] = len(inquiries)
        result.success = result.details['processing_time'] < 10.0  # Should complete within 10 seconds
        result.duration = result.details['processing_time']
    except Exception as e:
        result.error = e
        result.success = False
    results.append(result)
    
    return results


def run_enhanced_test_suite() -> Dict[str, Any]:
    """Run the complete enhanced test suite."""
    print("🧪 Running Enhanced Test Suite...")
    print("=" * 60)
    
    all_results = []
    test_start_time = time.time()
    
    # Test PDF files
    input_dir = Path("consumerreport/input")
    if input_dir.exists():
        pdf_files = list(input_dir.glob("*.pdf"))
        print(f"📄 Found {len(pdf_files)} PDF files to test")
        
        for pdf_file in pdf_files:
            print(f"\n🔍 Testing: {pdf_file.name}")
            
            # Test text extraction
            result = test_pdf_text_extraction(pdf_file)
            all_results.append(result)
            print(f"  📝 Text Extraction: {'✅' if result.success else '❌'} ({result.duration:.2f}s)")
            
            # Test account extraction
            result = test_account_extraction(pdf_file)
            all_results.append(result)
            print(f"  🏦 Account Extraction: {'✅' if result.success else '❌'} ({result.duration:.2f}s)")
            
            # Test inquiry extraction
            result = test_inquiry_extraction(pdf_file)
            all_results.append(result)
            print(f"  🔍 Inquiry Extraction: {'✅' if result.success else '❌'} ({result.duration:.2f}s)")
    else:
        print("⚠️ No input directory found, skipping PDF tests")
    
    # Test edge cases
    print(f"\n🔬 Testing Edge Cases...")
    edge_results = test_edge_cases()
    all_results.extend(edge_results)
    for result in edge_results:
        print(f"  {result.test_name}: {'✅' if result.success else '❌'} ({result.duration:.2f}s)")
    
    # Test performance
    print(f"\n⚡ Testing Performance...")
    perf_results = test_performance()
    all_results.extend(perf_results)
    for result in perf_results:
        print(f"  {result.test_name}: {'✅' if result.success else '❌'} ({result.duration:.2f}s)")
    
    # Compile results
    total_tests = len(all_results)
    successful_tests = sum(1 for r in all_results if r.success)
    failed_tests = total_tests - successful_tests
    total_duration = time.time() - test_start_time
    
    # Generate summary
    summary = {
        'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'failed_tests': failed_tests,
        'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
        'total_duration': total_duration,
        'results': [r.to_dict() for r in all_results]
    }
    
    # Save results
    output_file = Path("enhanced_test_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Successful: {successful_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"  Total Duration: {total_duration:.2f}s")
    print(f"  Results saved to: {output_file}")
    
    # Show failed tests
    if failed_tests > 0:
        print(f"\n❌ Failed Tests:")
        for result in all_results:
            if not result.success:
                print(f"  - {result.test_name}: {result.error}")
    
    return summary


if __name__ == "__main__":
    run_enhanced_test_suite()
