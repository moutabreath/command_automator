"""
Mapper utilities for LLM API
Handles conversion between MCP responses and API responses
"""
from typing import Dict, Any

from ..llm_proxy.models import MCPResponse, MCPResponseCode
from .models import LLMApiResponse, LLMApiResponseCode


def mcp_response_to_api_response(result: MCPResponse) -> Dict[str, Any]:
    """Convert MCPResponse to LLMApiResponse dictionary"""
    if not result:
        resp = LLMApiResponse(
            error_message="Operation was cancelled",
            code=LLMApiResponseCode.OPERATION_CANCELLED
        )
        return resp.model_dump()
    
    match result.code:
        case MCPResponseCode.OK:
            resp = LLMApiResponse(result_text=result.text, code=LLMApiResponseCode.OK)
        case MCPResponseCode.ERROR_MODEL_OVERLOADED:
            resp = LLMApiResponse(error_message="Model overloaded", code=LLMApiResponseCode.ERROR_MODEL_OVERLOADED)
        case MCPResponseCode.ERROR_MODEL_QUOTA_EXCEEDED:
            resp = LLMApiResponse(error_message="Model Exhausted", code=LLMApiResponseCode.ERROR_MODEL_QUOTA_EXCEEDED)
        case _:
            resp = LLMApiResponse(error_message="Error communicating with LLM", code=LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM)
    
    return resp.model_dump()
