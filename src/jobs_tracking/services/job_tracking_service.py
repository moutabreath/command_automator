import datetime
from enum import Enum
import logging
from time import timezone
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from jobs_tracking.models import JobApplicationState
from jobs_tracking.repository.company_mongo_persist import CompanyMongoPersist
from repository.abstract_mongo_persist import PersistenceResponse, PersistenceErrorCode
from services.abstract_persistence_service import AbstractPersistenceService
from utils.utils import AsyncRunner

class JobTrackingResponseCode(Enum):
    OK = 1
    ERROR = 2
    
class JobTrackingResponse:
    def __init__(self, job: Dict[str, Any], code: JobTrackingResponseCode):
        self.job = job
        self.code = code

class JobTrackingListResponse:
    def __init__(self, jobs: List[Dict], code: JobTrackingResponseCode):
        self.jobs = jobs
        self.code = code


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

    
    def add_or_update_position(self, user_id: str, company_name: str, 
                            job_url: str, job_title: str, job_state: JobApplicationState, 
                            contact_name: Optional[str] = None,
                            contact_linkedin: Optional[str] = None,
                            contact_email: Optional[str] = None) -> JobTrackingResponse:
        
        result = AsyncRunner.run_async(
            self.add_or_update_position_async(
            user_id=user_id,
            company_name=company_name,
            job_url=job_url,
            job_title=job_title,
            job_state=job_state,
            contact_name=contact_name,
            contact_linkedin=contact_linkedin,
            contact_email=contact_email
            )
        )
        return result
    
       
    async def add_or_update_position_async(self, user_id: str, company_name: str, 
                           job_url: str, job_title: str, job_state: JobApplicationState, 
                           contact_name: Optional[str] = None, contact_linkedin: Optional[str] = None,
                           contact_email: Optional[str] = None) -> JobTrackingListResponse:
        """Add or update a job in a company application
        
        Jobs are matched by job_url. If a job with the same URL exists, it's updated.
        If the company doesn't exist, it's created automatically.
        
        Returns:
            {"created": bool, "updated": bool}
        """
              
        if not user_id or not company_name or not job_url or not job_title:
            logging.error("Missing required parameters for add_or_update_position")
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        
        company_name = company_name.lower()
        try:
            job_url = urlparse(job_url).geturl()
        except (ValueError, AttributeError) as e:
            logging.error(f"Invalid job_url format: {e}")
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        
        mongoResult: PersistenceResponse[Dict[str, bool]] = await self.application_persist.add_or_update_position(
            user_id=user_id,
            company_name=company_name,
            job_url=job_url,
            update_time=datetime.now(timezone.utc),
            job_title=job_title,
            job_state=job_state,
            contact_name=contact_name,
            contact_linkedin=contact_linkedin,
            contact_email=contact_email
        )
        if mongoResult.code == PersistenceErrorCode.SUCCESS:
            return JobTrackingResponse(job = self._serialize_dict(mongoResult.data), code = JobTrackingResponseCode.OK)
        logging.error(f"Failed to add job for company {company_name}: {mongoResult.code}")
        return JobTrackingResponse(job = self._serialize_dict(mongoResult.data), code = JobTrackingResponseCode.ERROR)
    
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
            positions = await self.application_persist.get_positions(user_id, company_name)
            if positions:
                serialized_jobs = [self._serialize_dict(job) for job in positions.data] if positions.data else []
                return JobTrackingListResponse(jobs=serialized_jobs, code=JobTrackingResponseCode.OK)
            else:
                logging.error(f"No positions found for company {company_name}")
                return JobTrackingListResponse(jobs={}, code=JobTrackingResponseCode.ERROR)
        except Exception as e:
            logging.error(f"Failed to get positions for company {company_name}: {e}")
            return JobTrackingListResponse(jobs={}, code=JobTrackingResponseCode.ERROR)            

    def _serialize_dict(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not data:
            return {}
        new_data = data.copy()
        for key, value in new_data.items():
            if isinstance(value, (datetime.datetime, datetime.date)):
                new_data[key] = value.isoformat()
            elif hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
                new_data[key] = str(value)
            elif key == 'job_state' and isinstance(value, int):
                try:
                    new_data[key] = JobApplicationState(value).name
                except ValueError:
                    logging.warning(f"Invalid job_state value '{value}' found in data, defaulting to UNKNOWN.")
                    new_data[key] = JobApplicationState.UNKNOWN.name
        return new_data