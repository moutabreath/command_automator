import re
from docx import Document
import docx
from docx.shared import Pt
from docx.shared import RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.oxml.shared import OxmlElement

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
        url = extract_link(line)
        if  url is not None:                    
            link_name = "link"
            if line.find('linkedin') != -1:
                link_name = "linkedin"
            if line.find('github') != -1:
                link_name = 'github'
            line = line.replace(url, '')
            p = doc.add_paragraph(line)
            add_link(doc, link_name, url)
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

def extract_link(text):
    # Regex pattern to find URLs
    pattern =  r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None

def add_link(doc, link_name, url):
    paragraph = doc.add_paragraph()
    # This gets access to the document.xml.rels file and gets a new relation id value
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    # Create the w:hyperlink tag and add needed values
    hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
    hyperlink.set(docx.oxml.shared.qn('r:id'), r_id, )

    # Create a new run object (a wrapper over a 'w:r' element)
    new_run = docx.text.run.Run(
        docx.oxml.shared.OxmlElement('w:r'), paragraph)
    new_run.text = link_name

    new_run.font.color.rgb = docx.shared.RGBColor(0, 0, 255)
    new_run.font.underline = True

    # Join all the xml elements together
    hyperlink.append(new_run._element)
    paragraph._p.append(hyperlink)
    return hyperlink

#This is only needed if you're using the builtin style above
def get_or_create_hyperlink_style(d):
    """If this document had no hyperlinks so far, the builtin
       Hyperlink style will likely be missing and we need to add it.
       There's no predefined value, different Word versions
       define it differently.
       This version is how Word 2019 defines it in the
       default theme, excluding a theme reference.
    """
    if "Hyperlink" not in d.styles:
        if "Default Character Font" not in d.styles:
            ds = d.styles.add_style("Default Character Font",
                                    docx.enum.style.WD_STYLE_TYPE.CHARACTER,
                                    True)
            ds.element.set(docx.oxml.shared.qn('w:default'), "1")
            ds.priority = 1
            ds.hidden = True
            ds.unhide_when_used = True
            del ds
        hs = d.styles.add_style("Hyperlink",
                                docx.enum.style.WD_STYLE_TYPE.CHARACTER,
                                True)
        hs.base_style 

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