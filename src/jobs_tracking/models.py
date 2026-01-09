from enum import Enum
from typing import Dict, List, Optional

from typing import Any

from pydantic import BaseModel


class JobTrackingApiResponseCode(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


class JobTrackingApiResponse(BaseModel):
    job: Dict[str, Any]
    code: JobTrackingApiResponseCode


class JobTrackingApiListResponse(BaseModel):
    jobs: List[Dict]
    company_name: str
    code: JobTrackingApiResponseCode


class TrackedJobDto(BaseModel):
    job_id: str
    job_url: str
    job_title: str
    job_state: str
    company_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None

class CompanyDto(BaseModel):
    company_id: str
    company_name: str
    tracked_jobs: List[TrackedJobDto]