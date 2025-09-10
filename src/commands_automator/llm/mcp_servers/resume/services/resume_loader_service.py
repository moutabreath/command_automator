import logging
import os
import aiofiles
import os
from pathlib import Path

class ResumeLoaderService:
    # Resolve the path to …/mcp_servers/resume
    BASE_DIR = Path(__file__).resolve().parents[1]  # …/resume
    RESOURCES_DIR = BASE_DIR / "resources"
    ADDITIONAL_FILE_PATH_PREFIX = RESOURCES_DIR / "additional_files"

    async def get_main_part_guide_lines(self):
        file_path = self.ADDITIONAL_FILE_PATH_PREFIX / 'guidelines.txt'     
        file_text = await self.read_file(file_path)      
        return file_text

    async def get_resume_and_applicant_name(self):
        resume_path, applicant_name = self.find_resume_file()
        if resume_path is None or not resume_path:
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
        if resume_sections_content is None:
            logging.error(f"No resume_sections file found in {self.ADDITIONAL_FILE_PATH_PREFIX}")
            return None 
        return resume_sections_content.split('\n')
    
    async def get_job_description(self):
        job_desc = await self.read_file(f'{self.ADDITIONAL_FILE_PATH_PREFIX}/job_description.txt')
        if job_desc is None:
            logging.error(f"No job description file found in {self.ADDITIONAL_FILE_PATH_PREFIX}")
            return None
        return job_desc
    
   
    async def get_cover_letter_guide_lines(self):
        file_path = f'{self.ADDITIONAL_FILE_PATH_PREFIX}/cover_letter_guidelines.txt'  
        file_text = await self.read_file(file_path)
        if file_text is None:
            logging.error(f"No cover letter file found in {self.ADDITIONAL_FILE_PATH_PREFIX}")
            return None
        return file_text
    
    async def read_file(self, file_path):
        content = ""
        try:
            async with aiofiles.open(file_path, 'r', encoding="utf8") as file:
                content = await file.read()
        except UnicodeDecodeError as e:
            logging.error(f"Error reading file: {file_path} {e}", exc_info=True)
        except IOError as ioError:
            logging.error(f"Error reading file: {file_path} - {ioError}", exc_info=True)  
        return content
        