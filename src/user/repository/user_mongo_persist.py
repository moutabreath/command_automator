import logging
from typing import Optional, Dict
import uuid

from pymongo.errors import DuplicateKeyError

from repository.abstract_owner_mongo_persist import AbstractOwnerMongoPersist


class UserMongoPersist(AbstractOwnerMongoPersist):

    def _setup_collections(self):
        self.users = self.async_db.users
        self.applications = self.async_db.job_applications

    async def create_index(self):
        if self.users is not None:
            await self.users.create_index([("email", 1)], unique=True)        

    async def create_or_update_user(self, email: str) -> Optional[Dict]:
        # No defensive check needed - create() guarantees readiness
        existing_user = await self.get_user_by_email(email)
        
        if existing_user:
            return existing_user
        
        user_id = str(uuid.uuid4())
        user = {
            "_id": user_id,
            "email": email
        }
        try:
            await self.users.insert_one(user)
            return user
        except DuplicateKeyError:
            # Another process created the user concurrently
            return await self.get_user_by_email(email)
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return None
    
    async def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        return await self.users.find_one({"_id": user_id})

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return await self.users.find_one({"email": email})

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
        async with await self.async_db.client.start_session() as session:
            async with session.start_transaction():
                await self.applications.delete_many({"user_id": user_id}, session=session)
                result = await self.users.delete_one({"_id": user_id}, session=session)
                return result.deleted_count > 0