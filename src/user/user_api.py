
from services.configuration_service import ConfigurationService
from user.services.user_registry_service import UserRegistryService
from utils.file_utils import USER_CONFIG_FILE


class UserApi:

    def __init__(self):
        self.user_config = ConfigurationService(USER_CONFIG_FILE)
        self.user_registry_service = UserRegistryService()
    
    def load_configuration(self):
        config = self.user_config.load_configuration()
        return config
    
    def save_configuration(self, config):
        self.user_config.save_configuration(config)

    def login_or_register(self, user_email:str):
       self.user_registry_service.login_or_register_user(user_email=user_email)

