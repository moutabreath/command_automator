import json
import logging
from google.genai.chats import Chat
from commands_automator.llm.llm_agents.agent_services.resume_saver_service import ResumeSaverService
from commands_automator.llm.llm_agents.gemini.gemini_utils import GeminiUtils

class ResumeRefinerService:
    def __init__(self, resume_chat: Chat, gemini_utils: GeminiUtils):
        self.resume_saver_service: ResumeSaverService = ResumeSaverService()
        self.resume_chat: Chat = resume_chat
        self.gemini_utils: GeminiUtils = gemini_utils


    def refine_resume(self, tool_result: str, output_file_path: str) -> str:
        try:
            resume_data_dict = json.loads(tool_result)
            if not isinstance(resume_data_dict, dict):
                logging.error(
                    "tool_result JSON must be an object; got %s",
                    type(resume_data_dict).__name__
                )
                return ""
        except (json.JSONDecodeError, TypeError) as exc:
            logging.exception("Failed to parse tool_result JSON: %s", exc,exc_info=True)
            return ""

        resume_text = self.get_refined_resume(resume_data_dict)
        cover_letter_text = self.get_cover_letter(resume_data_dict)
        self.save_resume_files(output_file_path, resume_data_dict, resume_text, cover_letter_text)

        if cover_letter_text:
            return resume_text + "\n\n" + cover_letter_text
        return resume_text        
    
    def get_refined_resume(self, resume_data_dict: dict) -> str:
        prompt = self.format_prompts_for_resume(resume_data_dict)
        resume_text = self.gemini_utils.get_response_from_gemini(prompt=prompt,
                                                                      chat=self.resume_chat)
       
        return resume_text
    
    def format_prompts_for_resume(self, resume_data_dict: dict) -> str:
        general_guidelines = resume_data_dict.get('general_guidelines', '')
        resume = resume_data_dict.get('resume', '')
        jobs_desc = resume_data_dict.get('job_description', '')

        prompt = f"""
You have finished using the mcp tool. Now output text according to the following guidelines.\n\n
{general_guidelines}
\n\nResume:\n\n {resume}
\n\n\nJob Description:\n\n
{jobs_desc}"""
        return prompt
    
    def get_cover_letter(self, resume_data_dict: dict) -> str:
        cover_letter_guidelines = resume_data_dict.get('cover_letter_guidelines', '')
        cover_letter_text = ''
        if cover_letter_guidelines:
            cover_letter_text= self.gemini_utils.get_response_from_gemini(prompt=cover_letter_guidelines, chat=self.resume_chat)         
        return cover_letter_text
    
    def save_resume_files(self, output_file_path, resume_data_dict, resume_text, cover_letter_text):
        resume_highlighted_sections = resume_data_dict.get('resume_highlighted_sections', '')
        applicant_name = resume_data_dict.get('applicant_name', '')
        resume_file_name = self.resume_saver_service.get_resume_file_name(resume_text, applicant_name)
        self.resume_saver_service.save_resume(resume_text, output_file_path, applicant_name, resume_file_name, resume_highlighted_sections)
        if (cover_letter_text != ''):
            self.resume_saver_service.save_cover_letter(cover_letter_text, output_file_path, applicant_name, resume_file_name)
