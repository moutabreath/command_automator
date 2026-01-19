from abc import ABC, abstractmethod
import logging

class AbstractMongoPersist(ABC):
    __slots__ = ('connection_string', 'db_name', 'async_client', 'async_db')
    
    def __init__(self, connection_string: str, db_name: str):  
        self.connection_string = connection_string
        self.db_name = db_name
        # Initialize slots that will be set later
        self.async_client = None
        self.async_db = None
        
        logging.getLogger("pymongo").setLevel(logging.WARNING)
    
    def __repr__(self):
        # Hide sensitive connection string, only show database name and connection status
        conn_status = "connected" if self.async_client is not None else "not connected"
        # Optionally show sanitized connection info (just host, no credentials)
        try:
            # Parse connection string to show only host (remove credentials)
            if self.connection_string.startswith('mongodb'):
                # Simple extraction - just show it's a mongodb connection
                conn_info = "mongodb://***"
            else:
                conn_info = "***"
        except:
            conn_info = "***"
        
        return f"{self.__class__.__name__}(db={self.db_name!r}, connection={conn_info}, status={conn_status})"
    
    @classmethod
    async def create(cls, connection_string: str, db_name: str) -> "AbstractMongoPersist":
        """
        Async Factory: The ONLY safe way to instantiate persistence classes.
        This guarantees that the returned instance is fully connected and initialized.
        """
        # 1. Create the instance (sync)
        instance = cls(connection_string, db_name)
        
        # 2. Run the async initialization immediately
        # This will attach to the CURRENT running loop (Background Loop)
        await instance.initialize_connection()
        
        # 3. Return the ready-to-use instance
        return instance

    async def initialize_connection(self):
        """
        Internal initialization logic. 
        Should be called automatically by create(), not manually.
        """
        self._init_motor_client()
            
        self.async_db = self.async_client[self.db_name]

        # disable processing of pywebview of the motor objects, which are not serializable
        self.async_client._serializable = False
        self.async_db._serializable = False

    @abstractmethod
    def _init_motor_client(self):
        pass