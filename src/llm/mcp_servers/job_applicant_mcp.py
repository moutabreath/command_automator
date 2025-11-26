import logging
import multiprocessing
from multiprocessing import freeze_support
from typing import Dict, List, Type, cast
from typing import TypeVar

from mcp.server.fastmcp import FastMCP

from llm.mcp_servers.job_search.services.glassdoor_jobs_scraper import GlassdoorJobsScraper
from llm.mcp_servers.job_search.services.jobs_saver import JobsSaver
from llm.mcp_servers.job_search.services.linkedin_scraper import LinkedInJobScraper
from llm.mcp_servers.resume.services.resume_loader_service import ResumeLoaderService
from llm.mcp_servers.resume.models import ResumeData
from llm.mcp_servers.services.shared_service import SharedService
from utils.logger_config import setup_logging
from utils.file_utils import JOB_SEARCH_CONFIG_FILE, read_json_file


# Initialize FastMCP
mcp = FastMCP("job_applicant_helper")

# Global variable for service access within the child process
# This will be initialized in the child process only
_shared_services = None


class ServiceNames:
    RESUME_LOADER = 'resume_loader_service'
    LINKEDIN_SCRAPER = 'linkedin_job_scraper'
    GLASSDOOR_SCRAPER = 'glassdoor_jobs_scraper'
    JOB_SAVER = 'job_saver'

# Define a TypeVar that can be any service type
ServiceT = TypeVar('ServiceT')

class ServiceRegistry:
    """Type-safe service registry using generics"""
    
    def __init__(self):
        self._services: Dict[str, object] = {}
    
    def register(self, name: str, service: object) -> None:
        """Register a service with a name"""
        self._services[name] = service
        logging.debug(f"Registered service: {name} -> {type(service).__name__}")
    
    def get(self, name: str, service_type: Type[ServiceT]) -> ServiceT:
        """
        Get a service by name with type safety.
        
        Args:
            name: The service name
            service_type: The expected type of the service (for type checking)
            
        Returns:
            The service instance, typed as ServiceT
            
        Example:
            resume_service = registry.get(ServiceNames.RESUME_LOADER, ResumeLoaderService)
            # resume_service is now typed as ResumeLoaderService
        """
        service = self._services.get(name)
        if service is None:
            raise ValueError(f"Service '{name}' not found in registry")
        
        # Runtime type check (optional but recommended)
        if not isinstance(service, service_type):
            raise TypeError(
                f"Service '{name}' is {type(service).__name__}, "
                f"expected {service_type.__name__}"
            )
        
        return cast(ServiceT, service)
    
    def has(self, name: str) -> bool:
        """Check if a service is registered"""
        return name in self._services
    
    def clear(self) -> None:
        """Clear all registered services"""
        self._services.clear()


# Global service registry instance
_service_registry: ServiceRegistry | None = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance"""
    global _service_registry
    if _service_registry is None:
        raise RuntimeError(
            "Service registry not initialized. "
            "This should only be called in the MCP subprocess."
        )
    return _service_registry


def init_shared_services() -> ServiceRegistry:
    """Initialize services in the child process. Returns the service registry."""
    global _service_registry
    
    logging.info("Initializing shared services in MCP subprocess")
    
    # Create the registry
    registry = ServiceRegistry()
    
    # Register all services
    registry.register(ServiceNames.RESUME_LOADER, ResumeLoaderService())
    registry.register(ServiceNames.LINKEDIN_SCRAPER, LinkedInJobScraper())
    registry.register(ServiceNames.GLASSDOOR_SCRAPER, GlassdoorJobsScraper())
    registry.register(ServiceNames.JOB_SAVER, JobsSaver())
    
    # Store globally
    _service_registry = registry
    
    logging.info("Shared services initialized successfully")
    return registry

@mcp.tool()
async def get_resume_files() -> ResumeData:
    """
    Fetch resume file, applicant name, job description and guidelines
    """    
    try:
        registry = get_service_registry()
        
        # Type-safe service retrieval - IDE will know this is ResumeLoaderService
        resume_loader_service = registry.get(
            ServiceNames.RESUME_LOADER, 
            ResumeLoaderService
        )
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
    

async def _run_linkedin_scraper(job_title: str, location: str, remote: bool) -> list:
    """Run the LinkedIn job scraper"""
    registry = get_service_registry()
    
    # Type-safe retrieval
    linkedin_scraper = registry.get(
        ServiceNames.LINKEDIN_SCRAPER, 
        LinkedInJobScraper
    )
    jobs_saver = registry.get(
        ServiceNames.JOB_SAVER, 
        JobsSaver
    )
    
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

@mcp.tool()
async def get_jobs_from_glassdoor(job_title: str | None = None, location: str | None = None, 
                                  remote: bool | None = None) -> List:
    """
    Search for jobs on Glassdoor.

    Returns:
        List of Job objects
    """
    return await _run_glassdoor_scraper(job_title, location, remote)


async def _run_glassdoor_scraper(job_title: str, location: str, remote: bool, forbidden_titles: list = None) -> List:
    """Run the Glassdoor job scraper"""
    max_pages: int = 3
    max_jobs_per_page: int = 20
    registry = get_service_registry()
    
    glassdoor_scraper = registry.get(
        ServiceNames.GLASSDOOR_SCRAPER, 
        GlassdoorJobsScraper
    )
    job_saver = registry.get(
        ServiceNames.JOB_SAVER, 
        JobsSaver
    )

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
        global _shared_services
        
        try:
            # Initialize logging in the child process
            setup_logging()
            
            # Initialize services in the child process
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
        while mcp_runner.mcp_process.is_alive():
            mcp_runner.mcp_process.join(timeout=1.0)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down...")
    finally:
        mcp_runner.stop_mcp()

if __name__ == '__main__':
    main()