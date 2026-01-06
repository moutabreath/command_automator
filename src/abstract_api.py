from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from services.configuration_service import ConfigurationService


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

class AbstractApi(ABC):

    def __init__(self, config_file_path: Path = None):        
        if config_file_path:
            self.config_service = ConfigurationService(config_file_path)

    def load_configuration(self):
        return self.config_service.load_configuration()
    
    def save_configuration(self, config):
        return self.config_service.save_configuration(config)
       
    