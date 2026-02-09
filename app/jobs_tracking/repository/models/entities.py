from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from bson import ObjectId

@dataclass
class JobEntity:
    """Represents a single job entry inside the 'jobs' array in MongoDB"""
    job_id: str
    job_url: str
    job_title: str
    job_state: str 
    update_time: datetime
    
    # Contact info fields are optional/nullable in the provided JSON
    contact_name: Optional[str] = None
    contact_url: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_email: Optional[str] = None

@dataclass
class CompanyEntity:
    """The root MongoDB document for the 'company' collection"""    
    company_id: str
    company_name: str
    user_id: str
    jobs: list[JobEntity] = field(default_factory=list)