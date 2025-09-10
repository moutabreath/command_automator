import json
import logging
import multiprocessing
from multiprocessing import Manager, freeze_support
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

from commands_automator.llm.mcp_servers.job_search.models import Job
from commands_automator.llm.mcp_servers.job_search.services.jobs_saver import JobsSaver
from commands_automator.llm.mcp_servers.job_search.services.linkedin_scraper import LinkedInJobScraper
from commands_automator.llm.mcp_servers.resume.services.resume_loader_service import ResumeLoaderService
from commands_automator.llm.mcp_servers.resume.models import ResumeData


# Initialize FastMCP
mcp = FastMCP("job_applicant_helper")

# Global variables for service access
_manager = None
_shared_services = None

@mcp.tool()
async def get_resume_files() -> ResumeData:
    """
    Fetch resume file, applicant name, job description and guidelines
    """    
    global _shared_services
    if _shared_services is None:
        logging.warning("Shared services not initialized, creating new instance")
        resume_loader_service = ResumeLoaderService()
    else:
        resume_loader_service = _shared_services.get('resume_loader_service')
        if resume_loader_service is None:
            logging.warning("ResumeLoaderService not found in shared services")
            resume_loader_service = ResumeLoaderService()        
    try:
        resume_content, applicant_name = await resume_loader_service.get_resume_and_applicant_name()
        if resume_content is None or applicant_name is None:
            raise ValueError("Resume content or applicant name is missing")

        guide_lines = await resume_loader_service.get_main_part_guide_lines()
        if guide_lines is None:
            guide_lines = ""  
        else:
            guide_lines = guide_lines.replace('***applicant_name***', applicant_name)

        highlighted_sections = await resume_loader_service.get_highlighted_sections()
        if highlighted_sections is None:
            highlighted_sections = []

        job_description_content = await resume_loader_service.get_job_description()
        if job_description_content is None:
            job_description_content = ""

        cover_letter_guide_lines = await resume_loader_service.get_cover_letter_guide_lines()
        if cover_letter_guide_lines is None:
            cover_letter_guide_lines = ""

        # Create dictionary first to validate data
        data_dict = {
            "applicant_name": applicant_name or "",
            "general_guidelines": guide_lines or "",
            "resume": resume_content or "",
            "resume_highlighted_sections": highlighted_sections or [],
            "job_description": job_description_content or "",
            "cover_letter_guidelines": cover_letter_guide_lines or ""
        }
        logging.debug(f"Creating ResumeData with: {data_dict}")
        
        resume_data = ResumeData(**data_dict)
        logging.debug(f"Created ResumeData successfully: {resume_data.model_dump()}")
        return resume_data
    except Exception as ex:
        logging.error(f"Error fetching resume: {ex}")
        return ResumeData(
            applicant_name="",
            general_guidelines="",
            resume="",
            resume_highlighted_sections=[],
            job_description="",
            cover_letter_guidelines=""
        )
    
@mcp.tool()
async def get_jobs_from_linkedin():
    """
    Search for jobs on LinkedIn.    
    
    Returns:
        List of Job objects
    """
    
    keywords: str = "Software Engineer"
    location: str = "Tel Aviv, Israel"
    remote: bool = True
    max_pages: int = 2
    logging.info(f"Searching for '{keywords}' jobs in '{location}'...")
    linkedin_scraper = LinkedInJobScraper()
    
    search_url = linkedin_scraper.build_search_url(
        keywords=keywords,
        location=location,
        remote=remote  # Include remote jobs
    )
    
    logging.debug(f"Search URL: {search_url}")
    
    jobs = linkedin_scraper.scrape_job_listings(search_url, max_pages=max_pages)
    
    logging.info(f"Found {len(jobs)} jobs")
    logging.debug("=" * 60)
    
    jobs_saver = JobsSaver()
    await jobs_saver.save_jobs_to_file(jobs, 'linkedin_jobs.json')

    # Optional: Get detailed description for first job
    if jobs:
        logging.info(f"Getting detailed description for: {jobs[0].title}")
        description = linkedin_scraper.get_job_description(jobs[0].link)
        logging.debug(f"Description: {description[:300]}...")

    return jobs

class MCPRunner:

    def init_mcp(self):
        """Initialize and start the MCP server process"""
            
            # Start the MCP process
        self.mcp_process = multiprocessing.Process(target=self.run_mcp)
        self.mcp_process.start()
        
    def stop_mcp(self):
        """Cleanup method to terminate the MCP process when the agent is destroyed"""
        try:
            if hasattr(self, 'mcp_process'):
                if self.mcp_process.is_alive():
                    logging.info("Stopping MCP server...")
                    self.mcp_process.terminate()
                    self.mcp_process.join(timeout=5)  # Wait up to 5 seconds for clean shutdown
                    if self.mcp_process.is_alive():
                        logging.warning("MCP process did not terminate gracefully, killing...")
                        self.mcp_process.kill()  # Force kill if it doesn't terminate
                    logging.info("MCP server stopped")
            
            if _manager:
                _manager.shutdown()
        except Exception as ex:
            logging.error(f"Error stopping MCP server: {ex}", exc_info=True)

    def run_mcp(self):
        """Run the MCP server"""
        # Set server configuration through the settings property
        mcp.settings.mount_path = "/mcp"
        mcp.settings.port = 8765
        mcp.settings.host = "127.0.0.1"
        
        # Run the server with streamable-http transport
        logging.debug(f"Starting MCP server at http://{mcp.settings.host}:{mcp.settings.port}{mcp.settings.mount_path}")
        mcp.run(transport="streamable-http")

    def __enter__(self):  
        return self  

    def __exit__(self, exc_type, exc_val, exc_tb):  
        self.stop_mcp()  

def main():
    # This is required for multiprocessing to work with frozen executables
    freeze_support()
    
    mcp_runner = MCPRunner()
    mcp_runner.init_mcp()
    
    try:
        # Keep the main process running
        mcp_runner.mcp_process.join()
    except KeyboardInterrupt:
        mcp_runner.stop_mcp()

if __name__ == '__main__':
    main()