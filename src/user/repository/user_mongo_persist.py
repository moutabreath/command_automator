import logging
from typing import Optional, Dict
import uuid

from repository.abstract_mongo_persist import AbstractMongoPersist

class UserMongoPersist(AbstractMongoPersist):
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "job_tracker"):
        """Initialize MongoDB connection"""
        super().__init__(connection_string=connection_string, db_name=db_name)        
    
    def create_index(self):
        self.users = self.db.users
        self.users.create_index([("email", 1)], unique=True)
        self.applications = self.db.job_applications
        
    def create_or_update_user(self, email: str) -> str:
        """Create a new user or return existing user
        
        Generates a UUID as the user ID on insert.
        If email exists, returns existing user record.
        If email doesn't exist, creates new user with GUID ID.
        
        Returns:
            str: The user_id of the existing or newly created user, or empty string on error        """
        existing_user = self.get_user_by_email(email)
        
        if existing_user:
            logging.debug(f"User with email {email} already exists")
            return existing_user["_id"]
        
        # Create new user with GUID ID
        user_id = str(uuid.uuid4())
        user = {
            "_id": user_id,
            "email": email
        }
        try:
            self.users.insert_one(user)
            logging.debug(f"Created new user with ID {user_id}")
            return user_id
        except Exception as e:
            logging.error(f"Error creating user {email}: {e}")
            return ""

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        return self.users.find_one({"_id": user_id})

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return self.users.find_one({"email": email})

    def update_user_email(self, user_id: str, new_email: str) -> bool:
        """Update user email"""
        result = self.users.update_one(
            {"_id": user_id},
            {"$set": {"email": new_email}}
        )
        return result.modified_count > 0

    def delete_user(self, user_id: str) -> bool:
        """Delete user and all their applications"""
        self.applications.delete_many({"user_id": user_id})
        result = self.users.delete_one({"_id": user_id})
        return result.deleted_count > 0