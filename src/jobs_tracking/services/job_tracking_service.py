from datetime import datetime, timezone
import logging
from urllib.parse import urlparse
from jobs_tracking.job_tracking_linkedin_parser import extract_linkedin_job
from jobs_tracking.repository.company_mongo_persist import CompanyMongoPersist
from jobs_tracking.services.models import TrackedJob, JobTrackingListResponse, JobTrackingResponse, JobTrackingResponseCode, JobAndCompanyTrackingResponse
from repository.abstract_mongo_persist import PersistenceResponse, PersistenceErrorCode
from services.abstract_persistence_service import AbstractPersistenceService
from utils import file_utils
from utils.utils import AsyncRunner
from typing import List

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

    def add_or_update_position(self, user_id: str, company_name: str, trackedJob: TrackedJob) -> JobTrackingResponse:
        
        result = AsyncRunner.run_async(
            self.add_or_update_position_async(
            user_id=user_id,
            company_name=company_name,
            tracked_job=trackedJob
            )
        )
        return result
    
       
    async def add_or_update_position_async(self, user_id: str, company_name: str, tracked_job: TrackedJob) -> JobTrackingResponse:
        """Add or update a job in a company application
        
        Jobs are matched by job_url. If a job with the same URL exists, it's updated.
        If the company doesn't exist, it's created automatically.
        
        Returns:
            {"created": bool, "updated": bool}
        """
              
        if not user_id or not company_name or not tracked_job.job_url or not tracked_job.job_title:
            logging.error("Missing required parameters for add_or_update_position")
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        
        if tracked_job.contact_name and not all(c.isalpha() or c in (' ', '-', "'") for c in tracked_job.contact_name):
            logging.error("Contact name must contain only letters")
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        company_name = company_name.lower()
        try:
            job_url = urlparse(tracked_job.job_url).geturl()
        except (ValueError, AttributeError) as e:
            logging.error(f"Invalid job_url format: {e}")
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        
        tracked_job.job_url = job_url
        
        mongoResult: PersistenceResponse[TrackedJob] = await self.application_persist.add_or_update_position(
            user_id=user_id,
            company_name=company_name,
            tracked_job=tracked_job,
            update_time=datetime.now(timezone.utc),
        )
        if mongoResult.code == PersistenceErrorCode.SUCCESS:
            return JobTrackingResponse(job = mongoResult.data, code = JobTrackingResponseCode.OK)
        logging.error(f"Failed to add job for company {company_name}: {mongoResult.code}")
        return JobTrackingResponse(job = mongoResult.data , code = JobTrackingResponseCode.ERROR)
    
    def get_positions(self, user_id: str, company_name: str) -> JobTrackingListResponse:
        result = AsyncRunner.run_async(
            self.get_positions_async(
            user_id=user_id,
            company_name=company_name
            )
        )
        return result
    
    async def get_positions_async(self, user_id: str, company_name: str) -> JobTrackingListResponse:
        """Get all positions for a user at a specific company"""
        if not user_id or not company_name:
            logging.error("Missing required parameters for get_positions")
            return JobTrackingListResponse(jobs=[], code=JobTrackingResponseCode.ERROR)
            
        company_name = company_name.lower()
        
        try:
            response: PersistenceResponse[List[TrackedJob]] = await self.application_persist.get_tracked_jobs(user_id, company_name)
            if response.code == PersistenceErrorCode.SUCCESS:
                if not response.data:
                    logging.warning(f"No positions found for company {company_name}")
                    return JobTrackingListResponse(jobs={}, code=JobTrackingResponseCode.OK)
                return JobTrackingListResponse(jobs=response.data, code=JobTrackingResponseCode.OK)
            else:
                logging.warning(f"No positions found for company {company_name}")
                return JobTrackingListResponse(jobs={}, code=JobTrackingResponseCode.ERROR)
        except Exception as e:
            logging.error(f"Failed to get positions for company {company_name}: {e}")
            return JobTrackingListResponse(jobs={}, code=JobTrackingResponseCode.ERROR)

    def extract_job_title_and_company(self, url:str):
        return extract_linkedin_job(url)        
    
    async def _get_job_title_keyword(self):
        job_title_keywords = await file_utils.read_json_file(file_utils.JOB_TITLES_CONFIG_FILE)        
        if job_title_keywords == {}:            
            return  ["senior", "junior", "manager", "engineer", "analyst", "administrator", "designer", "writer"]
        titles = []
        titles.extend(job_title_keywords.get("software_engineer", []))
        titles.extend(job_title_keywords.get("general", []))

        return titles