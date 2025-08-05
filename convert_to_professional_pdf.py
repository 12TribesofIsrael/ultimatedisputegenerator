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
        if 'Dear Experian' in line or 'Dear' in line and 'Credit Bureau' in line:
            content_start = i
            break
        elif 'I am writing to formally' in line:
            content_start = i
            break
    
    # Extract letter body
    letter_body = []
    for line in lines[content_start:]:
        if line.strip() and not line.startswith('**') and not line.startswith('#'):
            letter_body.append(line.strip())
    
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
    story.append(Paragraph("Experian Information Solutions, Inc.", header_style))
    story.append(Paragraph("Attn: Dispute Department", header_style))
    story.append(Paragraph("P.O. Box 4500", header_style))
    story.append(Paragraph("Allen, TX 75013", header_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Subject line
    story.append(Paragraph("Re: Demand for Immediate Deletion - FCRA Violations", title_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Salutation
    story.append(Paragraph("Dear Experian,", body_style))
    
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
    story.append(Paragraph("[Your Signature]", body_style))
    
    # Add certified mail tracking
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("SENT VIA CERTIFIED MAIL", body_style))
    story.append(Paragraph("Tracking Number: [Insert tracking number]", body_style))
    story.append(Paragraph("CC: Consumer Financial Protection Bureau (CFPB)", body_style))
    
    # Build the PDF
    doc.build(story)
    print(f"Professional PDF created: {output_file}")

def create_editable_text_file(markdown_file, text_file, consumer_name):
    """Step 1: Convert markdown to clean, editable text file"""
    
    print(f"Converting {markdown_file} to editable text...")
    
    # Read the markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Extract and clean content
    professional_content = extract_professional_content(markdown_content)
    
    # Create editable text format with proper business letter structure
    text_content = f"""[YOUR NAME]
[YOUR COMPLETE ADDRESS]
[CITY, STATE ZIP CODE]
[YOUR PHONE NUMBER]
[YOUR EMAIL ADDRESS]

{datetime.now().strftime('%B %d, %Y')}

Experian Information Solutions, Inc.
Attn: Dispute Department
P.O. Box 4500
Allen, TX 75013

Re: Demand for Immediate Deletion - FCRA Violations

Dear Experian,

{professional_content}

Sincerely,

[YOUR SIGNATURE]
{consumer_name}

SENT VIA CERTIFIED MAIL
Tracking Number: [INSERT TRACKING NUMBER]
CC: Consumer Financial Protection Bureau (CFPB)
"""
    
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

def main():
    """Main execution with two-step process"""
    import sys
    
    # Input files
    markdown_file = Path("outputletter/ULTIMATE_DELETION_DEMAND_KNOWLEDGEBASE.md")
    consumer_name = "Marnaysha Alicia Lee"
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Output files
    text_file = Path(f"outputletter/EDITABLE_DISPUTE_LETTER_{consumer_name.replace(' ', '_')}_{date_str}.txt")
    pdf_file = Path(f"outputletter/PROFESSIONAL_DELETION_DEMAND_{consumer_name.replace(' ', '_')}_{date_str}.pdf")
    
    # Check if user wants step 1 or step 2
    if len(sys.argv) > 1 and sys.argv[1] == "pdf":
        # Step 2: Convert text to PDF
        if not text_file.exists():
            print(f"Error: Editable text file not found: {text_file}")
            print(f"Run the script without 'pdf' argument first to create the text file.")
            return
        
        create_pdf_from_text(text_file, pdf_file, consumer_name)
        
        print(f"\n=== STEP 2 COMPLETE - PDF READY FOR MAILING ===")
        print(f"Edited Text File: {text_file}")  
        print(f"Professional PDF: {pdf_file}")
        print(f"✅ Ready for printing, signing, and certified mail!")
        
    else:
        # Step 1: Create editable text file
        if not markdown_file.exists():
            print(f"Error: Markdown file not found: {markdown_file}")
            return
        
        create_editable_text_file(markdown_file, text_file, consumer_name)
        
        print(f"\n=== STEP 1 COMPLETE - TEXT FILE READY FOR EDITING ===")
        print(f"Original Markdown: {markdown_file}")
        print(f"Editable Text File: {text_file}")
        print(f"Consumer: {consumer_name}")
        
        print(f"\n📝 NEXT STEPS:")
        print(f"1. ✏️  EDIT the text file: {text_file}")
        print(f"2. ✅  Add any additional content you want")
        print(f"3. 🔧  Customize address fields and details")
        print(f"4. 🚀  Run 'python convert_to_professional_pdf.py pdf' to create PDF")
        
        print(f"\n💡 The text file has:")
        print(f"✅ All emojis removed")
        print(f"✅ Professional business letter format")
        print(f"✅ Placeholder fields for your information")
        print(f"✅ Legal content preserved")
        print(f"✅ Ready for your manual edits")

if __name__ == "__main__":
    main()