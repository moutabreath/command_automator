from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from jobs_tracking.services.models import JobApplicationState
from typing import Any


class JobTrackingApiResponseCode(Enum):
    OK = 1
    ERROR = 2

class JobTrackingApiResponse:

    def __init__(self, job: Dict[str, Any], code: JobTrackingApiResponseCode):
        self.job = job
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "job": self.job,
            "code": self.code.name if isinstance(self.code, Enum) else str(self.code)
        }

    def __getstate__(self) -> Dict[str, Any]:
        """Support pickling/serialization by returning a dict."""
        return self.to_dict()

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore instance from pickled state."""
        self.job = state["job"]
        # Restore the Enum from its name
        self.code = JobTrackingApiResponseCode[state["code"]]

class JobTrackingApiListResponse:
    def __init__(self, job: List[Dict], code: JobTrackingApiResponseCode):
        self.jobs = job
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "jobs": self.jobs,
            "code": self.code.name if isinstance(self.code, Enum) else str(self.code)
        }

@dataclass
class TrackedJobDto:
    job_url: str
    job_title: str
    job_state: JobApplicationState
    contact_name: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None