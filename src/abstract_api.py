from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    text: Optional[str] = None
    error_message: Optional[str] = None
    code: str
    
    def __init__(self, code: Enum, text: str = None, error_message: str = None, **data):
        super().__init__(
            text=text,
            error_message=error_message,
            code=code.name if isinstance(code, Enum) else str(code),
            **data
        )

       
    