import logging
import re

from llm.llm_agents.agent_services.file_stylers import docx_styler


class ResumeSaverService:

    def save_resume(self, text, output_file_path, applicant_name, resume_file_name, resume_highlighted_sections):                
        docx_styler.save_text_as_word(f'{output_file_path}/{resume_file_name}.docx', applicant_name, text, resume_highlighted_sections)

    def save_cover_letter(self, text, output_file_path, applicant_name, resume_file_name):
        docx_styler.save_text_as_word(f'{output_file_path}/{resume_file_name}_Cover_Letter.docx', applicant_name, text)

        

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