import asyncio
import logging
import multiprocessing
from multiprocessing import freeze_support
from typing import List

from llm.mcp_servers.mcp_dependency_container import MCPContainer
from llm.mcp_servers.resume.models import ResumeData
from mcp.server.fastmcp import FastMCP


from utils.logger_config import setup_logging
from utils.file_utils import JOB_SEARCH_CONFIG_FILE, read_json_file


# Initialize FastMCP
mcp = FastMCP("job_applicant_helper")



@mcp.tool()
async def get_resume_files() -> ResumeData:
    """
    Fetch resume file, applicant name, job description and guidelines
    """    
    try:
        container = MCPContainer.get_container()
        resume_loader_service = container.resume_loader_service()
        resume_content, applicant_name = await resume_loader_service.get_resume_and_applicant_name()
        if resume_content is None:
            logging.error("Couldn't parse resume content")
            return ResumeData(
                applicant_name="",
                general_guidelines="",
                resume="",
                resume_highlighted_sections=[],
                job_description="",
                cover_letter_guidelines=""
            )

        if applicant_name is None:
            applicant_name = "John Doe"

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
        
        resume_data = ResumeData(**data_dict)
        logging.debug(f"Created ResumeData successfully")
        return resume_data
    except Exception as e:
        logging.error(f"Unhandled error in get_resume_files: {e}", exc_info=True)
        return ResumeData(
            applicant_name="",
            general_guidelines="",
            resume="",
            resume_highlighted_sections=[],
            job_description="",
            cover_letter_guidelines=""
        )

@mcp.tool()
async def search_jobs_from_the_internet(job_title: str | None = None, location:str | None = None, 
                                        remote: bool | None = None) -> list:
    """
    Search for jobs from multiple sources (LinkedIn and Glassdoor).
    
    Returns:
        List of Job objects from all sources
    """

    jobs = []
    linkedin_jobs = await _run_linkedin_scraper(job_title=job_title, location=location, remote=remote)
    if linkedin_jobs and len(linkedin_jobs) > 0:
        jobs.extend(linkedin_jobs)

    glassdoor_jobs = await _run_glassdoor_scraper(job_title=job_title, location=location, remote=remote, forbidden_titles=None)
    if glassdoor_jobs and len(glassdoor_jobs) > 0:
        jobs.extend(glassdoor_jobs)

    return jobs
    
@mcp.tool()
async def get_jobs_from_linkedin(job_title: str | None = None,
    location: str | None = None,
    remote: bool | None = None)  -> list:
    """
    Search for jobs on LinkedIn.    
    
    Returns:
        List of Job objects
    """ 
    return await _run_linkedin_scraper(job_title=job_title, location=location, remote=remote)

@mcp.tool()
async def get_jobs_from_glassdoor(job_title: str | None = None, location: str | None = None, 
                                  remote: bool | None = None) -> List:
    """
    Search for jobs on Glassdoor.

    Returns:
        List of Job objects
    """
    return await _run_glassdoor_scraper(job_title, location, remote)

@mcp.tool()
async def get_user_applications_for_company(user_id: str, company_name: str) -> dict:
    """
    Get all job applications for a specific user and company.
    
    Args:
        user_id: The user's unique identifier
        company_name: The name of the company to get applications for
    
    Returns:
        Dictionary containing application data with jobs list
    """
    try:        
        container = MCPContainer.get_container()
        company_persist = container.company_mongo_persist()
        
        # Get the application data
        response = await company_persist.get_application(user_id, company_name.lower())
        
        from repository.abstract_mongo_persist import PersistenceErrorCode
        
        if response.code == PersistenceErrorCode.SUCCESS:
            return {
                "success": True,
                "company_name": company_name,
                "user_id": user_id,
                "application_data": response.data
            }
        elif response.code == PersistenceErrorCode.NOT_FOUND:
            return {
                "success": True,
                "company_name": company_name,
                "user_id": user_id,
                "application_data": None,
                "message": "No applications found for this company"
            }
        else:
            return {
                "success": False,
                "error": response.error_message or "Unknown error occurred"
            }
            
    except Exception as e:
        logging.error(f"Error getting user applications: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
            
    except Exception as e:
        logging.error(f"Error getting user applications: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def _run_linkedin_scraper(job_title: str, location: str, remote: bool) -> list:
    """Run the LinkedIn job scraper"""
    container = container = MCPContainer.get_container()
    linkedin_scraper = container.linkedin_scraper()
    jobs_saver = container.job_saver()
    
    max_pages: int = 2
    logging.info(f"Searching for '{job_title}' jobs in '{location}'...")

    job_title,location, remote, forbidden_titles = await _get_search_params_from_config_or_default(job_title, location, remote)
    jobs = []
    try:
        jobs = linkedin_scraper.run_scraper(job_title=job_title,
            location=location,
            remote=remote,
            forbidden_titles = forbidden_titles,
            max_pages=max_pages)
    
    except Exception as e:
        logging.error(f"Error finding jobs from linkedin {e}", exc_info=True)
        return []
    
    logging.info(f"Found {len(jobs)} jobs")
    logging.debug("=" * 60)
    if jobs and len(jobs) > 0:    
        await jobs_saver.save_jobs_to_file(jobs, 'linkedin_jobs.json')
    else:
        logging.warning("No jobs found from LinkedIn scraper")
   
    return jobs

async def _run_glassdoor_scraper(job_title: str, location: str, remote: bool, forbidden_titles: list = None) -> List:
    """Run the Glassdoor job scraper"""
    max_pages: int = 3
    max_jobs_per_page: int = 20
    container = MCPContainer.get_container()
    glassdoor_scraper = container.glassdoor_scraper()
    job_saver = container.job_saver()

    job_title,location, _, forbidden_titles = await _get_search_params_from_config_or_default(job_title, location, remote, forbidden_titles)
    try:
        jobs = await glassdoor_scraper.run_scraper(
            job_title=job_title,
            location=location,
            forbidden_titles=forbidden_titles,
            max_pages=max_pages,
            max_jobs_per_page=max_jobs_per_page)

        if jobs and len(jobs) > 0:
            await job_saver.save_jobs_to_file(jobs, 'glassdoor_jobs.json')
        else:
            logging.warning("No jobs found from Glassdoor scraper")

        return jobs
    except Exception as e:
        logging.error("Error finding jobs from glassdoor")
        return []

async def _get_search_params_from_config_or_default(job_title: str | None = None, location: str | None = None,
    remote: bool | None = None, forbidden_titles: list | None = None) :
     # If any parameter is None, try loading defaults from llm-config.json
    try:
        llm_conf = await read_json_file(JOB_SEARCH_CONFIG_FILE)
        logging.debug(f"LLM config loaded for job search defaults: {llm_conf}")
    except Exception as e:
        logging.debug(f"Could not load LLM config for defaults: {e}")
        llm_conf = {}

    # Use values from config when provided, otherwise use hardcoded defaults
    if job_title is None:
        job_title = llm_conf.get('job_search', {}).get('job_title') if llm_conf else None
    if location is None:
        location = llm_conf.get('job_search', {}).get('location') if llm_conf else None
    if remote is None:
        # store boolean default; allow string like 'true' or bool
        remote_val = llm_conf.get('job_search', {}).get('remote') if llm_conf else None
        remote = bool(remote_val) if remote_val is not None else True

    # forbidden_titles: try to load from job_keywords.json if not provided
    if forbidden_titles is None:
        try:
            forbidden_titles = llm_conf.get('forbidden_titles', ['QA', 'Devops', 'Junior', 'Graduate', 'Front End'])
            logging.debug(f"Loaded forbidden_titles from config: {forbidden_titles}")
        except Exception as e:
            logging.debug(f"Could not load forbidden_titles from config: {e}")
            forbidden_titles = ['QA', 'Devops', 'Junior', 'Graduate', 'Front End']

    # Final defaults if nothing found
    job_title = job_title or "Software Engineer"
    location = location or "Tel Aviv, Israel"
    return job_title, location, remote, forbidden_titles

class MCPRunner:
    """Manages the MCP server subprocess"""
    
    def __init__(self):
        self.mcp_process = None

    def init_mcp(self):
        """Initialize services in the child process"""
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
        try:
            # Initialize logging in the child process
            setup_logging()
            
            # Initialize DI container in the child process
            asyncio.run(MCPContainer.init_container())
            
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
        while mcp_runner.mcp_process.is_alive():
            mcp_runner.mcp_process.join(timeout=1.0)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down...")
    finally:
        mcp_runner.stop_mcp()

if __name__ == '__main__':
    main()