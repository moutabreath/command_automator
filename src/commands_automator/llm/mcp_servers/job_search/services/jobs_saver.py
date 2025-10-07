import json
import logging
import os
from typing import List

from commands_automator.llm.mcp_servers.job_search.models import Job
from commands_automator.llm.mcp_servers.services.shared_service import SharedService
from commands_automator.utils import file_utils


class JobsSaver(SharedService):
    
    async def save_jobs_to_file(self, jobs: List[Job], filename: str) -> bool:
        """Save jobs to JSON file

        Args:
            jobs: List of Job objects to save
            filename: Name of the file (without path)

        Returns:
            bool: True if jobs were successfully saved, False otherwise

        Raises:
            ValueError: If filename is invalid or jobs list is empty
            IOError: If file cannot be written
        """
        if not jobs:
            raise ValueError("Cannot save empty jobs list")
        
        if not filename or ".." in filename or os.path.isabs(filename):
            raise ValueError(f"Invalid filename: {filename}")
        
        file_path = os.path.join(file_utils.JOB_FILE_DIR, filename)
        jobs_json_string = file_utils.serialize_objects(jobs)
        return await file_utils.save_file(file_path, jobs_json_string)

