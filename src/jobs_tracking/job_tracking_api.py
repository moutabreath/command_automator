import logging
from typing import Dict, List, Optional

from jobs_tracking.models import JobApplicationState
from jobs_tracking.services.job_tracking_service import JobTrackingService
from abstract_api import AbstractApi
from utils.file_utils import JOB_TRACKING_CONFIG_FILE
from utils import utils

class JobTrackingApi(AbstractApi):
    def __init__(self):
        super().__init__(JOB_TRACKING_CONFIG_FILE)
        self.job_tracking_service = JobTrackingService()

    def get_job_application_states(self) -> List[str]:
        """Get list of available job application states"""
        try:
            return [state.name for state in JobApplicationState if not state==JobApplicationState.UNKNOWN ]
        except Exception as e:
            logging.exception(f"Error getting job application states: {e}")
            return []       
    
        
    def add_job_to_company(self, user_id: str, company_name: str, 
                           job_url: str, job_title: str, state: str, 
                           contact: Optional[str] = None, contact_url: Optional[str] = None) -> Dict[str, bool]:
        # Convert string to enum
        try:
            job_state = JobApplicationState[state.upper()] if state else JobApplicationState.UNKNOWN
        except KeyError:
            job_state = JobApplicationState.UNKNOWN
        
        update_status =  utils.run_async_method(
            self.job_tracking_service.add_job_to_company(user_id=user_id, company_name=company_name, 
                                                        job_url=job_url,
                                                        job_title=job_title, 
                                                        state=job_state, contact=contact))
        if update_status:
            return update_status
        return {"created": False, "updated": False}