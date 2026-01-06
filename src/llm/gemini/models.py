from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Any

class LLMResponseCode(Enum):
    """Enumeration of possible Gemini API operation results"""
    OK = 1
    ERROR_USING_GEMINI_API = 2
    GEMINI_UNAVAILABLE = 3
    MODEL_OVERLOADED = 4
    RESOURCE_EXHAUSTED = 5
    
class LLMResponse:
    def __init__(self, text: str, code: LLMResponseCode):
        self.text = text
        self.code = code


class LLMToolResponseCode(Enum):
    """Enumeration of possible Gemini API operation results"""
    USING_TOOL = 1
    NOT_USING_TOOL = 2
    MODEL_OVERLOADED = 3


@dataclass
class LLMToolResponse:
    code : LLMToolResponseCode
    selected_tool: Optional[str] = None
    args: Optional[List[Any]] = None
    error_message: Optional[str] = None