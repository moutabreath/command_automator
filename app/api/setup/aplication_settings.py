from pydantic import MongoDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


from ...core.log_level import LogLevel

class ApplicationSettings(BaseSettings):
    # MongoDB Connection
    # Using MongoDsn ensures the string is a valid MongoDB URI format
    mongo_uri: MongoDsn = Field(
        default="mongodb://localhost:27017/job_tracker",
        validation_alias="MONGO_URI"
    )
  
    # Database Names
    mongo_db_name: str = Field(default="job_tracker", validation_alias="MONGODB_DB_NAME")
    job_application_collection_name: str = Field(default="job_applications", validation_alias="APPLICATION_COLLECTION_NAME")


    # Scaling/Logging Levels
    # Optionally different levels for Read vs Write services
    log_level: LogLevel = Field(default=LogLevel.INFO, validation_alias="LOG_LEVEL")
    log_file: str = Field(default="commands_automator.log", validation_alias="LOG_FILE")
  
    # Pydantic Settings: 
    # 1. Check OS Environment variables first.
    # 2. If not found, look in a .env file.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instantiate once
application_settings = ApplicationSettings()