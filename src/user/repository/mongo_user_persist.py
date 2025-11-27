import logging
from pymongo import MongoClient
from typing import Optional, Dict
import uuid

class MongoUserPerist:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "job_tracker"):
        """Initialize MongoDB connection"""
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.users = self.db.users
        
        # Create indexes
    def create_or_update_user(self, email: str) -> Dict[str, str]:
        """Create a new user or return existing user
        
        MongoDB generates the GUID ID on insert.
        If email exists, returns existing user record.
        If email doesn't exist, creates new user with GUID ID.
        
        Returns:
            {"user_id": str, "created": bool}
        """
        existing_user = self.get_user_by_email(email)
        
        if existing_user:
            logging.debug(f"User with email {email} already exists")
            return {
                "user_id": existing_user["_id"],
                "created": False
            }
        
        # Create new user with GUID ID
        user_id = str(uuid.uuid4())
        user = {
            "_id": user_id,
            "email": email
        }
        try:
            self.users.insert_one(user)
            logging.debug(f"Created new user with ID {user_id}")
            return {
                "user_id": user_id,
                "created": True
            }
        except Exception as e:
            logging.error(f"Error creating user {email}: {e}")
            raise

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