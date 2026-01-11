from services.abstract_persistence_service import AbstractPersistenceService
from user.repository.user_mongo_persist import UserMongoPersist
from user.services.models import UserRegistryResponse, UserRegistryResponseCode
from utils.utils import AsyncRunner
import logging


        
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
            return UserRegistryResponse(error_message="Error during login or register", code=UserRegistryResponseCode.ERROR)

    async def login_or_register_user_async(self, user_email: str) -> UserRegistryResponse:
        if not user_email or not user_email.strip():
            return UserRegistryResponse(code=UserRegistryResponseCode.ERROR, error_message="Email is required")
        user_email = user_email.strip().lower()
        response = await self.user_persist.create_or_update_user(user_email)
        if response and '_id' in response:
             return UserRegistryResponse(user_id=str(response['_id']), code=UserRegistryResponseCode.OK)
        logging.error("Failed to create or update user")
        return UserRegistryResponse(error_message="Failed to create or update user", code=UserRegistryResponseCode.ERROR)