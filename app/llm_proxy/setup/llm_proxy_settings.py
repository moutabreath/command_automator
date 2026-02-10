from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ...core.log_level import LogLevel



class LLMProxySettings(BaseSettings):
    
    mcp_server_host: str = Field(default="127.0.0.1", validation_alias="MCP_HOST")
    mcp_server_port: int = Field(default=8765, validation_alias="MCP_PORT")


    # Scaling/Logging Levels
    # Optionally different levels for Read vs Write services
    log_level: LogLevel = Field(default=LogLevel.INFO, validation_alias="LOG_LEVEL")
    log_file: str = Field(default="commands_automator.log", validation_alias="LOG_FILE")
  
    # Pydantic Settings: 
    # 1. Check OS Environment variables first.
    # 2. If not found, look in a .env file.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instantiate once
llm_proxy_settings = LLMProxySettings()