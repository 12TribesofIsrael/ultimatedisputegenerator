#!/usr/bin/env python3
"""
Test script to verify enhanced template content integration fixes.

This script tests:
1. Template search query improvements
2. PDF content extraction enhancements
3. Direct template file integration
4. Content display improvements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.template_integration import generate_enhanced_dispute_letter, get_direct_template_content
from utils.knowledgebase_enhanced import build_comprehensive_kb_references, get_template_letter_queries

def test_template_search_queries():
    """Test that template search queries are improved."""
    print("=== Testing Template Search Queries ===")
    
    # Test queries for different account types
    test_cases = [
        ("charge off", "major_bank", 1),
        ("collection", "collection_agency", 1),
        ("late", "general_creditor", 1),
        ("repossession", "auto_lender", 1)
    ]
    
    for account_status, creditor_type, round_number in test_cases:
        queries = get_template_letter_queries(account_status, creditor_type, round_number)
        print(f"\nAccount Status: {account_status}")
        print(f"Creditor Type: {creditor_type}")
        print(f"Round: {round_number}")
        print(f"Number of queries: {len(queries)}")
        print(f"Sample queries: {queries[:5]}")
        
        # Check for broader search terms
        broad_terms = ['debt validation', 'violations', 'FCRA', 'FDCPA', 'Metro 2']
        found_broad_terms = [term for term in broad_terms if any(term in query.lower() for query in queries)]
        print(f"Broad search terms found: {found_broad_terms}")

def test_direct_template_content():
    """Test direct template content extraction."""
    print("\n=== Testing Direct Template Content ===")
    
    test_account = {
        'creditor': 'CAPITAL ONE',
        'account_number': '1234567890',
        'status': 'charge off',
        'balance': '$5000'
    }
    
    templates = get_direct_template_content(test_account, 1)
    print(f"Number of direct templates found: {len(templates)}")
    
    for i, template in enumerate(templates):
        print(f"\nTemplate {i+1}:")
        print(f"File: {template.get('file_name', 'Unknown')}")
        print(f"Content length: {len(template.get('content', ''))}")
        print(f"Score: {template.get('score', 0)}")
        print(f"Priority: {template.get('priority', 'Unknown')}")
        
        # Show first 200 characters of content
        content = template.get('content', '')
        if content:
            print(f"Content preview: {content[:200]}...")

def test_enhanced_letter_generation():
    """Test enhanced letter generation."""
    print("\n=== Testing Enhanced Letter Generation ===")
    
    test_account = {
        'creditor': 'CHASE BANK',
        'account_number': '9876543210',
        'status': 'charge off',
        'balance': '$8000'
    }
    
    try:
        enhanced_letter = generate_enhanced_dispute_letter(test_account, 1)
        
        print(f"Letter generated successfully: {bool(enhanced_letter)}")
        print(f"Account info: {enhanced_letter.get('account_info', {})}")
        print(f"Letter content length: {len(enhanced_letter.get('letter_content', ''))}")
        print(f"Template sources: {len(enhanced_letter.get('template_sources', []))}")
        print(f"Success probability: {enhanced_letter.get('success_probability', 0)}")
        print(f"Content quality score: {enhanced_letter.get('content_quality_score', 0)}")
        print(f"Template utilization count: {enhanced_letter.get('template_utilization_count', 0)}")
        
        # Show letter content preview
        letter_content = enhanced_letter.get('letter_content', '')
        if letter_content:
            print(f"\nLetter content preview (first 500 chars):")
            print(letter_content[:500])
            
    except Exception as e:
        print(f"Error generating enhanced letter: {e}")

def test_knowledgebase_references():
    """Test knowledgebase reference building."""
    print("\n=== Testing Knowledgebase References ===")
    
    test_account = {
        'creditor': 'AMERICAN EXPRESS',
        'account_number': '111122223333',
        'status': 'collection',
        'balance': '$3000'
    }
    
    try:
        references = build_comprehensive_kb_references(test_account, 1, 3)
        
        print(f"Template letters found: {len(references.get('template_letters', []))}")
        print(f"Case law found: {len(references.get('case_law', []))}")
        print(f"Creditor strategies found: {len(references.get('creditor_strategies', []))}")
        print(f"Strategy documents found: {len(references.get('strategy_documents', []))}")
        
        # Show sample template letters
        template_letters = references.get('template_letters', [])
        if template_letters:
            print(f"\nSample template letters:")
            for i, template in enumerate(template_letters[:3]):
                print(f"  {i+1}. {template.get('file_name', 'Unknown')} (Score: {template.get('score', 0)})")
                
    except Exception as e:
        print(f"Error building knowledgebase references: {e}")

def main():
    """Run all tests."""
    print("Enhanced Template Content Integration Fix Test")
    print("=" * 50)
    
    test_template_search_queries()
    test_direct_template_content()
    test_enhanced_letter_generation()
    test_knowledgebase_references()
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()
