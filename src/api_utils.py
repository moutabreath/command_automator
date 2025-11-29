from typing import Dict
import asyncio
from enum import Enum
import logging
from typing import Any

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



def run_async_method(async_method, *args, **kwargs):
    try:
        return asyncio.run(async_method(*args, **kwargs))
    except Exception as e:
        logging.exception("Error running async method")      
        return ApiResponse("Error running async method", ApiResponseCode.ERROR_RUNNIG_ASYNC_METHOD)