import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import multiprocessing
import threading
import webview

from services.commands_automator_service import CommandsAutomatorService
from services.configuration_service import ConfigurationService
from services.llm_service import LLMService
from llm.mcp_servers.resume_mcp import run_mcp

# logging.basicConfig(level=logging.DEBUG)

class CommandsAutomatorApi:

    llm_sevice: LLMService = LLMService()
    
    def __init__(self):
        self.commands_automator_service = CommandsAutomatorService()
        self.commands_automator_config = ConfigurationService("config/commands-executor-config.json")
        self.llm_config = ConfigurationService('config/llm-config.json')
        self.loop = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.setup_event_loop()
    
    def setup_event_loop(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()

        while self.loop is None:
            threading.Event().wait(0.01)

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
            if self.loop and self.loop.is_running():
                # If loop is running in another thread, use asyncio.run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(
                    async_method(*args, **kwargs), 
                    self.loop
                )
                return future.result(timeout=30)  # 30 second timeout
            else:
                # If no loop or loop not running, create new one
                return asyncio.run(async_method(*args, **kwargs))
        except Exception as e:
            logging.error(f"Error running async method: {e}")
            return {"error": str(e)}
   

    def execute_script(self, script_name, additional_text, flags):
        return self.commands_automator_service.execute_script(script_name, additional_text, flags)    


    def call_llm(self, prompt):
        return self.run_async_method(self.llm_sevice.chat_with_bot, prompt)
    
    def load_llm_configuration(self):
        return self.run_async_method(self.llm_config.load_configuration_async)

    def save_llm_configuration(self, config):
        return self.run_async_method(self.llm_config.save_configuration_async, config)


    def select_folder(self):
        # Opens a native folder dialog and returns the selected folder path as a list
        return webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
    
    def init_mcp(self):
        self.mcp_process = multiprocessing.Process(target=run_mcp)
        self.mcp_process.start()
        
    def __del__(self):
        """Cleanup method to terminate the MCP process when the agent is destroyed"""
        if hasattr(self, 'mcp_process') and self.mcp_process.is_alive():
            self.mcp_process.terminate()
            self.mcp_process.join()



if __name__ == '__main__':   
    api = CommandsAutomatorApi()
    api.init_mcp()
    window = webview.create_window(
        'Commands Automator',
        'ui/commands_automator.html',
        js_api=api,
        width=1000,
        height=800
    )
    webview.start(debug=True)