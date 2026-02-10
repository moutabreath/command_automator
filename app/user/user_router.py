import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from ..api.setup.api_dependency_container import Container
from .schemas.responses import UserApiResponse, UserApiResponseCode
from .services.models import UserRegistryResponseCode
from .services.user_registry_service import UserRegistryService

router = APIRouter(prefix="/api/users", tags=["users"])


def get_user_registry_service() -> UserRegistryService:
    """Dependency injection for UserRegistryService"""
    
    return Container.user_registry_service()


@router.post("/login", response_model=UserApiResponse)
async def login(
    user_email: str,
    user_registry_service: UserRegistryService = Depends(get_user_registry_service)
) -> Dict[str, Any]:
    """Login a user"""
    if not user_email or not user_email.strip():
        logging.error("Invalid email provided")
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    try:
        response = user_registry_service.login(user_email)
    except Exception as e:
        logging.exception(f"Exception calling user registry service: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
     
    if not response: 
        raise HTTPException(status_code=500, detail="Unknown error occurred")
    
    if response.code == UserRegistryResponseCode.OK:
        return UserApiResponse(user_id=response.user_id, code=UserApiResponseCode.OK).model_dump()
    
    error_detail = getattr(response, 'error_message', 'Unknown error')
    logging.error(f"Failed to login user: {error_detail}")
    raise HTTPException(status_code=401, detail=f"Error logging in user: {error_detail}")


@router.post("/register", response_model=UserApiResponse)
async def register(
    user_email: str,
    user_registry_service: UserRegistryService = Depends(get_user_registry_service)
) -> Dict[str, Any]:
    """Register a new user"""
    if not user_email or not user_email.strip():
        logging.error("Invalid email provided")
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    try:
        response = user_registry_service.register(user_email)
    except Exception as e:
        logging.exception(f"Exception calling user registry service: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
     
    if not response: 
        raise HTTPException(status_code=500, detail="Unknown error occurred")
    
    if response.code == UserRegistryResponseCode.OK:
        return UserApiResponse(user_id=response.user_id, code=UserApiResponseCode.OK).model_dump()
    
    error_detail = getattr(response, 'error_message', 'Unknown error')
    logging.error(f"Failed to register user: {error_detail}")
    raise HTTPException(status_code=400, detail=f"Error registering user: {error_detail}")
