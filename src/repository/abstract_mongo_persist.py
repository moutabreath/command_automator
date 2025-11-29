from enum import Enum
from dataclasses import dataclass
import logging
from pymongo import MongoClient
from abc import ABC

from typing import Generic, TypeVar, Optional
class PersistenceErrorCode(Enum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND",
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

  def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "job_tracker"):  
      """Initialize MongoDB connection"""
      self._disable_debug_logging()
      self.connection_string = connection_string
      self.db_name = db_name
   

  def _disable_debug_logging(self):
      # Suppress all MongoDB debug logs
      logging.getLogger("pymongo").setLevel(logging.ERROR)
      logging.getLogger("pymongo.connection").setLevel(logging.ERROR)
      logging.getLogger("pymongo.pool").setLevel(logging.ERROR)
      
  def initialize_connection(self):
      self.connect()
      self.create_index()
      
  def connect(self):
      self.client = MongoClient(self.connection_string)
      self.client._serializable = False  # Prevent webview introspection
      self.db = self.client[self.db_name]
      self.db._serializable = False  # Prevent webview introspection

  def create_index(self):
    pass

  