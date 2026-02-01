from dataclasses import dataclass
from ...services.domain.models import TrackedJob, Company

@dataclass
class GetTrackedJobsQuery:
    user_id: str
    company_name: str

@dataclass
class TrackNewJobDbQuery:
    user_id: str
    company_name: str
    tracked_job: TrackedJob

@dataclass
class TrackExistingJobDbQuery:
    user_id: str
    company_id: str
    tracked_job: TrackedJob

@dataclass
class DeleteApplicationDbQuery:
    user_id: str
    company_name: str

@dataclass
class DeleteJobDbQuery:
    user_id: str
    company_name: str
    job_url: str

@dataclass
class DeleteTrackedJobsDbQuery:
    user_id: str
    companies: list[Company]

@dataclass
class GetAllApplicationsQuery:
    user_id: str

@dataclass
class GetJobsByStateQuery:
    user_id: str
    state: str

@dataclass
class GetRecentJobsQuery:
    user_id: str
    limit: int = 10