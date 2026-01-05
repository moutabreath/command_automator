import logging

from llm.llm_client.mcp_client import SmartMCPClient
from llm.llm_client.models import MCPResponse, MCPResponseCode

from llm.mcp_servers.job_applicant_mcp import MCPRunner

class LLMService:

    def __init__(self):
        self.mcp_client = SmartMCPClient()

    def run_mcp_server(self):
        # Initialize MCP Runner
        mcp_runner = MCPRunner()
        try:
            mcp_runner.init_mcp()
            logging.info("MCP Runner initialized successfully")
        except Exception as ex:
            logging.exception(f"Failed to initialize MCP Runner: {ex}")
            raise

 
    async def chat_with_bot(self, prompt: str, image_path: str | None, output_file_path: str | None, user_id: str) -> MCPResponse:
        """
        Process a chat query using the MCP client.
        
        Args:
            prompt: The user's text prompt
            image_path: Optional path to an image file
            output_file_path: Optional path for output file
            user_id: User identifier for the query
            
        Returns:
           MCPResponse: The processed response from the MCP client
            
        Note:
            Exceptions are caught and returned as error responses rather than raised.
        """
        try:
            return await self.mcp_client.process_query(prompt, image_path, output_file_path, user_id)
        except Exception as e:
            logging.error(f"Error processing LLM query: {e}", exc_info=True)
            return MCPResponse("Unknown error occurred", MCPResponseCode.ERROR_COMMUNICATING_WITH_LLM)
        