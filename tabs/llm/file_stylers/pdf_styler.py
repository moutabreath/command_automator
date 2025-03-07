from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, ListItem, ListFlowable

def save_text_as_pdf(file_path, text, bullet_points):
    # Create a PDF document
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Define a custom style for bold text
    bold_style = ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='Helvetica-Bold')

    # Create a list of flowables (elements to be added to the PDF)
    flowables = []

    # Add the main text with bold formatting
    flowables.append(Paragraph(text, bold_style))

    # Add bullet points
    bullet_items = [ListItem(Paragraph(item, styles['Normal'])) for item in bullet_points]
    bullet_list = ListFlowable(bullet_items, bulletType='bullet', start='circle')
    flowables.append(bullet_list)

    # Build the PDF
    doc.build(flowables)

# Example usage
file_path = 'output.pdf'
text = 'This is some bold text.'
bullet_points = ['Bullet point 1', 'Bullet point 2', 'Bullet point 3']
save_text_as_pdf(file_path, text, bullet_points)