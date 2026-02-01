import logging
from typing import Optional
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

import pymongo.errors as mongo_errors
from pymongo import UpdateOne

from .models.entities import CompanyJobsDocument, JobEntity
from .mapper import EntitiesMapper
from .models.projections import JobWithCompanyContext
from ..services.domain.models import TrackedJob, Company
from ...repository.abstract_owner_mongo_persist import AbstractOwnerMongoPersist
from ...repository.models import PersistenceResponse, PersistenceErrorCode
from .models.queries import (
    GetTrackedJobsQuery,
    TrackNewJobDbQuery,
    TrackExistingJobDbQuery,
    DeleteApplicationDbQuery,
    DeleteJobDbQuery,
    DeleteTrackedJobsDbQuery,
    GetAllApplicationsQuery,
    GetJobsByStateQuery,
    GetRecentJobsQuery
)


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
       
    async def get_tracked_jobs(self, query: GetTrackedJobsQuery) -> PersistenceResponse[list[JobWithCompanyContext]]:        
        """Get all application by user and company"""
        user_id, company_name = query.user_id, query.company_name
        try:
            result_dict = await self.job_applications.find_one({
                "user_id": user_id, "company_name": company_name
            })

            entity = EntitiesMapper.to_company_document(result_dict)
            tracked_jobs_context = [
                JobWithCompanyContext(
                    company_id=entity.company_id,
                    company_name=entity.company_name,
                    # Entity handles the inner Job data
                    job=EntitiesMapper.to_domain(job_entity)
                ) for job_entity in entity.jobs
            ]
        
            return PersistenceResponse(
                id=entity.company_id, 
                data=tracked_jobs_context, 
                code=PersistenceErrorCode.SUCCESS
            )
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
        existing_job = next((existing_job for existing_job in existing_company_application.jobs 
                    if existing_job.job_url == new_tracked_job.job_url and 
                    self._has_job_changes(new_tracked_job, existing_job)), None)
        if existing_job:
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
    
    async def get_all_applications(self, query: GetAllApplicationsQuery) -> PersistenceResponse[list[Company]]:
        """Get all applications for a user"""
        user_id = query.user_id
        try:
            cursor = self.job_applications.find({"user_id": user_id})
            results = await cursor.to_list(length=None)
            
            domain_companies = []
            for doc in results:
                jobs = [TrackedJob.from_dict(j) for j in doc.get("jobs", [])]
                domain_companies.append(Company(company_id=doc.get("company_id"), company_name=doc.get("company_name"), tracked_jobs=jobs))
                
            return PersistenceResponse(data=domain_companies, code=PersistenceErrorCode.SUCCESS)
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
    
    # ==================== QUERY HELPERS ====================
    
    
    async def get_jobs_by_state(self, query: GetJobsByStateQuery) -> PersistenceResponse[list[JobWithCompanyContext]]:
        """Get all jobs with a specific state across all companies"""
        user_id, state = query.user_id, query.state
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$jobs"},
            {"$match": {"jobs.job_state": state}},
            {"$project": {
                "company_id": 1,
                "company_name": 1,
                "job": "$jobs"
            }}
        ]
        # Assuming result.data contains the list of dicts from MongoDB
        result = await self._execute_job_aggregation(pipeline)

        if not result:
            return PersistenceResponse(error_message="couldn't find anything", code=PersistenceErrorCode.OPERATION_ERROR)

        # Map the list of dicts to your Projection objects
        projected_jobs = [
            JobWithCompanyContext.from_mongo(item)
            for item in result.data
        ]

        return PersistenceResponse(data=projected_jobs, code=PersistenceErrorCode.SUCCESS)

   
    async def get_recent_jobs(self, query: GetRecentJobsQuery) -> PersistenceResponse[list[JobWithCompanyContext]]:
        """Get most recently updated jobs"""
        user_id, limit = query.user_id, query.limit
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$jobs"},
            {"$sort": {"jobs.update_time": -1}},
            {"$limit": limit},
            {"$project": {
                "company_id": 1,
                "company_name": 1,
                "job": "$jobs"
            }}
        ]
        result = await self._execute_job_aggregation(pipeline)
        if result.code == PersistenceErrorCode.SUCCESS and result.data:
            projected_jobs = [JobWithCompanyContext.from_mongo(item) for item in result.data]
            return PersistenceResponse(data=projected_jobs, code=PersistenceErrorCode.SUCCESS)
            
        return PersistenceResponse(data=[], code=result.code, error_message=result.error_message)

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
