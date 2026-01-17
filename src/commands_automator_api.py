import configparser, webview, logging, os
from typing import Any

from jobs_tracking.job_tracking_api import JobTrackingApi
from jobs_tracking.models import CompanyDto, TrackedJobDto

from llm.llm_api import LLMApi

from scripts_manager.scripts_manager_api import ScriptsManagerApi

from user.user_api import UserApi

from utils.file_utils import CONFIG_FILE


class CommandsAutomatorApi:

    def __init__(self, scripts_manager_api: ScriptsManagerApi, llm_api: LLMApi, user_api: UserApi, job_tracking_api: JobTrackingApi):
        self.scripts_manager_api = scripts_manager_api
        self.llm_api = llm_api
        self.user_api = user_api
        self.job_tracking_api = job_tracking_api
        self.config_path = str(CONFIG_FILE)
        self._config_cache = None
        
    def _load_config_once(self):
        """Load configuration once and cache it"""
        if self._config_cache is None:
            if not os.path.exists(self.config_path):
                self._config_cache = {}
            else:
                config = configparser.ConfigParser()
                config.read(self.config_path)
                self._config_cache = {}
                for section in config.sections():
                    self._config_cache[section] = dict(config[section])
        return self._config_cache
        
    def _invalidate_config_cache(self):
        """Invalidate config cache when config is saved"""
        self._config_cache = None
        

    def save_configuration(self, config_data, section):
        """Save unified configuration to commands_automator.config"""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path)
        
        if not config.has_section(section):
            config.add_section(section)
            
        for key, value in config_data.items():
            config.set(section, key, str(value))
            
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            config.write(f)
        
        # Invalidate cache after saving
        self._invalidate_config_cache()
            
    def get_configuration(self):
        """Load unified configuration from commands_automator.config"""
        return self._load_config_once()


    def load_scripts(self):
        return self.scripts_manager_api.load_scripts()
        
    def get_script_description(self, script_name):
        return self.scripts_manager_api.get_script_description(script_name)
        
        
    def execute_script(self, script_name, additional_text, flags):
        return self.scripts_manager_api.execute_script(script_name, additional_text, flags)


        
    def call_llm(self, prompt: str, image_data: str, output_file_path: str, user_id:str = None):
        return self.llm_api.call_llm(prompt, image_data, output_file_path, user_id)
    
    def cancel_llm_operation(self):
        self.llm_api.cancel_operation()
    
    
    def select_folder(self):
        if not webview.windows:
            logging.error("No webview windows available")
            return None
        return webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
    
        
    def login_or_register(self, email:str):
        if self.user_api is None:
            return {"error": "User API not available - MongoDB configuration missing"}
        return self.user_api.login_or_register(email)
    

    def get_job_application_states(self):
        """Get list of job application states"""
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        return self.job_tracking_api.get_job_application_states()
    
    def track_new_job(self, user_id: str, company_name: str, job_dto_dict: dict) -> dict[str, Any]:
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}        
        
        job_dto = TrackedJobDto(**job_dto_dict)
        return self.job_tracking_api.track_job(user_id=user_id, company_name=company_name, job_dto=job_dto)
    
    def track_existing_job(self, user_id: str, company_id: str, job_dto_dict: dict) -> dict[str, Any]:
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}        
        
        job_dto = TrackedJobDto(**job_dto_dict)
        return self.job_tracking_api.track_existing_job(user_id=user_id, company_id=company_id, job_dto=job_dto)
      
    def get_tracked_jobs(self, user_id: str, company_name: str) -> list[dict] | dict:
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        return self.job_tracking_api.get_tracked_jobs(user_id, company_name)
            
    def extract_job_title_and_company(self, url:str):
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        return self.job_tracking_api.extract_job_title_and_company(url)
        
    def delete_tracked_jobs(self, user_id: str, companies_jobs: list[dict[str, list[dict]]]):
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        companies = [CompanyDto(**item) for item in companies_jobs]
        return self.job_tracking_api.delete_tracked_jobs(user_id, companies)