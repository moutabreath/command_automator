import logging
import os

from commands_automator.llm.llm_agents.gemini.gemini_utils import GeminiUtils
from commands_automator.utils import file_utils

class JobSearchService:

    def __init__(self, gemini_utils: GeminiUtils):
        self.gemini_utils = gemini_utils       
        self.job_search_chat = self.gemini_utils.init_chat()
        

    def get_unified_jobs(self):
        try:
            # Upload each JSON file to Gemini
            file_paths = self.get_job_files_path()         

            if not file_paths:
                return "No valid job files could be uploaded"

            # Prepare the prompt for Gemini
            prompt = self.phrase_prompt()

            # Send to Gemini with file attachments
            return self.gemini_utils.get_response_from_gemini(chat=self.job_search_chat, prompt=prompt, file_paths=file_paths)
    
        except Exception as e:
            logging.error(f"Error processing unified jobs: {e}", exc_info=True)
            return "Sorry, I couldn't process the job listings."
    
    def phrase_prompt(self):
        return """I am attaching JSON files containing job listings. Return a unifed list of jobs
             according to the following criteria:
1. Only include jobs that are in the center district of Israel
2. Only include jobs that are actually a software engineer. No deveops or QA.
3. Jobs may appear in multiple files. In that case, merge as much details as you can into one list item.
4. Filter out if the job has a requirement for profiency with node.js or requires experience with it

Please format the response in a clear, structured way."""

    def get_job_files_path(self):
        file_paths = []
        # Get all JSON files from the jobs directory
        json_files = [f for f in os.listdir(file_utils.JOB_FILE_DIR) if f.endswith('.json')]
        if not json_files:
            logging.warning("No job files found in directory")
            return file_paths
     
        for file_name in json_files:
            file_path = os.path.join(file_utils.JOB_FILE_DIR, file_name)
            file_paths.append(file_path)
            
        return file_paths