import logging
from jobs_tracking.job_tracking_api import JobTrackingApi
from llm.llm_api import LLMApi
from scripts_manager.scripts_manager_api import ScriptsManagerApi
from user.user_api import UserApi
import webview
import sys

from utils.logger_config import setup_logging

class CommandsAutomatorApi:

    def __init__(self, scripts_manager_api: ScriptsManagerApi, llm_api: LLMApi, user_api: UserApi, job_tracking_api: JobTrackingApi):
        self.scripts_manager_api = scripts_manager_api
        self.llm_api = llm_api
        self.user_api = user_api
        self.job_tracking_api = job_tracking_api        

    def load_scripts(self):
        return self.scripts_manager_api.load_scripts()
        
    def get_script_description(self, script_name):
        return self.scripts_manager_api.get_script_description(script_name)
        
    def load_commands_configuration(self):
        """Load and serialize commands configuration"""
        return self.scripts_manager_api.load_configuration()

    def save_commands_configuration(self, config):
        """Save commands configuration after ensuring it's serializable"""
        return self.scripts_manager_api.save_configuration(config)
        
    def execute_script(self, script_name, additional_text, flags):
        return self.scripts_manager_api.execute_script(script_name, additional_text, flags)


        
    def call_llm(self, prompt: str, image_data: str, output_file_path: str, user_id:str = None):
        return self.llm_api.call_llm(prompt, image_data, output_file_path, user_id)
    
    def load_llm_configuration(self):
       return self.llm_api.load_configuration()

    def save_llm_configuration(self, config):
        return self.llm_api.save_configuration(config)
    
    def select_folder(self):
        if not webview.windows:
            logging.error("No webview windows available")
            return None
        return webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
    
    
    def load_user_config(self):
        return self.user_api.load_configuration()
    
    def login_or_register(self, email:str):
        return self.user_api.login_or_register(email)
    

    def load_job_tracking_configuration(self):
        return self.job_tracking_api.load_configuration()
    
    def save_job_tracking_configuration(self, config):
        return self.job_tracking_api.save_configuration(config)
    
    
    def get_job_application_states(self):
        """Get list of job application states"""
        return self.job_tracking_api.get_job_application_states()
    
    def track_job_application(self, user_id:str, company_name:str, job_url:str, job_title:str, state:str , contact:str):
        return self.job_tracking_api.add_job_to_company(user_id, company_name, job_url, job_title, state, contact)
    

def main():
    try:
        setup_logging()  # Set up logging at the application entry point
        logging.info("Starting Commands Automator application...")

        scripts_manager_api = ScriptsManagerApi()
        
        llm_api = LLMApi()
        llm_api.run_mcp_server()

        user_api = UserApi()
        
        job_tracking_api = JobTrackingApi()
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
        webview.start(icon='ui/resources/Commands_Automator.ico', debug=True)
    except Exception as ex:
        logging.error(f"Fatal error in main: {ex}", exc_info=True)
        raise

if __name__ == '__main__':
    if sys.platform == "win32":
        import multiprocessing
        multiprocessing.freeze_support()
    main()