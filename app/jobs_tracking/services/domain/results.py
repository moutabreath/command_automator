from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from .models import TrackedJob, Company
from ....repository.models import PersistenceErrorCode


class JobTrackingResponseCode(StrEnum):
    OK = "OK"
    ERROR = "ERROR"
    NO_TRACKED_JOBS = "NO_TRACKED_JOBS"


@dataclass
class JobTrackingResponse:
    job: TrackedJob
    code: JobTrackingResponseCode
    company_id: Optional[str] = None


@dataclass
class CompanyResponse:
    code: PersistenceErrorCode
    company: Optional[Company] = None
    error_message: Optional[str] = None