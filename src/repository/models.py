from enum import Enum
from typing import Generic, Optional, TypeVar

from attr import dataclass


class PersistenceErrorCode(str, Enum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND"
    OPERATION_ERROR = "OPERATION_ERROR"
    DUPLICATE_KEY = "DUPLICATE_KEY"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


T = TypeVar('T')

@dataclass(slots=True, frozen=True)
class PersistenceResponse(Generic[T]):
    """
    Note: dataclasses don't support __slots__ directly in Python < 3.10.
    In Python 3.10+, you can use @dataclass(slots=True, frozen=True)
    """
    code: PersistenceErrorCode
    data: Optional[T]
    id: Optional[str] = None
    error_message: Optional[str] = None
    
    def __repr__(self):
        # Safe repr - don't expose potentially sensitive data content
        data_repr = f"<{type(self.data).__name__}>" if self.data is not None else "None"
        error_repr = f"'{self.error_message[:50]}...'" if self.error_message and len(self.error_message) > 50 else repr(self.error_message)
        return f"PersistenceResponse(data={data_repr}, code={self.code}, error_message={error_repr})"
    
    @property
    def is_success(self) -> bool:
        return self.code == PersistenceErrorCode.SUCCESS
    
    @property
    def is_error(self) -> bool:
        return not self.is_success