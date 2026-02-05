from enum import StrEnum
from pydantic import BaseModel
from typing import Optional


class LLMApiResponseCode(StrEnum):
    """Enumeration of possible LLM operation results"""
    OK = "OK"
    ERROR_COMMUNICATING_WITH_LLM = "ERROR_COMMUNICATING_WITH_LLM"
    ERROR_MODEL_OVERLOADED = "ERROR_MODEL_OVERLOADED"
    ERROR_LOADING_IMAGE_TO_MODEL = "ERROR_LOADING_IMAGE_TO_MODEL"
    ERROR_MODEL_QUOTA_EXCEEDED = "ERROR_MODEL_QUOTA_EXCEEDED"
    OPERATION_CANCELLED = "OPERATION_CANCELLED"


class LLMApiResponse(BaseModel):
    code: LLMApiResponseCode
    error_message: Optional[str] = ""
    result_text: Optional[str] = ""