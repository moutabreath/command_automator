import logging
from dependency_injector import providers

from llm.mcp_servers.persistence.mcp_company_mongo_persist import MCPCompanyMongoPersist
from llm.mcp_servers.job_search.services.glassdoor_jobs_scraper import GlassdoorJobsScraper
from llm.mcp_servers.job_search.services.jobs_saver import JobsSaver
from llm.mcp_servers.job_search.services.linkedin_jobs_scraper import LinkedInJobsScraper
from llm.mcp_servers.services.company_mcp_service import CompanyMCPService
from llm.mcp_servers.resume.services.resume_loader_service import ResumeLoaderService
from utils.dependency_container import Container

class MCPContainer(Container):
    
    # MongoDB persistence
    mcp_mongo_company_persist = providers.Resource(
        MCPCompanyMongoPersist,
        connection_string=Container.config.mongo.connection_string,
        db_name=Container.config.mongo.db_name
    )
    
    # Services
    resume_loader_service = providers.Factory(ResumeLoaderService)
    linkedin_scraper = providers.Factory(LinkedInJobsScraper)
    glassdoor_scraper = providers.Factory(GlassdoorJobsScraper)
    job_saver = providers.Factory(JobsSaver)
    
    # Company MCP Service
    company_mcp_service = providers.Factory(
        CompanyMCPService,
        company_persist=mcp_mongo_company_persist
    )
    
    @classmethod
    async def init_container(cls) -> 'MCPContainer':
        """Initialize the dependency injection container"""
     
        logging.info("Initializing MCP DI container")
        container = MCPContainer()
        
        try:
            # Initialize resources first
            container.init_resources()
            
            company_mcp_service = container.company_mcp_service()
            # Then initialize MongoDB connection
            await company_mcp_service.initialize()
            
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