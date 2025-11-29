from abc import ABC
from pathlib import Path

from services.configuration_service import ConfigurationService
class AbstractApi(ABC):

    def __init__(self, config_file_path:Path):
        self.config_service = ConfigurationService(config_file_path)

    def load_configuration(self):
        return self.config_service.load_configuration()
    
    def save_configuration(self, config):
        return self.config_service.save_configuration(config)
       
    