import logging
import os
from typing import Any, Dict, List
from dotenv import load_dotenv
import configparser


from jobs_tracking.job_tracking_api import JobTrackingApi
from jobs_tracking.models import TrackedJobDto
from jobs_tracking.services.job_tracking_service import JobTrackingService
from llm.llm_api import LLMApi
from llm.services.llm_service import LLMService
from scripts_manager.scripts_manager_api import ScriptsManagerApi
from user.services.user_registry_service import UserRegistryService
from user.user_api import UserApi
from utils import file_utils
from utils.utils import AsyncRunner
import webview
import sys

from utils.logger_config import setup_logging

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
    
    
    def select_folder(self):
        if not webview.windows:
            logging.error("No webview windows available")
            return None
        return webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
    
        
    def login_or_register(self, email:str):
        if self.user_api is None:
            return {"error": "User API not available - MongoDB configuration missing"}
        return self.user_api.login_or_register(email)
    

    def load_job_tracking_configuration(self):
        """Load job tracking configuration from unified config"""
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        config = self.get_configuration()
        return config.get('job_tracking', {})
    
    
    
    def get_job_application_states(self):
        """Get list of job application states"""
        return self.job_tracking_api.get_job_application_states()
    
    def track_job_application(self, user_id: str, company_name: str, job_dto_dict: Dict) -> Dict[str, Any]:
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        job_dto = TrackedJobDto(
             job_title=job_dto_dict['job_url'],
            job_url= job_dto_dict['job_title'],
            contact_linkedin=job_dto_dict['contact_linkedin'],
            contact_name=job_dto_dict['contact_name'],
            job_state=job_dto_dict['job_state'],
            contact_email=job_dto_dict['contact_email']
        )
        return self.job_tracking_api.track_job_application(user_id, company_name, job_dto)
    
    def get_positions(self, user_id: str, company_name: str) -> List[Dict]:
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        return self.job_tracking_api.get_positions(user_id, company_name)
    
    def track_job_application_from_text(self, user_id: str, text:str):
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        return self.job_tracking_api.track_job_application_from_text(user_id, text)


def load_environment():
    """Load environment variables from .env.local file"""
    try:
        # Try to load .env.local from current directory first (development)
        if os.path.exists('.env.local'):
            load_dotenv('.env.local')
        # For PyInstaller, try loading from the executable's directory
        elif hasattr(sys, '_MEIPASS'):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            env_path = os.path.join(os.path.dirname(sys.executable), '.env.local')
            if os.path.exists(env_path):
                load_dotenv(env_path)
        # Try APPDATA directory as fallback
        else:
            appdata_env = os.path.join(os.getenv('APPDATA', ''), 'commands_automator', '.env.local')
            if os.path.exists(appdata_env):
                load_dotenv(appdata_env)
    except Exception as e:
        logging.warning(f"Could not load .env.local file: {e}")

async def initialize_apis():
    """Initialize all APIs"""

    scripts_manager_api = ScriptsManagerApi()
    
    llm_service = LLMService()
    llm_service.run_mcp_server()
    llm_api = LLMApi(llm_service)

    user_api = None
    job_tracking_api = None

    load_environment()
    
    mongo_connection_string = os.getenv('MONGODB_URI')
    db_name = os.getenv('MONGODB_DB_NAME')
    
    if not db_name or not mongo_connection_string:
        logging.warning("MongoDB configuration not found in .env.local. Database-related features will be disabled.")
    else:
        try:
            user_registry_service = await UserRegistryService.create(mongo_connection_string=mongo_connection_string, db_name=db_name)
            user_api = UserApi(user_registry_service)

            job_tracking_service = await JobTrackingService.create(mongo_connection_string=mongo_connection_string, db_name=db_name)
            job_tracking_api = JobTrackingApi(job_tracking_service)
        except Exception as e:
            logging.error(f"Error initializing database APIs: {e}")

    return scripts_manager_api, llm_api, user_api, job_tracking_api

def main():
    try:
        setup_logging()  # Set up logging at the application entry point
        logging.info("Starting Commands Automator application...")

        AsyncRunner.start()

        scripts_manager_api, llm_api, user_api, job_tracking_api = AsyncRunner.run_async(initialize_apis())
        # Initialize API and create window
        api = CommandsAutomatorApi(scripts_manager_api, llm_api, user_api, job_tracking_api)
        window = webview.create_window(
            'Commands Automator',
            'ui/commands_automator.html',
            js_api=api,
            width=1000,
            height=800
        )
        
        logging.info("Starting webview...")
        webview.start(icon='ui/resources/Commands_Automator.ico')
    except Exception as ex:
        logging.exception(f"Fatal error in main: {ex}")
        raise

if __name__ == '__main__':
    if sys.platform == "win32":
        import multiprocessing
        multiprocessing.freeze_support()
    main()