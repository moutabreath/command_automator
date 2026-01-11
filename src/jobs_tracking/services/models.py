from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from repository.models import PersistenceErrorCode

class JobApplicationState(str, Enum):
    CONNECTION_REQUESTED = "CONNECTION_REQUESTED"
    MESSAGE_SENT = "MESSAGE_SENT"
    EMAIL_SENT = "EMAIL_SENT"
    APPLIED = "APPLIED"
    UNKNOWN = "UNKNOWN"
    
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
    job_id: str
    job_url: str
    job_title: str
    job_state: JobApplicationState
    contact_name: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None
    update_time: Optional[datetime] = None
    

@dataclass
class Company:
    company_id: str
    company_name: str
    tracked_jobs: list[TrackedJob]

    # 2. The Mapper Logic
    @classmethod
    def from_dto(cls, dto: 'CompanyDto') -> 'Company':
        # Convert the list of Job DTOs to Job Domain objects
        domain_jobs = [
            TrackedJob(
                job_id=job_dto.job_id,
                job_url=job_dto.job_url,
                job_title=job_dto.job_title,
                job_state=JobApplicationState.from_string(job_dto.job_state),
                contact_name=job_dto.contact_name
            )
            for job_dto in dto.tracked_jobs
        ]
        
        return cls(
            company_id=dto.company_id,
            name=dto.company_name,
            tracked_jobs=domain_jobs
        )

class JobTrackingResponseCode(str, Enum):
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