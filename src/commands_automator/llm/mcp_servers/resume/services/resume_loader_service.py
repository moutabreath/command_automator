import logging
import os
import sys
import aiofiles
from pathlib import Path

from commands_automator.llm.mcp_servers.services.shared_service import SharedService

class ResumeLoaderService(SharedService):
    def __init__(self):
        # Check if we're running in a PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            bundle_dir = Path(sys._MEIPASS)
            self.BASE_DIR = bundle_dir / "llm" / "mcp_servers" / "resume"
        else:
            # Running in normal Python environment
            self.BASE_DIR = Path(__file__).resolve().parents[1]  # …/resume
        
        self.RESOURCES_DIR = self.BASE_DIR / "resources"
        self.ADDITIONAL_FILE_PATH_PREFIX = self.RESOURCES_DIR / "additional_files"
        logging.info(f"Initialized ResumeLoaderService with BASE_DIR: {self.BASE_DIR}")

    async def get_main_part_guide_lines(self):
        file_path = self.ADDITIONAL_FILE_PATH_PREFIX / 'guidelines.txt'     
        file_text = await self.read_file(file_path)      
        return file_text

    async def get_resume_and_applicant_name(self):
        resume_path, applicant_name = self.find_resume_file()
        if not resume_path or not applicant_name:
            logging.error(f"No .txt resume file found in {self.RESOURCES_DIR}")
            return "", ""
        resume_text = await self.read_file(resume_path)
        return resume_text, applicant_name
    
    def find_resume_file(self):
        resume_dir = self.RESOURCES_DIR
        resume_path, applicant_name = "", ""
        if not resume_dir.exists():
            logging.error(f"Resumes directory not found: {resume_dir}")
            return resume_path, applicant_name
            
        for root, _, files in os.walk(self.RESOURCES_DIR):
            for file in files:
                if file.lower().endswith('.txt'):
                    resume_path = os.path.join(root, file)
                    applicant_name = file[0:len(file) - 4]
                    applicant_name = applicant_name.replace('_', ' ').replace('-', ' ')
                    return resume_path, applicant_name
        return resume_path, applicant_name
        

    async def get_highlighted_sections(self):
        resume_sections_content = await self.read_file(f'{self.ADDITIONAL_FILE_PATH_PREFIX}/resume_sections.txt')
        if not resume_sections_content:
            logging.error(f"No resume_sections file found in {self.ADDITIONAL_FILE_PATH_PREFIX}")
            return []
        return resume_sections_content.split('\n')
    
    async def get_job_description(self):
        job_desc = await self.read_file(f'{self.ADDITIONAL_FILE_PATH_PREFIX}/job_description.txt')
        if not job_desc:
            logging.error(f"No job description file found in {self.ADDITIONAL_FILE_PATH_PREFIX}")
            return ""
        return job_desc
    
   
    async def get_cover_letter_guide_lines(self):
        file_path = f'{self.ADDITIONAL_FILE_PATH_PREFIX}/cover_letter_guidelines.txt'  
        file_text = await self.read_file(file_path)
        if not file_text:
            logging.error(f"No cover letter file found in {self.ADDITIONAL_FILE_PATH_PREFIX}")
            return ""
        return file_text
    
    async def read_file(self, file_path):
        content = ""
        logging.info(f"Reading file: {file_path}")
        try:
            async with aiofiles.open(file_path, 'r', encoding="utf8") as file:
                content = await file.read()
        except UnicodeDecodeError as e:
            logging.error(f"Error reading file: {file_path} {e}", exc_info=True)
        except IOError as ioError:
            logging.error(f"Error reading file: {file_path} - {ioError}", exc_info=True)  
        return content
        