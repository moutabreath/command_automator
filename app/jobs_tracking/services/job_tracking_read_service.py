import logging
from typing import Optional

from ..repository import JobTrackingReadPersistMongo
from ..repository.models.projections import JobWithCompanyContext
from .domain.models import Company, TrackedJob
from .domain.results import CompanyResponse, JobTrackingResponse, JobTrackingResponseCode, UserApplicationResponse, UserApplicationResponseCode
from .domain.commands import (
    GetTrackedJobsCommand,
)
from ..repository.models.queries import (
    GetTrackedJobsQuery
)
from ...repository.models import PersistenceErrorCode, PersistenceResponse
from ...utils import file_utils


class JobTrackingReadService:

    def __init__(self, application_persist: JobTrackingReadPersistMongo):        
        self.application_persist = application_persist

      
    async def get_tracked_jobs(self, get_tracked_jobs_command: GetTrackedJobsCommand) -> CompanyResponse:
        """Get all positions for a user at a specific company"""

        user_id, company_name = get_tracked_jobs_command.user_id, get_tracked_jobs_command.company_name

        logging.info(f"started with user: {user_id} company: \"{company_name}\"")
        if not user_id or not company_name:
            logging.error("Missing required parameters for get_positions")
            return CompanyResponse(code=JobTrackingResponseCode.ERROR)
            
        company_name = company_name.lower()
        
        try:
            response: PersistenceResponse[list[JobWithCompanyContext]] = await self.application_persist.get_tracked_jobs(
                GetTrackedJobsQuery(user_id=user_id, company_name=company_name)
            )
            if response.code == PersistenceErrorCode.SUCCESS:
                if not response.data:
                    logging.warning(f"No tracked jobs found for company {company_name}")
                    return CompanyResponse(company=None, code=JobTrackingResponseCode.NO_TRACKED_JOBS)
                tracked_jobs = [context.job for context in response.data]
                company = Company(company_id=response.id, company_name=company_name, tracked_jobs=tracked_jobs)
                return CompanyResponse(company=company, code=JobTrackingResponseCode.OK)
            else:
                logging.warning(f"No tracked jobs found for company {company_name}")
                return CompanyResponse(company=None, code=JobTrackingResponseCode.NO_TRACKED_JOBS, error_message="No tracked jobs for this company")
        except Exception as e:
            logging.error(f"Failed to get tracked jobs for company {company_name}: {e}")
            return CompanyResponse(company=None, code=JobTrackingResponseCode.ERROR)
      
    async def get_all_user_applications(self, user_id: str) -> UserApplicationResponse:
        """
        Get all job applications for a specific user.
        """
        response = await self.application_persist.get_all_applications(user_id)
        if response.code == PersistenceErrorCode.SUCCESS:
            user_applications = [
                UserApplicationResponse(
                    company_name=app["company_name"], 
                    tracked_job=app["jobs"]
                ) for app in response.data
            ]
            return UserApplicationResponse(
                code=UserApplicationResponseCode.SUCCESS,
                user_applications=user_applications
            )
        else:
            return UserApplicationResponse(
                code=UserApplicationResponseCode.ERROR, 
                user_applications=[], 
                error_message=response.error_message or "Unknown error occurred"
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

    
    async def _get_job_title_keyword(self):
        job_title_keywords = await file_utils.read_json_file(file_utils.JOB_TITLES_CONFIG_FILE)        
        if job_title_keywords == {}:            
            return  ["senior", "junior", "manager", "engineer", "analyst", "administrator", "designer", "writer"]
        titles = []
        titles.extend(job_title_keywords.get("software_engineer", []))
        titles.extend(job_title_keywords.get("general", []))

        return titles