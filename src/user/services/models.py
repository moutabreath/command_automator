from dataclasses import dataclass
from enum import Enum


class UserRegistryResponseCode(Enum):
    OK = 1
    ERROR = 2
    

@dataclass
class UserRegistryResponse:
    code: UserRegistryResponseCode
    user_id: str = ""
    error_message: str = ""