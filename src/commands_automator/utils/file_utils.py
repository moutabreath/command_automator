import json
import logging
import os
from pathlib import Path
from typing import List, TypeVar
import aiofiles
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

# Define base paths
BASE_DIR = Path(__file__).resolve().parents[2]
JOB_FILE_DIR = os.path.join(BASE_DIR, "llm", "mcp_servers", "job_search", "results")


async def save_file(file_path, content):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
        return True
    except Exception as e:
        logging.error(f"Error saving file {e}", exc_info=True)
        return False
    
async def serialize_to_json(text):
    try:
        return json.dumps(text, indent=4)
    except (json.JSONDecodeError) as e:
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
        except (json.JSONDecodeError) as e:
            logging.error(f"Error converting list to JSON: {e}", exc_info=True)
            return "{}"


  
async def read_file_as_json(file_path):
    try:
        async with aiofiles.open(file_path, "r") as f:
            data = await f.read()
        return json.loads(data)
    except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError) as e:  
        logging.error(f"Error loading config file: {e}", exc_info=True)  
        return {}