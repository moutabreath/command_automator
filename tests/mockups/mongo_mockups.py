import pytest
import mongomock
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from jobs_tracking.models import JobApplicationState
from repository.abstract_mongo_persist import PersistenceResponse, PersistenceErrorCode



@pytest.fixture
def db():
    return mongomock.MongoClient().job_tracker_test

class MockUserMongoPersist:

    def __init__(self, db):
        self.users = db.users

    async def create_or_update_user(self, email: str) -> Optional[Dict]:
        user = self.users.find_one({"email": email})
        if user:
            return user
        
        user_id = str(uuid.uuid4())
        new_user = {"_id": user_id, "email": email}
        self.users.insert_one(new_user)
        return new_user

class MockCompanyMongoPersist:

    def __init__(self, db):
        self.job_applications = db.job_applications

    async def add_or_update_position(self, user_id: str, company_name: str, job_url: str, 
                job_title: Optional[str], job_state: JobApplicationState, contact_name: Optional[str], 
                contact_linkedin: Optional[str], contact_email: Optional[str]) -> PersistenceResponse[Dict[str, Any]]:
        
        doc = self.job_applications.find_one({"user_id": user_id, "company_name": company_name})
        
        state_val = job_state.value if hasattr(job_state, 'value') else job_state
        
        job_entry = {
            "job_url": job_url,
            "job_title": job_title,
            "job_state": state_val,
            "contact_name": contact_name,
            "contact_linkedin": contact_linkedin,
            "contact_email": contact_email,
            "update_time": datetime.now(timezone.utc)
        }

        if not doc:
            doc = {
                "user_id": user_id,
                "company_name": company_name,
                "jobs": [job_entry]
            }
            self.job_applications.insert_one(doc)
        else:
            jobs = doc.get("jobs", [])
            existing_idx = next((i for i, j in enumerate(jobs) if j["job_url"] == job_url), -1)
            if existing_idx >= 0:
                jobs[existing_idx].update(job_entry)
            else:
                jobs.append(job_entry)
            
            self.job_applications.update_one(
                {"_id": doc["_id"]},
                {"$set": {"jobs": jobs}}
            )
            
        return PersistenceResponse(data=job_entry, code=PersistenceErrorCode.SUCCESS)
