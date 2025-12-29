import logging
import asyncio
from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
    """Dependency injection container"""        

    # Global container instance
    _container = None
    _lock = asyncio.Lock()

    # Configuration
    config = providers.Configuration()
    
    config.mongo.connection_string.from_value("mongodb://localhost:27017/")
    config.mongo.db_name.from_value("job_tracker")

    @classmethod
    def get_container(cls) -> 'Container':
        """Get the global container instance"""
        if cls._container is None:
            raise RuntimeError("Container not initialized")
        return cls._container
    
    @classmethod
    async def init_container(cls) -> 'Container':
        """Initialize the dependency injection container"""

        
        logging.info("Initializing DI container in MCP subprocess")
        
        # Create and configure container
        container = Container()
        # Initialize resources
        container.init_resources()
        
        
        cls._container = container
        logging.info("DI container initialized successfully")
        return container