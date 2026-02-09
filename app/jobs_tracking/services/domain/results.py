from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from .models import TrackedJob, Company


class JobTrackingResponseCode(StrEnum):
    OK = "OK"
    ERROR = "ERROR"
    NO_TRACKED_JOBS = "NO_TRACKED_JOBS"

class UserApplicationResponseCode(StrEnum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


@dataclass
class JobTrackingResponse:
    job: TrackedJob
    code: JobTrackingResponseCode
    company_id: Optional[str] = None


@dataclass
class CompanyResponse:
    code: JobTrackingResponseCode
    company: Optional[Company] = None
    error_message: Optional[str] = None

@dataclass
class UserApplicationResponse:
    code: UserApplicationResponseCode
    company_jobs: list[Company]
