import logging
import os
from dotenv import load_dotenv
import configparser


from jobs_tracking.job_tracking_api import JobTrackingApi
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
        

    def save_config(self, config_data):
        """Save unified configuration to commands_automator.config"""
        config = configparser.ConfigParser()
        
        # Parse the config_data and write to sections
        for section, values in config_data.items():
            config[section] = values
            
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            config.write(f)
            
    def load_config(self):
        """Load unified configuration from commands_automator.config"""
        if not os.path.exists(self.config_path):
            return {}
            
        config = configparser.ConfigParser()
        config.read(self.config_path)
        
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        return result


    def load_scripts(self):
        return self.scripts_manager_api.load_scripts()
        
    def get_script_description(self, script_name):
        return self.scripts_manager_api.get_script_description(script_name)
        
    def load_commands_configuration(self):
        """Load commands configuration from unified config"""
        config = self.load_config()
        return config.get('scripts_manager', {})

    def save_commands_configuration(self, config):
        """Save commands configuration to unified config"""
        full_config = self.load_config()
        full_config['scripts_manager'] = config
        self.save_config(full_config)
        
    def execute_script(self, script_name, additional_text, flags):
        return self.scripts_manager_api.execute_script(script_name, additional_text, flags)


        
    def call_llm(self, prompt: str, image_data: str, output_file_path: str, user_id:str = None):
        return self.llm_api.call_llm(prompt, image_data, output_file_path, user_id)
    
    def load_llm_configuration(self):
        """Load LLM configuration from unified config"""
        config = self.load_config()
        return config.get('llm', {})

    def save_llm_configuration(self, config):
        """Save LLM configuration to unified config"""
        full_config = self.load_config()
        full_config['llm'] = config
        self.save_config(full_config)
    
    def select_folder(self):
        if not webview.windows:
            logging.error("No webview windows available")
            return None
        return webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
    
    
    def load_user_config(self):
        """Load user configuration from unified config"""
        if self.user_api is None:
            return {"error": "User API not available - MongoDB configuration missing"}
        config = self.load_config()
        return config.get('user', {})
    
    def login_or_register(self, email:str):
        if self.user_api is None:
            return {"error": "User API not available - MongoDB configuration missing"}
        return self.user_api.login_or_register(email)
    

    def load_job_tracking_configuration(self):
        """Load job tracking configuration from unified config"""
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        config = self.load_config()
        return config.get('job_tracking', {})
    
    def save_job_tracking_configuration(self, config):
        """Save job tracking configuration to unified config"""
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        full_config = self.load_config()
        full_config['job_tracking'] = config
        self.save_config(full_config)
    
    
    def get_job_application_states(self):
        """Get list of job application states"""
        return self.job_tracking_api.get_job_application_states()
    
    def track_job_application(self, user_id:str, company_name:str, job_url:str, job_title:str, state:str,
                              contact_name:str, contact_linkedin:str, contact_email:str):
        if self.job_tracking_api is None:
            return {"error": "Job Tracking API not available - MongoDB configuration missing"}
        return self.job_tracking_api.add_job_to_company(user_id, company_name, job_url, job_title, state,
                                                         contact_name, contact_linkedin, contact_email)


async def initialize_apis():
    """Initialize all APIs"""

    scripts_manager_api = ScriptsManagerApi()
    
    llm_service = LLMService()
    llm_service.run_mcp_server()
    llm_api = LLMApi(llm_service)

    user_api = None
    job_tracking_api = None

    load_dotenv('.env.local')
    
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
        logging.error(f"Fatal error in main: {ex}", exc_info=True)
        raise

if __name__ == '__main__':
    if sys.platform == "win32":
        import multiprocessing
        multiprocessing.freeze_support()
    main()