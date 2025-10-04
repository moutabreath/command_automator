import json
from commands_automator.utils import file_utils


class ConfigurationService:
    def __init__(self, config_path):
        self.config_path = config_path

    async def load_configuration_async(self):
        return await file_utils.read_file_as_json(self.config_path)

    async def save_configuration_async(self, config):
        return await file_utils.save_file(self.config_path, file_utils.serialize_to_json(config))