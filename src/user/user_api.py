from enum import Enum
from typing import Dict, Any

from abstract_api import AbstractApi, ApiResponse
from user.services.user_registry_service import UserRegistryResponseCode, UserRegistryService
from utils.file_utils import USER_CONFIG_FILE

class UserApiResponseCode(Enum):
    OK = 1
    ERROR = 2

class UserApiResponse(ApiResponse):
    def __init__(self, user_id: str, code: UserApiResponseCode):
        super().__init__(user_id, code)

class UserApi(AbstractApi):

    def __init__(self):
        super().__init__(USER_CONFIG_FILE)
        self.user_registry_service = UserRegistryService()   


    def login_or_register(self, user_email:str) -> Dict[str, Any]:
        response = self.user_registry_service.login_or_register_user(user_email=user_email)
        if response.code == UserRegistryResponseCode.OK:
              if response.code == UserRegistryResponseCode.OK:
                return UserApiResponse(response.user_id, UserApiResponseCode.OK).to_dict()        
        return UserApiResponse(f"Error registering or logging in {user_email}", UserApiResponseCode.ERROR).to_dict()

