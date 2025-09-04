from pydantic import BaseModel

class ResumeData(BaseModel):
    applicant_name: str
    general_guidelines: str
    resume: str
    resume_highlighted_sections: list[str]
    job_description: str
    cover_letter_guidelines: str    