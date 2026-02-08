import logging
from dependency_injector import providers
from ...core.config import settings
from ...jobs_tracking.services.job_tracking_read_service import JobTrackingReadService

from ..job_search.services.online_job_search.online_job_sources import GlassdoorJobsSearchService, LinkedInJobsSearchService
from ..job_search.services import JobsSaverService, JobsFilterService
from ..job_search.services.online_job_search import  JobSearchRunnerService

from ..resume.services import ResumeLoaderService
from ...jobs_tracking.repository.job_tracking_read_persist_mongo import JobTrackingReadPersistMongo

from ...utils.dependency_container import Container

class MCPContainer(Container):

    config = providers.Configuration()
    
    config.mongo.connection_string.from_value(str(settings.mcp_mongo_uri))
    config.mongo.db_name.from_value(settings.mcp_mongo_db_name)
    config.mongo.application_collection_name.from_value(settings.mcp_job_tracking_collection_name)

    
    # MongoDB persistence
    job_tracking_reader_persist = providers.Resource(
        JobTrackingReadPersistMongo,
        connection_string=config.mongo.connection_string,
        db_name=config.mongo.db_name,
        collection_name=config.mongo.application_collection_name
    )
    
    # Services
    resume_loader_service = providers.Factory(ResumeLoaderService)
    linkedin_jobs_search_service = providers.Factory(LinkedInJobsSearchService)
    glassdoor_jobs_search_service = providers.Factory(GlassdoorJobsSearchService)
    job_saver_service = providers.Factory(JobsSaverService)

    job_tracking_reader_service = providers.Singleton(
        JobTrackingReadService,
        application_persist=job_tracking_reader_persist
    )
    
    jobs_filter_service = providers.Factory(
        JobsFilterService,
        job_tracking_reader_service=job_tracking_reader_service
    )
    
    job_search_service = providers.Factory(
        JobSearchRunnerService,
        linkedin_jobs_scraper_service=linkedin_jobs_search_service,
        glassdoor_jobs_scraper_service=glassdoor_jobs_search_service,
        jobs_saver_service=job_saver_service,
        jobs_filter_service=jobs_filter_service,
        company_mcp_service=job_tracking_reader_service
    )

    @classmethod
    async def init_container(cls) -> 'MCPContainer':
        """Initialize the dependency injection container"""
     
        logging.info("Initializing MCP DI container")
        container = MCPContainer()
        
        try:
            # Initialize resources first
            container.init_resources()
                                    
            cls._container = container
            logging.info("MCP DI container initialized successfully")
            return container
        except Exception as e:
            logging.error(f"Failed to initialize MCP DI container: {e}")
            # Cleanup any partially initialized resources
            try:
                # Clean up manually initialized service if it exists
                container.shutdown_resources()
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup: {cleanup_error}")
            raise