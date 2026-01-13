from enum import StrEnum
from pydantic import BaseModel
from typing import Optional

class UserApiResponseCode(StrEnum):
    OK = "OK"
    ERROR = "ERROR"

class UserApiResponse(BaseModel):
    code: UserApiResponseCode
    user_id: Optional[str] = None
    error_message: Optional[str] = None
