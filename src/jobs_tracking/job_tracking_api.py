import logging
from typing import Any
from dataclasses import asdict

from jobs_tracking.models import CompanyDto, JobTrackingApiResponse, JobTrackingApiResponseCode, CompanyApiResponse, TrackedJobDto
from jobs_tracking.services.models import Company, CompanyResponse, JobApplicationState, JobTrackingResponse, TrackedJob
from jobs_tracking.services.job_tracking_service import JobTrackingResponseCode, JobTrackingService

class JobTrackingApi:
    
    def __init__(self, job_tracking_service: JobTrackingService):
        self.job_tracking_service = job_tracking_service

    def get_job_application_states(self) -> list[str]:
        """Get list of available job application states"""
        try:
            return [state.name for state in JobApplicationState if not state == JobApplicationState.UNKNOWN]
        except Exception as e:
            logging.exception(f"Error getting job application states: {e}")
            return []    
        
    def track_job(self, user_id: str, company_name: str, job_dto: TrackedJobDto) -> TrackedJobDto:
        
        if not user_id or not company_name or not job_dto:
            logging.error("Missing required parameter: user_id, company_name, or job_dto")
            return JobTrackingApiResponse(job=None, code=JobTrackingApiResponseCode.ERROR).model_dump()
               
        tracked_job = self._map_dto_to_tracked_job(job_dto)
        
        response = self.job_tracking_service.track_job(
            user_id=user_id,
            company_name=company_name,
            tracked_job=tracked_job
        )
        return self.create_job_tracking_response(response)
 
    def get_tracked_jobs(self, user_id: str, company_name: str) -> CompanyApiResponse:
        if not user_id or not company_name:
            logging.error("Missing required parameter: user_id or company_name")
            return CompanyApiResponse(company=None, code=JobTrackingApiResponseCode.ERROR).model_dump()
        
        company_response: CompanyResponse = self.job_tracking_service.get_tracked_jobs(user_id, company_name)
        if company_response and company_response.code == JobTrackingResponseCode.OK:
            serialized_jobs = [self._map_tracked_job_to_dto(job) for job in company_response.company.tracked_jobs]
            company_dto = CompanyDto(company_id=company_response.company.company_id, company_name=company_response.company.company_name, tracked_jobs=serialized_jobs)
            return CompanyApiResponse(company=company_dto,
                                                code=JobTrackingApiResponseCode.OK).model_dump(exclude_none=True)
        return CompanyApiResponse(company=None, code=JobTrackingApiResponseCode.ERROR).model_dump()
    
    def extract_job_title_and_company(self, url:str):
        if not url:
            logging.error("Missing required parameter: url")
            return {"error": "URL is required"}

        try:
            return self.job_tracking_service.extract_job_title_and_company(url)
        except Exception as e:
            logging.exception(f"Error extracting job info from URL: {e}")
            return {"error": "Failed to extract job information"}
    
    def delete_tracked_jobs(self, user_id:str, companies_jobs:list[CompanyDto]):
        if not user_id or not companies_jobs:
            logging.error("Missing required parameter: user_id or companies_jobs")
            return {"success": False}
        
        domain_companies = self._map_dto_to_domain_companies(companies_jobs)
        success = self.job_tracking_service.delete_tracked_jobs(user_id, domain_companies)
        return {"success" : success}

    def _map_dto_to_tracked_job(self, job_dto: TrackedJobDto) -> TrackedJob:
        """Convert TrackedJobDto to domain TrackedJob"""
        return TrackedJob(
            job_id=job_dto.job_id,
            job_url=job_dto.job_url,
            job_title=job_dto.job_title,
            job_state=JobApplicationState.from_string(job_dto.job_state) if isinstance(job_dto.job_state, str) else job_dto.job_state,
            contact_name=job_dto.contact_name,
            contact_linkedin=job_dto.contact_linkedin,
            contact_email=job_dto.contact_email
        )

    def _map_dto_to_domain_companies(self, companies_jobs: list[CompanyDto]) -> list[Company]:
        domain_companies = []
        for company in companies_jobs:
            domain_company = Company(
                company_id=company.company_id,
                company_name=company.company_name,
                tracked_jobs=[self._map_dto_to_tracked_job(job) for job in company.tracked_jobs]
            )
            domain_companies.append(domain_company)
    
        return domain_companies
        

    def create_job_tracking_response(self, response: JobTrackingResponse) -> JobTrackingApiResponse:
        if response and response.code == JobTrackingResponseCode.OK:
            job_dto = self._map_tracked_job_to_dto(response.job)
            return JobTrackingApiResponse(job=job_dto, code=JobTrackingApiResponseCode.OK).model_dump()
        return JobTrackingApiResponse(code=JobTrackingApiResponseCode.ERROR).model_dump()

    def _map_tracked_job_to_dto(self, job: TrackedJob):
        return TrackedJobDto(
            job_id=job.job_id,
            job_url=job.job_url,
            job_title=job.job_title,
            job_state=job.job_state,
            update_time=job.update_time.strftime("%d/%m/%Y"),
            contact_name=job.contact_name,
            contact_linkedin=job.contact_linkedin,
            contact_email=job.contact_email
        )

    