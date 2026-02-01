import logging

from .schemas.models import CompanyDto, TrackedJobDto
from .schemas.requests import TrackNewJobRequest, TrackExistingJobRequest, GetTrackedJobsRequest, DeleteTrackedJobsRequest
from .schemas.response import JobTrackingApiResponse, JobTrackingApiResponseCode, CompanyApiResponse
from ..services.domain.models import JobApplicationState, TrackedJob, Company
from ..services.domain.results import JobTrackingResponseCode, CompanyResponse, JobTrackingResponse
from ..services.job_tracking_service import JobTrackingService
from ..services.domain.commands import (
    TrackNewJobCommand,
    TrackExistingJobCommand,
    GetTrackedJobsCommand,
    DeleteTrackedJobsCommand,
    ExtractJobInfoCommand
)
from ...utils.utils import is_valid_uuid4


class JobTrackingApi:
    
    def __init__(self, job_tracking_service: JobTrackingService):
        self.job_tracking_service = job_tracking_service

 
    @staticmethod
    def get_job_application_states() -> list[str]:
        """Get list of available job application states"""
        try:
            return [state.name for state in JobApplicationState if not state == JobApplicationState.UNKNOWN]
        except Exception as e:
            logging.exception(f"Error getting job application states: {e}")
            return []    
        
    def track_new_job(self, request: TrackNewJobRequest) -> JobTrackingApiResponse:
        
        if not is_valid_uuid4(request.user_id):
            logging.error(f"Invalid user_id: '{request.user_id}' is not a valid UUID4")
            return JobTrackingApiResponse(job=None, code=JobTrackingApiResponseCode.ERROR).model_dump()
        
        if not request.company_name or not request.job_dto or not request.job_dto.job_title or not request.job_dto.job_url:
            logging.error("Missing required parameter: user_id, company_name, job_dto , job url or job title")
            return JobTrackingApiResponse(job=None, code=JobTrackingApiResponseCode.ERROR).model_dump()
               
        tracked_job = self._map_dto_to_tracked_job(request.job_dto)
        
        command = TrackNewJobCommand(
            user_id=request.user_id,
            company_name=request.company_name,
            tracked_job=tracked_job
        )
        response = self.job_tracking_service.track_new_job_sync(command)
        return self.create_job_tracking_response(response)

    def track_existing_job(self, request: TrackExistingJobRequest) -> JobTrackingApiResponse:
        
        if not is_valid_uuid4(request.user_id) or not is_valid_uuid4(request.company_id):
            logging.error(f"Invalid id: '{request.user_id}' or '{request.company_id} is not a valid UUID4")
            return JobTrackingApiResponse(job=None, code=JobTrackingApiResponseCode.INVALID_PARAMETER).model_dump()
        
        if not request.job_dto:
            logging.error("Missing required parameter: job_dto")
            return JobTrackingApiResponse(job=None, code=JobTrackingApiResponseCode.INVALID_PARAMETER).model_dump()
        
        if not is_valid_uuid4(request.job_dto.job_id):
            logging.error("invalid parameter: job_dto.job_id")
            return JobTrackingApiResponse(job=None, code=JobTrackingApiResponseCode.INVALID_PARAMETER).model_dump()
        
        tracked_job = self._map_dto_to_tracked_job(request.job_dto)
        
        command = TrackExistingJobCommand(
            user_id=request.user_id,
            company_id=request.company_id,
            tracked_job=tracked_job
        )
        response = self.job_tracking_service.track_existing_job_sync(command)
        return self.create_job_tracking_response(response)
 
    def get_tracked_jobs(self, request: GetTrackedJobsRequest) -> CompanyApiResponse:
        
        if not is_valid_uuid4(request.user_id):
            logging.error(f"Invalid user_id: '{request.user_id}' is not a valid UUID4")
            return CompanyApiResponse(company=None, code=JobTrackingApiResponseCode.ERROR).model_dump()
        
        if not request.company_name:
            logging.error("Missing required parameter: company_name")
            return CompanyApiResponse(company=None, code=JobTrackingApiResponseCode.ERROR).model_dump()
        
        command = GetTrackedJobsCommand(user_id=request.user_id, company_name=request.company_name)
        company_response: CompanyResponse = self.job_tracking_service.get_tracked_jobs_sync(command)
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
            command = ExtractJobInfoCommand(url=url)
            return self.job_tracking_service.extract_job_title_and_company(command)
        except Exception as e:
            logging.exception(f"Error extracting job info from URL: {e}")
            return {"error": "Failed to extract job information"}
    
    def delete_tracked_jobs(self, request: DeleteTrackedJobsRequest):
        
        if not is_valid_uuid4(request.user_id):
            logging.error(f"Invalid user_id: '{request.user_id}' is not a valid UUID4")
            return {"success": False}
        
        if not request.companies_jobs or len(request.companies_jobs) == 0:
            logging.error("Missing required parameter: companies_jobs")
            return {"success": False}
        
        domain_companies = self._map_dto_to_domain_companies(request.companies_jobs)
        command = DeleteTrackedJobsCommand(user_id=request.user_id, companies_jobs=domain_companies)
        success = self.job_tracking_service.delete_tracked_jobs_sync(command)
        return {"success" : success}

    def _map_dto_to_tracked_job(self, job_dto: TrackedJobDto) -> TrackedJob:
        """Convert TrackedJobDto to domain TrackedJob"""
        return TrackedJob(
            job_id=job_dto.job_id,
            job_url=job_dto.job_url,
            job_title=job_dto.job_title,
            job_state=job_dto.job_state,
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

    @staticmethod
    def _map_tracked_job_to_dto(job: TrackedJob):
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
