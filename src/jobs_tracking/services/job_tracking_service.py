from dataclasses import asdict
from datetime import datetime, timezone, date
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from jobs_tracking.services.models import JobApplicationState
from jobs_tracking.repository.company_mongo_persist import CompanyMongoPersist
from jobs_tracking.services.models import TrackedJob, JobTrackingListResponse, JobTrackingResponse, JobTrackingResponseCode
from repository.abstract_mongo_persist import PersistenceResponse, PersistenceErrorCode
from services.abstract_persistence_service import AbstractPersistenceService
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
        
        if tracked_job.contact_name and not tracked_job.contact_name.replace(' ', '').isalpha():
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
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        
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

    
    def track_position_from_text(self, user_id: str, text:str) -> JobTrackingResponse:
        result = AsyncRunner.run_async(
            self.track_positions_from_text_async(
            user_id=user_id,
            text=text
            )
        )
        return result

    async def track_positions_from_text_async(self, user_id: str, text: str) -> JobTrackingResponse:
        """Parse text to extract job information and track positions"""
        import re
        
        if not user_id or not text:
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        
        # Split text by spaces and newlines
        parts = re.split(r'\s+', text.strip())
        
        job_url = None
        contact_linkedin = None
        contact_name = None
        job_state = JobApplicationState.UNKNOWN
        job_title_parts = []
        
        for part in parts:
            if self._is_url(part):
                if 'linkedin.com' in part.lower():
                    if '/in/' in part:
                        contact_linkedin = part
                        # Extract contact name from LinkedIn URL
                        extracted_name = part.split('/in/')[-1].split('/')[0].replace('-', ' ').title()
                        if extracted_name.replace(' ', '').isalpha():
                            contact_name = extracted_name
                else:
                    job_url = part
            elif self._is_job_state(part):
                try:
                    job_state = JobApplicationState[part.upper()]
                except (KeyError, ValueError):
                    job_state = JobApplicationState.UNKNOWN
            else:
                job_title_parts.append(part)
        
        if not job_url:
            return JobTrackingResponse(job={"error": "No job URL found"}, code=JobTrackingResponseCode.ERROR)
        
        job_title = ' '.join(job_title_parts) if job_title_parts else "Unknown Position"
        company_name = self._extract_company_from_url(job_url)
        
        job_params = TrackedJob(
            job_url=job_url,
            job_title=job_title,
            job_state=job_state,
            contact_name=contact_name,
            contact_linkedin=contact_linkedin
        )

        return await self.add_or_update_position_async(
            user_id=user_id,
            company_name=company_name,
            tracked_job=job_params
        )
    
    def _is_url(self, text: str) -> bool:
        return text.startswith(('http://', 'https://', 'www.'))
    
    def _is_job_state(self, text: str) -> bool:
        return text.upper() in [state.name for state in JobApplicationState]
    
    def _extract_company_from_url(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. and common TLDs to get company name
            company = domain.replace('www.', '').split('.')[0]
            return company.title()
        except:
            return "Unknown Company"