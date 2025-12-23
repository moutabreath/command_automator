import logging
from abstract_api import AbstractApi
from scripts_manager.services.scripts_manager_service import ScriptsManagerService


class ScriptsManagerApi(AbstractApi):
    def __init__(self):
        self.scripts_manager_service = ScriptsManagerService()       

    def load_scripts(self):
        try:
            return self.scripts_manager_service.load_scripts()
        except Exception as e:
            logging.exception(f"Error loading scripts: {e}")
            return []
        
    def get_script_description(self, script_name):
        try:
            name_to_scripts = self.scripts_manager_service.get_name_to_scripts()
            if script_name not in name_to_scripts:
                logging.error(f"Script not found: {script_name}")
                return ""
            script_file = name_to_scripts[script_name]
            return self.scripts_manager_service.get_script_description(script_file)
        except Exception as e:
            logging.exception(f"Error getting script description for {script_name}: {e}")
            return ""
                
    def execute_script(self, script_name, additional_text, flags):
        return self.scripts_manager_service.execute_script(script_name, additional_text, flags)
