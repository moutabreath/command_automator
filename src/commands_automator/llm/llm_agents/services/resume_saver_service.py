import logging
import re

from commands_automator.llm.llm_agents.services.file_stylers import docx_styler



class ResumeSaverService:

    def save_file(self, text, output_file_path, applicant_name, file_name, resume_highlighted_sections = []):                
        try:
            docx_styler.save_text_as_word(f'{output_file_path}/{file_name}.docx', applicant_name, text, resume_highlighted_sections)
        except Exception as ex:
            logging.error(f"error saving word file {ex}", exc_info=True)

    def get_resume_file_name(self, text, applicant_name):
        pattern = re.compile(f"{applicant_name}[^ \n]*", re.IGNORECASE)
        match = pattern.search(text)
        try:
            if match:
                resume_file_name = match.group()
                logging.log(logging.DEBUG, f"found full string {resume_file_name}")    
                return resume_file_name
        except Exception:
            logging.error("Error saving resume", exc_info=True)
            return ""