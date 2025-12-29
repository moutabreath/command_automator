from enum import Enum
from services.abstract_persistence_service import AbstractPersistenceService
from services.configuration_service import ConfigurationService
from user.repository.user_mongo_persist import UserMongoPersist
from utils import file_utils
from utils.utils import AsyncRunner
import logging

class UserRegistryResponseCode(Enum):
    OK = 1
    ERROR = 2
    
class UserRegistryResponse:
    def __init__(self, user_id: str, code: UserRegistryResponseCode):
        self.user_id = user_id
        self.code = code
        
class UserRegistryService(AbstractPersistenceService):
    
    def __init__(self, user_persist: UserMongoPersist):
        # We now REQUIRE an initialized persistence object to be passed in
        self.user_persist = user_persist
        super().__init__(self.user_persist)

    @classmethod
    async def create(cls, mongo_connection_string, db_name):
        # 1. Create the initialized persistence layer
        # This will fail if DB is down or logic is wrong, preventing "Zombie" services
        user_persist = await UserMongoPersist.create(mongo_connection_string, db_name)
        
        # 2. Return the fully formed service
        return cls(user_persist)

    def login_or_register(self, user_email: str) -> UserRegistryResponse:        
        try:
            response: UserRegistryResponse = AsyncRunner.run_async(
                self.login_or_register_user_async(user_email)
            )
            return response
        except Exception:
            logging.exception("Error during login or register")
            return UserRegistryResponse(f"Error during login or register:", UserRegistryResponseCode.ERROR)


    async def login_or_register_user_async(self, user_email) -> UserRegistryResponse:
        if not user_email or not user_email.strip():
            return UserRegistryResponse("", UserRegistryResponseCode.ERROR)
        user_email = user_email.strip().lower()
        response = await self.user_persist.create_or_update_user(user_email)
        if response and '_id' in response:            
            return UserRegistryResponse(response['_id'], UserRegistryResponseCode.OK)
        logging.error(f"Failed to create or update user: {response}")
        return UserRegistryResponse("", UserRegistryResponseCode.ERROR)