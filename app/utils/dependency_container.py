import logging
import asyncio
from dependency_injector import containers, providers

from ..llm_proxy.llm_proxy_service import LLMProxyService

from ..jobs_tracking.repository.job_tracking_read_persist_mongo import JobTrackingReadPersistMongo
from ..jobs_tracking.repository.job_tracking_write_persist_mongo import JobTrackingWritePersistMongo
from ..jobs_tracking.services.job_tracking_read_service import JobTrackingReadService
from ..jobs_tracking.services.job_tracking_write_service import JobTrackingWriteService
from ..core.config import settings


class Container(containers.DeclarativeContainer):
    """Dependency injection container"""
    
    _lock = None

    @classmethod
    def _get_lock(cls):
        """Lazily initialize the lock"""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock
        

    # Global container instance
    _container = None

    # Configuration
    config = providers.Configuration()
    
    config.mongo.connection_string.from_value(str(settings.mongo_uri))
    config.mongo.db_name.from_value(settings.mongo_db_name)
    config.mongo.application_collection_name.from_value(settings.job_application_collection_name)
    
    

    job_tracking_read_persist = providers.Resource(
        JobTrackingReadPersistMongo,
        connection_string=config.mongo.connection_string,
        db_name=config.mongo.db_name,
        collection_name=config.mongo.application_collection_name
    )
    job_tracking_read_service = providers.Singleton(
        JobTrackingReadService,
        application_persist=job_tracking_read_persist,
    )

    
    job_tracking_write_persist = providers.Resource(
        JobTrackingWritePersistMongo,
        connection_string=config.mongo.connection_string,
        db_name=config.mongo.db_name,
        collection_name=config.mongo.application_collection_name
    )
    job_tracking_write_service = providers.Singleton(
        JobTrackingWriteService,
        application_persist=job_tracking_write_persist
    )

    llm_proxy_service = providers.Singleton(
        LLMProxyService,
        mcp_server_url=f"http://{settings.mcp_host}:{settings.mcp_port}/mcp"
    )



    @classmethod
    def get_container(cls) -> 'Container':
        """Get the global container instance"""
        if cls._container is None:
            raise RuntimeError("Container not initialized")
        return cls._container
    
    @classmethod
    async def init_container(cls) -> 'Container':
        """Initialize the dependency injection container"""
        async with cls._get_lock():
            if cls._container is not None:
                return cls._container

            logging.info("Initializing DI container in MCP subprocess")

            # Create and configure container
            container = Container()
            # Initialize resources
            container.init_resources()

            cls._container = container
            logging.info("DI container initialized successfully")
            return container