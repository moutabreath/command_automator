from datetime import datetime, timezone
import logging
from typing import Optional, List, Dict
import pymongo.errors as mongo_errors
from motor.motor_asyncio import AsyncIOMotorClient

from jobs_tracking.models import JobApplicationState

from repository.abstract_mongo_persist import AbstractMongoPersist, PersistenceErrorCode, PersistenceResponse


class CompanyMongoPersist(AbstractMongoPersist):

    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "job_tracker"):
        """Initialize MongoDB connection"""
        super().__init__(connection_string=connection_string, db_name=db_name)        
      
    def create_index(self):
        try:
            self.job_applications = self.db.job_applications
            self.job_applications.create_index([("user_id", 1), ("company_name", 1)])      
        except Exception as e:
            logging.exception(f"failed creating job application document or creating index {e}")
        
    # ==================== APPLICATION CRUD ====================
  
    async def get_application(self, user_id: str, company_name: str) -> PersistenceResponse[Dict]:
        """Get application by user and company"""
        try:
            result = await self.job_applications.find_one({
                "user_id": user_id,
                "company_name": company_name
                })
            if result:
                return PersistenceResponse(
                    data=result,
                    code=PersistenceErrorCode.SUCCESS
                )
            logging.error(f"Document not found {user_id}, {company_name}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.NOT_FOUND,
                error_message=f"Document with id {user_id} and company name {company_name} not found"
            )
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
    
    async def get_all_applications(self, user_id: str) -> PersistenceResponse[List[Dict]]:
        """Get all applications for a user"""
        try:
            cursor = self.job_applications.find({"user_id": user_id})
            results = await cursor.to_list(length=None)
            return PersistenceResponse(
                data=results,
                code=PersistenceErrorCode.SUCCESS
            )
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
    
    async def delete_application(self, user_id: str, company_name: str) -> PersistenceResponse[bool]:
        """Delete an entire company application"""
        try:
            result = await self.job_applications.delete_one({
                "user_id": user_id,
                "company_name": company_name
            })
            if result.deleted_count > 0:
                return PersistenceResponse(data=True, code=PersistenceErrorCode.SUCCESS)
            return PersistenceResponse(
                data=False,
                code=PersistenceErrorCode.NOT_FOUND,
                error_message=f"Application for user {user_id} and company {company_name} not found."
            )
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
    
    # ==================== JOB CRUD ====================
    
    async def add_job(self, user_id: str, company_name: str, job_url: str, 
                job_title: Optional[str], state: JobApplicationState, contact: Optional[str] = None, contact_url: Optional[str] = None) -> PersistenceResponse[Dict[str, bool]]:
        """Add or update a job in a company application
        
        Returns:
            A PersistenceResponse with a dictionary indicating if the job was created or updated: `{"created": bool, "updated": bool}`.
        """
      
        job = {
            "job_url": job_url,
            "job_title": job_title,
            "update_time": datetime.now(timezone.utc),
            "state": state.value if hasattr(state, 'value') else state,
            "contact": contact,
            "contact_url": contact_url
        }
        try:
            existing = await self._find_existing_application(user_id, company_name, job_url)
        
            if existing:
                result_data = await self._update_existing_application(company_name=company_name, user_id=user_id, job_url=job_url, job=job)
            else:
                # Add new job (create company application if needed)
                await self.job_applications.update_one(
                    {"user_id": user_id, "company_name": company_name},
                    {"$push": {"jobs": job}},
                    upsert=True
                )
                result_data = {"created": True, "updated": False}
            return PersistenceResponse(data=result_data, code=PersistenceErrorCode.SUCCESS)
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
            logging.exception(f"MongoDB error occurred: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
    
    async def get_jobs(self, user_id: str, company_name: str) -> PersistenceResponse[List[Dict]]:
        """Get all jobs for a company"""
        try:
            app_response = await self.get_application(user_id, company_name)
            if app_response.code == PersistenceErrorCode.SUCCESS and app_response.data:
                return PersistenceResponse(data=app_response.data.get("jobs", []), code=PersistenceErrorCode.SUCCESS)
            elif app_response.code == PersistenceErrorCode.NOT_FOUND:
                return PersistenceResponse(data=[], code=PersistenceErrorCode.NOT_FOUND) # Return empty list if company not found
            return app_response # Propagate other errors
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
    
    def update_job(self, user_id: str, company_name: str, job_url: str, 
                   update_fields: Dict) -> PersistenceResponse[bool]:
        """Update a specific job (identified by job_url)"""
        try:
            update_fields["update_time"] = datetime.now(timezone.utc)
            # Convert enum to value if present
            if "state" in update_fields and hasattr(update_fields["state"], 'value'):
                update_fields["state"] = update_fields["state"].value
            
            # Build update query for nested array element
            set_fields = {f"jobs.$.{k}": v for k, v in update_fields.items()}
            
            result = self.job_applications.update_one(
                {"user_id": user_id, "company_name": company_name, "jobs.job_url": job_url},
                {"$set": set_fields}
            )
            
            if result.modified_count > 0:
                return PersistenceResponse(data=True, code=PersistenceErrorCode.SUCCESS)
            return PersistenceResponse(data=False, code=PersistenceErrorCode.NOT_FOUND, error_message="Job not found for update.")
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
    
    def delete_job(self, user_id: str, company_name: str, job_url: str) -> PersistenceResponse[bool]:
        """Delete a specific job from a company application"""
        try:
            result = self.job_applications.update_one(
                {"user_id": user_id, "company_name": company_name},
                {"$pull": {"jobs": {"job_url": job_url}}}
            )
            if result.modified_count > 0:
                return PersistenceResponse(data=True, code=PersistenceErrorCode.SUCCESS)
            return PersistenceResponse(data=False, code=PersistenceErrorCode.NOT_FOUND, error_message="Job not found for deletion.")
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
    
    # ==================== QUERY HELPERS ====================
    
    def get_jobs_by_state(self, user_id: str, state: str) -> PersistenceResponse[List[Dict]]:
        """Get all jobs with a specific state across all companies"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$jobs"},
            {"$match": {"jobs.state": state}},
            {"$project": {
                "company_name": 1,
                "job": "$jobs"
            }}
        ]
        try:
            results = list(self.job_applications.aggregate(pipeline))
            return PersistenceResponse(data=results, code=PersistenceErrorCode.SUCCESS)
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
    
    def get_recent_jobs(self, user_id: str, limit: int = 10) -> PersistenceResponse[List[Dict]]:
        """Get most recently updated jobs"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$jobs"},
            {"$sort": {"jobs.update_time": -1}},
            {"$limit": limit},
            {"$project": {
                "company_name": 1,
                "job": "$jobs"
            }}
        ]
        try:
            results = list(self.job_applications.aggregate(pipeline))
            return PersistenceResponse(data=results, code=PersistenceErrorCode.SUCCESS)
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))


    async def _find_existing_application(self, user_id, company_name, job_url):
        try:
            # Check if job already exists
            existing = await self.job_applications.find_one({
                "user_id": user_id,
                "company_name": company_name,
                "jobs.job_url": job_url
            })
            return existing
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            raise
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logging.exception(f"Unexpected error in add_job: {e}")
            raise 

    async def _update_existing_application(self, job, user_id, company_name, job_url)-> Dict[str, bool]:
        # Use the '$' positional operator to update the matched job element in the jobs array
        set_fields = {f"jobs.$.{k}": v for k, v in job.items()}
        try:
            result = await self.job_applications.update_one(
                {
                    "user_id": user_id,
                    "company_name": company_name,
                    "jobs.job_url": job_url
                },
                {"$set": set_fields}
            )
            return {"created": False, "updated": result.modified_count > 0}
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            raise
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logging.exception(f"Unexpected error in add_job: {e}")
            raise 