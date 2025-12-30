from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Any, Dict

from services.configuration_service import ConfigurationService



class ApiResponse:
    def __init__(self,  code: Enum, result_text: str = None, error_message: str = None):
        self.text = result_text
        self.error_message = error_message
        self.code = code
        
    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "text": self.text,
            "error_message": self.error_message,
            "code": self.code.name if isinstance(self.code, Enum) else str(self.code)
        }

    def __getstate__(self) -> Dict[str, Any]:
        """Support pickling/serialization by returning a dict."""
        return self.to_dict()

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore instance from pickled state."""
        try:
            self.text = state["text"]
            self.code = state["code"]
            self.error_message = state["error_message"]
        except KeyError as e:
            raise ValueError(f"Invalid pickled state: missing or invalid key {e}")

class AbstractApi(ABC):

    def __init__(self, config_file_path: Path):        
        self.config_service = ConfigurationService(config_file_path)

    def load_configuration(self):
        return self.config_service.load_configuration()
    
    def save_configuration(self, config):
        return self.config_service.save_configuration(config)
       
    