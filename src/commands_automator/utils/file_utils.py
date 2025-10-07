import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import List, TypeVar
import aiofiles
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

# Define base paths
BASE_DIR = Path(__file__).resolve().parents[2]
JOB_FILE_DIR = os.path.join(BASE_DIR, "llm", "mcp_servers", "job_search", "results")


async def save_file(file_path: str, content: str) -> bool:
    try:
        # Ensure the directory exists
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
        return True
    except Exception as e:
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
        async with aiofiles.open(file_path, "r") as f:
            data = await f.read()
        return json.loads(data)
    except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError) as e:
        logging.error(f"Error reading JSON file {file_path}: {e}", exc_info=True)
        return {}
    
async def read_text_file(file_path: str | Path) -> str:
    content: str = ""
    logging.info(f"Reading file: {file_path}")
    try:
        async with aiofiles.open(file_path, 'r', encoding="utf8") as file:
            content = await file.read()
    except UnicodeDecodeError as e:
        logging.error(f"Error reading file: {file_path} {e}", exc_info=True)
    except IOError as ioError:
        logging.error(f"Error reading file: {file_path} - {ioError}", exc_info=True)  
    return content

def get_mime_type(self, file_path: str) -> str:
    """Detect MIME type based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.txt': 'text/plain',
        '.json': 'application/json',
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        return mime_types.get(ext, 'application/octet-stream')
    return mime_type  