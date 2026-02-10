
from typing import Optional

from pydantic import BaseModel


class LLMProcessRequest(BaseModel):
    """Request model for LLM processing"""
    prompt: str
    image_data: Optional[str] = None
    output_file_path: Optional[str] = None
    user_id: Optional[str] = None