import json
import logging
import os
from typing import List
import aiofiles

from commands_automator.llm.mcp_servers.job_search.models import Job
from commands_automator.llm.mcp_servers.services.shared_service import SharedService
from commands_automator.utils import file_utils


class JobsSaver(SharedService):
    async def save_jobs_to_file(self, jobs: List[Job], filename: str):
        """Save jobs to JSON file"""
        file_path = os.path.join(file_utils.JOB_FILE_DIR, filename)
        jobs_json_string = file_utils.serialize_objects(jobs)
        return await file_utils.save_file(file_path, jobs_json_string)

