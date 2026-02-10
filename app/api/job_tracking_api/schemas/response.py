from enum import StrEnum
from typing import Optional
from pydantic import BaseModel

from .models import CompanyDto



class CompanyTrackingApiResponseCode(StrEnum):
    OK = "OK"
    ERROR = "ERROR"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    NO_TRACKED_JOBS = "NO_TRACKED_JOBS"

class CompanyApiResponse(BaseModel):    
    code: CompanyTrackingApiResponseCode
    company: Optional[CompanyDto] = None
