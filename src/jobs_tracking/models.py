from enum import StrEnum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from jobs_tracking.services.models import JobApplicationState


class TrackedJobDto(BaseModel):
    company_id: Optional[str] = None
    job_id: Optional[str]
    job_url: str
    job_title: str
    job_state: JobApplicationState
    update_time: Optional[str] = None   
    contact_name: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None

class CompanyDto(BaseModel):    
    company_name: str
    tracked_jobs: list[TrackedJobDto]
    company_id: Optional[str] = None


class JobTrackingApiResponseCode(StrEnum):
    OK = "OK"
    ERROR = "ERROR"
    INVALID_PARAMETER = "INVALID_PARAMETER"


class JobTrackingApiResponse(BaseModel):    
    code: JobTrackingApiResponseCode
    job: Optional[TrackedJobDto] = None


class CompanyApiResponse(BaseModel):    
    code: JobTrackingApiResponseCode
    company: Optional[CompanyDto] = None


