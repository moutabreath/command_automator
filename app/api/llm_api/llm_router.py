import base64
import logging

from fastapi import APIRouter, HTTPException, Depends, Body, Form, Query
from typing import Dict, Any, Optional


from .schemas.responses import LLMApiResponse, LLMApiResponseCode
from .llm_mapper import mcp_response_to_api_response

from ..setup.api_dependency_container import Container
from ...llm_proxy import LLMProxyService




router = APIRouter(prefix="/api/llm", tags=["llm"])


def get_llm_proxy_service() -> LLMProxyService:
    """Dependency injection for LLMProxyService"""
    
    return Container.get_container().llm_proxy_service()


def _decode_image_data(image_data: Optional[str]) -> Optional[bytes]:
    """Helper to decode base64 image data"""
    if not image_data or image_data == '':
        return None

    try:
        parts = image_data.split(',', 1)
        if len(parts) != 2:
            raise ValueError("Invalid image data format: expected 'prefix,base64data'")
        _, encoded = parts
        # Validate size before decoding (e.g., 10MB limit)
        if len(encoded) > 10 * 1024 * 1024 * 4 // 3:  # base64 is ~4/3 size of original
            raise ValueError("Image data exceeds maximum allowed size")
        return base64.b64decode(encoded)
    except Exception as e:
        logging.exception(f"Error processing image data: {e}")
        raise HTTPException(status_code=400, detail={
            "code": LLMApiResponseCode.ERROR_LOADING_IMAGE_TO_MODEL,
            "error_message": "Error loading image"
        })


@router.post("/process", response_model=LLMApiResponse)
async def call_llm(
    prompt: str = Form(...),
    image_data: Optional[str] = Form(default=None),
    output_file_path: Optional[str] = Form(default=None),
    user_id: Optional[str] = Form(default=None),
    llm_proxy: LLMProxyService = Depends(get_llm_proxy_service)
) -> Dict[str, Any]:
    """
    Process a query with the LLM using form-data.
    
    Parameters:
    - prompt (required): The prompt to send to LLM
    - image_data (optional): Base64 encoded image data
    - output_file_path (optional): Path to save output
    - user_id (optional): User identifier
    """
    if not prompt or not prompt.strip():
        resp = LLMApiResponse(
            error_message="Prompt cannot be empty",
            code=LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM
        )
        raise HTTPException(status_code=400, detail=resp.model_dump())
    
    decoded_data = _decode_image_data(image_data)
    response = await llm_proxy.process_query(
        prompt, 
        decoded_data, 
        output_file_path, 
        user_id
    )
    return mcp_response_to_api_response(response)