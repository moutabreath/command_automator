
from ..repository.user_mongo_persist import UserMongoPersist
from .models import UserRegistryResponse, UserRegistryResponseCode
import logging

        
class UserRegistryService:
    
    def __init__(self, user_persist: UserMongoPersist):
        self.user_persist = user_persist


    async def login(self, user_email: str) -> UserRegistryResponse:
        if not user_email or not user_email.strip():
            return UserRegistryResponse(code=UserRegistryResponseCode.ERROR, error_message="Email is required")
        user_email = user_email.strip().lower()
        response = await self.user_persist.get_user(user_email)
        if response:
             return UserRegistryResponse(user_id=str(response.data['_id']), code=UserRegistryResponseCode.OK)
        logging.error("User not found")
        return UserRegistryResponse(error_message="User not found", code=UserRegistryResponseCode.ERROR)

    async def register(self, user_email: str) -> UserRegistryResponse:
        if not user_email or not user_email.strip():
            return UserRegistryResponse(code=UserRegistryResponseCode.ERROR, error_message="Email is required")
        user_email = user_email.strip().lower()
        response = await self.user_persist.register_user(user_email)
        if response:
             return UserRegistryResponse(user_id=str(response.data['_id']), code=UserRegistryResponseCode.OK)
        logging.error("Failed to create user")
        return UserRegistryResponse(error_message="Failed to create user", code=UserRegistryResponseCode.ERROR)