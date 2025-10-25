import asyncio
import logging
import webview
import sys
import base64

from commands_automator.llm.llm_agents.mcp_client import MCPResponseCode
from commands_automator.llm.mcp_servers.job_applicant_mcp import MCPRunner
from commands_automator.scripts_manager.scripts_manager_service import ScriptsManagerService
from commands_automator.services.configuration_service import ConfigurationService
from commands_automator.llm.llm_service import LLMService
from commands_automator.utils.file_utils import LLM_CONFIG_DIR, SCRIPTS_MANAGER_CONFIG_FILE
from commands_automator.utils.logger_config import setup_logging

class CommandsAutomatorApi:
    def __init__(self):
        self.commands_automator_service = ScriptsManagerService()
        self.llm_service: LLMService = LLMService()
        self.commands_automator_config = ConfigurationService(SCRIPTS_MANAGER_CONFIG_FILE)
        self.llm_config = ConfigurationService(LLM_CONFIG_DIR)

    def load_scripts(self):
        return self.commands_automator_service.load_scripts()

    def get_script_description(self, script_name):
        script_file = self.commands_automator_service.get_name_to_scripts()[script_name]
        return self.commands_automator_service.get_script_description(script_file)
    
    def load_commands_configuration(self):
        return self.run_async_method(self.commands_automator_config.load_configuration_async)

    def save_commands_configuration(self, config):
        return self.run_async_method(self.commands_automator_config.save_configuration_async, config)

    def run_async_method(self, async_method, *args, **kwargs):
        try:
            return asyncio.run(async_method(*args, **kwargs))
        except Exception as e:
            logging.error(f"Error running async method {e}", exc_info=True)
            return "error"
   

    def execute_script(self, script_name, additional_text, flags):
        return self.commands_automator_service.execute_script(script_name, additional_text, flags)

    def call_llm(self, prompt: str, image_data: str, output_file_path: str):
        decoded_data = None
        if image_data and image_data != '':
            try:
                _, encoded = image_data.split(',', 1)
                decoded_data = base64.b64decode(encoded)
            except Exception as e:
                logging.error(f"Error processing image data: {e}", exc_info=True)
        result = self.run_async_method(self.llm_service.chat_with_bot, prompt, decoded_data, output_file_path)

        if result.code == MCPResponseCode.OK:
            return result.text
        return "error"

    def load_llm_configuration(self):
        return self.run_async_method(self.llm_config.load_configuration_async)

    def save_llm_configuration(self, config):
        return self.run_async_method(self.llm_config.save_configuration_async, config)
	

    def select_folder(self):
        return webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)


def main():
    try:
        setup_logging()  # Set up logging at the application entry point
        logging.info("Starting Commands Automator application...")
        
        # Initialize MCP Runner
        mcp_runner = MCPRunner()
        try:
            mcp_runner.init_mcp()
            logging.info("MCP Runner initialized successfully")
        except Exception as ex:
            logging.error(f"Failed to initialize MCP Runner: {ex}", exc_info=True)
            raise
        
        # Initialize API and create window
        api = CommandsAutomatorApi()
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