#!/usr/bin/env python3
"""
Professional PDF Converter for Dispute Letters
Converts markdown dispute letters to professional PDF format for mailing
Based on knowledgebase formatting standards
"""

import re
import markdown
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

def remove_emojis_and_formatting(text):
    """Remove all emojis and markdown formatting for professional appearance"""
    
    # Remove emojis using regex
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", flags=re.UNICODE)
    
    text = emoji_pattern.sub(r'', text)
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold** -> text
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic* -> text
    text = re.sub(r'`(.*?)`', r'\1', text)        # `code` -> text
    text = re.sub(r'#{1,6}\s*', '', text)         # # headers -> plain text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](link) -> text
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)  # bullets
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # numbered lists
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)  # quotes
    text = re.sub(r'---+', '', text)  # horizontal rules
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)  # code blocks
    
    # Clean up multiple spaces and line breaks
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # max 2 line breaks
    text = re.sub(r' +', ' ', text)  # multiple spaces -> single space
    
    return text.strip()

def extract_professional_content(markdown_content):
    """Extract and structure content for professional letter format"""
    
    # Clean the content
    clean_content = remove_emojis_and_formatting(markdown_content)
    
    # Extract key components
    lines = clean_content.split('\n')
    
    # Find the main letter content (skip title and headers)
    content_start = 0
    for i, line in enumerate(lines):
        if 'Dear' in line and any(bureau in line for bureau in ['Experian', 'Equifax', 'TransUnion']):
            content_start = i
            break
        elif 'I am writing to formally' in line:
            content_start = i
            break
    
    # Extract letter body, skipping the salutation line since we'll add our own
    letter_body = []
    skip_salutation = False
    for line in lines[content_start:]:
        line_stripped = line.strip()
        # Skip the "Dear [Bureau]," line since we'll add our own
        if line_stripped.startswith('Dear ') and ('Experian' in line_stripped or 'Equifax' in line_stripped or 'TransUnion' in line_stripped):
            skip_salutation = True
            continue
        if line_stripped and not line_stripped.startswith('**') and not line_stripped.startswith('#'):
            letter_body.append(line_stripped)
    
    return '\n\n'.join(letter_body)

def create_professional_pdf(input_file, output_file, consumer_name, consumer_address=None):
    """Create professional PDF from markdown dispute letter"""
    
    print(f"Converting {input_file} to professional PDF...")
    
    # Read the markdown file
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Extract professional content
    professional_content = extract_professional_content(markdown_content)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=letter,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles for professional letter
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leftIndent=0,
        rightIndent=0
    )
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_LEFT,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    # Build the document content
    story = []
    
    # Header block (consumer information)
    if not consumer_address:
        consumer_address = [
            "[Your Complete Address]",
            "[City, State ZIP Code]",
            "[Your Phone Number]",
            "[Your Email Address]"
        ]
    
    story.append(Paragraph(consumer_name, header_style))
    for addr_line in consumer_address:
        story.append(Paragraph(addr_line, header_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Date
    current_date = datetime.now().strftime('%B %d, %Y')
    story.append(Paragraph(current_date, header_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Recipient block
    # Credit Bureau address block - Smart detection
    bureau_info = detect_bureau_from_markdown(markdown_content)
    bureau_name = bureau_info['name']
    bureau_company = bureau_info['company']
    bureau_address_lines = bureau_info['address'].split('\n')
    
    print(f"📄 PDF Bureau detected: {bureau_name}")
    
    story.append(Paragraph(bureau_company, header_style))
    story.append(Paragraph("Attn: Dispute Department", header_style))
    for address_line in bureau_address_lines:
        story.append(Paragraph(address_line, header_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Subject line
    story.append(Paragraph("Re: Demand for Immediate Deletion - FCRA Violations", title_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Salutation
    # Greeting - Dynamic based on detected bureau
    story.append(Paragraph(f"Dear {bureau_name},", body_style))
    
    # Process the professional content into paragraphs
    paragraphs = professional_content.split('\n\n')
    
    for para in paragraphs:
        if para.strip():
            # Clean up the paragraph
            clean_para = para.strip()
            
            # Skip empty paragraphs or titles
            if len(clean_para) < 10 or clean_para.upper() == clean_para:
                continue
                
            # Handle section headers
            if clean_para.endswith(':') and len(clean_para) < 100:
                story.append(Paragraph(clean_para, title_style))
            else:
                # Regular paragraph
                story.append(Paragraph(clean_para, body_style))
    
    # Professional closing
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Sincerely,", body_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(consumer_name, body_style))
    
    # Extract certified mail tracking and AG CC from markdown (if present)
    tracking_number = None
    ag_cc_line = None
    try:
        m_track = re.search(r"\*\*CERTIFIED MAIL TRACKING:\*\*\s*([^\n]+)", markdown_content)
        if not m_track:
            m_track = re.search(r"CERTIFIED MAIL TRACKING:\s*([^\n]+)", markdown_content, flags=re.IGNORECASE)
        if m_track:
            tracking_number = m_track.group(1).strip()
            if '[' in tracking_number or 'Insert' in tracking_number:
                tracking_number = None
        m_ag = re.search(r"\*\*CC:\*\*\s*([^\n]*Attorney General\'s Office)", markdown_content, flags=re.IGNORECASE)
        if not m_ag:
            m_ag = re.search(r"CC:\s*([^\n]*Attorney General\'s Office)", markdown_content, flags=re.IGNORECASE)
        if m_ag:
            ag_cc_line = m_ag.group(1).strip()
            ag_cc_line = re.sub(r"\s+", " ", ag_cc_line)
            if '[' in ag_cc_line:
                ag_cc_line = None
    except Exception:
        pass

    # Add mailing/CC lines
    story.append(Spacer(1, 0.3*inch))
    if tracking_number:
        story.append(Paragraph("SENT VIA CERTIFIED MAIL", body_style))
        story.append(Paragraph(f"Tracking Number: {tracking_number}", body_style))
    story.append(Paragraph("CC: Consumer Financial Protection Bureau (CFPB)", body_style))
    if ag_cc_line:
        story.append(Paragraph(f"CC: {ag_cc_line}", body_style))
    
    # Build the PDF
    doc.build(story)
    print(f"Professional PDF created: {output_file}")

def detect_bureau_from_markdown(markdown_content):
    """Detect which bureau this letter is for from the markdown content"""
    content_lower = markdown_content.lower()
    
    # Order matters; check for specific bureau names
    if "equifax" in content_lower:
        return {
            "name": "Equifax",
            "company": "Equifax Information Services LLC",
            "address": "P.O. Box 740256\nAtlanta, GA 30374",
        }
    if "experian" in content_lower:
        return {
            "name": "Experian",
            "company": "Experian Information Solutions, Inc.",
            "address": "P.O. Box 4500\nAllen, TX 75013",
        }
    if "transunion" in content_lower or "trans union" in content_lower:
        return {
            "name": "TransUnion",
            "company": "TransUnion Consumer Solutions",
            "address": "P.O. Box 2000\nChester, PA 19016-2000",
        }
    else:
        # Default fallback
        return {
            "name": "Credit Bureau",
            "company": "[CREDIT BUREAU NAME]",
            "address": "[CREDIT BUREAU ADDRESS]"
        }

def extract_consumer_info_from_markdown(markdown_content):
    """Extract consumer name and address from markdown file"""
    consumer_info = {
        'name': 'Consumer Name',
        'address': 'Consumer Address'
    }
    
    try:
        # Extract name from "**From:** Name" pattern
        name_match = re.search(r'\*\*From:\*\*\s+(.+)', markdown_content)
        if name_match:
            consumer_info['name'] = name_match.group(1).strip()
        
        # Extract address from "**Address:** address" pattern (consumer's address, not bureau's)
        # Look for the consumer address pattern specifically - the one that comes after "**From:**"
        lines = markdown_content.split('\n')
        for i, line in enumerate(lines):
            if '**From:**' in line:
                # Found the From line, now look for the next Address line
                for j in range(i + 1, min(i + 5, len(lines))):  # Look within next 5 lines
                    if '**Address:**' in lines[j]:
                        address_raw = lines[j].replace('**Address:**', '').strip()
                        address_lines = [line.strip() for line in address_raw.split(';') if line.strip()]
                        consumer_info['address'] = '\n'.join(address_lines)
                        break
                break  # Found the consumer From/Address pair, stop looking
        
        # If that didn't work, try to extract from signature block
        if consumer_info['address'] == 'Consumer Address':
            sig_match = re.search(r'Sincerely,\s*\n\s*(.+?)\n(.+?)\n(.+?)(?:\n|$)', markdown_content, re.MULTILINE | re.DOTALL)
            if sig_match:
                potential_name = sig_match.group(1).strip()
                address_line1 = sig_match.group(2).strip()
                address_line2 = sig_match.group(3).strip()
                
                # Use signature info if we didn't get it from header
                if not name_match and not potential_name.startswith('[') and len(potential_name.split()) >= 2:
                    consumer_info['name'] = potential_name
                
                # Build address from signature block
                if not address_line1.startswith('[') and not address_line2.startswith('['):
                    consumer_info['address'] = f"{address_line1}\n{address_line2}"
        
        print(f"📋 Extracted consumer info: {consumer_info['name']}")
        print(f"📋 Extracted address: {consumer_info['address']}")
        
    except Exception as e:
        print(f"⚠️ Error extracting consumer info: {e}")
    
    return consumer_info

def create_editable_text_file(markdown_file, text_file, consumer_name):
    """Step 1: Convert markdown to clean, editable text file with smart bureau detection"""
    
    print(f"Converting {markdown_file} to editable text...")
    
    # Read the markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Extract consumer information from the markdown file
    consumer_info = extract_consumer_info_from_markdown(markdown_content)
    
    # Detect which bureau this letter is for
    bureau_info = detect_bureau_from_markdown(markdown_content)
    bureau_name = bureau_info['name']
    bureau_company = bureau_info['company']
    bureau_address = bureau_info['address']
    
    print(f"📄 Detected bureau: {bureau_name}")
    print(f"👤 Using consumer info: {consumer_info['name']}")
    
    # Extract and clean content
    professional_content = extract_professional_content(markdown_content)

    # Extract certified mail tracking and AG CC from markdown (if present)
    tracking_number = None
    ag_cc_line = None
    try:
        m_track = re.search(r"\*\*CERTIFIED MAIL TRACKING:\*\*\s*([^\n]+)", markdown_content)
        if not m_track:
            m_track = re.search(r"CERTIFIED MAIL TRACKING:\s*([^\n]+)", markdown_content, flags=re.IGNORECASE)
        if m_track:
            tracking_number = m_track.group(1).strip()
            # Filter out placeholder-y values
            if '[' in tracking_number or 'Insert' in tracking_number:
                tracking_number = None
        m_ag = re.search(r"\*\*CC:\*\*\s*([^\n]*Attorney General\'s Office)", markdown_content, flags=re.IGNORECASE)
        if not m_ag:
            m_ag = re.search(r"CC:\s*([^\n]*Attorney General\'s Office)", markdown_content, flags=re.IGNORECASE)
        if m_ag:
            ag_cc_line = m_ag.group(1).strip()
            # Normalize spacing/casing a bit
            ag_cc_line = re.sub(r"\s+", " ", ag_cc_line)
            # Drop placeholder values
            if '[' in ag_cc_line:
                ag_cc_line = None
    except Exception:
        pass
    
    # Create editable text format with actual consumer information
    text_content = f"""{consumer_info['name']}
{consumer_info['address']}

{datetime.now().strftime('%B %d, %Y')}

{bureau_company}
Attn: Dispute Department
{bureau_address}

Re: Demand for Immediate Deletion - FCRA Violations

Dear {bureau_name},

{professional_content}

Sincerely,

{consumer_info['name']}

"""

    # Append mailing and CC lines conditionally
    footer_lines = []
    if tracking_number:
        footer_lines.append("SENT VIA CERTIFIED MAIL")
        footer_lines.append(f"Tracking Number: {tracking_number}")
    # Always include CFPB CC
    footer_lines.append("CC: Consumer Financial Protection Bureau (CFPB)")
    if ag_cc_line:
        footer_lines.append(f"CC: {ag_cc_line}")

    if footer_lines:
        text_content = text_content + "\n" + "\n".join(footer_lines) + "\n"
    
    # Write to text file
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    print(f"✅ Editable text file created: {text_file}")
    return text_content

def create_pdf_from_text(text_file, pdf_file, consumer_name):
    """Step 2: Convert edited text file to professional PDF"""
    
    print(f"Converting edited text file to PDF...")
    
    # Read the edited text file
    with open(text_file, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=letter,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=12,
        leftIndent=0,
        rightIndent=0
    )
    
    # Build the document content
    story = []
    
    # Split content into paragraphs and process
    paragraphs = text_content.split('\n\n')
    
    for para in paragraphs:
        if para.strip():
            # Clean up the paragraph
            clean_para = para.strip()
            
            # Add paragraph to story
            story.append(Paragraph(clean_para.replace('\n', '<br/>'), body_style))
    
    # Build the PDF
    doc.build(story)
    print(f"✅ Professional PDF created: {pdf_file}")

def find_latest_bureau_files():
    """Find the most recent markdown file per bureau.

    Returns a list of tuples: [(md_path, bureau), ...] for all bureaus
    that have at least one markdown file.
    """
    results = []
    for bureau in ["Experian", "Equifax", "TransUnion"]:
        bureau_path = Path("outputletter") / bureau
        if not bureau_path.exists():
            continue
        latest_file = None
        latest_time = 0
        for md_file in bureau_path.glob("*.md"):
            try:
                file_time = md_file.stat().st_mtime
            except Exception:
                file_time = 0
            if file_time > latest_time:
                latest_time = file_time
                latest_file = md_file
        if latest_file is not None:
            results.append((latest_file, bureau))
    return results

def main():
    """Main execution - supports processing all bureaus in one run.

    Behavior (unchanged flow, enhanced scope):
    - No args: Create editable text for the latest markdown in each bureau folder.
    - 'pdf': Convert the corresponding editable text to PDF for each bureau.
    """
    import sys
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Find the latest bureau-specific files (one per bureau)
    items = find_latest_bureau_files()
    if not items:
        print("❌ No bureau-specific markdown files found!")
        print("💡 Run extract_account_details.py first to generate dispute letters")
        return
    
    pdf_mode = len(sys.argv) > 1 and sys.argv[1].lower() == 'pdf'
    
    if pdf_mode:
        print("📄 Converting edited text files to professional PDFs for available bureaus...")
        for latest_markdown, detected_bureau in items:
            try:
                with open(latest_markdown, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                consumer_info = extract_consumer_info_from_markdown(markdown_content)
                consumer_name = consumer_info['name']
                bureau_folder = Path("outputletter") / detected_bureau
                bureau_folder.mkdir(exist_ok=True)
                text_file = bureau_folder / f"EDITABLE_DISPUTE_LETTER_{consumer_name.replace(' ', '_')}_{date_str}.txt"
                pdf_file = bureau_folder / f"PROFESSIONAL_DELETION_DEMAND_{consumer_name.replace(' ', '_')}_{date_str}.pdf"
                if text_file.exists():
                    create_pdf_from_text(text_file, pdf_file, consumer_name)
                    print(f"✅ {detected_bureau}: PDF created: {pdf_file}")
                else:
                    print(f"⚠️  {detected_bureau}: Text file not found: {text_file} — run without 'pdf' first")
            except Exception as e:
                print(f"❌ {detected_bureau}: Failed to create PDF: {e}")
        print("\n=== PDF CONVERSION COMPLETE ===")
        return
    
    print("📄 Creating editable text files for available bureaus...")
    for latest_markdown, detected_bureau in items:
        try:
            with open(latest_markdown, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            consumer_info = extract_consumer_info_from_markdown(markdown_content)
            consumer_name = consumer_info['name']
            bureau_folder = Path("outputletter") / detected_bureau
            bureau_folder.mkdir(exist_ok=True)
            text_file = bureau_folder / f"EDITABLE_DISPUTE_LETTER_{consumer_name.replace(' ', '_')}_{date_str}.txt"
            create_editable_text_file(latest_markdown, text_file, consumer_name)
            print(f"✅ {detected_bureau}: Editable text created: {text_file}")
        except Exception as e:
            print(f"❌ {detected_bureau}: Failed to create editable text: {e}")
    
    print("\n=== TEXT FILE CREATION COMPLETE ===")

if __name__ == "__main__":
    main()
