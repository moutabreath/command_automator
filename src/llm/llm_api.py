import base64, logging
import asyncio
from typing import Dict, Any

from utils.utils import run_async_method, cancel_current_async_operation
from llm.llm_client.models import MCPResponse, MCPResponseCode
from llm.services.llm_service import LLMService
from llm.models import LLMApiResponse, LLMApiResponseCode

class LLMApi:

    def __init__(self,llm_service: LLMService):
        self.llm_service = llm_service

    def cancel_operation(self):
        """Cancel the current LLM operation"""
        cancel_current_async_operation()
  

    def call_llm(self, prompt: str, image_data: str, output_file_path: str, user_id:str = None) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            resp = LLMApiResponse(
                error_message="Prompt cannot be empty",
                code=LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM
            )
            return resp.model_dump()
        
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
                return resp.model_dump()

        try:
            # Create and track the LLM task
            async def llm_task():
                return await self.llm_service.chat_with_bot(prompt, decoded_data, output_file_path, user_id)
            
            result: MCPResponse = run_async_method(llm_task)
            return self._convert_mcp_response_to_api_response(result)
        except asyncio.CancelledError:
            logging.debug("LLM operation was cancelled")
            resp = LLMApiResponse(error_message="Operation was cancelled", code=LLMApiResponseCode.OPERATION_CANCELLED)
            return resp.dict()
        except Exception as e:
            logging.error("Unexpected error during LLM operation")
            resp = LLMApiResponse(error_message="Error communicating with LLM", code=LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM)
            return resp.model_dump()
        
    def _convert_mcp_response_to_api_response(self, result: MCPResponse) -> Dict[str, Any]:
        """Convert MCPResponse to LLMApiResponse dictionary"""
        if not result:
            return LLMApiResponse(error_message="Operation was cancelled", code=LLMApiResponseCode.OPERATION_CANCELLED).model_dump()
        
        match result.code:
            case MCPResponseCode.OK:
                resp = LLMApiResponse(result_text=result.text, code=LLMApiResponseCode.OK)
            case MCPResponseCode.ERROR_MODEL_OVERLOADED:
                resp = LLMApiResponse(error_message="Model overloaded", code =LLMApiResponseCode.ERROR_MODEL_OVERLOADED)
            case MCPResponseCode.ERROR_MODEL_QUOTA_EXCEEDED:
                resp = LLMApiResponse(error_message="Model Exhausted", code=LLMApiResponseCode.ERROR_MODEL_QUOTA_EXCEEDED)
            case _:
                resp = LLMApiResponse(error_message="Error communicating with LLM", code=LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM)
        return resp.model_dump()