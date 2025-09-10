from datetime import date
from pydantic import BaseModel, Field, HttpUrl

class Job(BaseModel):
    title: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    link: HttpUrl
    posted_date: date