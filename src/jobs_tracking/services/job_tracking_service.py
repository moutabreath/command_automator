from enum import Enum
from typing import Optional
from urllib.parse import urlparse
from jobs_tracking.models import JobApplicationState
from jobs_tracking.repository.company_mongo_persist import CompanyMongoPersist
from repository.abstract_mongo_persist import PersistenceResponse, PersistenceErrorCode

from typing import Optional, Dict

class JobTrackingService:

    def __init__(self):        
        self.application_persist = CompanyMongoPersist()
        self.application_persist.initialize_connection()
       
    def add_job_to_company(self, user_id: str, company_name: str, 
                           job_url: str, job_title: str, state: JobApplicationState, 
                           contact: Optional[str] = None) -> Dict[str, bool]:
        """Add or update a job in a company application
        
        Jobs are matched by job_url. If a job with the same URL exists, it's updated.
        If the company doesn't exist, it's created automatically.
        
        Returns:
            {"created": bool, "updated": bool}
        """
        company_name = company_name.lower()
        job_url = urlparse(job_url).geturl()
        job_title = job_title

        mongoResult:  PersistenceResponse[Dict[str, bool]] = self.application_persist.add_job(
            user_id=user_id,
            company_name=company_name,
            job_url=job_url,
            job_title=job_title,
            state=state,
            contact=contact
        )
        if mongoResult.code == PersistenceErrorCode.SUCCESS:
            return mongoResult.data
        else:
            return {"created": False, "updated": False}