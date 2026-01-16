import pytest
import uuid

from user.services.user_registry_service import UserRegistryService, UserRegistryResponseCode

from tests.mockups.mongo_mockups import MockUserMongoPersist

 
@pytest.fixture
def user_service(db):
    mock_persist = MockUserMongoPersist(db)
    return UserRegistryService(mock_persist)

@pytest.mark.asyncio
async def test_register_user_returns_id(user_service):
    email = f"test-async-{uuid.uuid4()}@example.com"
    response = await user_service.register_async(email)
    
    assert response.code == UserRegistryResponseCode.OK
    assert response.user_id is not None
    assert len(response.user_id) > 0
