from enum import StrEnum
from dataclasses import dataclass
from typing import List, Optional, Any

class LLMResponseCode(StrEnum):
    """Enumeration of possible Gemini API operation results"""
    OK = "OK"
    ERROR_USING_GEMINI_API = "ERROR_USING_GEMINI_API"
    GEMINI_UNAVAILABLE = "GEMINI_UNAVAILABLE"
    MODEL_OVERLOADED = "MODEL_OVERLOADED"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    
@dataclass
class LLMResponse:
    text: str
    code: LLMResponseCode

class LLMToolResponseCode(StrEnum):
    """Enumeration of possible Gemini API operation results"""
    USING_TOOL = "USING_TOOL"
    NOT_USING_TOOL = "NOT_USING_TOOL"
    MODEL_OVERLOADED = "MODEL_OVERLOADED"


@dataclass
class LLMToolResponse:
    code: LLMToolResponseCode
    selected_tool: Optional[str] = None
    args: Optional[List[Any]] = None
    error_message: Optional[str] = None