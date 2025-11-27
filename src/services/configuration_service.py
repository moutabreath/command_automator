from pathlib import Path
from typing import Dict, Any
import logging
from utils import file_utils, utils


class ConfigurationService:
    def __init__(self, config_path: Path | str) -> None:
        """Initialize configuration service with a path to the config file"""
        self.config_path = str(config_path) if isinstance(config_path, Path) else config_path
        self._config: Dict[str, Any] = {}

    def __getstate__(self) -> Dict[str, Any]:
        """Custom serialization for the class"""
        return {
            'config_path': self.config_path,
            'config': self._config
        }

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Custom deserialization for the class"""
        self.config_path = state['config_path']
        self._config = state['config']

    def load_configuration(self) -> Dict[str, Any] | None:
        """Load configuration from JSON file (synchronous wrapper)"""
        return utils.run_async_method(self.load_configuration_async)
          
    async def load_configuration_async(self) -> Dict[str, Any] | None:
        """Load configuration from JSON file"""    
        self._config = await file_utils.read_json_file(self.config_path)
        return self._config
    
    def save_configuration(self, config):
        return utils.run_async_method(self.save_configuration_async, config)
    
    async def save_configuration_async(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file"""
        success = await file_utils.save_file(self.config_path, 
                                        file_utils.serialize_to_json(config))
        if success:
            self._config = config
        return success
        