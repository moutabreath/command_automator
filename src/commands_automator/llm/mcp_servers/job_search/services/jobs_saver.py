import json
import logging
import os
from pathlib import Path
from typing import List

import aiofiles

from commands_automator.llm.mcp_servers.job_search.models import Job


class JobsSaver:

    BASE_DIR = Path(__file__).resolve().parents[1]
    JOB_FILE_DIR = os.path.join(BASE_DIR,"results")

    async def save_jobs_to_file(self, jobs: List[Job], filename: str):
        """Save jobs to JSON file"""
        file_path = os.path.join(self.JOB_FILE_DIR, filename)
        jobs_dict = [job.model_dump() for job in jobs]
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(jobs_dict, indent=4))
            return True
        except Exception as e:
            logging.error(f"Error saving config file {e}", exc_info=True)
            return False