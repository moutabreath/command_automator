from enum import Enum
from user.repository.user_mongo_persist import UserMongoPersist

class UserRegistryResponseCode(Enum):
    OK = 1
    ERROR = 2
    
class UserRegistryResponse:
    def __init__(self, user_id: str, code: UserRegistryResponseCode):
        self.user_id = user_id
        self.code = code
        
class UserRegistryService:
    def __init__(self, user_persist: UserMongoPersist = None):
        self.user_persist = user_persist if user_persist is not None else UserMongoPersist()

    def login_or_register_user(self, user_email) -> UserRegistryResponse:
        if not user_email or not user_email.strip():
            return UserRegistryResponse("", UserRegistryResponseCode.ERROR)
        
        result = self.user_persist.create_or_update_user(user_email)
        if result == "":
            return UserRegistryResponse("", UserRegistryResponseCode.ERROR)
        return UserRegistryResponse(result, UserRegistryResponseCode.OK)