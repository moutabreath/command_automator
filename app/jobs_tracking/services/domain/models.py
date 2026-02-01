from dataclasses import dataclass, fields
from datetime import datetime
from typing import Optional

from ...api.schemas.models import CompanyDto
from .job_application_state import JobApplicationState

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
            company_name=dto.company_name,
            tracked_jobs=domain_jobs
        )
