import logging
from typing import Optional
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

import pymongo.errors as mongo_errors
from pymongo import UpdateOne
from motor.motor_asyncio import AsyncIOMotorClient


from .models.entities import CompanyJobsDocument, JobEntity
from .mapper import EntitiesMapper
from .models.projections import JobWithCompanyContext
from ..services.domain.models import TrackedJob
from ...repository.models import PersistenceResponse, PersistenceErrorCode
from .models.queries import (
    TrackNewJobDbQuery,
    TrackExistingJobDbQuery,
    DeleteApplicationDbQuery,
    DeleteJobDbQuery,
    DeleteTrackedJobsDbQuery
)


class JobTrackingWriterPersistMongo:

    
    def __init__(self, connection_string: str, db_name: str):
        
        self.async_client = AsyncIOMotorClient(
            connection_string
        )
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        self.job_applications = self.async_client[db_name]
        #fields to ignore on update
        self.excluded_fields = {'job_url', 'user_id', 'company_name', 'job_id', 'company_id', 'update_time'}
      
        
    # ==================== APPLICATION CRUD ====================
       

    async def track_new_job(self, query: TrackNewJobDbQuery) -> PersistenceResponse[JobWithCompanyContext]:
        """Add or update a job in a company application
        
        Returns:
            A PersistenceResponse with a dictionary indicating if the job was created or updated: `{"created": bool, "updated": bool}`.
        """
        user_id, company_name, new_tracked_job = query.user_id, query.company_name, query.tracked_job
        new_job_entity = EntitiesMapper.to_job_entity(new_tracked_job)
        logging.info(f"started with user: {user_id} company: \"{company_name}\" job: \"{new_tracked_job.job_title}\"")
        
        try:
            existing_company_application: CompanyJobsDocument= await self._find_existing_application(user_id, company_name)
            # init company id 
            company_id = self._get_company_id(existing_company_application)
            
            if existing_company_application:
                return await self._update_existing_company_application(
                    user_id, company_name, company_id, new_tracked_job, existing_company_application
                )
            # Company does not exist, need to create the company with the new job
            result = await self._add_new_job_to_new_company(new_job_entity, company_name, company_id, user_id)
            if not (result and result.inserted_id):
                return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message="Failed to add new job to new company application.")
            
            context = JobWithCompanyContext(company_id=company_id, company_name=company_name, job=EntitiesMapper.to_domain(new_job_entity))
            return PersistenceResponse(data=context, code=PersistenceErrorCode.SUCCESS)
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(data=None,code=PersistenceErrorCode.CONNECTION_ERROR, error_message=f"MongoDB connection failed: {e}")
        except Exception as e:
            logging.exception(f"MongoDB error occurred: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
    
    async def _update_existing_company_application(self, user_id: str, company_name: str, company_id: str,
                                                    new_tracked_job: TrackedJob, 
                                                    existing_company_application: CompanyJobsDocument
    ) -> PersistenceResponse[JobWithCompanyContext]:
        # find a tracked job with the same job url
        existing_job = next((job for job in existing_company_application.jobs 
                    if job.job_url == new_tracked_job.job_url), None)
        
        if existing_job:
            if self._has_job_changes(new_tracked_job, existing_job):
                new_tracked_job.job_id = existing_job.job_id
                response = await self.track_existing_job(TrackExistingJobDbQuery(
                    user_id=user_id,
                    company_id=company_id,
                    tracked_job=new_tracked_job
                ))
                if response.code == PersistenceErrorCode.SUCCESS:
                    return PersistenceResponse(data=JobWithCompanyContext(company_id=company_id, company_name=company_name, job=response.data),
                        code=PersistenceErrorCode.SUCCESS
                    )
                return PersistenceResponse(data=None, code=response.code, error_message=response.error_message)
            else:
                # Job exists but no changes detected; return success without DB write
                return PersistenceResponse(
                    data=JobWithCompanyContext(company_id=company_id, company_name=company_name, job=EntitiesMapper.to_domain(existing_job)),
                    code=PersistenceErrorCode.SUCCESS
                )
        
        new_job_entity=EntitiesMapper.to_job_entity(new_tracked_job)
        response = await self._add_new_job_to_existing_company(
            company_id=company_id,
            user_id=user_id,
            new_job_entity=new_job_entity)
        if not (response and response.modified_count > 0):
                return PersistenceResponse(data=None,code=PersistenceErrorCode.OPERATION_ERROR,error_message="Failed to add new job to existing company application.")

        new_tracked_job = EntitiesMapper.to_domain(new_job_entity) # return back all changes that need to be updated
        return PersistenceResponse(data=new_tracked_job, code=PersistenceErrorCode.SUCCESS)
    
    async def _add_new_job_to_new_company(self, job_entity: JobEntity, company_name: str, company_id: str, user_id: str):
        """
        Creates a brand new CompanyJobsDocument in MongoDB when the user 
        tracks their first job for a specific company.
        """
        try:
            # 1. Prepare the Root Entity
            new_application = CompanyJobsDocument(company_id=company_id,company_name=company_name,user_id=user_id,
                jobs=[job_entity]
            )

            # 2. Convert to Dictionary for the Driver
            doc_to_insert = asdict(new_application)
            
            # Don't send a None ID to Mongo
            if doc_to_insert.get("id") is None:
                doc_to_insert.pop("id")

            # 3. Persistence
            logging.info(f"Creating new company document for '{company_name}' (User: {user_id})")
            return await self.job_applications.insert_one(doc_to_insert)            

        except mongo_errors.DuplicateKeyError:
            # High-concurrency edge case: another request created the doc 
            # between our 'find' check and this 'insert'.
            logging.warning(f"Conflict: Document for {company_name} already exists. Falling back to push.")
            return await self._add_new_job_to_existing_company(job_entity, company_id, user_id)
            
        except Exception as e:
            logging.exception(f"Failed to create new company application: {e}")
            raise

    async def _add_new_job_to_existing_company(self, new_job_entity:JobEntity, company_id:str, user_id:str):
            return await self.job_applications.update_one(
                    {"user_id": user_id, "company_id": company_id},
                    {"$push": {"jobs": asdict(new_job_entity)}}
                )

 
    def _get_company_id(self, existing_company_application: CompanyJobsDocument) -> str:
         if existing_company_application:
            return existing_company_application.company_id
         return str(uuid.uuid4())
    
    async def track_existing_job(self, query: TrackExistingJobDbQuery)-> PersistenceResponse[TrackedJob]:

        user_id, company_id, tracked_job = query.user_id, query.company_id, query.tracked_job
        logging.info(f"started with user: {user_id} company: \"{company_id}\"")        
        tracked_job.update_time = datetime.now(timezone.utc)
        tracked_job_dict = asdict(tracked_job)

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
                return PersistenceResponse(data=tracked_job, code=PersistenceErrorCode.SUCCESS)
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message="Failed to update job")
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.CONNECTION_ERROR,error_message=f"MongoDB connection failed: {e}")
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(data=None,code=PersistenceErrorCode.UNKNOWN_ERROR,error_message=str(e))
  
    
    async def delete_application(self, query: DeleteApplicationDbQuery) -> PersistenceResponse[bool]:
        """Delete an entire company application"""
        user_id, company_name = query.user_id, query.company_name
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
 
        
    async def delete_job(self, query: DeleteJobDbQuery) -> PersistenceResponse[bool]:
        """Delete a specific job from a company application"""
        user_id, company_name, job_url = query.user_id, query.company_name, query.job_url

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

    async def delete_tracked_jobs(self, query: DeleteTrackedJobsDbQuery) -> bool:
        """
        Removes jobs from the database using company_name and job_url 
            as unique identifiers.
            """
        user_id, companies = query.user_id, query.companies
        logging.info(f"started with user {user_id} with {len(companies)} companies")

        requests = []
        for company in companies:
            tracked_jobs = company.tracked_jobs
            urls_to_remove = [job.job_url for job in tracked_jobs]
            if not urls_to_remove:
                continue
            
            requests.append(
                UpdateOne(
                    {"user_id": user_id, "company_name": company.company_name},
                    {"$pull": {"jobs": {"job_url": {"$in": urls_to_remove}}}}
                )
            )

        if not requests:
            return False

        try:
            result = await self.job_applications.bulk_write(requests)
            return result.modified_count > 0
        except Exception as e:
            logging.exception(f"Failed to delete jobs for user {user_id}: {e}")
            return False
  
    
    # ==================== QUERY HELPERS ====================
    
 
    async def _find_existing_application(self, user_id: str, company_name: str) -> Optional[CompanyJobsDocument]:
        try:
            # Check if job already exists
            existing = await self.job_applications.find_one({
                "user_id": user_id,
                "company_name": company_name
            })
            if not existing:
                return None
            company_entity = EntitiesMapper.to_company_document(existing)
            return company_entity
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            raise
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logging.exception(f"Unexpected error in add_job: {e}")
            raise 

    def _has_job_changes(self, new_tracked_job: TrackedJob, existing_entity_job: JobEntity) -> bool:
        """Compare existing job with new job data (excluding job identifiers and update_time)"""
        new_job = asdict(new_tracked_job)
        existing_job = asdict(existing_entity_job)
        for key, value in new_job.items():
            if key not in self.excluded_fields:
                if existing_job.get(key) != value:
                    return True
        return False
