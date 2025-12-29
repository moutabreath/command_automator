import logging
import asyncio
from abc import abstractmethod

from motor.motor_asyncio import AsyncIOMotorClient

from repository.abstract_mongo_persist import AbstractMongoPersist

class AbstractOwnerMongoPersist(AbstractMongoPersist):
    """
    Base class for the mongo collections owners. They initialize the collection and indexes.
    They are executed before other mongo connection classes for their respective collections.
    Apart from instantiating the collections for the first time, they use an existing event loop for motor (mongo async).
    See users and job applications (non MCP) flows.
    """    
    async def initialize_connection(self):
        """
        Internal initialization logic. 
        Should be called automatically by create(), not manually.
        """        
        await super().initialize_connection()
        
        # Setup specific collections for the subclass
        self._setup_collections()
        
        await self.create_index()

    def _init_motor_client(self):
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

    @abstractmethod
    def _setup_collections(self):
        """Subclasses must assign self.collection_name here"""
        pass

    @abstractmethod
    async def create_index(self):
        pass