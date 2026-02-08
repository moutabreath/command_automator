from abc import ABC
import logging
from motor.motor_asyncio import AsyncIOMotorClient

class AbstractJobTrackingPersistMongo(ABC):

    
    def __init__(self, connection_string: str, db_name: str, collection_name: str):
        
        self.async_client = AsyncIOMotorClient(
            connection_string
        )
        
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        self.job_applications = self.async_client[db_name][collection_name]
    