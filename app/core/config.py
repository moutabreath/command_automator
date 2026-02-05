from pydantic import MongoDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import str

class LogLevel(str):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class Settings(BaseSettings):
    # MongoDB Connection
    # Using MongoDsn ensures the string is a valid MongoDB URI format
    mongo_uri: MongoDsn = Field(
        default="mongodb://localhost:27017/job_tracker",
        validation_alias="MONGO_URI"
    )
    
    # Scaling/Logging Levels
    # Optionally different levels for Read vs Write services
    log_level: LogLevel = Field(default=LogLevel.INFO, validation_alias="LOG_LEVEL")
    
    # Database Names
    mongo_db_name: str = Field(default="job_tracker_db", validation_alias="MONGODB_DB_NAME")
    collection_name: str = Field(default="job_applications", validation_alias="COLLECTION_NAME")

    # Pydantic Settings: 
    # 1. Check OS Environment variables first.
    # 2. If not found, look in a .env file.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instantiate once
settings = Settings()