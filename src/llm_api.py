import base64
from enum import Enum
import logging
import api_utils
from llm.llm_agents.mcp_response import MCPResponse, MCPResponseCode
from llm.llm_service import LLMService
from llm.mcp_servers.job_applicant_mcp import MCPRunner
from utils.file_utils import LLM_CONFIG_FILE
from services.configuration_service import ConfigurationService
from typing import Dict, Any


class LLMApiResponseCode(Enum):
    """Enumeration of possible LLM operation results"""
    OK = 1
    ERROR_COMMUNICATING_WITH_LLM = 2
    ERROR_MODEL_OVERLOADED = 3
    ERROR_LOADING_IMAGE_TO_MODEL = 4

class LLMApiResponse:
    def __init__(self, text: str, code: LLMApiResponseCode):
        self.text = text
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "text": self.text,
            "code": self.code.name if isinstance(self.code, Enum) else str(self.code)
        }

    def __getstate__(self) -> Dict[str, Any]:
        """Support pickling/serialization by returning a dict."""
        return self.to_dict()

class LLMApi:
    def __init__(self):
        self.llm_service: LLMService = LLMService()
        self.llm_config = ConfigurationService(LLM_CONFIG_FILE)
    
    def run_mcp_server(self):
        # Initialize MCP Runner
        mcp_runner = MCPRunner()
        try:
            mcp_runner.init_mcp()
            logging.info("MCP Runner initialized successfully")
        except Exception as ex:
            logging.error(f"Failed to initialize MCP Runner: {ex}", exc_info=True)
            raise


    def load_llm_configuration(self):
        """Load and serialize LLM configuration"""
        try:
            config = api_utils.run_async_method(self.llm_config.load_configuration_async)
            if isinstance(config, dict):
                return config
            return {}
        except Exception as e:
            logging.error(f"Error loading LLM configuration: {e}", exc_info=True)
            return {}

    def save_llm_configuration(self, config) -> bool:
        """Save LLM configuration after ensuring it's serializable"""
        try:
            if not isinstance(config, dict):
                logging.error("Invalid configuration format")
                return False
            result = api_utils.run_async_method(self.llm_config.save_configuration_async, config)
            return result if isinstance(result, bool) else False
        except Exception as e:
            logging.error(f"Error saving LLM configuration: {e}", exc_info=True)
            return False
        
    def call_llm(self, prompt: str, image_data: str, output_file_path: str) -> Dict[str, Any]:
        decoded_data = None
        if image_data and image_data != '':
            try:
                _, encoded = image_data.split(',', 1)
                decoded_data = base64.b64decode(encoded)
            except Exception as e:
                logging.error(f"Error processing image data: {e}", exc_info=True)
                resp = LLMApiResponse("Error loading image", LLMApiResponseCode.ERROR_LOADING_IMAGE_TO_MODEL)
                return resp.to_dict()

        result: MCPResponse = api_utils.run_async_method(self.llm_service.chat_with_bot, prompt, decoded_data, output_file_path)
        
        if result.code == MCPResponseCode.OK:
            resp = LLMApiResponse(result.text, LLMApiResponseCode.OK)
            return resp.to_dict()
        if result.code == MCPResponseCode.ERROR_MODEL_OVERLOADED:
            resp = LLMApiResponse("Model overloaded", LLMApiResponseCode.ERROR_MODEL_OVERLOADED)
            return resp.to_dict()
        resp = LLMApiResponse("Error communicating with LLM", LLMApiResponseCode.ERROR_COMMUNICATING_WITH_LLM)
        return resp.to_dict()