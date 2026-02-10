import asyncio
import logging


from .api.job_applicant_mcp import mcp
from .setup.mcp_dependency_container import MCPContainer
from ..core.logger_config import setup_logging
from ..core.config import settings


class MCPRunner:
    """Manages the MCP server subprocess"""

    async def run_mcp(self):
        """Run the MCP server in the subprocess"""
        try:
            # Initialize logging in the child process
            setup_logging()
            
            # Initialize DI container in the child process
            await MCPContainer.init_container()

            # Set server configuration
            mcp.settings.mount_path = "/mcp"
            mcp.settings.port = settings.mcp_port
            mcp.settings.host = settings.mcp_host
            
            logging.info("Starting MCP server in subprocess...")
            logging.debug(f"Server URL: http://{mcp.settings.host}:{mcp.settings.port}{mcp.settings.mount_path}")
            
            # Run the server with streamable-http transport
            mcp.run(transport="streamable-http")
        except Exception as ex:
            logging.error(f"Error running MCP server: {ex}", exc_info=True)
            raise

async def main():
    """Main entry point"""
    
    setup_logging()
    
    mcp_runner = MCPRunner()
    await mcp_runner.run_mcp()

if __name__ == '__main__':
    asyncio.run(main())