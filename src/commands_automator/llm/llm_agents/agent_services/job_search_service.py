import logging
import os
from google.genai.chats import Chat

from commands_automator.llm.llm_agents.gemini.gemini_utils import GeminiUtils
from commands_automator.utils import file_utils

class JobSearchService:

    def __init__(self, gemini_utils: GeminiUtils):
        self.gemini_utils: GeminiUtils = gemini_utils       
        self.job_search_chat: Chat = self.gemini_utils.init_chat()
        

    def get_unified_jobs(self):
        try:
            # Upload each JSON file to Gemini
            file_paths = self.get_job_files_path()         

            if not file_paths:
                return "No job files found in the directory"
            # Prepare the prompt for Gemini
            prompt = self.phrase_prompt()

            # Send to Gemini with file attachments
            return self.gemini_utils.get_response_from_gemini(chat=self.job_search_chat, prompt=prompt, file_paths=file_paths)
    
        except Exception as e:
            logging.error(f"Error processing unified jobs: {e}", exc_info=True)
            return "Sorry, I couldn't process the job listings."
    
    def phrase_prompt(self) -> str:
        """Build the prompt for Gemini to unify and filter job listings.
        
        Returns:
            Formatted prompt string with filtering criteria.
        """
        return """I am attaching JSON files containing job listings. Return a unified list of jobs
according to the following criteria:
1. Only include jobs that are in the center district of Israel
2. Only include jobs that are actually a software engineer. No devops or QA.
3. Jobs may appear in multiple files. In that case, merge as much details as you can into one list item.
4. Filter out if the job has a requirement for proficiency with node.js or requires experience with it

Please format the response in a clear, structured way."""

    def get_job_files_path(self) -> list[str]:
        file_paths = []
        # Get all JSON files from the jobs directory
        try:
            json_files = [
                f
                for f in os.listdir(file_utils.JOB_FILE_DIR)
                if f.endswith('.json')
            ]
            if not json_files:
                logging.warning("No job files found in directory")
                return file_paths
        except (FileNotFoundError, PermissionError) as e:
            logging.error(f"Cannot access job files directory: {e}", exc_info=True)
            return file_paths

        for file_name in json_files:
            file_path = os.path.join(file_utils.JOB_FILE_DIR, file_name)
            file_paths.append(file_path)
            
        return file_paths