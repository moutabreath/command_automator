import logging
from pathlib import Path
from typing import Tuple, List, Optional

from llm.mcp_servers.resume.models import ResumeData
from utils import file_utils

class ResumeLoaderService:

    async def get_resume_files(self) -> ResumeData:
        """Fetch resume file, applicant name, job description and guidelines"""    
        try:
            resume_content, applicant_name = await self.get_resume_and_applicant_name()
            
            if resume_content is None:
                logging.error("Couldn't parse resume content")
                return self._create_empty_resume_data()

            if applicant_name is None:
                applicant_name = "John Doe"

            guide_lines = await self.get_main_part_guide_lines()
            if guide_lines:
                guide_lines = guide_lines.replace('***applicant_name***', applicant_name)
            
            highlighted_sections = await self.get_highlighted_sections()
            job_description_content = await self.get_job_description()
            cover_letter_guide_lines = await self.get_cover_letter_guide_lines()

            data_dict = {
                "applicant_name": applicant_name or "",
                "general_guidelines": guide_lines or "",
                "resume": resume_content or "",
                "resume_highlighted_sections": highlighted_sections or [],
                "job_description": job_description_content or "",
                "cover_letter_guidelines": cover_letter_guide_lines or ""
            }
            
            resume_data = ResumeData(**data_dict)
            logging.debug("Created ResumeData successfully")
            return resume_data
            
        except Exception as e:
            logging.error(f"Unhandled error in get_resume_files: {e}", exc_info=True)
            return self._create_empty_resume_data()

    async def get_main_part_guide_lines(self) -> str:
        file_path: Path = file_utils.RESUME_ADDITIONAL_FILES_DIR / 'guidelines.txt'     
        file_text: str = await file_utils.read_text_file(file_path)      
        if not file_text:
            logging.error(f"No guidelines file found at {file_path}")
            return ""
        return file_text
    
    async def get_resume_and_applicant_name(self) -> Tuple[str, str]:
        resume_path, applicant_name = self.find_resume_file()
        if not resume_path or not applicant_name:
            logging.error(f"No .txt resume file found in {file_utils.RESUME_RESOURCES_DIR}")
            return "", ""
        resume_text: str = await file_utils.read_text_file(resume_path)
        return resume_text, applicant_name
                
    def find_resume_file(self) -> Tuple[str, str]:
        resume_dir: Path = file_utils.RESUME_RESOURCES_DIR
        if not resume_dir.exists():
            logging.error(f"Resume directory not found: {resume_dir}")
            return "", ""

        # Only look for .txt files directly in the RESOURCES folder
        txt_files: List[Path] = sorted(p for p in resume_dir.glob('*.txt') 
                                     if p.is_file())
        if not txt_files:
            logging.error(f"No .txt files found directly in {resume_dir}")
            return "", ""

        resume_path: Path = txt_files[0]
        applicant_name: str = resume_path.stem.replace('_', ' ').replace('-', ' ')
        logging.debug(f"Found resume file: {resume_path} for applicant: {applicant_name}")
        return str(resume_path), applicant_name

    async def get_highlighted_sections(self) -> List[str]:
        resume_sections_content: Optional[str] = await file_utils.read_text_file(
            file_utils.RESUME_ADDITIONAL_FILES_DIR  / 'resume_sections.txt'
        )
        if not resume_sections_content:
            logging.error(f"No resume_sections file found in {file_utils.RESUME_ADDITIONAL_FILES_DIR}")
            return []
        return [line for line in resume_sections_content.splitlines() if line.strip()]
    
    async def get_job_description(self) -> str:
        file_path: Path = file_utils.RESUME_ADDITIONAL_FILES_DIR / 'job_description.txt'
        job_desc: str = await file_utils.read_text_file(file_path)
        if not job_desc:
            logging.error(f"No job description file found at {file_path}")
            return ""
        return job_desc
    
    async def get_cover_letter_guide_lines(self) -> str:
        file_path: Path = file_utils.RESUME_ADDITIONAL_FILES_DIR  / 'cover_letter_guidelines.txt'
        file_text: str = await file_utils.read_text_file(file_path)
        if not file_text:
            logging.error(f"No cover letter file found at {file_path}")
            return ""
        return file_text
    
    def _create_empty_resume_data(self) -> ResumeData:
        """Create empty ResumeData object"""
        return ResumeData(
            applicant_name="",
            general_guidelines="",
            resume="",
            resume_highlighted_sections=[],
            job_description="",
            cover_letter_guidelines=""
        )