import logging, os
from typing import List

from llm.mcp_servers.job_search.models import ScrapedJob
from utils import file_utils


class JobsSaverService:
    
    async def save_jobs_to_file(self, jobs: List[ScrapedJob], filename: str) -> bool:
        """Save jobs to JSON file

        Args:
            jobs: List of ScrapedJob objects to save
            filename: Name of the file (without path)

        Returns:
            bool: True if jobs were successfully saved, False otherwise
        """
        if not jobs:
            raise ValueError("Cannot save empty jobs list")
        
        if not filename or ".." in filename or os.path.isabs(filename) or "/" in filename or "\\" in filename:
            raise ValueError(f"Invalid filename: {filename}")
        
        if len(jobs) == 0:
            logging.info(f"No jobs to save for {filename}.")
            return False
                
        file_path = os.path.join(file_utils.JOB_FILE_DIR, filename)
        jobs_json_string = file_utils.serialize_objects(jobs)
        return await file_utils.save_file(file_path, jobs_json_string)

