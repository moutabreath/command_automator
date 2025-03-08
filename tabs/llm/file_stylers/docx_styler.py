from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def save_resume_as_word(file_path, resume_text):
    # Create a Word document
    doc = Document()

    # Add the main text with bold formatting
    p = doc.add_paragraph()
    run = p.add_run("Tal Druckmann")
    run.bold = True
    p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    # Split the resume text into lines
    lines = resume_text.split('\n')

    # Add the resume content
    for line in lines:
        if line.startswith('-'):
            # Add bullet points
            p = doc.add_paragraph(line, style='ListBullet')
        else:
            # Add regular text
            p = doc.add_paragraph(line)

    # Save the document
    doc.save(file_path)