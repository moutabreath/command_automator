import json
import logging

from commands_automator.llm.llm_agents.agent_services.resume_saver_service import ResumeSaverService


class ResumeRefinerService:
    def __init__(self, resume_chat):
        self.resume_saver_service: ResumeSaverService = ResumeSaverService()
        self.resume_chat = resume_chat


    def refine_resume(self, tool_result, output_file_path):
        try:
            resume_data_dict = json.loads(tool_result)
        except json.JSONDecodeError as jde:
            logging.error(f"error with json structure of tool {jde}")
            return ""
        resume_text = self.get_refined_resume(resume_data_dict)
        cover_letter_text = self.get_cover_letter(resume_data_dict)
        self.save_resume_files(output_file_path, resume_data_dict, resume_text, cover_letter_text)
        return resume_text + "\n\n" + cover_letter_text
        
    
    def get_refined_resume(self, resume_data_dict):
        prompt = self.format_prompts_for_resume(resume_data_dict)
        self.resume_chat._config["response_mime_type"] = "text/plain"
        gemini_response = self.resume_chat.send_message(prompt)
        resume_text = gemini_response._get_text()
        return resume_text
        
    def format_prompts_for_resume(self, resume_data_dict):       
        general_guidelines = resume_data_dict.get('general_guidelines', '')
        resume = resume_data_dict.get('resume', '')        
        jobs_desc = self.convert_none_to_empty_string(resume_data_dict.get('job_description', ''))
     
        prompt = f"""You have finished using the mcp tool. Now output text according to the following guidelines.\n\n
                    {general_guidelines}\n\n{resume}\n\n\n"""
        prompt += jobs_desc
        return prompt 

    
    def save_resume_files(self, output_file_path, resume_data_dict, resume_text, cover_letter_text):
        resume_highlighted_sections = self.convert_none_to_empty_string(resume_data_dict.get('resume_highlighted_sections', ''))
        applicant_name = resume_data_dict.get('applicant_name', '')
        resume_file_name = self.resume_saver_service.get_resume_file_name(resume_text, applicant_name)
        self.resume_saver_service.save_resume(resume_text, output_file_path, applicant_name, resume_file_name, resume_highlighted_sections)
        if (cover_letter_text != ''):
            self.resume_saver_service.save_cover_letter(cover_letter_text, output_file_path, applicant_name, resume_file_name)


    def get_cover_letter(self, resume_data_dict):
        cover_letter_guidelines = resume_data_dict.get('cover_letter_guidelines', '')
        cover_letter_text = ''
        if cover_letter_guidelines is not None:
            gemini_response = self.resume_chat.send_message(cover_letter_guidelines)
            cover_letter_text = gemini_response._get_text()
        return cover_letter_text


    def convert_none_to_empty_string(self, text):
        if text == None:
            return ""
        return text