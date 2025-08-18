#!/usr/bin/env python3
"""
Test script for enhanced knowledgebase functionality.

This script tests the new comprehensive knowledgebase search capabilities
and measures the improvement in utilization from 10-15% to 60-80%.
"""

import sys
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.knowledgebase_enhanced import (
    classify_creditor_type,
    get_creditor_specific_queries,
    get_template_letter_queries,
    get_case_law_queries,
    get_strategy_document_queries,
    search_template_letters,
    find_legal_precedents,
    get_creditor_specific_strategies,
    get_strategy_documents,
    build_comprehensive_kb_references,
    get_knowledgebase_utilization_stats
)

def test_creditor_classification():
    """Test creditor type classification."""
    print("🧪 Testing Creditor Classification...")
    
    test_cases = [
        ("CHASE BANK", "major_bank"),
        ("NAVY FCU", "credit_union"),
        ("DEPT OF EDUCATION/NELN", "student_loan"),
        ("PORTFOLIO RECOVERY ASSOCIATES", "collection_agency"),
        ("MEDICAL CENTER HOSPITAL", "medical"),
        ("TOYOTA MOTOR CREDIT", "auto_lender"),
        ("TARGET STORE CARD", "store_card"),
        ("UNKNOWN CREDITOR", "general_creditor")
    ]
    
    for creditor_name, expected_type in test_cases:
        actual_type = classify_creditor_type(creditor_name)
        status = "✅" if actual_type == expected_type else "❌"
        print(f"  {status} {creditor_name} -> {actual_type} (expected: {expected_type})")
    
    print()

def test_query_generation():
    """Test query generation for different account types."""
    print("🧪 Testing Query Generation...")
    
    test_accounts = [
        {
            "creditor": "CHASE BANK",
            "status": "charge off",
            "expected_queries": ["major bank charge off dispute template", "bank charge-off deletion strategy"]
        },
        {
            "creditor": "NAVY FCU", 
            "status": "late",
            "expected_queries": ["credit union late dispute", "FCU EMPCU dispute letter template"]
        },
        {
            "creditor": "PORTFOLIO RECOVERY",
            "status": "collection",
            "expected_queries": ["collection agency collection dispute", "FDCPA collection validation letter"]
        }
    ]
    
    for account in test_accounts:
        creditor_type = classify_creditor_type(account["creditor"])
        queries = get_creditor_specific_queries(creditor_type, account["status"])
        
        print(f"  📋 {account['creditor']} ({account['status']}):")
        print(f"     Creditor Type: {creditor_type}")
        print(f"     Generated {len(queries)} queries")
        for i, query in enumerate(queries[:3], 1):  # Show first 3 queries
            print(f"     {i}. {query}")
        print()

def test_comprehensive_search():
    """Test comprehensive knowledgebase search."""
    print("🧪 Testing Comprehensive Knowledgebase Search...")
    
    test_account = {
        "creditor": "CHASE BANK",
        "status": "charge off",
        "account_number": "XXXX-XXXX-XXXX-1234",
        "balance": "$5,000"
    }
    
    print(f"  📊 Testing account: {test_account['creditor']} ({test_account['status']})")
    
    # Test comprehensive references
    try:
        comprehensive_refs = build_comprehensive_kb_references(test_account, round_number=1, max_refs_per_type=2)
        
        print(f"  📈 Results by category:")
        for category, refs in comprehensive_refs.items():
            print(f"     {category}: {len(refs)} references")
            for ref in refs[:2]:  # Show first 2 references
                print(f"       - {ref.get('file_name', 'Unknown')}")
        print()
        
        return comprehensive_refs
        
    except Exception as e:
        print(f"  ❌ Error testing comprehensive search: {e}")
        return None

def test_utilization_improvement():
    """Test and measure knowledgebase utilization improvement."""
    print("🧪 Testing Knowledgebase Utilization Improvement...")
    
    # Get current stats
    stats = get_knowledgebase_utilization_stats()
    
    print(f"  📊 Current Knowledgebase Stats:")
    print(f"     Total files: {stats['total_files']}")
    print(f"     Indexed files: {stats['indexed_files']}")
    print(f"     Current utilization: {stats['current_utilization']}")
    print(f"     Target utilization: {stats['target_utilization']}")
    print(f"     Improvement potential: {stats['improvement_potential']}")
    print()
    
    # Test with sample accounts
    sample_accounts = [
        {"creditor": "CHASE BANK", "status": "charge off"},
        {"creditor": "NAVY FCU", "status": "late"},
        {"creditor": "PORTFOLIO RECOVERY", "status": "collection"},
        {"creditor": "DEPT OF EDUCATION", "status": "late"},
        {"creditor": "MEDICAL CENTER", "status": "collection"}
    ]
    
    total_refs = 0
    unique_refs = set()
    
    for account in sample_accounts:
        try:
            refs = build_comprehensive_kb_references(account, round_number=1, max_refs_per_type=2)
            account_refs = 0
            
            for category, category_refs in refs.items():
                account_refs += len(category_refs)
                for ref in category_refs:
                    unique_refs.add(ref.get('file_name', ''))
            
            total_refs += account_refs
            print(f"  📋 {account['creditor']}: {account_refs} references")
            
        except Exception as e:
            print(f"  ❌ Error with {account['creditor']}: {e}")
    
    print(f"  📈 Utilization Summary:")
    print(f"     Total references generated: {total_refs}")
    print(f"     Unique files referenced: {len(unique_refs)}")
    print(f"     Average per account: {total_refs / len(sample_accounts):.1f}")
    print(f"     Unique file utilization: {len(unique_refs) / stats['indexed_files'] * 100:.1f}%")
    print()

def test_round_based_queries():
    """Test round-based query generation."""
    print("🧪 Testing Round-Based Query Generation...")
    
    test_account = {"creditor": "CHASE BANK", "status": "charge off"}
    
    for round_num in [1, 2, 3, 4]:
        print(f"  📋 Round {round_num} queries:")
        
        # Template queries
        template_queries = get_template_letter_queries(test_account["status"], "major_bank", round_num)
        print(f"     Template queries: {len(template_queries)}")
        for i, query in enumerate(template_queries[:2], 1):
            print(f"       {i}. {query}")
        
        # Strategy queries
        strategy_queries = get_strategy_document_queries(test_account["status"], round_num)
        print(f"     Strategy queries: {len(strategy_queries)}")
        for i, query in enumerate(strategy_queries[:2], 1):
            print(f"       {i}. {query}")
        
        print()

def main():
    """Run all tests."""
    print("🚀 Enhanced Knowledgebase Testing Suite")
    print("=" * 50)
    print()
    
    # Run all tests
    test_creditor_classification()
    test_query_generation()
    test_comprehensive_search()
    test_utilization_improvement()
    test_round_based_queries()
    
    print("✅ Enhanced Knowledgebase Testing Complete!")
    print()
    print("📊 Expected Improvements:")
    print("  • Query patterns: 2-3 → 10-15 per account")
    print("  • Knowledgebase utilization: 10-15% → 60-80%")
    print("  • Template integration: 0 → 3-5 templates per letter")
    print("  • Case law references: 0 → 2-3 precedents per dispute")
    print("  • Creditor-specific tactics: 0 → targeted approaches")
    print("  • Round-based strategies: 0 → escalation tactics")

if __name__ == "__main__":
    main()
