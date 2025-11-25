import logging

from llm.llm_agents.mcp_client import SmartMCPClient
from llm.llm_agents.mcp_response import MCPResponse
from llm.llm_agents.mcp_response import MCPResponseCode

class LLMService:

    def __init__(self):
        self.mcp_client = SmartMCPClient()

 
    async def chat_with_bot(
        self,
        prompt: str,
        image_path: str | None,
        output_file_path: str | None
    ) -> MCPResponse:
        """
        Process a chat query using the MCP client.
        
        Args:
            prompt: The user's text prompt
            image_path: Optional path to an image file
            output_file_path: Optional path for output file
            
        Returns:
           MCPResponse: The processed response from the MCP client
            
        Note:
            Exceptions are caught and returned as error responses rather than raised.
        """
        try:
            return await self.mcp_client.process_query(prompt, image_path, output_file_path)
        except Exception as e:
            logging.error(f"Error processing LLM query: {e}", exc_info=True)
            return MCPResponse("Unknown error occurred", MCPResponseCode.ERROR_COMMUNICATING_WITH_LLM)
        