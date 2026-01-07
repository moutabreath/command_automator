from dataclasses import dataclass
from enum import Enum

from jobs_tracking.services.models import TrackedJob

class UserApplicationResponseCode(Enum):
    SUCCESS = 1
    ERROR = 2


@dataclass
class UserApplication:
    company_name: str
    tracked_job: list[TrackedJob]



@dataclass
class UserApplicationResponse:
    code: UserApplicationResponseCode
    user_applications: list[UserApplication]
    error_message: str = None
          
