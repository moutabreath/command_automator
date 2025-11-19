import logging
import re
from pathlib import Path

from llm.llm_agents.services.file_stylers import docx_styler



class ResumeSaverService:

    def save_file(self, text, output_file_path, applicant_name, file_name, resume_highlighted_sections=None):
        if resume_highlighted_sections is None:
            resume_highlighted_sections = []        
        try:
           file_path = Path(output_file_path) / f'{file_name}.docx'
           docx_styler.save_text_as_word(str(file_path), applicant_name, text, resume_highlighted_sections)
           return True
        except Exception as ex:
            logging.error(f"error saving word file {ex}", exc_info=True)
            return False

    def get_resume_file_name(self, text, applicant_name):        
        try:
            pattern = re.compile(f"{re.escape(applicant_name)}[^ \n]*", re.IGNORECASE)
            match = pattern.search(text)
            if match:
                resume_file_name = match.group()
                logging.debug(f"found full string {resume_file_name}")    
                return resume_file_name
            return ""
        except Exception:
            logging.error("Error extracting resume", exc_info=True)
            return ""