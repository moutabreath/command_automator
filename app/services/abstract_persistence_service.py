from repository.abstract_mongo_persist import AbstractMongoPersist


class AbstractPersistenceService:

    def __init__(self, abstractMongoPersist:AbstractMongoPersist):
        self.abstractMongoPersist = abstractMongoPersist
        
    
    async def initialize_connection(self):
        await self.abstractMongoPersist.initialize_connection()