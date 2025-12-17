from enum import Enum
from repository.abstract_mongo_persist import AbstractMongoPersist
from services.abstract_persistence_service import AbstractPersistenceService
from user.repository.user_mongo_persist import UserMongoPersist
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
    async def create(cls):
        # 1. Create the initialized persistence layer
        # This will fail if DB is down or logic is wrong, preventing "Zombie" services
        user_persist = await UserMongoPersist.create()
        
        # 2. Return the fully formed service
        return cls(user_persist)

    def login_or_register(self, user_email: str) -> UserRegistryResponse:
        if not user_email or not user_email.strip():
            return UserRegistryResponse("", UserRegistryResponseCode.ERROR)
        try:
            response: UserRegistryResponse = AsyncRunner.run_async(
                self._login_or_register_user_async(user_email)
            )
            return response
        except Exception:
            logging.exception("Error during login or register")
            return UserRegistryResponse(f"Error during login or register:", UserRegistryResponseCode.ERROR)


    async def _login_or_register_user_async(self, user_email) -> UserRegistryResponse:
        response = await self.user_persist.create_or_update_user(user_email)
        if response:            
            return UserRegistryResponse(response['_id'], UserRegistryResponseCode.OK)
        return UserRegistryResponse("Error registering or logging in", UserRegistryResponseCode.ERROR)