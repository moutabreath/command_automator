from enum import Enum
from typing import Optional

from pydantic import BaseModel

class MCPResponseCode(Enum):
    """Enumeration of possible MCP operation results"""
    OK = 1
    ERROR_TOOL_RETURNED_NO_RESULT = 2
    ERROR_COMMUNICATING_WITH_TOOL = 3
    ERROR_WITH_TOOL_RESPONSE = 4
    ERROR_COMMUNICATING_WITH_LLM = 5
    ERROR_MODEL_OVERLOADED = 6
    ERROR_MODEL_QUOTA_EXCEEDED = 7
    OPERATION_CANCELLED = 8

class MCPResponse(BaseModel):    
    code: MCPResponseCode
    result_text: Optional[str] = None
    error_message: Optional[str] = None
