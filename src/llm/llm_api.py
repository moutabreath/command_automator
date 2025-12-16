import base64
from enum import Enum
import logging
from abstract_api import AbstractApi, ApiResponse
from utils.utils import run_async_method
from llm.llm_client.mcp_response import MCPResponse, MCPResponseCode
from llm.services.llm_service import LLMService
from llm.mcp_servers.job_applicant_mcp import MCPRunner
from utils.file_utils import LLM_CONFIG_FILE
from typing import Dict, Any

class LLMApiResponseCode(Enum):
    """Enumeration of possible LLM operation results"""
    OK = 1
    ERROR_COMMUNICATING_WITH_LLM = 2
    ERROR_MODEL_OVERLOADED = 3
    ERROR_LOADING_IMAGE_TO_MODEL = 4
    ERROR_MODEL_QUOTA_EXCEEDED = 5

class LLMApiResponse(ApiResponse):
    def __init__(self, text: str, code: LLMApiResponseCode):
        super().__init__(text, code)

class LLMApi(AbstractApi):

    def __init__(self,llm_service: LLMService):
        super().__init__(LLM_CONFIG_FILE)
        self.llm_service = llm_service
  
        
    def call_llm(self, prompt: str, image_data: str, output_file_path: str, user_id:str = None) -> Dict[str, Any]:
        decoded_data = None
        if image_data and image_data != '':
            try:
                parts = image_data.split(',', 1)
                if len(parts) != 2:
                    raise ValueError("Invalid image data format: expected 'prefix,base64data'")
                _, encoded = parts
                decoded_data = base64.b64decode(encoded)   
            except Exception as e:
                logging.exception(f"Error processing image data: {e}")
                resp = LLMApiResponse("Error loading image", LLMApiResponseCode.ERROR_LOADING_IMAGE_TO_MODEL)
                return resp.to_dict()

        result: MCPResponse = run_async_method(self.llm_service.chat_with_bot, prompt, decoded_data, output_file_path, user_id)
        if not result:
            return LLMApiResponse("Unknown error occurred", LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM).to_dict()
        
        match result.code:
            case MCPResponseCode.OK:
                resp = LLMApiResponse(result.text, LLMApiResponseCode.OK)
            case MCPResponseCode.ERROR_MODEL_OVERLOADED:
                resp = LLMApiResponse("Model overloaded", LLMApiResponseCode.ERROR_MODEL_OVERLOADED)
            case MCPResponseCode.ERROR_MODEL_QUOTA_EXCEEDED:
                resp = LLMApiResponse("Model Exhausted", LLMApiResponseCode.ERROR_MODEL_QUOTA_EXCEEDED)
            case _:
                resp = LLMApiResponse("Error communicating with LLM", LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM)
        return resp.to_dict()