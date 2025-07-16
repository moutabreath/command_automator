import asyncio
import logging
import webview
import logging.handlers
import os
import sys

from llm.mcp_servers.resume_mcp import MCPRunner
from services.commands_automator_service import CommandsAutomatorService
from services.configuration_service import ConfigurationService
from services.llm_service import LLMService

class CommandsAutomatorApi:
    def __init__(self):
        self.commands_automator_service = CommandsAutomatorService()
        self.llm_sevice: LLMService = LLMService()
        self.commands_automator_config = ConfigurationService("config/commands-executor-config.json")
        self.llm_config = ConfigurationService('llm/config/llm-config.json')

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
            logging.error(f"Error running async method", exc_info=True)
            return "error"
   

    def execute_script(self, script_name, additional_text, flags):
        return self.commands_automator_service.execute_script(script_name, additional_text, flags)

    def call_llm(self, prompt: str, image_path: str, should_save_files: bool, output_file_path: str):
        return self.run_async_method(self.llm_sevice.chat_with_bot, prompt, image_path, should_save_files, output_file_path)
    
    def load_llm_configuration(self):
        return self.run_async_method(self.llm_config.load_configuration_async)

    def save_llm_configuration(self, config):
        return self.run_async_method(self.llm_config.save_configuration_async, config)
	

    def select_folder(self):
        # Opens a native folder dialog and returns the selected folder path as a list
        return webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)

    def init_logger(self):
        handler = logging.handlers.WatchedFileHandler(
        os.environ.get("LOGFILE", "commands_automator.log"))
        formatter =logging.Formatter("%(asctime)s:%(name)s:%(levelname)s {%(module)s %(funcName)s}:%(message)s")
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", "DEBUG"))
        root.addHandler(handler)


def main():
    mcp_runner = MCPRunner()
    mcp_runner.init_mcp()
    api = CommandsAutomatorApi()
    window = webview.create_window(
        'Commands Automator',
        'ui/commands_automator.html',
        js_api=api,
        width=1000,
        height=800
    )
    webview.start(icon='ui/resources/Commands_Automator.ico')

if __name__ == '__main__':
    # Multiprocessing freeze support for onefile builds on Windows
    if sys.platform == "win32":
        import multiprocessing
        multiprocessing.freeze_support()
    main()