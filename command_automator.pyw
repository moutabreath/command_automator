import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
import threading
import aiofiles
import webview
from logic_handler import LogicHandler

# logging.basicConfig(level=logging.DEBUG)

class CommandsAutomatorApi:
    def __init__(self):
        self.logic_handler = LogicHandler()
        self.config_path = "config/commands-executor-config.json"
    
        self.loop = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._setup_event_loop()
    
    def _setup_event_loop(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()

        while self.loop is None:
            threading.Event().wait(0.01)

    def load_scripts(self):
        return self.logic_handler.load_scripts()

    def get_script_description(self, script_name):
        script_file = self.logic_handler.get_name_to_scripts()[script_name]
        return self.logic_handler.get_script_description(script_file)
    
    def load_configuration(self):
        return self.run_async_method(self.load_configuration_async)

    def save_configuration(self, config):
        return self.run_async_method(self.save_configuration_async, config)

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
        
    async def load_configuration_async(self):
        async with aiofiles.open(self.config_path, "r") as f:
            data = await f.read()
        return json.loads(data)

    async def save_configuration_async(self, config):
        async with aiofiles.open(self.config_path, "w") as f:
            await f.write(json.dumps(config, indent=4))
        
        return True

    def execute_script(self, script_name, additional_text, flags):
        return self.logic_handler.execute_script(script_name, additional_text, flags)
    

if __name__ == '__main__':
    api = CommandsAutomatorApi()
    window = webview.create_window(
        'Commands Automator',
        'resources/commands_automator.html',
        js_api=api,
        width=1000,
        height=800
    )
    webview.start(debug=True)