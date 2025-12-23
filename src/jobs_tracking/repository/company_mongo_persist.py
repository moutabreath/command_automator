from dataclasses import asdict
import logging
from typing import List, Dict
import pymongo.errors as mongo_errors

from jobs_tracking.services.models import TrackedJob, JobApplicationState

from repository.abstract_mongo_persist import PersistenceErrorCode, PersistenceResponse
from repository.abstract_owner_mongo_persist import AbstractOwnerMongoPersist

class CompanyMongoPersist(AbstractOwnerMongoPersist):


    def _setup_collections(self):
        self.job_applications = self.async_db.job_applications
      
    async def create_index(self):
        if self.job_applications is not None:
            await self.job_applications.create_index([("user_id", 1), ("company_name", 1)])
        
    # ==================== APPLICATION CRUD ====================
       
    async def get_tracked_jobs(self, user_id: str, company_name: str) -> PersistenceResponse[List[TrackedJob]]:        
        """Get all application by user and company"""
        try:
            result = await self.job_applications.find_one({
                "user_id": user_id,
                "company_name": company_name
                })
            if result and "jobs" in result:
                tracked_jobs = self.convert_mongo_result_to_tracked_job_list(result)
                return PersistenceResponse(
                    data=tracked_jobs,
                    code=PersistenceErrorCode.SUCCESS
                )
            return PersistenceResponse(
                data=[],
                code=PersistenceErrorCode.SUCCESS
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

    def convert_mongo_result_to_tracked_job_list(self, result):
        tracked_jobs = [
                    TrackedJob(
                        job_url=job["job_url"],
                        job_title=job["job_title"],
                        job_state=JobApplicationState(job["job_state"]),
                        contact_name=job.get("contact_name"),
                        contact_linkedin=job.get("contact_linkedin"),
                        contact_email=job.get("contact_email"),
                        update_time=job.get("update_time")
                    )
                    for job in result["jobs"]
                ]
        
        return tracked_jobs

    
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
    
    async def add_or_update_position(self, user_id: str, company_name: str, tracked_job: TrackedJob, update_time) -> PersistenceResponse[TrackedJob]:
        """Add or update a job in a company application
        
        Returns:
            A PersistenceResponse with a dictionary indicating if the job was created or updated: `{"created": bool, "updated": bool}`.
        """
        job = {
            "job_url": tracked_job.job_url,
            "job_title": tracked_job.job_title,
            "update_time": update_time,
            "job_state": tracked_job.job_state.value if hasattr(tracked_job.job_state, 'value') else tracked_job.job_state,
            "contact_name": tracked_job.contact_name,
            "contact_linkedin": tracked_job.contact_linkedin,
            "contact_email" : tracked_job.contact_email
        }
       
        try:
            existing = await self._find_existing_application(user_id, company_name, tracked_job.job_url)
        
            if existing:
                result = await self._update_existing_application(user_id, company_name, job)
                if not result or result.modified_count == 0:
                    return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message="Failed to update job")
            else:
                result = await self.job_applications.update_one(
                    {"user_id": user_id, "company_name": company_name},
                    {"$push": {"jobs": job}},
                    upsert=True
                )
                if not result or (result.matched_count == 0 and result.upserted_id is None):
                    return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message="Failed to add job")
            tracked_job.update_time = update_time
            return PersistenceResponse(data=tracked_job, code=PersistenceErrorCode.SUCCESS)
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
        
    async def delete_job(self, user_id: str, company_name: str, job_url: str) -> PersistenceResponse[bool]:
        """Delete a specific job from a company application"""
        try:
            result = await self.job_applications.update_one(
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
    
    async def get_jobs_by_state(self, user_id: str, state: str) -> PersistenceResponse[List[Dict]]:
        """Get all jobs with a specific state across all companies"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$jobs"},
            {"$match": {"jobs.job_state": state}},
            {"$project": {
                "company_name": 1,
                "job": "$jobs"
            }}
        ]
        try:
            cursor = self.job_applications.aggregate(pipeline)
            results = await cursor.to_list(length=None)
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
    
    async def get_recent_jobs(self, user_id: str, limit: int = 10) -> PersistenceResponse[List[Dict]]:
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
            cursor = self.job_applications.aggregate(pipeline)
            results = await cursor.to_list(length=None)
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

    async def _update_existing_application(self, user_id, company_name, job)-> Dict[str, bool]:
        # Use the '$' positional operator to update the matched job element in the jobs array
        EXCLUDED_FIELDS = {'job_url', 'user_id', 'company_name'}

        set_fields = {f"jobs.$.{key}": value for key, value in asdict(job).items() 
              if key not in EXCLUDED_FIELDS}
        try:
            result = await self.job_applications.update_one(
                {
                    "user_id": user_id,
                    "company_name": company_name,
                    "jobs.job_url": job['job_url']
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