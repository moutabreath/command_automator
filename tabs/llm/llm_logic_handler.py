import glob
import logging
import os
from typing import List
import re

from tabs.llm.file_stylers import docx_styler
from tabs.llm.llm_agents.gemini.gemini_agent import GeminiAgent
from tabs.llm.llm_agents.gpt.gpt_agent import GptAgent

class LLMLogicHanlder():

    CURRENT_PATH = '/tabs/llm'
    LLM_RESOURCES = f'{os.getcwd()}/{CURRENT_PATH}/resources'
    RESUME_FILES_PATH_PREFIX = f'{LLM_RESOURCES}/resume'
    OUTPUT_RESUME_PATH_PREFIX = f'{LLM_RESOURCES}/tailored_resume'
    CONFIG_PATH_PREFIX = f'{os.getcwd()}/{CURRENT_PATH}/config'
    resume_file_name = "Missing"

    def __init__(self):
        self.gemini_agent = None
        self.gpt_agent = None
        self.init_llm_agents()

    def init_llm_agents(self):        
        llm_agents_keys = self.get_keys()
        self.gemini_agent = GeminiAgent(llm_agents_keys[GeminiAgent.API_KEY_NAME])
        self.gpt_agent = GptAgent(llm_agents_keys[GptAgent.API_KEY_NAME])      

    def get_keys(self):
        files = glob.glob(os.getcwd() + '/**/chat_bot_keys.txt', recursive=True)
        with open(files[0], 'r') as file:
            agent_keys = {}
            for line in file:
                key_line_parts = line.split("=")
                agent_keys[key_line_parts[0]] = key_line_parts[1]
            return agent_keys
         # Return the first match
        return None
        
    def chat_using_guidelines(self, applicant_name: str, resume_path: str, job_desc_path: str, output_path: str, should_save_as_file):
        guide_lines = self.get_main_part_guide_lines(applicant_name)
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

    def get_highlighted_sections(self):
         resume_setctions_content = self.read_file(f'{self.RESUME_FILES_PATH_PREFIX}/resume_sections.txt')
         return resume_setctions_content.split('\n')
    

    def analyze_from_links(self, links_text):
        links = self.get_links(links_text)
        response = ""
        for link in links:    
            text = self.gemini_agent.chat_with_gemini(link)
            response +=text

    def get_links(self, links_text) -> List[str]:
        links_array = links_text.split('\n')
        links = []
        for link_html in links_array:
            link = self.get_links_from_html(link_html)
            if link != '':
                links.append(link)
        return links
        

    
    def get_links_from_html(self,html_snippet):
        link_pattern = re.compile(r'HREF="([^"]+)"')
        match = link_pattern.search(html_snippet)

        if match:
            link = match.group(1)
            return link
        else:
            logging.log(logging.ERROR, f"couldn't find link in {html_snippet}")
            return ''
        
    
    def read_file(self, file_path):
        line = None
        content = ''
        try:
            with open(file_path, 'r', encoding="utf8") as file:               
                line = file.readline()                
                while line:
                    content += line
                    line = file.readline()
        except UnicodeDecodeError as e:
            logging.error("Error reading resume file: UnicodeDecodeError", exc_info=True)
            return ""
        except IOError as e:
            logging.error("Error reading resume file", exc_info=True)
            return ""
        
        return content
        
    def get_main_part_guide_lines(self, applicant_name):
        file_path = f'{self.RESUME_FILES_PATH_PREFIX}/guidelines.txt'    
        file_text = self.read_file(file_path)
        guide_lines = file_text.replace('***applicant_name***', applicant_name)
        return guide_lines
    
    def get_cover_letter_guide_lines(self):
        file_path = f'{self.RESUME_FILES_PATH_PREFIX}/cover_letter_guidelines.txt'  
        file_text = self.read_file(file_path)
        return file_text