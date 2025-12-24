import logging
from typing import Dict, List, Any

from jobs_tracking.models import JobTrackingApiResponse, JobTrackingApiResponseCode, JobTrackingApiListResponse, TrackedJobDto
from jobs_tracking.services.models import JobApplicationState, TrackedJob
from jobs_tracking.services.job_tracking_service import JobTrackingResponseCode, JobTrackingService
from abstract_api import AbstractApi
from dataclasses import asdict


class JobTrackingApi(AbstractApi):
    
    def __init__(self, jobTrackingService: JobTrackingService):
        self.job_tracking_service = jobTrackingService

    def get_job_application_states(self) -> List[str]:
        """Get list of available job application states"""
        try:
            return [state.name for state in JobApplicationState if not state==JobApplicationState.UNKNOWN ]
        except Exception as e:
            logging.exception(f"Error getting job application states: {e}")
            return []       
    
        
    def track_job_application(self, user_id: str, company_name: str, job_dto: TrackedJobDto) -> Dict[str, Any]:
        
        if not user_id or not company_name or not job_dto:
            logging.error("missing company name or user_id")
            return JobTrackingApiResponse(None, JobTrackingApiResponseCode.ERROR).to_dict()
        
        tracked_job = TrackedJob(
            job_url=job_dto.job_url,
            job_title=job_dto.job_title,
            job_state=job_dto.job_state,
            contact_name=job_dto.contact_name,
            contact_linkedin=job_dto.contact_linkedin,
            contact_email=job_dto.contact_email
        )
        
        response = self.job_tracking_service.add_or_update_position(
            user_id=user_id,
            company_name=company_name,
            trackedJob=tracked_job
        )
        if response and response.code == JobTrackingResponseCode.OK:
            job_dict = self._get_job_dict_from_tracked_job(response.job)
            return JobTrackingApiResponse(job_dict, JobTrackingApiResponseCode.OK).to_dict()
        return JobTrackingApiResponse(None, JobTrackingApiResponseCode.ERROR).to_dict()

    def get_positions(self, user_id: str, company_name: str) -> List[Dict]:
        response = self.job_tracking_service.get_positions(user_id, company_name)
        if response and response.code == JobTrackingResponseCode.OK:
            serialized_jobs = [self._get_job_dict_from_tracked_job(job) for job in response.jobs]
            return JobTrackingApiListResponse(serialized_jobs, JobTrackingApiResponseCode.OK).to_dict()
        return JobTrackingApiListResponse(None, JobTrackingApiResponseCode.ERROR).to_dict()
    
    def track_job_application_from_text(self, user_id: str, text:str):
        response = self.job_tracking_service.track_position_from_text(user_id, text)
        if response and response.code == JobTrackingResponseCode.OK:            
            return JobTrackingApiListResponse(self._get_job_dict_from_tracked_job(response.job), JobTrackingApiResponseCode.OK).to_dict()
        return JobTrackingApiListResponse(None, JobTrackingApiResponseCode.ERROR).to_dict()

    def _get_job_dict_from_tracked_job(self, job: TrackedJob):
        job_dict = asdict(job)
        job_dict['job_state'] = job.job_state.name  # Convert enum to string
        if job_dict.get('update_time'):
            job_dict['update_time'] = job_dict['update_time'].isoformat() if hasattr(job_dict['update_time'], 'isoformat') else str(job_dict['update_time'])
        return job_dict
    