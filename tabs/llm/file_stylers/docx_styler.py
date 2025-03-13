from docx import Document
from docx.shared import Pt
from docx.shared import RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def save_resume_as_word(file_path, applicant_name, resume_text):
    # Create a Word document
    doc = Document()
    keywords = ["education", "professional experience", "about me", "contact"]    
    
    style = doc.styles['Normal']
    style.paragraph_format.line_spacing_rule = 1

    # Add the main text with bold formatting
    p = doc.add_paragraph()
    run = p.add_run(applicant_name)
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 255)
    p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    # Split the resume text into lines
    lines = resume_text.split('\n')

    # Add the resume content
    for line in lines:    
        is_header = add_header(doc, keywords, line)
        if is_header:
            is_header = False
            continue

        if "*" in line:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
     
            run = p.add_run(line) 
            run.bold = True
        elif line.startswith('-'):
            p = doc.add_paragraph(line[1:], style='ListBullet')
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)

        else:
            p = doc.add_paragraph(line)

    doc.save(file_path)

def add_header(doc, keywords, line):
    text = line.lower() 
    is_header = False       
    for keyword in keywords:
        if keyword in text:
            p = doc.add_paragraph()
            run = p.add_run(line)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run.bold = True                
            run.font.color.rgb = RGBColor(0, 0, 255)
            is_header = True
            break
    return is_header