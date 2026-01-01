import logging
from typing import Dict, List, Any

from jobs_tracking.models import CompanyDto, JobTrackingApiResponse, JobTrackingApiResponseCode, JobTrackingApiListResponse, TrackedJobDto
from jobs_tracking.services.models import Company, JobApplicationState, TrackedJob
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
            logging.error("Missing required parameter: user_id, company_name, or job_dto")
            return JobTrackingApiResponse(None, JobTrackingApiResponseCode.ERROR).to_dict()
               
        tracked_job = TrackedJob(
            job_url=job_dto.job_url,
            job_title=job_dto.job_title,
            job_state=JobApplicationState.from_string(job_dto.job_state) if isinstance(job_dto.job_state, str) else job_dto.job_state,
            contact_name=job_dto.contact_name,
            contact_linkedin=job_dto.contact_linkedin,
            contact_email=job_dto.contact_email
        )
        
        response = self.job_tracking_service.add_or_update_position(
            user_id=user_id,
            company_name=company_name,
            trackedJob=tracked_job
        )
        return self._create_job_response(response, company_name)

    def get_positions(self, user_id: str, company_name: str) -> Dict[str, Any]:
        if not user_id or not company_name:
            logging.error("Missing required parameter: user_id or company_name")
            return JobTrackingApiListResponse(None, None, JobTrackingApiResponseCode.ERROR).to_dict()
        
        response = self.job_tracking_service.get_positions(user_id, company_name)
        if response and response.code == JobTrackingResponseCode.OK:
            serialized_jobs = [self._get_job_dict_from_tracked_job(job) for job in response.jobs]
            return JobTrackingApiListResponse(serialized_jobs, company_name, JobTrackingApiResponseCode.OK).to_dict()
        return JobTrackingApiListResponse(None, company_name, JobTrackingApiResponseCode.ERROR).to_dict()
    
    def track_job_application_from_text(self, user_id: str, text:str):
        response = self.job_tracking_service.track_position_from_text(user_id, text)
        company_name = getattr(response, 'company_name', None)
        return self._create_job_response(response, company_name)

    def extract_job_title_and_company(self, url:str):
        return self.job_tracking_service.extract_job_title_and_company(url)
    
    def delete_tracked_jobs(self, userid:str, companies_jobs:List[CompanyDto]):
        domain_companies = self._convert_to_domain_companies(companies_jobs)
        success = self.job_tracking_service.delete_tracked_jobs(userid, domain_companies)
        return {"success" : success}

    def _convert_to_domain_companies(self, companies_jobs: List[CompanyDto]) -> List[Company]:
        domain_companies = []
        for company in companies_jobs:
            domain_company = Company(
                name=company.company_name,
                tracked_jobs=[TrackedJob(
                    job_url=job.job_url,
                    job_title=job.job_title,
                    job_state=JobApplicationState.from_string(job.job_state) if isinstance(job.job_state, str) else job.job_state,
                    contact_name=job.contact_name,
                    contact_linkedin=job.contact_linkedin,
                    contact_email=job.contact_email
                ) for job in company.tracked_jobs]
            )
            domain_companies.append(domain_company)
    
        return domain_companies
        

    def _create_job_response(self, response, company_name: str) -> Dict[str, Any]:
        if response and response.code == JobTrackingResponseCode.OK:
            job_dict = self._get_job_dict_from_tracked_job(response.job)
            job_dict['company_name'] = company_name
            return JobTrackingApiResponse(job_dict, JobTrackingApiResponseCode.OK).to_dict()
        return JobTrackingApiResponse(None, JobTrackingApiResponseCode.ERROR).to_dict()

    def _get_job_dict_from_tracked_job(self, job: TrackedJob):
        job_dict = asdict(job)
        job_dict['job_state'] = job.job_state.name  # Convert enum to string
        if job_dict.get('update_time'):
            job_dict['update_time'] = job_dict['update_time'].isoformat() if hasattr(job_dict['update_time'], 'isoformat') else str(job_dict['update_time'])
        return job_dict
    