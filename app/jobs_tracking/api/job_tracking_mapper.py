"""
Mapper utilities for Job Tracking API
Handles conversion between DTOs, domain models, and API responses
"""
from typing import List

from .schemas.models import CompanyDto, TrackedJobDto
from .schemas.response import JobTrackingApiResponse, JobTrackingApiResponseCode, CompanyApiResponse
from ..services.domain.models import TrackedJob, Company
from ..services.domain.results import JobTrackingResponseCode, JobTrackingResponse, CompanyResponse


def dto_to_tracked_job(job_dto: TrackedJobDto) -> TrackedJob:
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


def dto_list_to_domain_company_list(companies_jobs: List[CompanyDto]) -> List[Company]:
    """Convert list of CompanyDto to domain Company objects"""
    domain_companies = []
    for company in companies_jobs:
        domain_company = Company(
            company_id=company.company_id,
            company_name=company.company_name,
            tracked_jobs=[dto_to_tracked_job(job) for job in company.tracked_jobs]
        )
        domain_companies.append(domain_company)
    return domain_companies


def tracked_job_to_dto(job: TrackedJob) -> TrackedJobDto:
    """Convert domain TrackedJob to DTO"""
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


def company_dto_to_company_domain(company_dto: CompanyDto) -> Company:
    domain_jobs = [
        dto_to_tracked_job(job_dto)
        for job_dto in company_dto.tracked_jobs
    ]
    
    return Company(
        company_id=company_dto.company_id,
        company_name=company_dto.company_name,
        tracked_jobs=domain_jobs
    )

def company_domain_to_company_dto(company: Company) -> CompanyDto:
    domain_jobs = [
        tracked_job_to_dto(domain_job)
        for domain_job in company.tracked_jobs
    ]
    
    return CompanyDto(
        company_id=company.company_id,
        company_name=company.company_name,
        tracked_jobs=domain_jobs
    )



def create_company_api_response(response: CompanyResponse) -> CompanyApiResponse:
    """Convert CompanyResponse to CompanyApiResponse"""
    if response and response.code == JobTrackingResponseCode.OK:
        company_dto = company_domain_to_company_dto(response.company)
        return CompanyApiResponse(company=company_dto, code=JobTrackingApiResponseCode.OK)
    
    if response and response.code == JobTrackingResponseCode.NO_TRACKED_JOBS:
        return CompanyApiResponse(company=None, code=JobTrackingApiResponseCode.NO_TRACKED_JOBS)

    return CompanyApiResponse(code=JobTrackingApiResponseCode.ERROR)

def create_job_tracking_api_response(response: JobTrackingResponse) -> JobTrackingApiResponse:
    """Convert JobTrackingResponse to JobTrackingApiResponse"""
    if response and response.code == JobTrackingResponseCode.OK:
        job_dto = tracked_job_to_dto(response.job)
        return JobTrackingApiResponse(job=job_dto, code=JobTrackingApiResponseCode.OK)
    return JobTrackingApiResponse(code=JobTrackingApiResponseCode.ERROR)
