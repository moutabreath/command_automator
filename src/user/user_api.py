from enum import Enum
from typing import Dict, Any

from abstract_api import AbstractApi, ApiResponse
from user.services.user_registry_service import UserRegistryResponseCode, UserRegistryService
import logging

class UserApiResponseCode(Enum):
    OK = 1
    ERROR = 2

class UserApiResponse(ApiResponse):
    def __init__(self, code: UserApiResponseCode, user_id: str = None, error_message: str = None):
        super().__init__(result_text=user_id, error_message=error_message, code=code)

class UserApi(AbstractApi):

    def __init__(self, user_registry_service: UserRegistryService):
        self.user_registry_service = user_registry_service   


    def login_or_register(self, user_email:str) -> Dict[str, Any]:
        response = self.user_registry_service.login_or_register(user_email)        
        
        if not response:
            logging.error("No response from user registry service")
            return UserApiResponse(error_message="Unknown error occurred", code=UserApiResponseCode.ERROR).to_dict()
        if response.code == UserRegistryResponseCode.OK:
            return UserApiResponse( user_id=response.user_id, code=UserApiResponseCode.OK).to_dict()
        logging.error(f"Failed to login or register user: {response}")
        return UserApiResponse(error_message="Error registering or logging in user", code=UserApiResponseCode.ERROR).to_dict()