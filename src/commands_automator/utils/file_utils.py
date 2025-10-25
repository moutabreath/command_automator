import json
import logging
import os
from pathlib import Path
from typing import List, TypeVar
import aiofiles
from pydantic import BaseModel

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Go up 3 levels from utils/file_utils.py

# Define base directories using proper path joining
BASE_DIR = PROJECT_ROOT / 'src' / 'commands_automator'
SCRIPTS_MANAGER_BASE_DIR = BASE_DIR / 'scripts_manager'
LLM_BASE_DIR = BASE_DIR / 'llm'

# Define specific directories
SCRIPTS_MANAGER_CONFIG_FILE = SCRIPTS_MANAGER_BASE_DIR / 'config' / 'commands-executor-config.json'
SCRIPTS_CONFIG_FILE = SCRIPTS_MANAGER_BASE_DIR / 'config' / 'scripts_config.json'
SCRIPTS_DIR = SCRIPTS_MANAGER_BASE_DIR / 'user_scripts'

LLM_CONFIG_DIR = LLM_BASE_DIR / 'config' / 'llm-config.json'
JOB_FILE_DIR = LLM_BASE_DIR /'mcp_servers' / 'job_search' /'results'

T = TypeVar('T', bound=BaseModel)

async def save_file(file_path: str, content: str) -> bool:
    try:
        # Ensure the directory exists
        dir_path = Path(file_path).parent
        if dir_path:
            dir_path.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content)
        return True
    except (OSError, IOError) as e:
        logging.error(f"Error saving file {file_path}: {e}", exc_info=True)
        return False    
    
def serialize_to_json(text) -> str:
    try:
        return json.dumps(text, indent=4)
    except (TypeError, ValueError) as e:
        logging.error(f"Error converting text to JSON: {e}", exc_info=True)
        return "{}"
    
def serialize_objects(objects: List[T]) -> str:
    """
    Serialize a list of Pydantic models to JSON string
    Args:
        objects: List of any Pydantic model objects
    Returns:
        JSON string representation of the objects
    """
    try:
        return json.dumps([obj.model_dump(mode='json') for obj in objects], indent=4)
    except (TypeError, ValueError) as e:
        logging.error(f"Error converting list to JSON: {e}", exc_info=True)
        return "[]"
    
async def read_json_file(file_path: str) -> dict:
    try:
        async with aiofiles.open(file_path, "r", encoding='utf-8') as f:
            data = await f.read()
        return json.loads(data)
    except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError) as e:
        logging.error(f"Error reading JSON file {file_path}: {e}", exc_info=True)
        return {}
    
async def read_text_file(file_path: str | Path) -> str:
    content: str = ""
    logging.info(f"Reading file: {file_path}")
    try:
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
    except UnicodeDecodeError as e:
        logging.error(f"Error reading file: {file_path} {e}", exc_info=True)
    except IOError as ioError:
        logging.error(f"Error reading file: {file_path} - {ioError}", exc_info=True)  
    return content