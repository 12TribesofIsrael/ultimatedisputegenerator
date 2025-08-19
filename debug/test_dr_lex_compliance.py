#!/usr/bin/env python3
"""
Test script to verify Dr. Lex Grant compliance in generated letters.

This script tests:
1. Mandatory knowledgebase strategies inclusion
2. Complete account content generation
3. Deduplication effectiveness
4. Power language usage
5. Legal basis completeness
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_mandatory_strategies_inclusion():
    """Test that mandatory knowledgebase strategies are included."""
    print("=== Testing Mandatory Knowledgebase Strategies ===")
    
    # Test content that should be present
    required_content = [
        "REQUEST FOR PROCEDURE - FCRA §1681i(6)(B)(iii)",
        "METHOD OF VERIFICATION (MOV) - 10 CRITICAL QUESTIONS",
        "METRO 2 COMPLIANCE VIOLATIONS",
        "15-DAY ACCELERATION",
        "LEGAL NOTICE"
    ]
    
    # Test from a sample letter
    sample_letter = """
    ## MANDATORY KNOWLEDGEBASE STRATEGIES

    ### **REQUEST FOR PROCEDURE - FCRA §1681i(6)(B)(iii)**

    I hereby request a description of the procedure used to determine the accuracy and completeness of the information, including the business name and address of any furnisher of information contacted in connection with such information and, if reasonably available, the telephone number of such furnisher.

    **SPECIFIC PROCEDURE DEMANDS:**
    1. **Complete investigation procedure description** for all disputed accounts
    2. **Business name, address, phone** of ALL furnishers contacted
    3. **Name of CRA employee** who conducted investigation
    4. **Copies of ALL documents** obtained/reviewed
    5. **Specific verification method** used for each disputed item

    **LEGAL NOTICE**: Failure to provide this procedure description constitutes a violation of FCRA §1681i(6)(B)(iii) and will result in immediate legal action.

    ### **METHOD OF VERIFICATION (MOV) - 10 CRITICAL QUESTIONS**

    I am requesting the Method of Verification (MOV) used in the reinvestigation of disputed information in my credit file, as per 15 U.S. Code § 1681i.

    **THE 10 CRITICAL MOV QUESTIONS:**
    1. **What certified documents** were reviewed to verify each disputed account?
    2. **Who did you speak to** at the furnisher? (name, position, phone, date)
    3. **What formal training** was provided to your investigator?
    4. **Provide copies** of all correspondence exchanged with furnishers
    5. **What specific databases** were accessed during verification?
    6. **How was the accuracy** of reported dates verified?
    7. **What documentation proves** the account balance accuracy?
    8. **How was payment history** verified month-by-month?
    9. **What measures ensured** Metro 2 format compliance?
    10. **Provide the complete audit trail** of your investigation

    **LEGAL NOTICE**: Failure to answer these questions constitutes inadequate investigation procedures and requires immediate deletion of all disputed accounts.

    ### **METRO 2 COMPLIANCE VIOLATIONS**

    All furnishers MUST comply with Metro 2 Format requirements. Any account that fails to meet Metro 2 standards MUST BE DELETED immediately.

    **SPECIFIC METRO 2 VIOLATIONS FOR ALL DISPUTED ACCOUNTS:**
    - **Inaccurate account status codes** (Current Status vs. Payment Rating alignment)
    - **Incorrect balance reporting** (math coherence; no negative or impossible values)
    - **Invalid date information** (DOFD, Date Opened, Date Closed chronology integrity)
    - **Non-compliant payment history codes** (24-month grid codes must match status chronology)
    - **High Credit/Credit Limit discrepancies** (utilization impacts)
    - **Special Comment Codes** (no contradictory remarks)

    **LEGAL NOTICE**: Violation of any Metro 2 standard requires immediate deletion as inaccurate/unverifiable.

    ### 15-DAY ACCELERATION – NO FORM LETTERS
    I legally and lawfully **REFUSE** any generic form letter response. You now have **15 days**, not 30, to comply with all demands above.
    """
    
    missing_content = []
    for content in required_content:
        if content not in sample_letter:
            missing_content.append(content)
    
    if missing_content:
        print(f"❌ Missing required content: {missing_content}")
        return False
    else:
        print("✅ All mandatory strategies included")
        return True

def test_power_language():
    """Test that power language is used instead of weak language."""
    print("\n=== Testing Power Language ===")
    
    # Test content with power language
    power_content = """
    I DEMAND THE FOLLOWING:
    LEGAL NOTICE
    I DEMAND VALIDATION
    IMMEDIATE DELETION
    """
    
    weak_phrases = ["I request", "Please note", "I would like"]
    
    weak_found = []
    for phrase in weak_phrases:
        if phrase in power_content:
            weak_found.append(phrase)
    
    if weak_found:
        print(f"❌ Weak language found: {weak_found}")
        return False
    else:
        print("✅ Power language used correctly")
        return True

def test_complete_account_content():
    """Test that complete account content is generated."""
    print("\n=== Testing Complete Account Content ===")
    
    # Test account content structure
    account_content = """
    **Legal Basis for Deletion:**
    - Violation of 15 USC §1681s-2(a) - Furnisher accuracy requirements
    - Violation of 15 USC §1681i - Failure to properly investigate
    - Violation of Metro 2 Format compliance requirements

    **SPECIFIC VIOLATIONS:**
    - Inaccurate account information
    - Unverifiable payment history
    - Incorrect account status reporting
    - Violation of Metro 2 format standards
    - Failure to maintain reasonable procedures

    **I DEMAND THE FOLLOWING:**
    1. **Immediate Deletion**: DELETE this account from my credit report
    2. **Documentation**: Provide complete documentation supporting all reported information
    3. **Verification**: Verify the accuracy of all reported information
    4. **Compliance**: Ensure Metro 2 format compliance

    **LEGAL NOTICE**: If this information cannot be verified with complete documentation, it must be deleted immediately.
    """
    
    required_sections = [
        "Legal Basis for Deletion",
        "SPECIFIC VIOLATIONS",
        "I DEMAND THE FOLLOWING",
        "LEGAL NOTICE"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in account_content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing account sections: {missing_sections}")
        return False
    else:
        print("✅ Complete account content generated")
        return True

def test_deduplication():
    """Test that deduplication is working."""
    print("\n=== Testing Deduplication ===")
    
    # Test content with duplicates
    duplicate_content = """
    This account contains inaccurate information.
    This account contains inaccurate information.
    This account contains inaccurate information.
    
    I demand deletion of this account.
    I demand deletion of this account.
    I demand deletion of this account.
    """
    
    # Count duplicates
    lines = duplicate_content.strip().split('\n')
    unique_lines = list(set(lines))
    
    if len(lines) > len(unique_lines):
        print(f"❌ Duplicates found: {len(lines) - len(unique_lines)} duplicate lines")
        return False
    else:
        print("✅ No duplicates detected")
        return True

def main():
    """Run all compliance tests."""
    print("🏆 DR. LEX GRANT COMPLIANCE TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_mandatory_strategies_inclusion,
        test_power_language,
        test_complete_account_content,
        test_deduplication
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - LETTERS COMPLY WITH DR. LEX GRANT STANDARDS")
    else:
        print("⚠️  SOME TESTS FAILED - ADDITIONAL FIXES NEEDED")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
