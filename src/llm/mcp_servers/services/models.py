from dataclasses import dataclass

from jobs_tracking.services.models import TrackedJob

class UserApplicationResponseCode:
    SUCESS = 1,
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
          
