from enum import Enum
from user.repository.user_mongo_persist import UserMongoPersist

class UserRegistryResponseCode(Enum):
    OK = 1,
    ERROR = 2

class UserRegistryResponse:
    def __init__(self, user_id: str, code: UserRegistryResponseCode):
        self.user_id = user_id
        self.code = code
        
class UserRegistryService:
    def __init__(self):
        self.logged_in_user = ""
        self.user_persist = UserMongoPersist()

    def login_or_register_user(self, user_email) -> UserRegistryResponse:
        result = self.user_persist.create_or_update_user(user_email)
        if result == "":
            return UserRegistryResponse("", UserRegistryResponseCode.ERROR)
        return UserRegistryResponse(result, UserRegistryResponseCode.OK)