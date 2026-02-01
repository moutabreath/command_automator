from pydantic import BaseModel

from .models import CompanyDto, TrackedJobDto



class TrackNewJobRequest(BaseModel):
    user_id: str
    company_name: str
    job_dto: TrackedJobDto

class TrackExistingJobRequest(BaseModel):
    user_id: str
    company_id: str
    job_dto: TrackedJobDto

class GetTrackedJobsRequest(BaseModel):
    user_id: str
    company_name: str

class DeleteTrackedJobsRequest(BaseModel):
    user_id: str
    companies_jobs: list[CompanyDto]
