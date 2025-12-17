import logging
from dependency_injector import containers, providers

from llm.mcp_servers.services.mongo_company_persist import MongoCompanyPersist
from llm.mcp_servers.job_search.services.glassdoor_jobs_scraper import GlassdoorJobsScraper
from llm.mcp_servers.job_search.services.jobs_saver import JobsSaver
from llm.mcp_servers.job_search.services.linkedin_scraper import LinkedInJobScraper
from llm.mcp_servers.resume.services.resume_loader_service import ResumeLoaderService
from jobs_tracking.services.job_tracking_service import JobTrackingService
from utils.dependency_container import Container

class MCPContainer(Container):
    
    # MongoDB persistence
    company_mongo_persist = providers.Resource(
        MongoCompanyPersist,
        connection_string=Container.config.mongo.connection_string,
        db_name=Container.config.mongo.db_name
    )
    
    # Services
    resume_loader_service = providers.Factory(ResumeLoaderService)
    linkedin_scraper = providers.Factory(LinkedInJobScraper)
    glassdoor_scraper = providers.Factory(GlassdoorJobsScraper)
    job_saver = providers.Factory(JobsSaver)
    
    # Job tracking service with injected dependency
    job_tracking_service = providers.Factory(
        JobTrackingService,
        application_persist=company_mongo_persist
    )
    
    @classmethod
    async def init_container(cls) -> 'MCPContainer':
        """Initialize the dependency injection container"""
     
        logging.info("Initializing MCP DI container")
        container = MCPContainer()
        
        try:
            # Initialize resources first
            container.init_resources()
            
            # Then initialize MongoDB connection
            await container.company_mongo_persist().initialize_connection()
            
            cls._container = container
            logging.info("MCP DI container initialized successfully")
            return container
        except Exception as e:
            logging.error(f"Failed to initialize MCP DI container: {e}")
            # Cleanup any partially initialized resources
            try:
                container.shutdown_resources()
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup: {cleanup_error}")
            raise