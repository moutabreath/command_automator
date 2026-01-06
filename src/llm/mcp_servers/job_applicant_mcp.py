import asyncio, logging, multiprocessing

from multiprocessing import freeze_support
from typing import List

from mcp.server.fastmcp import FastMCP

from llm.mcp_servers.mcp_dependency_container import MCPContainer
from llm.mcp_servers.resume.models import ResumeData

from utils.logger_config import setup_logging

# Initialize FastMCP
mcp = FastMCP("job_applicant_helper")

@mcp.tool()
async def get_resume_files() -> ResumeData:
    """Fetch resume file, applicant name, job description and guidelines"""
    global resume_load_service
    return await resume_loader_service.get_resume_files()

@mcp.tool()
async def search_jobs_from_the_internet(job_title: str | None = None, location: str | None = None, 
                                        remote: bool | str | None = None,
                                        user_id: str | None = None) -> list:
    """Search for jobs from multiple sources (LinkedIn and Glassdoor)"""
    global job_search_service
    if isinstance(remote, str):
        remote = remote.lower() in ('true', '1', 'yes', 'on')
    return await job_search_service.search_jobs_from_internet(job_title, location, remote, user_id)
    
@mcp.tool()
async def get_jobs_from_linkedin(job_title: str | None = None, location: str | None = None,
    remote: bool | str | None = None, user_id: str | None = None) -> list:
    """Search for jobs on LinkedIn"""
    global job_search_service
    if isinstance(remote, str):
        remote = remote.lower() in ('true', '1', 'yes', 'on')
    return await job_search_service.get_jobs_from_linkedin(job_title, location, remote, user_id)

@mcp.tool()
async def get_jobs_from_glassdoor(job_title: str | None = None, location: str | None = None, 
                                  remote: bool | str | None = None, user_id: str | None = None) -> List:
    """Search for jobs on Glassdoor"""
    global job_search_service
    if isinstance(remote, str):
        remote = remote.lower() in ('true', '1', 'yes', 'on')
    return await job_search_service.get_jobs_from_glassdoor(job_title, location, remote, user_id)

@mcp.tool()
async def get_user_applications_for_company(user_id: str, company_name: str) -> dict:
    global job_search_service
    """Get all job applications for a specific user and company"""
    return await job_search_service.get_user_applications_for_company(user_id, company_name)

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
            
            global container
            container = MCPContainer.get_container()
            global resume_loader_service, job_search_service
            resume_loader_service = container.resume_loader_service()
            job_search_service = container.job_search_service()

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