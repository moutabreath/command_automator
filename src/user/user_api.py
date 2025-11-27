from enum import Enum
from typing import Dict, Any

from api_utils import ApiResponse
from services.configuration_service import ConfigurationService
from user.services.user_registry_service import UserRegistryResponseCode, UserRegistryService
from utils.file_utils import USER_CONFIG_FILE

class UserApiResponseCode(Enum):
    OK = 1,
    ERROR = 2

class UserApiResponse(ApiResponse):
    def __init__(self, user_id: str, code: UserApiResponseCode):
        super().__init__(user_id, code)

class UserApi:

    def __init__(self):
        self.user_config = ConfigurationService(USER_CONFIG_FILE)
        self.user_registry_service = UserRegistryService()
    
    def load_configuration(self):
        config = self.user_config.load_configuration()
        return config
    
    def save_configuration(self, config):
        self.user_config.save_configuration(config)

    def login_or_register(self, user_email:str) -> Dict[str, Any]:
        response = self.user_registry_service.login_or_register_user(user_email=user_email)
        if response.code == UserRegistryResponseCode.OK:
              return UserApiResponse(response.user_id, UserApiResponseCode.OK).to_dict()
        return UserApiResponse(f"Error registering or logging in {user_email}", UserApiResponseCode.ERROR).to_dict()

