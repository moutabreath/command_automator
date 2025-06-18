import json
import aiofiles


class ConfigurationService:
    def __init__(self, config_path):
        self.config_path = config_path

    async def load_configuration_async(self):
        async with aiofiles.open(self.config_path, "r") as f:
            data = await f.read()
        return json.loads(data)

    async def save_configuration_async(self, config):
        async with aiofiles.open(self.config_path, "w") as f:
            await f.write(json.dumps(config, indent=4))
        
        return True