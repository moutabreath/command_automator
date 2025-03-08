import logging
import os
from typing import List
import re

from tabs.llm.file_stylers import docx_styler
from tabs.llm.llm_agents.gemini_agent import GeminiAgent
from tabs.llm.llm_agents.gpt_agent import GptAgent

class LLMLogicHanlder():

    CURRENT_PATH = '/tabs/llm'
    RESUME_FILES_PATH_PREFIX = f'{os.getcwd()}/{CURRENT_PATH}/resources/resume'
    OUTPUT_RESUME_PATH_PREFIX = f'{RESUME_FILES_PATH_PREFIX}/tailored_resume'
    CONFIG_PATH_PREFIX = f'{os.getcwd()}/{CURRENT_PATH}/config'

    def __init__(self):
        self.gemini_agent = None
        self.gpt_agent = None
        self.init_llm_agents()

    def init_llm_agents(self):        
        llm_agents_keys = self.get_keys()
        self.gemini_agent = GeminiAgent(llm_agents_keys[GeminiAgent.API_KEY_NAME])
        self.gpt_agent = GptAgent(llm_agents_keys[GptAgent.API_KEY_NAME])      

    def get_keys(self):
        with open(f'{self.CONFIG_PATH_PREFIX}/chat_bot_keys.txt', 'r') as file:
            agent_keys = {}
            for line in file:
                key_line_parts = line.split("=")
                agent_keys[key_line_parts[0]] = key_line_parts[1]
            return agent_keys


    def start_resume_building(self, applicant_name_value: str, resume_path: str, job_desc_path: str):
        guide_lines = self.get_guide_lines(applicant_name_value)
        resume = self.read_file(resume_path)
        prompt = f"{guide_lines} \n\n my resume:\n "
        prompt += resume
        success, resume_response = self.gemini_agent.chat_with_gemini(prompt)
        if (not(success)):
            logging.log("Error sending resume", resume_response)
            return "Something went wrong"
        prompt = "Here are the job descriptions\n"
        job_desc__content = self.read_file(job_desc_path)
        if (job_desc__content == ""):
            logging.log("Error reading job descriptions")
            return "Something went wrong"        
        prompt += job_desc__content
        success, jobs_desc_response = self.gemini_agent.chat_with_gemini(prompt)
        if (not(success)):
            logging.log("Error sending job descriptions", jobs_desc_response)
            return "Something went wrong"
        self.get_tesullt_to_save(applicant_name_value, jobs_desc_response)
        return jobs_desc_response

    
    def get_tesullt_to_save(self, applicant_name, text):
        pattern = re.compile(f"{applicant_name}.*", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            self.save_to_file(applicant_name, match, text)
        else:
            text = self.gemini_agent.chat_with_gemini("I want you to give me the resume as per the "
            "previous guidelines, not the job description")
            self.save_to_file(applicant_name,  pattern.search(text), text)

    def save_to_file(self, applicant_name, match, text):
        full_string = match.group()
        logging.log(logging.DEBUG, f"found full string {full_string}")    
        docx_styler.save_resume_as_word(f'{self.OUTPUT_RESUME_PATH_PREFIX}/{full_string}', applicant_name, text)

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
            with open(file_path, 'r') as file:               
                line = file.readline()                
                while line:
                    content += line
                    line = file.readline()
        except UnicodeDecodeError as e:
            logging.log(logging.ERROR,"Error reading resume file: UnicodeDecodeError", e)
            return ""
        except IOError as e:
            logging.log(logging.ERROR,"Error reading resume file", e)
            return ""
        
        return content
        
    def get_guide_lines(self, applicant_name):
        file_path = f'{self.RESUME_FILES_PATH_PREFIX}/guidelines.txt'    
        file_text = self.read_file(file_path)
        guide_lines = file_text.replace('***applicant_name***', applicant_name)
        return guide_lines