import logging

from typing import Dict, Any

from user.models import UserApiResponse, UserApiResponseCode
from user.services.models import UserRegistryResponseCode
from user.services.user_registry_service import UserRegistryService

class UserApi:

    def __init__(self, user_registry_service: UserRegistryService):
        self.user_registry_service = user_registry_service   

    def login(self, user_email: str) -> Dict[str, Any]:
        if not user_email or not user_email.strip():
            logging.error("Invalid email provided")
            return UserApiResponse(error_message="Invalid email address", code=UserApiResponseCode.ERROR).model_dump()
        
        try:
            response = self.user_registry_service.login(user_email)
        except Exception as e:
            logging.exception(f"Exception calling user registry service: {e}")
            return UserApiResponse(error_message="Service unavailable", code=UserApiResponseCode.ERROR).model_dump()
         
        if not response: 
            return UserApiResponse(error_message="Unknown error occurred", code=UserApiResponseCode.ERROR).model_dump()
        if response.code == UserRegistryResponseCode.OK:
            return UserApiResponse(user_id=response.user_id, code=UserApiResponseCode.OK).model_dump()
        error_detail = getattr(response, 'error_message', 'Unknown error')
        logging.error(f"Failed to login user: {error_detail}")
        return UserApiResponse(error_message=f"Error logging in user: {error_detail}", code=UserApiResponseCode.ERROR).model_dump()

    def register(self, user_email: str) -> Dict[str, Any]:
        if not user_email or not user_email.strip():
            logging.error("Invalid email provided")
            return UserApiResponse(error_message="Invalid email address", code=UserApiResponseCode.ERROR).model_dump()
        
        try:
            response = self.user_registry_service.register(user_email)
        except Exception as e:
            logging.exception(f"Exception calling user registry service: {e}")
            return UserApiResponse(error_message="Service unavailable", code=UserApiResponseCode.ERROR).model_dump()
         
        if not response: 
            return UserApiResponse(error_message="Unknown error occurred", code=UserApiResponseCode.ERROR).model_dump()
        if response.code == UserRegistryResponseCode.OK:
            return UserApiResponse(user_id=response.user_id, code=UserApiResponseCode.OK).model_dump()
        error_detail = getattr(response, 'error_message', 'Unknown error')
        logging.error(f"Failed to register user: {error_detail}")
        return UserApiResponse(error_message=f"Error registering user: {error_detail}", code=UserApiResponseCode.ERROR).model_dump()