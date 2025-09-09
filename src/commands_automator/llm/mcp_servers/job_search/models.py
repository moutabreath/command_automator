

from pydantic import BaseModel


class Job(BaseModel):
    title: str
    company: str
    location: str
    description: str
    link: str
    posted_date: str
