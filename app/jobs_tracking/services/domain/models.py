from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .enums import JobApplicationState

@dataclass
class TrackedJob:
    job_url: str
    job_title: str
    job_state: JobApplicationState
    job_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None
    update_time: Optional[datetime] = None



@dataclass
class Company:
    company_id: str
    company_name: str
    tracked_jobs: list[TrackedJob]
