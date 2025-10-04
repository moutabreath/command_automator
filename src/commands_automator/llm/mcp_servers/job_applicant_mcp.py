import logging
import multiprocessing
from multiprocessing import freeze_support
from mcp.server.fastmcp import FastMCP

from commands_automator.llm.mcp_servers.job_search.services.glassdoor_jobs_scraper import GlassdoorJobsScraper
from commands_automator.llm.mcp_servers.job_search.services.jobs_saver import JobsSaver
from commands_automator.llm.mcp_servers.job_search.services.linkedin_scraper import LinkedInJobScraper
from commands_automator.llm.mcp_servers.resume.services.resume_loader_service import ResumeLoaderService
from commands_automator.llm.mcp_servers.resume.models import ResumeData
from commands_automator.llm.mcp_servers.services.shared_service import SharedService
from commands_automator.utils.logger_config import setup_logging


# Initialize FastMCP
mcp = FastMCP("job_applicant_helper")

# Global variable for service access within the child process
# This will be initialized in the child process only
_shared_services = None


def get_shared_service(shared_service_name) -> SharedService:
    """Get a service from the shared services dict"""
    global _shared_services
    if _shared_services is None:
        raise RuntimeError("Shared services not initialized. This should only be called in the MCP subprocess.")
    service = _shared_services.get(shared_service_name)
    if service is None:
        raise ValueError(f"Service '{shared_service_name}' not found in shared services")
    return service


def init_shared_services():
    """Initialize services in the child process. Returns a dict of services."""
    logging.info("Initializing shared services in MCP subprocess")
    services = {
        'resume_loader_service': ResumeLoaderService(),
        'linkedin_job_scraper': LinkedInJobScraper(),
        'glassdoor_jobs_scraper': GlassdoorJobsScraper(),
        'job_saver': JobsSaver()
    }
    logging.info("Shared services initialized successfully")
    return services


@mcp.tool()
async def get_resume_files() -> ResumeData:
    """
    Fetch resume file, applicant name, job description and guidelines
    """    
    resume_loader_service = get_shared_service("resume_loader_service")
    try:
        resume_content, applicant_name = await resume_loader_service.get_resume_and_applicant_name()
        if resume_content is None or applicant_name is None:
            raise ValueError("Resume content or applicant name is missing")

        guide_lines = await resume_loader_service.get_main_part_guide_lines()
        if guide_lines:
            guide_lines = guide_lines.replace('***applicant_name***', applicant_name)
        highlighted_sections = await resume_loader_service.get_highlighted_sections()

        job_description_content = await resume_loader_service.get_job_description()

        cover_letter_guide_lines = await resume_loader_service.get_cover_letter_guide_lines()

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
async def search_jobs_from_the_internet() -> list:
    """
    Search for jobs from multiple sources (LinkedIn and Glassdoor).
    
    Returns:
        List of Job objects from all sources
    """
    jobs = []
    try:
        linkedin_jobs = await get_jobs_from_linkedin()
        jobs.extend(linkedin_jobs)
    except Exception as ex:
        logging.error(f"LinkedIn scraper failed: {ex}")
    
    try:
        glassdoor_jobs = await get_jobs_from_glassdoor()
        jobs.extend(glassdoor_jobs)
    except Exception as ex:
        logging.error(f"Glassdoor scraper failed: {ex}")

    return jobs

    
@mcp.tool()
async def get_jobs_from_linkedin():
    """
    Search for jobs on LinkedIn.    
    
    Returns:
        List of Job objects
    """ 
    return await run_linkedin_scraper()


async def run_linkedin_scraper():
    """Run the LinkedIn job scraper"""
    linkedin_scraper = get_shared_service("linkedin_job_scraper")
    jobs_saver = get_shared_service("job_saver")
    
    keywords: str = "Software Engineer"
    location: str = "Tel Aviv, Israel"
    remote: bool = True
    max_pages: int = 2
    logging.info(f"Searching for '{keywords}' jobs in '{location}'...")
    
    search_url = linkedin_scraper.build_search_url(
        keywords=keywords,
        location=location,
        remote=remote
    )
    
    logging.debug(f"Search URL: {search_url}")
    
    jobs = linkedin_scraper.scrape_job_listings(search_url, max_pages=max_pages)
    
    logging.info(f"Found {len(jobs)} jobs")
    logging.debug("=" * 60)
    
    await jobs_saver.save_jobs_to_file(jobs, 'linkedin_jobs.json')

    # Optional: Get detailed description for first job
    if jobs:
        logging.info(f"Getting detailed description for: {jobs[0].title}")
        description = linkedin_scraper.get_job_description(jobs[0].link)
        logging.debug(f"Description: {description[:300]}...")
    
    return jobs


@mcp.tool()
async def get_jobs_from_glassdoor():
    """
    Search for jobs on Glassdoor.

    Returns:
        List of Job objects
    """
    return await run_glassdoor_scraper()


async def run_glassdoor_scraper(
    job_title: str = "Software Engineer",
    location: str = "Tel Aviv, Israel",
    max_pages: int = 3,
    max_jobs_per_page: int = 20
):
    """Run the Glassdoor job scraper"""
    glassdoor_scraper = get_shared_service("glassdoor_jobs_scraper")
    job_saver = get_shared_service("job_saver")

    jobs = await glassdoor_scraper.run_scraper(
        job_title=job_title,
        location=location,
        max_pages=max_pages,
        max_jobs_per_page=max_jobs_per_page
    )
    
    await job_saver.save_jobs_to_file(jobs, 'glassdoor_jobs.json')
    return jobs


class MCPRunner:
    """Manages the MCP server subprocess"""
    
    def __init__(self):
        self.mcp_process = None

    def init_mcp(self):
        """Initialize and start the MCP server process"""
        try:
            logging.info("Initializing MCP process...")
            # Start the MCP process
            self.mcp_process = multiprocessing.Process(target=self.run_mcp)
            self.mcp_process.start()
            logging.info(f"MCP process started with PID: {self.mcp_process.pid}")
        except Exception as ex:
            logging.error(f"Error initializing MCP process: {ex}", exc_info=True)
            raise
        
    def stop_mcp(self):
        """Cleanup method to terminate the MCP process"""
        try:
            if self.mcp_process:
                if self.mcp_process.is_alive():
                    logging.info("Stopping MCP server...")
                    self.mcp_process.terminate()
                    self.mcp_process.join(timeout=5)  # Wait up to 5 seconds for clean shutdown
                    if self.mcp_process.is_alive():
                        logging.warning("MCP process did not terminate gracefully, killing...")
                        self.mcp_process.kill()  # Force kill if it doesn't terminate
                    logging.info("MCP server stopped")
        except Exception as ex:
            logging.error(f"Error stopping MCP server: {ex}", exc_info=True)

    def run_mcp(self):
        """Run the MCP server in the subprocess"""
        global _shared_services
        
        try:
            # Initialize logging in the child process
            setup_logging()
            
            # Initialize services in the child process)
            _shared_services = init_shared_services()
            
            # Set server configuration
            mcp.settings.mount_path = "/mcp"
            mcp.settings.port = 8765
            mcp.settings.host = "127.0.0.1"
            
            logging.info("Starting MCP server in subprocess...")
            logging.debug(f"Server URL: http://{mcp.settings.host}:{mcp.settings.port}{mcp.settings.mount_path}")
            
            # Run the server with streamable-http transport
            mcp.run(transport="streamable-http")
        except Exception as ex:
            logging.error(f"Error running MCP server: {ex}", exc_info=True)
            raise

    def __enter__(self):  
        return self  

    def __exit__(self, exc_type, exc_val, exc_tb):  
        self.stop_mcp()


def main():
    """Main entry point"""
    # This is required for multiprocessing to work with frozen executables
    freeze_support()
    
    # Set up logging for main process
    setup_logging()
    
    mcp_runner = MCPRunner()
    mcp_runner.init_mcp()
    
    try:
        # Keep the main process running
        logging.info("Main process waiting for MCP subprocess...")
        mcp_runner.mcp_process.join()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down...")
    finally:
        mcp_runner.stop_mcp()

if __name__ == '__main__':
    main()