import logging
from typing import Optional, Dict
import uuid

from repository.abstract_mongo_persist import AbstractMongoPersist


class UserMongoPersist(AbstractMongoPersist):
    def __init__(self, connection_string: str, db_name: str):
        super().__init__(connection_string, db_name)
        # Explicitly None to catch uninitialized usage
        self.users = None
        self.applications = None

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
            return await self.get_user(user_id)
        except Exception as e:
            logging.error(f"Error creating user {email}: {e}")
            return None

    async def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        return await self.users.find_one({"_id": user_id})

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return await self.users.find_one({"email": email})

    async def update_user_email(self, user_id: str, new_email: str) -> bool:
        """Update user email"""
        result = await self.users.update_one(
            {"_id": user_id},
            {"$set": {"email": new_email}}
        )
        return result.modified_count > 0

    async def delete_user(self, user_id: str) -> bool:
        """Delete user and all their applications"""
        await self.applications.delete_many({"user_id": user_id})
        result = await self.users.delete_one({"_id": user_id})
        return result.deleted_count > 0