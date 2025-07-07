import logging
import os
import re
import aiofiles

from tabs.llm.file_stylers import docx_styler


class ResumeLoaderService:
    CURRENT_PATH = '/tabs/llm'
    LLM_RESOURCES = f'{os.getcwd()}/{CURRENT_PATH}/resources'
    RESUME_FILES_PATH_PREFIX = f'{LLM_RESOURCES}/resume'
    ADDITIONAl_FILE_PATH_PREFIX = f'{RESUME_FILES_PATH_PREFIX}/addtional_files'
    resume_file_name = "Missing"



    def chat_using_guidelines(self, applicant_name: str, resume_path: str, job_desc_path: str, output_path: str, should_save_as_file):
        guide_lines = self.get_main_part_guide_lines(applicant_name)
        guide_lines = guide_lines.replace('***applicant_name***', applicant_name)
        logging.debug(f"guide_lines: {guide_lines}")
        highlighted_sections = self.get_highlighted_sections()
        main_part = self.read_file(resume_path)        
        prompt = f"{guide_lines}\n\n{main_part}\n\n\n"
        job_desc_content = self.read_file(job_desc_path)
        second_part = "" 
        if job_desc_content != "":        
            prompt += job_desc_content
        success, reponse = self.gemini_agent.chat_with_gemini(prompt)
        if not(success):
            logging.error("Error sending resume", reponse)
            return ""
        if (should_save_as_file):
            self.save_main_results(applicant_name, reponse, output_path, highlighted_sections)

        cover_letter_guide_lines = self.get_cover_letter_guide_lines()
        success, second_part = self.gemini_agent.chat_with_gemini(cover_letter_guide_lines)
        if (should_save_as_file):
            docx_styler.save_text_as_word(f'{output_path}/{self.resume_file_name}_Cover_Letter.docx', applicant_name, second_part)
        return f'{reponse}\n\n\n{second_part}'


    def save_main_results(self, applicant_name, text, output_path, resume_sections):
        pattern = re.compile(f"{applicant_name}[^ \n]*", re.IGNORECASE)
        match = pattern.search(text)
        try:
            if match:
                self.resume_file_name = match.group()
                logging.log(logging.DEBUG, f"found full string {self.resume_file_name}")    
                docx_styler.save_text_as_word(f'{output_path}/{self.resume_file_name}.docx', applicant_name, text, resume_sections)
        except Exception:
            logging.error("Error saving resume", exc_info=True)

    
    async def get_main_part_guide_lines(self):
        file_path = f'{self.ADDITIONAl_FILE_PATH_PREFIX}/guidelines.txt'    
        file_text = await self.read_file(file_path)      
        return file_text

    async def get_resume(self):
        resume_path, applicant_name = self.find_resume_file()
        if resume_path == None:
            logging.error(f"No .txt resume file found in {self.RESUME_FILES_PATH_PREFIX}")
            return None 
        resume = await self.read_file(resume_path)
        return resume, applicant_name
    
    def find_resume_file(self):
        for root, dirs, files in os.walk(self.RESUME_FILES_PATH_PREFIX):
            for file in files:
                if file.lower().endswith('.txt'):
                    resume_path = os.path.join(root, file)
                    applicant_name = file[0:len(file) - 4]
                    applicant_name = applicant_name.replace('_', ' ').replace('-', ' ')
                    return resume_path, applicant_name
        return None
        

    async def get_highlighted_sections(self):
        resume_setctions_content = await self.read_file(f'{self.ADDITIONAl_FILE_PATH_PREFIX}/resume_sections.txt')
        if resume_setctions_content == None:
            logging.error(f"No resume_sections file found in {self.ADDITIONAl_FILE_PATH_PREFIX}")
            return None 
        return resume_setctions_content.split('\n')
    
    async def get_job_description(self):
        job_desc = await self.read_file(f'{self.ADDITIONAl_FILE_PATH_PREFIX}/job_description.txt')
        if job_desc == None:
            logging.error(f"No job description file found in {self.ADDITIONAl_FILE_PATH_PREFIX}")
            return None
        return job_desc
    
   
    async def get_cover_letter_guide_lines(self):
        file_path = f'{self.ADDITIONAl_FILE_PATH_PREFIX}/cover_letter_guidelines.txt'  
        file_text = await self.read_file(file_path)
        if file_text == None:
            logging.error(f"No cover letter file found in {self.ADDITIONAl_FILE_PATH_PREFIX}")
            return None
        return file_text
    
    async def read_file(self, file_path):
        line = None
        content = ''
        try:
            async with aiofiles.open(file_path, 'r', encoding="utf8") as file:           
                line = await file.readline()                
                while line:
                    content += line
                    line = await file.readline()
        except UnicodeDecodeError as e:
            logging.error(f"Error reading file: {file_path}", exc_info=True)
            return None
        except IOError as e:
            logging.error(f"Error reading file: {file_path}", exc_info=True)
            return None
        return content
        