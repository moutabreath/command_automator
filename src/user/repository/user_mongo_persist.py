import logging
from typing import Optional, Dict
import uuid

from pymongo.errors import DuplicateKeyError
import pymongo.errors as mongo_errors

from repository.abstract_owner_mongo_persist import AbstractOwnerMongoPersist
from repository.models import PersistenceErrorCode, PersistenceResponse


class UserMongoPersist(AbstractOwnerMongoPersist):

    def _setup_collections(self):
        self.users = self.async_db.users
        self.job_applications = self.async_db.job_applications

    async def create_index(self):
        if self.users is not None:
            await self.users.create_index([("userid", 1)], unique=True)
    
    async def get_user(self, email: str) -> PersistenceResponse:
        """Register a new user"""
        response = await self.get_user_by_email(email)
        if response:
            logging.info(f"User {response['_id']} registered")
            return response
        
    async def register_user(self, email: str) -> PersistenceResponse:
        response = await self.get_user_by_email(email)
        
        if response.data != None:
            return response
        
        user_id = str(uuid.uuid4())
        user = {
            "_id": user_id,
            "email": email
        }
        try:
            await self.users.insert_one(user)
            return PersistenceResponse(data=user, code=PersistenceErrorCode.SUCCESS)
        except DuplicateKeyError:
            # Another process created the user concurrently
            return await self.get_user_by_email(email)
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.CONNECTION_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
        
    
    async def get_user(self, user_id: str) -> PersistenceResponse:
        """Get user by ID"""
        return await self.users.find_one({"_id": user_id})

    async def get_user_by_email(self, email: str) -> PersistenceResponse:
        """Get user by email"""
        try:
            mongo_result = await self.users.find_one({"email": email})
            return PersistenceResponse(data=mongo_result, code=PersistenceErrorCode.SUCCESS)
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.CONNECTION_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )


    async def update_user_email(self, user_id: str, new_email: str) -> bool:
        try:
            result = await self.users.update_one(
                {"_id": user_id},
                {"$set": {"email": new_email}}
            )
            return result.modified_count > 0
        except DuplicateKeyError:
            logging.warning(f"Cannot update user {user_id}: email {new_email} already exists")
            return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete user and all their applications"""
        try:
            async with await self.async_db.client.start_session() as session:
                async with session.start_transaction():
                    await self.job_applications.delete_many({"user_id": user_id}, session=session)
                    result = await self.users.delete_one({"_id": user_id}, session=session)
                    return result.deleted_count > 0
        except Exception as ex:
            logging.exception(f"Error deleting user {user_id}: {ex}")
            return False
