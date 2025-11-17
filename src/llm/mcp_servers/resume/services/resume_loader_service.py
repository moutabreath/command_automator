import logging
import sys
from pathlib import Path
from typing import Tuple, List, Optional

from llm.mcp_servers.services.shared_service import SharedService
from utils import file_utils

class ResumeLoaderService(SharedService):
    def __init__(self):
        # Check if we're running in a PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            bundle_dir = Path(sys._MEIPASS)
            self.BASE_DIR: Path = bundle_dir / "llm" / "mcp_servers" / "resume"
        else:
            # Running in normal Python environment
            self.BASE_DIR: Path = Path(__file__).resolve().parents[1]  # …/resume
        
        self.RESOURCES_DIR: Path = self.BASE_DIR / "resources"
        self.ADDITIONAL_FILE_PATH_PREFIX: Path = self.RESOURCES_DIR / "additional_files"
        logging.info(f"Initialized ResumeLoaderService with BASE_DIR: {self.BASE_DIR}")

    async def get_main_part_guide_lines(self) -> str:
        file_path: Path = self.ADDITIONAL_FILE_PATH_PREFIX / 'guidelines.txt'     
        file_text: str = await file_utils.read_text_file(file_path)      
        if not file_text:
            logging.error(f"No guidelines file found at {file_path}")
            return ""
        return file_text
    
    async def get_resume_and_applicant_name(self) -> Tuple[str, str]:
        resume_path, applicant_name = self.find_resume_file()
        if not resume_path or not applicant_name:
            logging.error(f"No .txt resume file found in {self.RESOURCES_DIR}")
            return "", ""
        resume_text: str = await file_utils.read_text_file(resume_path)
        return resume_text, applicant_name
                
    def find_resume_file(self) -> Tuple[str, str]:
        resume_dir: Path = self.RESOURCES_DIR
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
            self.ADDITIONAL_FILE_PATH_PREFIX / 'resume_sections.txt'
        )
        if not resume_sections_content:
            logging.error(f"No resume_sections file found in {self.ADDITIONAL_FILE_PATH_PREFIX}")
            return []
        return [line for line in resume_sections_content.splitlines() if line.strip()]
    
    async def get_job_description(self) -> str:
        file_path: Path = self.ADDITIONAL_FILE_PATH_PREFIX / 'job_description.txt'
        job_desc: str = await file_utils.read_text_file(file_path)
        if not job_desc:
            logging.error(f"No job description file found at {file_path}")
            return ""
        return job_desc
    
    async def get_cover_letter_guide_lines(self) -> str:
        file_path: Path = self.ADDITIONAL_FILE_PATH_PREFIX / 'cover_letter_guidelines.txt'
        file_text: str = await file_utils.read_text_file(file_path)
        if not file_text:
            logging.error(f"No cover letter file found at {file_path}")
            return ""
        return file_text

