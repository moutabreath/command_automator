
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Optional, TypeVar


class PersistenceErrorCode(Enum):
    SUCCESS = 1
    NOT_FOUND = 2
    OPERATION_ERROR = 3
    DUPLICATE_KEY = 4
    CONNECTION_ERROR = 5
    VALIDATION_ERROR = 6
    UNKNOWN_ERROR = 7


T = TypeVar('T')

@dataclass(slots=True, frozen=True)
class PersistenceResponse(Generic[T]):
    """
    Note: dataclasses don't support __slots__ directly in Python < 3.10.
    In Python 3.10+, you can use @dataclass(slots=True, frozen=True)
    """
    
    data: Optional[T]
    code: PersistenceErrorCode
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