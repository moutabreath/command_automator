import logging
import uuid
from datetime import datetime, timezone

import pymongo.errors as mongo_errors
from pymongo import UpdateOne

from jobs_tracking.services.models import TrackedJob
from repository.abstract_owner_mongo_persist import AbstractOwnerMongoPersist
from repository.models import PersistenceErrorCode, PersistenceResponse

class CompanyMongoPersist(AbstractOwnerMongoPersist):

    def _setup_collections(self):
        #fields to ignore on update
        self.excluded_fields = {'job_url', 'user_id', 'company_name', 'job_id', 'company_id'}
        self.job_applications = self.async_db.job_applications
        self.users = self.async_db.users
      
    async def create_index(self):
        if self.job_applications is not None:
            await self.job_applications.create_index([("user_id", 1), ("company_id", 1)])
        
    # ==================== APPLICATION CRUD ====================
       
    async def get_tracked_jobs(self, user_id: str, company_name: str) -> PersistenceResponse[list[dict]]:        
        """Get all application by user and company"""
        try:
            result = await self.job_applications.find_one({
                "user_id": user_id, "company_name": company_name
            })
            if result and "jobs" in result:
                jobs = result["jobs"]
                return PersistenceResponse(id=result["company_id"], data=jobs, code=PersistenceErrorCode.SUCCESS)
            return PersistenceResponse(data=[], code=PersistenceErrorCode.SUCCESS)
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

    async def track_new_job(self, user_id: str, company_name: str, tracked_job_dict: dict) -> PersistenceResponse[dict]:
        """Add or update a job in a company application
        
        Returns:
            A PersistenceResponse with a dictionary indicating if the job was created or updated: `{"created": bool, "updated": bool}`.
        """
        logging.info(f"started with user: {user_id} company: \"{company_name}\" job: \"{tracked_job_dict['job_title']}\"")
        
        try:
            existing_company_application = await self._find_existing_application(user_id, company_name)
            # init company id var
            company_id = self._get_company_id(existing_company_application)
            if existing_company_application:
                # find a tracked job with the same job url
                match = next((job for job in existing_company_application.get('jobs', []) 
                            if job['job_url'] == tracked_job_dict['job_url'] and 
                            self._has_job_changes(tracked_job_dict, job)), None)
                if match:
                    tracked_job_dict['job_id'] = match['job_id']
                    return await self.track_existing_job(user_id, company_id, tracked_job_dict)

            result, new_job = await self._create_new_job(tracked_job_dict, company_name, company_id, user_id)
            if result.matched_count == 0:
                return await self._create_new_application_if_possible(user_id, company_name, new_job)
            return PersistenceResponse(data=new_job, code=PersistenceErrorCode.SUCCESS)
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
    
    async def _create_new_job(self, tracked_job_dict:dict, company_name:str, company_id:str, user_id:str):
        job_id = str(uuid.uuid4())
        new_job = {
            "job_id": job_id,
            "job_url": tracked_job_dict["job_url"],
            "job_title": tracked_job_dict["job_title"],
            "update_time": datetime.now(timezone.utc),
            "job_state": str(tracked_job_dict["job_state"]),
            "contact_name": tracked_job_dict.get("contact_name"),
            "contact_linkedin": tracked_job_dict.get("contact_linkedin"),
            "contact_email": tracked_job_dict.get("contact_email"),
            "company_id": company_id
        }
        result = await self.job_applications.update_one(
            {"user_id": user_id, "company_name": company_name, "company_id": company_id},
            {"$push": {"jobs": new_job}}
        )
        return result, new_job
        
    async def _create_new_application_if_possible(self, user_id: str, company_name: str, new_job: dict) -> PersistenceResponse[dict]:
        # STEP 2: The "Discovery" Check
        # Now we check if the user exists at all in the system
        user_exists = await self.users.find_one({"_id": user_id})
        
        if not user_exists:
            logging.error(f"User {user_id} does not exist in the system.")
            return PersistenceResponse(
                data=None, 
                code=PersistenceErrorCode.NOT_FOUND, 
                error_message="USER_NOT_FOUND"
            )
        
        logging.info(f"User exists, but company '{company_name}' application is new.")
        # At this point, you know the user is valid, so you can safely 
        # perform a secondary 'upsert' just for this company document.
        await self._create_new_company_application(user_id, company_name, new_job)
        return PersistenceResponse(data=new_job, code=PersistenceErrorCode.SUCCESS)

    async def _create_new_company_application(self, user_id: str, company_name: str, new_job: dict):
        application = {
            "user_id": user_id,
            "company_name": company_name,
            "company_id": new_job.get("company_id"),
            "jobs": [new_job]
        }
        await self.job_applications.insert_one(application)

    def _get_company_id(self, existing_company_application):
         if existing_company_application:
            return  existing_company_application['company_id']
         return str(uuid.uuid4())
    
    async def track_existing_job(self, user_id:str, company_id:str,  tracked_job_dict: dict)-> PersistenceResponse[dict]:

        logging.info(f"started with user: {user_id} company: \"{company_id}\"")        
     
        tracked_job_dict['update_time'] = datetime.now(timezone.utc)

        # Use the '$' positional operator to update the matched job element in the jobs array
        set_fields = {f"jobs.$.{key}": value for key, value in tracked_job_dict.items()
                if key not in self.excluded_fields}
        try:
            result = await self.job_applications.update_one(
                {
                    "user_id": user_id,
                    "company_id": company_id,
                    "jobs.job_id": tracked_job_dict['job_id']
                },
                {"$set": set_fields}
            )
            success = result and result.modified_count > 0
            if success:
                return PersistenceResponse(data=tracked_job_dict, code=PersistenceErrorCode.SUCCESS)
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message="Failed to update job")
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
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
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
    
     
 
        
    async def delete_job(self, user_id: str, company_name: str, job_url: str) -> PersistenceResponse[bool]:
        """Delete a specific job from a company application"""

        logging.info(f"started with user: {user_id} company: \"{company_name}\" job: \"{job_url}\"")
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

    async def delete_tracked_jobs(self, user_id: str, companies_dicts: list[dict]) -> bool:
        """
        Removes jobs from the database using company_name and job_url 
            as unique identifiers.
            """
        logging.info(f"started with user {user_id} with {len(companies_dicts)} companies")

        for company_dict in companies_dicts:
            tracked_jobs = company_dict.get("tracked_jobs", [])
            urls_to_remove = [job["job_url"] for job in tracked_jobs]
            if not urls_to_remove:
                continue
            try:
                requests = [
                    UpdateOne(
                        {"user_id": user_id, "company_name": comp_dict["company_name"]},
                        {"$pull": {"jobs": {"job_url": {"$in": [job["job_url"] for job in comp_dict.get("tracked_jobs", [])]}}}}
                    )
                    for comp_dict in companies_dicts if comp_dict.get("tracked_jobs")
                ]
                
                if not requests:
                    return False
                
                result = await self.job_applications.bulk_write(requests)
                return result.modified_count > 0
            except Exception as e:
                logging.exception(f"Failed to delete jobs for user {user_id}: {e}")
                return False
    
    async def get_all_applications(self, user_id: str) -> PersistenceResponse[list[dict]]:
        """Get all applications for a user"""
        try:
            cursor = self.job_applications.find({"user_id": user_id})
            results = await cursor.to_list(length=None)
            companies = results
            return PersistenceResponse(data=companies, code=PersistenceErrorCode.SUCCESS)
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
    
    # ==================== QUERY HELPERS ====================
    
    
    async def get_jobs_by_state(self, user_id: str, state: str) -> PersistenceResponse[list[TrackedJob]]:
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
        return await self._execute_job_aggregation(pipeline)
   
    async def get_recent_jobs(self, user_id: str, limit: int = 10) -> PersistenceResponse[list[dict]]:
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
        return await self._execute_job_aggregation(pipeline)

    async def _execute_job_aggregation(self, pipeline: list[dict]) -> PersistenceResponse[list[dict]]:
        """Execute aggregation pipeline and convert results to dictionary list"""
        try:
            cursor = self.job_applications.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            tracked_jobs_dicts = [r["job"] for r in results]
            return PersistenceResponse(data=tracked_jobs_dicts, code=PersistenceErrorCode.SUCCESS)
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
    
    async def _find_existing_application(self, user_id: str, company_name: str) -> dict:
        try:
            # Check if job already exists
            existing = await self.job_applications.find_one({
                "user_id": user_id,
                "company_name": company_name
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

    def _has_job_changes(self, existing_job: dict, new_job: dict) -> bool:
        """Compare existing job with new job data (excluding job identifiers and update_time)"""
        for key, value in new_job.items():
            if key not in self.excluded_fields:
                if existing_job.get(key) != value:
                    return True
        return False
