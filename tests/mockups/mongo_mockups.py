import pytest
import mongomock
import uuid
from typing import Optional, Dict
import pymongo.errors as mongo_errors
from jobs_tracking.services.models import TrackedJob
from jobs_tracking.repository.company_mongo_persist import CompanyMongoPersist



@pytest.fixture
def db():
    return mongomock.MongoClient().job_tracker_test

class MockUserMongoPersist:

    def __init__(self, db):
        self.users = AsyncMockCollection(db.users)

    async def create_or_update_user(self, email: str) -> Optional[Dict]:
        user = await self.users.find_one({"email": email})
        if user:
            return user
        
        user_id = str(uuid.uuid4())
        new_user = {"_id": user_id, "email": email}
        await self.users.insert_one(new_user)
        return new_user

class AsyncMockCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.cursor)
        except StopIteration:
            raise StopAsyncIteration
    async def to_list(self, length=None):
        if length is None:
            return list(self.cursor)
        result = []
        for i, doc in enumerate(self.cursor):
            if i >= length:
                break
            result.append(doc)
        return result
    
class AsyncMockCollection:
    def __init__(self, collection):
        self.collection = collection

    async def find_one(self, *args, **kwargs):
        return self.collection.find_one(*args, **kwargs)

    async def insert_one(self, *args, **kwargs):
        return self.collection.insert_one(*args, **kwargs)

    async def update_one(self, *args, **kwargs):
        return self.collection.update_one(*args, **kwargs)

    async def delete_one(self, *args, **kwargs):
        return self.collection.delete_one(*args, **kwargs)
    
    async def create_index(self, *args, **kwargs):
        return self.collection.create_index(*args, **kwargs)

    def find(self, *args, **kwargs):
        return AsyncMockCursor(self.collection.find(*args, **kwargs))

    def aggregate(self, *args, **kwargs):
        return AsyncMockCursor(self.collection.aggregate(*args, **kwargs))

class AsyncMockDatabase:
    def __init__(self, db):
        self.db = db

    def __getattr__(self, name):
        return AsyncMockCollection(getattr(self.db, name))
    
    def __getitem__(self, name):
        return AsyncMockCollection(self.db[name])

class MockCompanyMongoPersist(CompanyMongoPersist):
    def __init__(self, db):
        self.async_db = AsyncMockDatabase(db)
        self._setup_collections()
