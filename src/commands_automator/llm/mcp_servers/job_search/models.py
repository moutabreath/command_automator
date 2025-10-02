from datetime import date
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class Job(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str = Field(min_length=1)
    description: Optional[str] = Field(min_length=1)    
    link: Optional[HttpUrl] = None
    posted_date: Optional[date] = None
    
    class Config:
        validate_assignment = True  # Validates values when attributes are set
        arbitrary_types_allowed = True  # Allows more flexible type validation