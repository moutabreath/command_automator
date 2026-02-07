import logging
from urllib.parse import urlparse
from typing import Optional

from .job_tracking_attributes_parser import extract_job_title_and_company

from ..repository.job_tracking_writer_persist_mongo import JobTrackingWriterPersistMongo
from ..repository.models.projections import JobWithCompanyContext
from .domain.models import TrackedJob
from .domain.results import JobTrackingResponse, JobTrackingResponseCode
from .domain.commands import (
    TrackNewJobCommand,
    TrackExistingJobCommand,
    DeleteTrackedJobsCommand,
    ExtractJobInfoCommand
)
from ..repository.models.queries import (
    TrackNewJobDbQuery,
    TrackExistingJobDbQuery,
    DeleteTrackedJobsDbQuery
)
from ...repository.models import PersistenceErrorCode, PersistenceResponse


class JobTrackingService:

    def __init__(self, company_writer_persist_mongo: JobTrackingWriterPersistMongo):        
        self.application_persist = company_writer_persist_mongo

       
    async def track_new_job(self, track_new_job_command: TrackNewJobCommand) -> JobTrackingResponse:
        """Add or update a job in a company application
        
        Jobs are matched by job_url. If a job with the same URL exists, it's updated.
        If the company doesn't exist, it's created automatically.
        
        """
        user_id, company_name, tracked_job = track_new_job_command.user_id, track_new_job_command.company_name, track_new_job_command.tracked_job

        logging.info(f"started with user: {user_id} company: \"{company_name}\" job: \"{tracked_job.job_title}\"")
              
        validation_error = self._validate_job_parameters(user_id, company_name, tracked_job)
        if validation_error:
            return validation_error
        
        company_name = company_name.lower()
        try:
            job_url = urlparse(tracked_job.job_url).geturl()
        except (ValueError, AttributeError) as e:
            logging.error(f"Invalid job_url format: {e}")
            return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)
        
        tracked_job.job_url = job_url
                
        persistence_response: PersistenceResponse[JobWithCompanyContext] = await self.application_persist.track_new_job(
            TrackNewJobDbQuery(
                user_id=user_id,
                company_name=company_name,
                tracked_job=tracked_job
            )
        )
        return self._create_job_tracking_response(persistence_response, company_name, tracked_job)
    

    async def track_existing_job(self, command: TrackExistingJobCommand) -> JobTrackingResponse:
        """Add or update a job in a company application
        
        Jobs are matched by job_url. If a job with the same URL exists, it's updated.
        If the company doesn't exist, it's created automatically.
        
        """
        user_id, company_id, tracked_job = command.user_id, command.company_id, command.tracked_job

        logging.info(f"started with user: {user_id} company: \"{company_id}\" job: \"{tracked_job.job_title}\"")

        validation_error = self._validate_job_parameters(user_id, company_id, tracked_job)
        if validation_error:
            return validation_error
        
        try:
            job_url = urlparse(tracked_job.job_url).geturl()
        except (ValueError, AttributeError) as e:
            logging.error(f"Invalid job_url format: {e}")
            return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)
        
        tracked_job.job_url = job_url
                
        persistence_response: PersistenceResponse[TrackedJob] = await self.application_persist.track_existing_job(
            TrackExistingJobDbQuery(
                user_id=user_id,
                company_id=company_id,
                tracked_job=tracked_job
            )
        )
        return self._create_job_tracking_response(persistence_response, company_id, tracked_job)
    

    
    async def delete_tracked_jobs(self, delete_tracked_jobs_command: DeleteTrackedJobsCommand):
        user_id, companies_jobs = delete_tracked_jobs_command.user_id, delete_tracked_jobs_command.companies_jobs

        logging.info(f"started with user: {user_id} with {len(companies_jobs)} companies")
        if not user_id or not companies_jobs:
            logging.error("Missing required parameters for delete_tracked_jobs")
            return False
        return await self.application_persist.delete_tracked_jobs(
            DeleteTrackedJobsDbQuery(user_id=user_id, companies=companies_jobs)
        )

    def _create_job_tracking_response(self, persistence_response: PersistenceResponse, company_id: str, tracked_job: TrackedJob) -> JobTrackingResponse:
        if persistence_response.code == PersistenceErrorCode.SUCCESS:
            data = persistence_response.data
            if isinstance(data, JobWithCompanyContext):
                return JobTrackingResponse(job=data.job, company_id=data.company_id, code=JobTrackingResponseCode.OK)
            elif isinstance(data, TrackedJob):
                return JobTrackingResponse(job=data, company_id=company_id, code=JobTrackingResponseCode.OK)
            
        logging.error(f"Failed to add job for company {company_id}: {persistence_response.code}")
        return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)

    def _validate_job_parameters(self, user_id: str, company_name: str, tracked_job: TrackedJob) -> Optional[JobTrackingResponse]:
        if not user_id or not company_name or not tracked_job.job_url or not tracked_job.job_title:
            logging.error("Missing required parameters for job operation")
            return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)
        
        if tracked_job.contact_name and not all(c.isalpha() or c in (' ', '-', "'") for c in tracked_job.contact_name):
            logging.error("Contact name must contain only letters")
            return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)
        return None