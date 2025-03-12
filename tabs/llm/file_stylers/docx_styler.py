from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def save_resume_as_word(file_path, applicant_name, resume_text):
    # Create a Word document
    doc = Document()

    # Add the main text with bold formatting
    p = doc.add_paragraph()
    run = p.add_run(applicant_name)
    run.bold = True
    p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    # Split the resume text into lines
    lines = resume_text.split('\n')

    # Add the resume content
    for line in lines:
        if line.startswith('**'):
            # Remove the ** and add as bold text
            p = doc.add_paragraph()
            if line.endswith('**'):
                line = line[:-2]
            run = p.add_run(line[2:])  # Remove the first two characters (**)
            run.bold = True
        elif line.startswith('-'):
            # Add bullet points
            p = doc.add_paragraph(line[1:], style='ListBullet')
        else:
            # Add regular text
            p = doc.add_paragraph(line)

    # Save the document
    doc.save(file_path)