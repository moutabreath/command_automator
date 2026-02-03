from datetime import date
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Optional

class ScrapedJob(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,  # Validates values when attributes are set
        arbitrary_types_allowed=True  # Allows more flexible type validation
    )
    
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str = Field(min_length=1)
    description: Optional[str] = Field(default=None, min_length=1)  
    link: Optional[HttpUrl] = None
    posted_date: Optional[date] = None