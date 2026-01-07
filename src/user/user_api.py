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
        super().__init__(text=user_id, error_message=error_message, code=code)

class UserApi(AbstractApi):

    def __init__(self, user_registry_service: UserRegistryService):
        self.user_registry_service = user_registry_service   


    def login_or_register(self, user_email: str) -> Dict[str, Any]:
        if not user_email or not user_email.strip():
            logging.error("Invalid email provided")
            return UserApiResponse(error_message="Invalid email address", code=UserApiResponseCode.ERROR).model_dump()
        
        try:
            response = self.user_registry_service.login_or_register(user_email)
        except Exception as e:
            logging.exception(f"Exception calling user registry service: {e}")
            return UserApiResponse(error_message="Service unavailable", code=UserApiResponseCode.ERROR).model_dump()
         
        if not response: 
            return UserApiResponse(error_message="Unknown error occurred", code=UserApiResponseCode.ERROR).model_dump()
        if response.code == UserRegistryResponseCode.OK:
            return UserApiResponse( user_id=response.user_id, code=UserApiResponseCode.OK).model_dump()
        error_detail = getattr(response, 'error_message', 'Unknown error')
        logging.error(f"Failed to login or register user: {error_detail}")
        return UserApiResponse(error_message=f"Error registering or logging in user: {error_detail}", code=UserApiResponseCode.ERROR).model_dump()