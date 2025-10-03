from pydantic import BaseModel

from pydantic import BaseModel, Field

class ResumeData(BaseModel):
    """Data model for resume and cover letter generation."""

    applicant_name: str = Field(..., min_length=1, description="Name of the job applicant")
    general_guidelines: str = Field(..., min_length=1, description="General guidelines for the application")
    resume: str = Field(..., min_length=1, description="Resume content")
    resume_highlighted_sections: list[str] = Field(..., min_length=1, description="Key sections to highlight from the resume")
    job_description: str = Field(..., min_length=1, description="Job description to tailor the application to")
    cover_letter_guidelines: str = Field(..., min_length=1, description="Guidelines for cover letter generation")