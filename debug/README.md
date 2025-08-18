# Debug and Utility Scripts

This folder contains debugging, testing, and utility scripts for the Ultimate Dispute Letter Generator.

## Script Categories

### Debug Scripts (`debug_*.py`)
- **`debug_filtering.py`** - Test filtering logic after positive status fixes
- **`debug_duplicates.py`** - Examine duplicate account detection
- **`debug_apple_card.py`** - Debug APPLE CARD extraction from Experian reports
- **`debug_apple_card_detailed.py`** - Detailed APPLE CARD analysis
- **`debug_positive_accounts.py`** - Test positive account detection
- **`debug_positive_detection.py`** - Debug positive account identification
- **`debug_late_extraction.py`** - Test late payment entry extraction
- **`debug_dept_ed.py`** - Debug Department of Education account handling
- **`debug_all_filtering.py`** - Comprehensive filtering tests
- **`debug_template.py`** - Template debugging utilities

### Test Scripts (`test_*.py`)
- **`test_harness.py`** - Main test harness for PDF parsing and OCR functionality
- **`test_positive_fix.py`** - Test positive account fixes
- **`test_regressions.py` - Regression testing suite
- **`enhanced_test_suite.py`** - Comprehensive test suite with edge case coverage and performance testing

### Letter Generation (`generate_*.py`)
- **`generate_next_round.py`** - Generate next-round dispute letters based on analysis results
- **`version_info.py`** - Version management and release notes generation

### Performance & Optimization (`performance_*.py`)
- **`performance_optimizer.py`** - Performance profiling, benchmarking, and optimization utilities

### Quick Utilities (`quick_*.py`)
- **`quick_95_percent.py`** - Quick 95% processing utility
- **`quick_enhance_ingest.py`** - Quick enhanced ingestion
- **`quick_organize.py`** - Quick file organization
- **`quick_status.py`** - Quick status checking

### Non-Interactive Scripts (`noninteractive_*.py`)
- **`noninteractive_generate.py`** - Non-interactive letter generation
- **`noninteractive_generate_transunion.py`** - TransUnion-specific generation

### Document Conversion (`convert_*.py`)
- **`convert_doc_simple.py`** - Simple DOC to PDF conversion
- **`convert_doc_to_pdf.py`** - DOC to PDF conversion
- **`convert_unindexed_doc_to_pdf.py`** - Convert unindexed DOC files
- **`convert_to_professional_pdf.py`** - Convert to professional PDF format

### Ingestion Scripts (`*ingest*.py`)
- **`knowledgebase_ingest.py`** - Knowledgebase ingestion
- **`fast_ingest.py`** - Fast ingestion utility
- **`visible_ingest.py`** - Visible ingestion process
- **`enhanced_ingest.py`** - Enhanced ingestion
- **`ingestion_monitor.py`** - Monitor ingestion process
- **`monitored_ingestion.py`** - Monitored ingestion

### Document Processing (`simple_doc_processor*.py`)
- **`simple_doc_processor.py`** - Simple document processor
- **`simple_doc_processor_fixed.py`** - Fixed version of document processor

### Other Utilities
- **`robust_doc_converter.py`** - Robust document conversion
- **`organize_unprocessable_files.py`** - Organize unprocessable files
- **`analyze_coverage_gaps.py`** - Analyze coverage gaps
- **`list_kb_index_status.py`** - List knowledgebase index status
- **`clean_workspace.py`** - Clean workspace utilities

## Usage

Most scripts can be run directly from this directory. For example:

```bash
# Run the main test harness
python debug/test_harness.py

# Test specific functionality
python debug/debug_filtering.py

# Generate next-round letters
python debug/generate_next_round.py analysis_Experian.json 2
python debug/generate_next_round.py analysis_Equifax.json 3

# Version management
python debug/version_info.py --version
python debug/version_info.py --update minor
python debug/version_info.py --release-notes

# Enhanced testing
python debug/enhanced_test_suite.py

# Performance optimization
python debug/performance_optimizer.py --all

# Quick utilities
python debug/quick_status.py
```

## Notes

- These scripts are primarily for development, testing, and debugging
- Some scripts may have dependencies on specific file structures or data
- Always check the script's docstring for specific usage instructions
- The main application entry point is `extract_account_details.py` in the root directory
