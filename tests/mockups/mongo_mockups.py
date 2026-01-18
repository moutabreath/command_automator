import pytest
import mongomock

from jobs_tracking.repository.company_mongo_persist import CompanyMongoPersist
from user.repository.user_mongo_persist import UserMongoPersist



@pytest.fixture
def db():
    return mongomock.MongoClient().job_tracker_test

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
    
    async def bulk_write(self, requests, *args, **kwargs):
        # Manual implementation to bypass mongomock/pymongo compatibility issues
        # specifically: TypeError: BulkOperationBuilder.add_update() got an unexpected keyword argument 'sort'
        modified_count = 0
        deleted_count = 0
        inserted_count = 0
        upserted_count = 0
        matched_count = 0
        
        for req in requests:
            op_type = type(req).__name__
            
            if op_type == 'InsertOne':
                self.collection.insert_one(req._doc)
                inserted_count += 1
            elif op_type == 'UpdateOne':
                res = self.collection.update_one(req._filter, req._doc, upsert=getattr(req, '_upsert', False))
                modified_count += res.modified_count
                matched_count += res.matched_count
                if res.upserted_id:
                    upserted_count += 1
            elif op_type == 'UpdateMany':
                res = self.collection.update_many(req._filter, req._doc, upsert=getattr(req, '_upsert', False))
                modified_count += res.modified_count
                matched_count += res.matched_count
                if res.upserted_id:
                    upserted_count += 1
            elif op_type == 'ReplaceOne':
                res = self.collection.replace_one(req._filter, req._doc, upsert=getattr(req, '_upsert', False))
                modified_count += res.modified_count
                matched_count += res.matched_count
                if res.upserted_id:
                    upserted_count += 1
            elif op_type == 'DeleteOne':
                res = self.collection.delete_one(req._filter)
                deleted_count += res.deleted_count
            elif op_type == 'DeleteMany':
                res = self.collection.delete_many(req._filter)
                deleted_count += res.deleted_count
                
        class MockBulkWriteResult:
            def __init__(self, modified, deleted, inserted, upserted, matched):
                self.modified_count = modified
                self.deleted_count = deleted
                self.inserted_count = inserted
                self.upserted_count = upserted
                self.matched_count = matched
                self.upserted_ids = {}

        return MockBulkWriteResult(modified_count, deleted_count, inserted_count, upserted_count, matched_count)
    
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

class MockUserMongoPersist(UserMongoPersist):
     def __init__(self, db):
        self.async_db = AsyncMockDatabase(db)
        self._setup_collections()

class MockCompanyMongoPersist(CompanyMongoPersist):
    def __init__(self, db):
        self.async_db = AsyncMockDatabase(db)
        self._setup_collections()
