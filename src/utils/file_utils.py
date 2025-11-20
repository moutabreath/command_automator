import json
import logging
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

# Use a known file like 'pyproject.toml' or 'README.md'
PROJECT_ROOT = find_project_root('README.md')

# Define base directories using proper path joining
BASE_DIR = PROJECT_ROOT / 'src' 
SCRIPTS_MANAGER_BASE_DIR = BASE_DIR / 'scripts_manager'
LLM_BASE_DIR = BASE_DIR / 'llm'

# Define specific directories
SCRIPTS_MANAGER_CONFIG_FILE = SCRIPTS_MANAGER_BASE_DIR / 'config' / 'commands-executor-config.json'
SCRIPTS_CONFIG_FILE = SCRIPTS_MANAGER_BASE_DIR / 'config' / 'scripts_config.json'
SCRIPTS_DIR = SCRIPTS_MANAGER_BASE_DIR / 'user_scripts'

LLM_CONFIG_FILE = LLM_BASE_DIR / 'config' / 'llm-config.json'

JOB_FILE_DIR = LLM_BASE_DIR / 'mcp_servers' / 'job_search' / 'results'
JOB_SEARCH_CONFIG_FILE = LLM_BASE_DIR / 'mcp_servers' / 'job_search' / 'config' /'job_keywords.json'
GLASSDOOR_SELECTORS_FILE = LLM_BASE_DIR / 'mcp_servers' / 'job_search' / 'config' / 'glassdoor_selectors.json'



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

def serialize_to_json(obj: Any) -> str:
    """Convert object to JSON string"""
    try:
        serializable_obj = make_serializable(obj)
        return json.dumps(serializable_obj, indent=4)
    except Exception as e:
        logging.error(f"Error serializing to JSON: {e}", exc_info=True)
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
    try:
        async with aiofiles.open(file_path, "r", encoding='utf-8') as f:
            data = await f.read()
        return json.loads(data)
    except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError) as e:
        logging.error(f"Error reading JSON file {file_path}: {e}", exc_info=True)
        return None
    
async def read_text_file(file_path: str | Path) -> str | None:
    content: str = ""
    logging.debug(f"Reading file: {file_path}")
    try:
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
        return content
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError) as e:
        logging.error(f"Error reading file: {file_path} - {e}", exc_info=True)
        return None