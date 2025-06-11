import asyncio
import json
import logging
import os
import aiofiles

from tabs.llm.llm_logic_handler import LLMLogicHanlder

class LLMPromptApi:
    CONFIG_FILE_PATH = os.path.join(os.getcwd(), "tabs/llm/llm-config.json")
    MAIN_FILE_PATH = 'main_file_path' 
    SECONDARY_FILE_PATH = 'secondary_file_dir'
    APPLICANT_NAME_TAG = 'applicant_name'
    applicant_name_value = ''
    SEND_QUERY_KEYBOARD_SHORTCUT = 'enter'
    OUTPUT_RESUME_DIR_PATH = "output_resume_path"
    SAVE_RESULTS_TO_FILE = "save_results_to_file"
    lLLMLogicHanlder: LLMLogicHanlder = LLMLogicHanlder()

    async def load_configuration(self):
        if not os.path.exists(self.CONFIG_FILE_PATH):
            return {}
        async with aiofiles.open(self.CONFIG_FILE_PATH, "r") as f:
            data = await f.read()
        return json.loads(data)

    async def save_configuration(self, config):
        async with aiofiles.open(self.CONFIG_FILE_PATH, "w") as f:
            await f.write(json.dumps(config, indent=4))
        return True
    
    def call_llm(self, query):
    # Implement your LLM logic here, or call your existing handler
    # For demonstration, just echo the query
        return "trial"
    
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
    
import webview

if __name__ == '__main__':
    api = LLMPromptApi()
    window = webview.create_window(
        'LLM Prompt',
        'resources/llm_prompt.html',
        js_api=api,
        width=800,
        height=600
    )
    webview.start(debug=True)