from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

class JobApplicationState(Enum):
    CONNECTION_REQUESTED = 1
    MESSAGE_SENT = 2
    EMAIL_SENT = 3
    APPLIED = 4
    UNKNOWN = 5

@dataclass
class TrackedJob:
    job_url: str
    job_title: str
    job_state: JobApplicationState
    contact_name: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None
    update_time: Optional[datetime] = None

class JobTrackingResponseCode(Enum):
    OK = 1
    ERROR = 2
    
class JobTrackingResponse:
    def __init__(self, job: TrackedJob, code: JobTrackingResponseCode):
        self.job = job
        self.code = code

class JobTrackingListResponse:
    def __init__(self, jobs: List[TrackedJob], code: JobTrackingResponseCode):
        self.jobs = jobs
        self.code = code


class JobAndCompanyTrackingResponse:
    def __init__(self, job: TrackedJob, company_name: str, code: JobTrackingResponseCode):
        self.job = job
        self.company_name = company_name
        self.code = code