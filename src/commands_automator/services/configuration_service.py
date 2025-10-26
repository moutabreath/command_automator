from typing import Dict, Any
from pathlib import Path
from commands_automator.utils import file_utils


class ConfigurationService:
    def __init__(self, config_path: Path | str) -> None:
        self.config_path = Path(config_path) if isinstance(config_path, str) else config_path

    async def load_configuration_async(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file asynchronously
        
        Returns:
            Dict[str, Any]: Configuration dictionary, empty dict if file not found
        """
        return await file_utils.read_json_file(self.config_path) or {}

    async def save_configuration_async(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to JSON file asynchronously
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        json_string = file_utils.serialize_to_json(config)
        return await file_utils.save_file(self.config_path, json_string)