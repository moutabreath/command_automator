from enum import Enum
from typing import Optional

from pydantic import BaseModel

class TrackedJobDto(BaseModel):
    job_id: Optional[str]
    job_url: str
    job_title: str
    job_state: str
    company_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None

class CompanyDto(BaseModel):    
    company_name: str
    tracked_jobs: list[dict]
    company_id: Optional[str] = None


class JobTrackingApiResponseCode(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


class JobTrackingApiResponse(BaseModel):    
    code: JobTrackingApiResponseCode
    job: Optional[TrackedJobDto] = None


class CompanyApiResponse(BaseModel):    
    code: JobTrackingApiResponseCode
    company: Optional[CompanyDto] = None


