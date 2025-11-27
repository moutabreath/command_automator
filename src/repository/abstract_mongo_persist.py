import logging
from pymongo import MongoClient

class AbstractMongoPersist:

    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "job_tracker"):  
      """Initialize MongoDB connection"""

      # Suppress all MongoDB debug logs
      logging.getLogger("pymongo").setLevel(logging.ERROR)
      logging.getLogger("pymongo.connection").setLevel(logging.ERROR)
      logging.getLogger("pymongo.pool").setLevel(logging.ERROR)

      self.client = MongoClient(connection_string)
      self.db = self.client[db_name]