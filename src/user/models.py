from enum import Enum
from pydantic import BaseModel
from typing import Optional

class UserApiResponseCode(str, Enum):
    OK = "OK"
    ERROR = "ERROR"

class UserApiResponse(BaseModel):
    code: UserApiResponseCode
    user_id: Optional[str] = None
    error_message: Optional[str] = None
