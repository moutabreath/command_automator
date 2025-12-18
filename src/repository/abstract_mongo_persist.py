import logging
import asyncio
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

# ==================== TYPES & ENUMS ====================

class PersistenceErrorCode(Enum):
    SUCCESS = 1
    NOT_FOUND = 2
    OPERATION_ERROR = 3
    DUPLICATE_KEY = 4
    CONNECTION_ERROR = 5
    VALIDATION_ERROR = 6
    UNKNOWN_ERROR = 7

T = TypeVar('T')

@dataclass(frozen=True)
class PersistenceResponse(Generic[T]):

    data: Optional[T]
    code: PersistenceErrorCode
    error_message: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        return self.code == PersistenceErrorCode.SUCCESS
    
    @property
    def is_error(self) -> bool:
        return not self.is_success


class AbstractMongoPersist(ABC):
    def __init__(self, connection_string: str, db_name: str):  
        self.connection_string = connection_string
        self.db_name = db_name
        
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        
    @classmethod
    async def create(cls, connection_string: str, db_name: str):
        """
        Async Factory: The ONLY safe way to instantiate persistence classes.
        This guarantees that the returned instance is fully connected and initialized.
        """
        # 1. Create the instance (sync)
        instance = cls(connection_string, db_name)
        
        # 2. Run the async initialization immediately
        # This will attach to the CURRENT running loop (Background Loop)
        await instance.initialize_connection()
        
        # 3. Return the ready-to-use instance
        return instance


    async def initialize_connection(self):
        """
        Internal initialization logic. 
        Should be called automatically by create(), not manually.
        """
        self._init_motor_client()
            
        self.async_db = self.async_client[self.db_name]

        # disable processing of pywebview of the motor objects, which are not serializable
        self.async_client._serializable = False
        self.async_db._serializable = False



    @abstractmethod
    def _init_motor_client(self):
        pass