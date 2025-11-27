from enum import Enum
from typing import Optional
from llm.mcp_servers.job_search.jobs_tracking.mongo_perist.mongo_company_persist import MongoCompanyPersist
from user.repository.user_mongo_persist import UserMongoPersist

from typing import Optional, Dict

class JobApplicationState(Enum):
    CONNECTION_REQUESTED = 1,
    MESSAGE_SENT = 2,
    EMAIL_SENT = 3,
    APPLIED = 4,
    UKNOWN = 5

class JobTrackerService:
    def __init__(self):        
        self.application_persist = MongoCompanyPersist()
       
    def add_job_to_company(self, user_id: str, company_name: str, 
                           job_url: str, job_title: str, state: str, 
                           contact: Optional[str] = None) -> Dict[str, bool]:
        """Add or update a job in a company application
        
        Jobs are matched by job_url. If a job with the same URL exists, it's updated.
        If the company doesn't exist, it's created automatically.
        
        Returns:
            {"created": bool, "updated": bool}
        """
        company_name = company_name.lower()
        job_url = job_url.lower()
        job_title = job_title.lower()
        contact = contact.lower() if contact else None
        
        state_upper = state.upper()
        if state_upper in JobApplicationState.__members__:
            job_state = JobApplicationState[state_upper]
        else:
            job_state = JobApplicationState.UKNOWN

        return self.application_persist.add_job(
            user_id=user_id,
            company_name=company_name,
            job_url=job_url,
            job_title=job_title,
            state=job_state,
            contact=contact
        )