from dataclasses import asdict
from datetime import datetime, timezone
import logging
from urllib.parse import urlparse

from jobs_tracking.job_tracking_linkedin_parser import extract_linkedin_job
from jobs_tracking.repository.company_mongo_persist import CompanyMongoPersist
from jobs_tracking.services.models import Company, TrackedJob, CompanyResponse, JobTrackingResponse, JobTrackingResponseCode
from jobs_tracking.services.models import JobApplicationState

from repository.models import PersistenceErrorCode, PersistenceResponse
from services.abstract_persistence_service import AbstractPersistenceService

from utils import file_utils
from utils.utils import AsyncRunner


class JobTrackingService(AbstractPersistenceService):

    def __init__(self, company_mongo_persist: CompanyMongoPersist):        
        self.application_persist = company_mongo_persist
        super().__init__(self.application_persist)

    @classmethod
    async def create(cls, mongo_connection_string, db_name):
        # 1. Create the initialized persistence layer
        # This will fail if DB is down or logic is wrong, preventing "Zombie" services
        company_persist = await CompanyMongoPersist.create(mongo_connection_string, db_name)
        return cls(company_persist)

    def track_job(self, user_id: str, company_name: str, tracked_job: TrackedJob) -> JobTrackingResponse:
        
        logging.info(f"started with user {user_id} company {company_name} job {tracked_job.job_title}")
        result = AsyncRunner.run_async(
            self.track_job_async(
            user_id=user_id,
            company_name=company_name,
            tracked_job=tracked_job
            )
        )
        return result
    
       
    async def track_job_async(self, user_id: str, company_name: str, tracked_job: TrackedJob) -> JobTrackingResponse:
        """Add or update a job in a company application
        
        Jobs are matched by job_url. If a job with the same URL exists, it's updated.
        If the company doesn't exist, it's created automatically.
        
        """
        logging.info(f"started with user {user_id} company {company_name} job {tracked_job.job_title}")
              
        if not user_id or not company_name or not tracked_job.job_url or not tracked_job.job_title:
            logging.error("Missing required parameters for add_or_update_position")
            return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)
        
        if tracked_job.contact_name and not all(c.isalpha() or c in (' ', '-', "'") for c in tracked_job.contact_name):
            logging.error("Contact name must contain only letters")
            return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)
        company_name = company_name.lower()
        try:
            job_url = urlparse(tracked_job.job_url).geturl()
        except (ValueError, AttributeError) as e:
            logging.error(f"Invalid job_url format: {e}")
            return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)
        
        tracked_job.job_url = job_url
        
        # Convert domain object to dict for persistence layer
        tracked_job_dict = asdict(tracked_job)
        
        mongo_result: PersistenceResponse[dict] = await self.application_persist.track_job(
            user_id=user_id,
            company_name=company_name,
            tracked_job_dict=tracked_job_dict,
            update_time=datetime.now(timezone.utc),
        )
        if mongo_result.code == PersistenceErrorCode.SUCCESS:
            # Convert dict back to domain object
            result_job = self._dict_to_tracked_job(mongo_result.data)
            return JobTrackingResponse(job=result_job, company_id=mongo_result.id, code=JobTrackingResponseCode.OK)
        logging.error(f"Failed to add job for company {company_name}: {mongo_result.code}")
        return JobTrackingResponse(job=tracked_job, code=JobTrackingResponseCode.ERROR)
    
    def get_tracked_jobs(self, user_id: str, company_name: str) -> CompanyResponse:

        logging.info(f"started with user {user_id} company {company_name}")
        result = AsyncRunner.run_async(
            self.get_tracked_jobs_async(
            user_id=user_id,
            company_name=company_name
            )
        )
        return result
    
    async def get_tracked_jobs_async(self, user_id: str, company_name: str) -> CompanyResponse:
        """Get all positions for a user at a specific company"""

        logging.info(f"started with user {user_id} company {company_name}")
        if not user_id or not company_name:
            logging.error("Missing required parameters for get_positions")
            return CompanyResponse(code=JobTrackingResponseCode.ERROR)
            
        company_name = company_name.lower()
        
        try:
            response: PersistenceResponse[list[dict]] = await self.application_persist.get_tracked_jobs(user_id, company_name)
            if response.code == PersistenceErrorCode.SUCCESS:
                if not response.data:
                    logging.warning(f"No tracked jobs found for company {company_name}")
                    return CompanyResponse(company_id=response.id, code=JobTrackingResponseCode.OK)
                # Convert dicts back to domain objects
                tracked_jobs = [self._dict_to_tracked_job(job_dict) for job_dict in response.data]
                company = Company(company_id=response.id, company_name=company_name, tracked_jobs=tracked_jobs)
                return CompanyResponse(company=company, code=JobTrackingResponseCode.OK)
            else:
                logging.warning(f"No tracked jobs found for company {company_name}")
                return CompanyResponse(company=None, code=JobTrackingResponseCode.NO_TRACKED_JOBS, error_message="No tracked jobs for this company")
        except Exception as e:
            logging.error(f"Failed to get tracked jobs for company {company_name}: {e}")
            return CompanyResponse(company=None, code=JobTrackingResponseCode.ERROR)

    def extract_job_title_and_company(self, url:str):
        logging.info(f"start with {url}")
        return extract_linkedin_job(url)       

    def delete_tracked_jobs(self, userid:str, companies_jobs: list[Company]):
        logging.info(f"started with user {user_id} with {len(companies_jobs)}")
        result = AsyncRunner.run_async(
            self.delete_tracked_jobs_async(
            user_id=userid,
            companies_jobs=companies_jobs
            )
        )
        return result
    
    async def delete_tracked_jobs_async(self, user_id: str, companies_jobs: list[Company]):
        logging.info(f"started with user {user_id} with {len(companies_jobs)}")
        if not user_id or not companies_jobs:
            logging.error("Missing required parameters for delete_tracked_jobs")
            return False
        # Convert domain objects to dicts
        companies_dicts = [asdict(company) for company in companies_jobs]
        return await self.application_persist.delete_tracked_jobs(user_id, companies_dicts)

    def _dict_to_tracked_job(self, job_dict: dict) -> TrackedJob:
        """Convert dictionary to TrackedJob domain object"""        
        
        job_state = job_dict.get("job_state")
        if isinstance(job_state, int):
            job_state = JobApplicationState.from_value(job_state)
        elif isinstance(job_state, str):
            job_state = JobApplicationState.from_string(job_state)
        
        return TrackedJob(
            job_id=job_dict.get("job_id", ""),
            job_url=job_dict.get("job_url", ""),
            job_title=job_dict.get("job_title", ""),
            job_state=job_state,
            contact_name=job_dict.get("contact_name"),
            contact_linkedin=job_dict.get("contact_linkedin"),
            contact_email=job_dict.get("contact_email"),
            update_time=job_dict.get("update_time")
        )

    
    async def _get_job_title_keyword(self):
        job_title_keywords = await file_utils.read_json_file(file_utils.JOB_TITLES_CONFIG_FILE)        
        if job_title_keywords == {}:            
            return  ["senior", "junior", "manager", "engineer", "analyst", "administrator", "designer", "writer"]
        titles = []
        titles.extend(job_title_keywords.get("software_engineer", []))
        titles.extend(job_title_keywords.get("general", []))

        return titles