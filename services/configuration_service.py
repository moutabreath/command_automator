import json
import logging
import aiofiles


class ConfigurationService:
    def __init__(self, config_path):
        self.config_path = config_path

    async def load_configuration_async(self):
        try:
            async with aiofiles.open(self.config_path, "r") as f:
                data = await f.read()
            return json.loads(data)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError) as e:  
            logging.error(f"Error loading config file: {e}", exc_info=True)  
            return {}  

    async def save_configuration_async(self, config):
        try:
            async with aiofiles.open(self.config_path, "w") as f:
                await f.write(json.dumps(config, indent=4))
            return True
        except Exception as e:
            logging.error(f"Error saving config file {e}", exc_info=True)
            return False