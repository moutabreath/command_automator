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
    
    @classmethod
    def from_string(cls, state_str: str) -> 'JobApplicationState':
        """Create JobApplicationState from string"""
        try:
            return cls[state_str.upper()]
        except KeyError:
            return cls.UNKNOWN
    
    @classmethod
    def from_value(cls, value: int) -> 'JobApplicationState':
        """Create JobApplicationState from integer value"""
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN

@dataclass
class TrackedJob:
    job_url: str
    job_title: str
    job_state: JobApplicationState
    contact_name: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None
    update_time: Optional[datetime] = None
    

@dataclass
class Company:
    name: str
    tracked_jobs: List[TrackedJob]

    # 2. The Mapper Logic
    @classmethod
    def from_dto(cls, dto: 'CompanyDto') -> 'Company':
        # Convert the list of Job DTOs to Job Domain objects
        domain_jobs = [
            TrackedJob(
                title=job_dto.title
                , url=job_dto.url
                , state=JobApplicationState.from_string(job_dto.state)
                , contact_name=job_dto.contact
            )
            for job_dto in dto.tracked_jobs
        ]
        
        return cls(
            company_name=dto.company_name,
            tracked_jobs=domain_jobs
            # company_id is generated automatically by default_factory
        )

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