from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Any, Dict

from services.configuration_service import ConfigurationService


class ApiResponseCode(Enum):
    OK = 1
    ERROR_RUNNING_ASYNC_METHOD = 2

class ApiResponse:
    def __init__(self, text: str, code: Enum):
        self.text = text
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "text": self.text,
            "code": self.code.name if isinstance(self.code, Enum) else str(self.code)
        }

    def __getstate__(self) -> Dict[str, Any]:
        """Support pickling/serialization by returning a dict."""
        return self.to_dict()

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore instance from pickled state."""
        self.text = state["text"]
        # Restore the Enum from its name
        self.code = ApiResponseCode[state["code"]]

class AbstractApi(ABC):

    def __init__(self, config_file_path: Path):        
        self.config_service = ConfigurationService(config_file_path)

    def load_configuration(self):
        return self.config_service.load_configuration()
    
    def save_configuration(self, config):
        return self.config_service.save_configuration(config)
       
    