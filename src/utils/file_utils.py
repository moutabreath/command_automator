import json
import logging
import os
from pathlib import Path
from typing import List, Any, TypeVar
import aiofiles
from pydantic import BaseModel


BASE_DIR = Path(os.getenv('APPDATA', os.path.expanduser('~/.config'))) / 'commands_automator'
CONFIG_FILE = BASE_DIR / 'commands_automator.config'

USER_SCRIPTS_DIR = BASE_DIR / 'scripts_manager' / 'user_scripts' 
USER_SCRIPTS_CONFIG_FILE = USER_SCRIPTS_DIR / 'config' / 'scripts_config.json'

RESUME_RESOURCES_DIR =  BASE_DIR / 'mcp_servers' /  'resume' / 'resources'
RESUME_ADDITIONAL_FILES_DIR = RESUME_RESOURCES_DIR / 'additional_files'

JOB_SEARCH_CONFIG_FILE = BASE_DIR / 'mcp_servers' / 'job_search' / 'config' /'job_keywords.json'
GLASSDOOR_SELECTORS_FILE = BASE_DIR / 'mcp_servers' / 'job_search' / 'config' / 'glassdoor_selectors.json'



T = TypeVar('T', bound=BaseModel)

async def save_file(file_path: str | Path, content: str) -> bool:
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
    

def make_serializable(obj: Any) -> Any:
    """Recursively convert objects to JSON-serializable format"""
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    return obj

def serialize_to_json(obj: Any) -> str | None:
    """Convert object to JSON string"""
    try:
        serializable_obj = make_serializable(obj)
        return json.dumps(serializable_obj, indent=4)
    except Exception as e:
        logging.error(f"Error serializing to JSON: {e}", exc_info=True)
        return None

def serialize_objects(objects: List[T]) -> str | None:
    """
    Serialize a list of Pydantic models to JSON string
    Args:
        objects: List of any Pydantic model objects
    Returns:
        JSON string representation of the objects, or None on error
    """
    try:
        return json.dumps([obj.model_dump(mode='json') for obj in objects], indent=4)
    except Exception as e:
        logging.error(f"Error converting list to JSON: {e}", exc_info=True)
        return None
    
async def read_json_file(file_path: str) -> dict | None:
    data = await read_text_file(file_path)
    if (data == None):
        return {}
    try:
        return json.loads(data)
    except (json.JSONDecodeError, OSError) as e:
        logging.error(f"Error reading JSON file {file_path}: {e}", exc_info=True)
        return {}
    
async def read_text_file(file_path: str | Path) -> str | None:
    content: str = ""
    logging.debug(f"Reading file: {file_path}")
    try:
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError) as e:
        logging.error(f"Error reading file: {file_path} - {e}", exc_info=True)
    return content