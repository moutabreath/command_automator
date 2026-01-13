from dataclasses import dataclass
from enum import StrEnum


class UserRegistryResponseCode(StrEnum):
    OK = "OK"
    ERROR = "ERROR"
    

@dataclass
class UserRegistryResponse:
    code: UserRegistryResponseCode
    user_id: str = ""
    error_message: str = ""