from services.shared_service import SharedService
from repository.abstract_mongo_persist import AbstractMongoPersist


class AbstractPersistenceService(SharedService):

    def __init__(self, abstractMongoPersist:AbstractMongoPersist):
        self.abstractMongoPersist = abstractMongoPersist
        
    
    async def initialize_connection(self):
        self.abstractMongoPersist.initialize_connection()