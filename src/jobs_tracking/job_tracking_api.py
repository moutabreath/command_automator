from enum import Enum
import logging
from typing import Dict, List, Optional

from jobs_tracking.models import JobApplicationState
from jobs_tracking.services.job_tracking_service import JobTrackingResponse, JobTrackingResponseCode, JobTrackingService
from abstract_api import AbstractApi, ApiResponse
from utils.file_utils import JOB_TRACKING_CONFIG_FILE
from utils import utils
from typing import Any


class JobTrackingApiResponseCode(Enum):
    OK = 1
    ERROR = 2

class JobTrackingApiResponse:

    def __init__(self, job: Dict[str, Any], code: JobTrackingApiResponseCode):
        self.job = job
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "job": self.job,
            "code": self.code.name if isinstance(self.code, Enum) else str(self.code)
        }

    def __getstate__(self) -> Dict[str, Any]:
        """Support pickling/serialization by returning a dict."""
        return self.to_dict()

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore instance from pickled state."""
        self.text = state["text"]
        # Restore the Enum from its name
        self.code = JobTrackingApiResponseCode[state["code"]]


class JobTrackingApi(AbstractApi):
    
    def __init__(self, jobTrackingService: JobTrackingService):
        super().__init__(JOB_TRACKING_CONFIG_FILE)
        self.job_tracking_service = jobTrackingService

    def get_job_application_states(self) -> List[str]:
        """Get list of available job application states"""
        try:
            return [state.name for state in JobApplicationState if not state==JobApplicationState.UNKNOWN ]
        except Exception as e:
            logging.exception(f"Error getting job application states: {e}")
            return []       
    
        
    def add_job_to_company(self, user_id: str, company_name: str, 
                           job_url: str, job_title: str, job_state: str, 
                           contact_name: Optional[str] = None,
                            contact_linkedin: Optional[str] = None,
                            contact_email: Optional[str] = None) -> Dict[str, bool]:
        # Convert string to enum
        try:
            job_state = JobApplicationState[job_state.upper()] if job_state else JobApplicationState.UNKNOWN
        except KeyError:
            logging.error(f"Invalid job state: {job_state}")
            job_state = JobApplicationState.UNKNOWN
        
        response = self.job_tracking_service.add_or_update_position(
            user_id=user_id,
            company_name=company_name,
            job_url=job_url,
            job_title=job_title,
            job_state=job_state,
            contact_name=contact_name,
            contact_linkedin=contact_linkedin,
            contact_email=contact_email
        )
        if response  and response.code == JobTrackingResponseCode.OK:            
            return JobTrackingApiResponse(response.job, JobTrackingApiResponseCode.OK).to_dict()
        return JobTrackingApiResponse(None, JobTrackingApiResponseCode.ERROR).to_dict()
    

    async def _add_job_to_company_async(self, user_id: str, company_name: str, 
                           job_url: str, job_title: str, job_state: str, 
                           contact: Optional[str] = None, contact_url: Optional[str] = None) -> Dict[str, bool]:
        return self.job_tracking_service.add_or_update_position(user_id=user_id, company_name=company_name, 
                                                        job_url=job_url, job_title=job_title, 
                                                        job_state=job_state, contact_name=contact, contact_linkedin=contact_url)