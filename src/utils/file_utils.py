import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Any, TypeVar
import aiofiles
from pydantic import BaseModel

def find_project_root(marker_filename: str) -> Path:
    """
    Traverse up the directory tree until a marker file is found.
    Uses the directory of the currently executing script as a starting point.
    """
    # Start search from the directory of this file
    current_dir = Path(__file__).resolve().parent
    
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / marker_filename).exists():
            return parent
    
    # Fallback/error if marker not found
    logging.error(f"Error: Could not find project root marker '{marker_filename}'")
    raise FileNotFoundError(
        f"Could not find project root marker '{marker_filename}' "
        f"starting from {current_dir}"
    )

# Determine project root in both dev and frozen (pyinstaller) modes.
try:
    if getattr(sys, 'frozen', False):
        # When frozen, use APPDATA for resources
        BASE_DIR = Path(os.getenv('APPDATA', os.path.expanduser('~/.config'))) / 'commands_automator'
    else:
        # In development, use source directory
        try:
            PROJECT_ROOT = find_project_root('README.md')
            BASE_DIR = PROJECT_ROOT / 'src'
        except FileNotFoundError:
            # Fallback to two levels up from this file if marker not present
            BASE_DIR = Path(__file__).resolve().parents[2] / 'src'
except Exception as e:
    logging.error(f"Error determining BASE_DIR: {e}")
    BASE_DIR = Path(__file__).resolve().parent

# Set paths based on BASE_DIR
if getattr(sys, 'frozen', False):
    # Frozen mode - use APPDATA structure
    RESUME_RESOURCES_DIR = BASE_DIR / 'mcp_servers' / 'resume' / 'resources'
    USER_SCRIPTS_DIR = BASE_DIR / 'scripts_manager' / 'user_scripts'
    JOB_SEARCH_CONFIG_FILE = BASE_DIR / 'mcp_servers' / 'job_search' / 'config' / 'job_keywords.json'
else:
    # Development mode - use source structure
    RESUME_RESOURCES_DIR = BASE_DIR / 'llm' / 'mcp_servers' / 'resume' / 'resources'
    USER_SCRIPTS_DIR = BASE_DIR / 'scripts_manager' / 'user_scripts'
    JOB_SEARCH_CONFIG_FILE = BASE_DIR / 'llm' / 'mcp_servers' / 'job_search' / 'config' / 'job_keywords.json'    

# Common paths
CONFIG_FILE = Path(os.getenv('APPDATA', os.path.expanduser('~/.config'))) / 'commands_automator' / 'commands_automator.config'
USER_SCRIPTS_CONFIG_FILE = USER_SCRIPTS_DIR / 'config' / 'scripts_config.json'
RESUME_ADDITIONAL_FILES_DIR = RESUME_RESOURCES_DIR / 'additional_files'
GLASSDOOR_SELECTORS_FILE = JOB_SEARCH_CONFIG_FILE.parent / 'glassdoor_selectors.json'
JOB_TITLES_CONFIG_FILE = BASE_DIR / 'jobs_tracking' / 'config' / 'job_titles_keywords.json'


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
        logging.exception(f"Error saving file {file_path}: {e}")
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
        logging.exception(f"Error serializing to JSON: {e}")
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
        logging.exception(f"Error converting list to JSON: {e}")
        return None
    
async def read_json_file(file_path: str) -> dict | None:
    data = await read_text_file(file_path)
    if (data == None):
        return {}
    try:
        return json.loads(data)
    except (json.JSONDecodeError, OSError) as e:
        logging.exception(f"Error reading JSON file {file_path}: {e}")
        return {}
    
async def read_text_file(file_path: str | Path) -> str | None:
    content: str = ""
    logging.debug(f"Reading file: {file_path}")
    try:
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError) as e:
        logging.exception(f"Error reading file: {file_path} - {e}")
    return content
