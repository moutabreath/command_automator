import logging
from typing import Optional

from ..repository import JobTrackingReadPersistMongo
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
            response: PersistenceResponse[Company] = await self.application_persist.get_tracked_jobs(
                GetTrackedJobsQuery(user_id=user_id, company_name=company_name)
            )
            if response.code == PersistenceErrorCode.SUCCESS:
                if not response.data:
                    logging.warning(f"No tracked jobs found for company {company_name}")
                    return CompanyResponse(company=None, code=JobTrackingResponseCode.NO_TRACKED_JOBS)
                return CompanyResponse(company=response.data, code=JobTrackingResponseCode.OK)
            else:
                logging.error(f"Failed to get tracked jobs for company {company_name}")
                return CompanyResponse(company=None, code=JobTrackingResponseCode.ERROR, error_message=f"Failed to get tracked jobs for company {company_name}")
        except Exception as e:
            logging.error(f"Failed to get tracked jobs for company {company_name}: {e}")
            return CompanyResponse(company=None, code=JobTrackingResponseCode.ERROR)
      
    async def get_all_user_applications(self, user_id: str) -> UserApplicationResponse:
        """
        Get all job applications for a specific user.
        """
        response = await self.application_persist.get_all_applications(user_id)
        if response.code == PersistenceErrorCode.SUCCESS:
            return UserApplicationResponse(
                code=UserApplicationResponseCode.SUCCESS,
                company_jobs=response.data
            )
        else:
            return UserApplicationResponse(
                code=UserApplicationResponseCode.ERROR, 
                user_applications=[], 
                error_message=response.error_message or "Unknown error occurred"
            )

   

    
    async def _get_job_title_keyword(self):
        job_title_keywords = await file_utils.read_json_file(file_utils.JOB_TITLES_CONFIG_FILE)        
        if job_title_keywords == {}:            
            return  ["senior", "junior", "manager", "engineer", "analyst", "administrator", "designer", "writer"]
        titles = []
        titles.extend(job_title_keywords.get("software_engineer", []))
        titles.extend(job_title_keywords.get("general", []))

        return titles