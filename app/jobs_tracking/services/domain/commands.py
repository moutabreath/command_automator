from dataclasses import dataclass
from .models import TrackedJob, Company

@dataclass
class TrackNewJobCommand:
    user_id: str
    company_name: str
    tracked_job: TrackedJob

@dataclass
class TrackExistingJobCommand:
    user_id: str
    company_id: str
    tracked_job: TrackedJob

@dataclass
class GetTrackedJobsCommand:
    user_id: str
    company_name: str

@dataclass
class DeleteTrackedJobsCommand:
    user_id: str
    companies_jobs: list[Company]

@dataclass
class ExtractJobInfoCommand:
    url: str