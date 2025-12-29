import json
import logging
from google.genai.chats import Chat

from llm.gemini.gemini_client_wrapper import GeminiClientWrapper, LLMAgentResponse, LLMResponseCode
from llm.llm_client.mcp_client import MCPResponse, MCPResponseCode
from llm.llm_client.services.resume_saver_service import ResumeSaverService

class ResumeRefinerService:
    def __init__(self, resume_chat: Chat, gemini_utils: GeminiClientWrapper):
        self.resume_saver_service: ResumeSaverService = ResumeSaverService()
        self.resume_chat: Chat = resume_chat
        self.gemini_agent: GeminiClientWrapper = gemini_utils


    async def refine_resume(self, tool_result: str, output_file_path: str) -> MCPResponse:
        try:
            resume_data_dict = json.loads(tool_result)
            if not isinstance(resume_data_dict, dict):
                error_msg = f"tool_result JSON must be an object; got {type(resume_data_dict).__name__}"
                logging.error(error_msg)
                return MCPResponse(error_msg, MCPResponseCode.ERROR_WITH_TOOL_RESPONSE)
        except (json.JSONDecodeError, TypeError) as exc:
            error_msg = f"Failed to parse tool_result JSON {exc}"
            logging.exception(error_msg)
            return MCPResponse(error_msg, MCPResponseCode.ERROR_WITH_TOOL_RESPONSE)

        refined_resume_response = await self.get_refined_resume(resume_data_dict)
        
        if refined_resume_response.code == MCPResponseCode.OK:
            return await self.save_resume_and_cover_letter(output_file_path, resume_data_dict, refined_resume_response)
        return refined_resume_response 
    
    async def save_resume_and_cover_letter(self, output_file_path, resume_data_dict, refined_resume_response):
        applicant_name = resume_data_dict.get('applicant_name', '')
        resume_highlighted_sections = resume_data_dict.get('resume_highlighted_sections', '')
            
        resume_file_name = self.resume_saver_service.get_resume_file_name(
                text=refined_resume_response.text,
                applicant_name=applicant_name,
                )
            
        self.resume_saver_service.save_file(
                text=refined_resume_response.text,
                output_file_path=output_file_path,
                applicant_name=applicant_name,
                file_name=resume_file_name,                                                 
                resume_highlighted_sections=resume_highlighted_sections
                )
            
        text = refined_resume_response.text
        cover_letter_response = await self.get_cover_letter(resume_data_dict)
        if cover_letter_response.code == MCPResponseCode.OK:
            cover_letter_file_name = f"{resume_file_name}_Cover_Letter"
            self.resume_saver_service.save_file(cover_letter_response.text, output_file_path, applicant_name, cover_letter_file_name)
            text = f"{text}\n\n\n{cover_letter_response.text}"
        return MCPResponse(text=text,code=MCPResponseCode.OK)
    
    async def get_refined_resume(self, resume_data_dict: dict) -> MCPResponse:
        prompt = self.format_prompts_for_resume(resume_data_dict)
        resume_response: LLMAgentResponse = await self.gemini_agent.get_response_from_gemini(prompt=prompt,
                                                                      chat=self.resume_chat)
        if resume_response.code == LLMResponseCode.OK:
            return MCPResponse(resume_response.text, MCPResponseCode.OK)
        if resume_response.code == LLMResponseCode.MODEL_OVERLOADED:
            return MCPResponse(resume_response.text, MCPResponseCode.ERROR_MODEL_OVERLOADED)
        return MCPResponse(resume_response.text, MCPResponseCode.ERROR_COMMUNICATING_WITH_LLM)
    
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
    
    async def get_cover_letter(self, resume_data_dict: dict) -> MCPResponse:
        cover_letter_guidelines = resume_data_dict.get('cover_letter_guidelines', '')
        if cover_letter_guidelines:
            cover_letter_response = await self.gemini_agent.get_response_from_gemini(prompt=cover_letter_guidelines, 
                                                                                 chat=self.resume_chat)         
            if cover_letter_response.code == LLMResponseCode.OK:
                return MCPResponse(cover_letter_response.text, MCPResponseCode.OK)
            if cover_letter_response.code == LLMResponseCode.MODEL_OVERLOADED:
                return MCPResponse(cover_letter_response.text, MCPResponseCode.ERROR_MODEL_OVERLOADED)
            return MCPResponse(cover_letter_response.text, MCPResponseCode.ERROR_COMMUNICATING_WITH_LLM)
        # No cover letter guidelines provided - not an error
        return MCPResponse("No cover letter guidelines provided", MCPResponseCode.OK)