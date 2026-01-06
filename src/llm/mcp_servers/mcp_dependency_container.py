import logging
from dependency_injector import providers

from llm.mcp_servers.job_search.services.job_scrapers.glassdoor_jobs_scraper_service import GlassdoorJobsScraperService
from llm.mcp_servers.job_search.services.job_scrapers.linkedin_jobs_scraper_service import LinkedInJobsScraperService
from llm.mcp_servers.job_search.services.jobs_saver_service import JobsSaverService
from llm.mcp_servers.services.job_search_service import JobSearchService
from llm.mcp_servers.job_search.services.jobs_filter_service import JobsFilterService
from llm.mcp_servers.resume.services.resume_loader_service import ResumeLoaderService
from llm.mcp_servers.persistence.mcp_company_mongo_persist import MCPCompanyMongoPersist
from llm.mcp_servers.services.company_mcp_service import CompanyMCPService

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
    linkedin_jobs_scraper_service = providers.Factory(LinkedInJobsScraperService)
    glassdoor_jobs_scraper_service = providers.Factory(GlassdoorJobsScraperService)
    job_saver_service = providers.Factory(JobsSaverService)

    # Company MCP Service
    company_mcp_service = providers.Singleton(
        CompanyMCPService,
        company_persist=mcp_mongo_company_persist
    )
    
    # Jobs Filter Service
    jobs_filter_service = providers.Factory(
        JobsFilterService,
        company_mcp_service=company_mcp_service
    )
    
    job_search_service = providers.Factory(
        JobSearchService,
        linkedin_jobs_scraper_service=linkedin_jobs_scraper_service,
        glassdoor_jobs_scraper_service=glassdoor_jobs_scraper_service,
        jobs_saver_service=job_saver_service,
        jobs_filter_service = jobs_filter_service,
        company_mcp_service=company_mcp_service
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
                # Clean up manually initialized service if it exists
                if 'company_mcp_service' in locals():
                    await company_mcp_service.shutdown()
                container.shutdown_resources()
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup: {cleanup_error}")
            raise