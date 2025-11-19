import logging
import api_utils
from llm_api import LLMApi
import webview
import sys

from llm.mcp_servers.job_applicant_mcp import MCPRunner
from scripts_manager.scripts_manager_service import ScriptsManagerService
from services.configuration_service import ConfigurationService
from utils.file_utils import SCRIPTS_MANAGER_CONFIG_FILE
from utils.logger_config import setup_logging

class CommandsAutomatorApi:
    def __init__(self, llm_api: LLMApi):
        self.commands_automator_service = ScriptsManagerService()
        self.commands_automator_config = ConfigurationService(SCRIPTS_MANAGER_CONFIG_FILE)
        self.llm_api = llm_api

    def load_scripts(self):
        try:
            return self.commands_automator_service.load_scripts()
        except Exception as e:
            logging.error(f"Error loading scripts: {e}", exc_info=True)
            return []
        
    def get_script_description(self, script_name):
        try:
            name_to_scripts = self.commands_automator_service.get_name_to_scripts()
            if script_name not in name_to_scripts:
                logging.error(f"Script not found: {script_name}")
                return ""
            script_file = name_to_scripts[script_name]
            return self.commands_automator_service.get_script_description(script_file)
        except Exception as e:
            logging.error(f"Error getting script description for {script_name}: {e}", exc_info=True)
            return ""
        
    def load_commands_configuration(self):
        """Load and serialize commands configuration"""
        try:
            config = api_utils.run_async_method(self.commands_automator_config.load_configuration_async)
            if isinstance(config, dict):
                return config
            return {}
        except Exception as e:
            logging.error(f"Error loading commands configuration: {e}", exc_info=True)
            return {}

    def save_commands_configuration(self, config):
        """Save commands configuration after ensuring it's serializable"""
        try:
            if not isinstance(config, dict):
                logging.error("Invalid configuration format")
                return False
            result = api_utils.run_async_method(self.commands_automator_config.save_configuration_async, config)
            return result if isinstance(result, bool) else False
        except Exception as e:
            logging.error(f"Error saving commands configuration: {e}", exc_info=True)
            return False 
        
    def execute_script(self, script_name, additional_text, flags):
        try:
            return self.commands_automator_service.execute_script(script_name, additional_text, flags)
        except Exception as e:
            logging.error(f"Error executing script {script_name}: {e}", exc_info=True)
            return None
        
    def call_llm(self, prompt: str, image_data: str, output_file_path: str):
        return self.llm_api.call_llm(prompt, image_data, output_file_path)
    
    def load_llm_configuration(self):
       return self.llm_api.load_llm_configuration()

    def save_llm_configuration(self, config):
        return self.llm_api.save_llm_configuration(config)	

    def select_folder(self):
        try:
            if not webview.windows:
                logging.error("No webview windows available")
                return None
            return webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        except Exception as e:
            logging.error(f"Error selecting folder: {e}", exc_info=True)
            return None
        
def main():
    try:
        setup_logging()  # Set up logging at the application entry point
        logging.info("Starting Commands Automator application...")
        
        lLMApi = LLMApi()
        lLMApi.run_mcp_server()
        
        # Initialize API and create window
        api = CommandsAutomatorApi(lLMApi)
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