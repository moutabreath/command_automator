from enum import StrEnum
from typing import Optional
from pydantic import BaseModel

from .models import CompanyDto, TrackedJobDto



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
