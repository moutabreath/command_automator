import logging
import asyncio
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from urllib.parse import urlparse
import uuid

import pymongo.errors as mongo_errors
from motor.motor_asyncio import AsyncIOMotorClient
# ==================== TYPES & ENUMS ====================

class PersistenceErrorCode(Enum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND"
    OPERATION_ERROR = "OPERATION_ERROR"
    DUPLICATE_KEY = "DUPLICATE_KEY"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

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
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", 
                 db_name: str = "job_tracker"):  
        self.connection_string = connection_string
        self.db_name = db_name
        
        # State indicators
        self.async_client = None
        self.async_db = None
        self._initialized = False
        logging.getLogger("pymongo").setLevel(logging.WARNING)

    @classmethod
    async def create(cls, connection_string: str = "mongodb://localhost:27017/", 
                     db_name: str = "job_tracker"):
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
        # CRITICAL: We grab the current loop (Background Loop)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError(f"Cannot initialize {self.__class__.__name__}: No running event loop.")

        logging.info(f"Initializing {self.__class__.__name__} on loop: {id(loop)}")

        self.async_client = AsyncIOMotorClient(
            self.connection_string,
            io_loop=loop
        )
        self.async_client._serializable = False
        
        self.async_db = self.async_client[self.db_name]
        self.async_db._serializable = False
        
        # Setup specific collections for the subclass
        self._setup_collections()
        
        await self.create_index()
        self._initialized = True

    @abstractmethod
    def _setup_collections(self):
        """Subclasses must assign self.collection_name here"""
        pass

    @abstractmethod
    async def create_index(self):
        pass