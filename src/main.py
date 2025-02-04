"""
XML Subtitle to PDF Converter
- Parses XML subtitle file
- Extracts text and timestamps
- Creates formatted PDF output
"""

import xml.etree.ElementTree as ET
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def parse_subtitle_xml(xml_file):
    """
    Parse XML file and extract timestamp and text content.
    
    Args:
        xml_file: Path to XML subtitle file
    Returns:
        List of tuples containing (timestamp, text)
    """
    # Parse XML with namespace handling
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Extract namespace from root tag
    namespace = root.tag.split('}')[0] + '}'
    
    subtitles = []
    
    # Find all paragraph elements
    for p in root.findall(f".//{namespace}p"):
        timestamp = p.get('begin')
        
        # Extract text from spans and handle line breaks
        text_parts = []
        for element in p:
            if element.tag == f"{namespace}span":
                text_parts.append(element.text)
            elif element.tag == f"{namespace}br":
                text_parts.append("\n")
                
        text = " ".join(filter(None, text_parts))
        subtitles.append((timestamp, text))
    
    return subtitles

def create_pdf(subtitles, output_file):
    """
    Create PDF document from subtitle data.
    
    Args:
        subtitles: List of (timestamp, text) tuples
        output_file: Path for output PDF
    """
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create custom styles
    styles = getSampleStyleSheet()
    timestamp_style = ParagraphStyle(
        'TimestampStyle',
        parent=styles['Normal'],
        textColor=colors.blue,
        fontSize=10,
        spaceAfter=5
    )
    text_style = ParagraphStyle(
        'TextStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceAfter=20
    )
    
    # Build document content
    story = []
    
    # Add title
    title = Paragraph("Subtitle Script", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 30))
    
    # Add subtitle entries
    for timestamp, text in subtitles:
        # Add timestamp
        time_para = Paragraph(f"[{timestamp}]", timestamp_style)
        story.append(time_para)
        
        # Add text (replace \n with <br/>)
        text = text.replace('\n', '<br/>')
        text_para = Paragraph(text, text_style)
        story.append(text_para)
    
    # Build PDF
    doc.build(story)

def main():
    """Main function to process XML and create PDF."""
    try:
        # Process XML and create PDF
        input_file = "subtitles.xml"  # Replace with your input file
        output_file = "subtitle_script.pdf"
        
        print("Parsing XML file...")
        subtitles = parse_subtitle_xml(input_file)
        
        print("Creating PDF...")
        create_pdf(subtitles, output_file)
        
        print(f"PDF created successfully: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()