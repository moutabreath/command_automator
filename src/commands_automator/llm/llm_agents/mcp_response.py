
from enum import Enum


class MCPResponseCode(Enum):
    """Enumeration of possible MCP operation results"""
    OK = 1
    ERROR_TOOL_RETURNED_NO_RESULT = 2
    ERROR_COMMUNICATING_WITH_TOOL = 3
    ERROR_WITH_TOOL_RESPONSE = 4
    ERROR_COMMUNICATING_WITH_LLM = 5

class MCPResponse:
    def __init__(self, text: str, code: MCPResponseCode):
        self.text = text
        self.code = code