import base64
from enum import Enum
import logging
from abstract_api import AbstractApi, ApiResponse
from utils.utils import run_async_method
from llm.llm_client.mcp_response import MCPResponse, MCPResponseCode
from llm.services.llm_service import LLMService
from typing import Dict, Any

class LLMApiResponseCode(Enum):
    """Enumeration of possible LLM operation results"""
    OK = 1
    ERROR_COMMUNICATING_WITH_LLM = 2
    ERROR_MODEL_OVERLOADED = 3
    ERROR_LOADING_IMAGE_TO_MODEL = 4
    ERROR_MODEL_QUOTA_EXCEEDED = 5

class LLMApiResponse(ApiResponse):
    def __init__(self, code: LLMApiResponseCode, error_message: str = "", result_text: str = ""):
        super().__init__(result_text=result_text, code=code, error_message=error_message)

class LLMApi(AbstractApi):

    def __init__(self,llm_service: LLMService):
        self.llm_service = llm_service
  
        
    def call_llm(self, prompt: str, image_data: str, output_file_path: str, user_id:str = None) -> Dict[str, Any]:
        decoded_data = None
        if image_data and image_data != '':
            try:
                parts = image_data.split(',', 1)
                if len(parts) != 2:
                    raise ValueError("Invalid image data format: expected 'prefix,base64data'")
                _, encoded = parts
                # Validate size before decoding (e.g., 10MB limit)
                if len(encoded) > 10 * 1024 * 1024 * 4 // 3:  # base64 is ~4/3 size of original
                    raise ValueError("Image data exceeds maximum allowed size")
                decoded_data = base64.b64decode(encoded)            
            except Exception as e:
                logging.exception(f"Error processing image data: {e}")
                resp = LLMApiResponse(error_message="Error loading image", code = LLMApiResponseCode.ERROR_LOADING_IMAGE_TO_MODEL)
                return resp.to_dict()

        result: MCPResponse = run_async_method(self.llm_service.chat_with_bot, prompt, decoded_data, output_file_path, user_id)
        if not result:
            return LLMApiResponse("Unknown error occurred", LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM).to_dict()
        
        match result.code:
            case MCPResponseCode.OK:
                resp = LLMApiResponse(result_text=result.text, code=LLMApiResponseCode.OK)
            case MCPResponseCode.ERROR_MODEL_OVERLOADED:
                resp = LLMApiResponse(error_message="Model overloaded", code =LLMApiResponseCode.ERROR_MODEL_OVERLOADED)
            case MCPResponseCode.ERROR_MODEL_QUOTA_EXCEEDED:
                resp = LLMApiResponse(error_message="Model Exhausted", code=LLMApiResponseCode.ERROR_MODEL_QUOTA_EXCEEDED)
            case _:
                resp = LLMApiResponse(error_message="Error communicating with LLM", code=LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM)
        return resp.to_dict()