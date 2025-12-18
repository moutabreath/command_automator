from enum import Enum
import logging
from typing import Optional, Dict, Any
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
        
        if not user_id or not company_name or not job_url or not job_title:
            logging.error("Missing required parameters for add_or_update_position")
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        
        company_name = company_name.lower()
        try:
            job_url = urlparse(job_url).geturl()
        except (ValueError, AttributeError) as e:
            logging.error(f"Invalid job_url format: {e}")
            return JobTrackingResponse(job={}, code=JobTrackingResponseCode.ERROR)
        
        result = AsyncRunner.run_async(
            self._add_or_update_position_async(
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
    
       
    async def _add_or_update_position_async(self, user_id: str, company_name: str, 
                           job_url: str, job_title: str, job_state: JobApplicationState, 
                           contact_name: Optional[str] = None, contact_linkedin: Optional[str] = None,
                           contact_email: Optional[str] = None) -> JobTrackingResponse:
        """Add or update a job in a company application
        
        Jobs are matched by job_url. If a job with the same URL exists, it's updated.
        If the company doesn't exist, it's created automatically.
        
        Returns:
            {"created": bool, "updated": bool}
        """
      
        mongoResult: PersistenceResponse[Dict[str, bool]] = await self.application_persist.add_or_update_position(
            user_id=user_id,
            company_name=company_name,
            job_url=job_url,
            job_title=job_title,
            job_state=job_state,
            contact_name=contact_name,
            contact_linkedin=contact_linkedin,
            contact_email=contact_email
        )
        if mongoResult.code == PersistenceErrorCode.SUCCESS:
            return JobTrackingResponse(job = mongoResult.data, code = JobTrackingResponseCode.OK)
        logging.error(f"Failed to add job for company {company_name}: {mongoResult.code}")        
        return JobTrackingResponse(job = mongoResult.data, code = JobTrackingResponseCode.ERROR)
    
     