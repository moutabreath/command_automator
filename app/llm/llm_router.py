import base64
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional

from ..llm_proxy import LLMProxyService
from .models import LLMApiResponse, LLMApiResponseCode
from ..utils.utils import run_async_method, cancel_current_async_operation
from .llm_mapper import convert_mcp_response_to_api_response

router = APIRouter(prefix="/api/llm", tags=["llm"])


def get_llm_proxy_service() -> LLMProxyService:
    """Dependency injection for LLMProxyService"""
    from ..utils.dependency_container import container
    return container.llm_proxy_service()


@router.post("/process", response_model=LLMApiResponse)
async def call_llm(
    prompt: str,
    image_data: Optional[str] = None,
    output_file_path: Optional[str] = None,
    user_id: Optional[str] = None,
    llm_proxy: LLMProxyService = Depends(get_llm_proxy_service)
) -> Dict[str, Any]:
    """Process a query with the LLM"""
    if not prompt or not prompt.strip():
        resp = LLMApiResponse(
            error_message="Prompt cannot be empty",
            code=LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM
        )
        raise HTTPException(status_code=400, detail=resp.model_dump())
    
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
            raise HTTPException(status_code=400, detail={
                "code": LLMApiResponseCode.ERROR_LOADING_IMAGE_TO_MODEL,
                "error_message": "Error loading image"
            })

    try:
        # Create and track the LLM task
        async def llm_task():
            return await llm_proxy.process_query(prompt, decoded_data, output_file_path, user_id)
        
        result: MCPResponse = run_async_method(llm_task)
        return convert_mcp_response_to_api_response(result)
    except asyncio.CancelledError:
        logging.debug("LLM operation was cancelled")
        raise HTTPException(status_code=499, detail={
            "code": LLMApiResponseCode.OPERATION_CANCELLED,
            "error_message": "Operation was cancelled"
        })
    except Exception as e:
        logging.error(f"Unexpected error during LLM operation: {e}")
        raise HTTPException(status_code=500, detail={
            "code": LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM,
            "error_message": "Error communicating with LLM"
        })


@router.post("/cancel")
async def cancel_operation():
    """Cancel the current LLM operation"""
    try:
        cancel_current_async_operation()
        return {"status": "cancelled"}
    except Exception as e:
        logging.exception(f"Error cancelling operation: {e}")
        raise HTTPException(status_code=500, detail="Error cancelling operation")
