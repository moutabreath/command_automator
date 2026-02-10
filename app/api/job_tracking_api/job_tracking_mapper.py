"""
Mapper utilities for Job Tracking API
Handles conversion between DTOs, domain models, and API responses
"""

from .schemas.models import CompanyDto, TrackedJobDto
from .schemas.response import CompanyTrackingApiResponseCode

from ...jobs_tracking.services.domain.models import TrackedJob, Company
from ...jobs_tracking.services.domain.results import JobTrackingResponseCode, CompanyResponse

# DTO to Model
def api_tracked_job_to_model_tracked_job(job_dto: TrackedJobDto) -> TrackedJob:
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

def api_company_to_domain_company(company_dto: CompanyDto) -> Company:
    domain_jobs = [
        api_tracked_job_to_model_tracked_job(job_dto)
        for job_dto in company_dto.tracked_jobs
    ]
    
    return Company(
        company_id=company_dto.company_id,
        company_name=company_dto.company_name,
        tracked_jobs=domain_jobs
    )

def api_company_list_to_domain_company_list(companies_jobs: list[CompanyDto]) -> list[Company]:
    """Convert list of CompanyDto to domain Company objects"""
    domain_companies = []
    for company in companies_jobs:
        domain_company = Company(
            company_id=company.company_id,
            company_name=company.company_name,
            tracked_jobs=[api_tracked_job_to_model_tracked_job(job) for job in company.tracked_jobs]
        )
        domain_companies.append(domain_company)
    return domain_companies

# Model To DTO

def domain_tracked_job_to_api_tracked_job(job: TrackedJob) -> TrackedJobDto:
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


def domain_company_to_api_company(company: Company) -> CompanyDto:
    domain_jobs = [
        domain_tracked_job_to_api_tracked_job(domain_job)
        for domain_job in company.tracked_jobs
    ]
    
    return CompanyDto(
        company_id=company.company_id,
        company_name=company.company_name,
        tracked_jobs=domain_jobs
    )

# Create API Responses

def create_company_api_response(response: CompanyResponse) -> CompanyResponse:
    """Convert CompanyResponse to CompanyApiResponse"""
    if response and response.code == JobTrackingResponseCode.OK:
        company_dto = domain_company_to_api_company(response.company)
        return CompanyResponse(company=company_dto, code=CompanyTrackingApiResponseCode.OK)
    
    if response and response.code == JobTrackingResponseCode.NO_TRACKED_JOBS:
        return CompanyResponse(company=None, code=CompanyTrackingApiResponseCode.NO_TRACKED_JOBS)

    return CompanyResponse(code=CompanyTrackingApiResponseCode.ERROR)

