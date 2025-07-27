from llm.llm_agents.gemini.gemini_mcp_client import SmartMCPClient

class LLMService():

    def __init__(self):
        self.mcp_client = SmartMCPClient()

 
    async def chat_with_bot(
        self,
        prompt: str,
        image_path: str | None,
        should_save_results_to_file: bool,
        output_file_path: str | None
    ) -> str:
        """
        Process a chat query using the MCP client.
        
        Args:
            prompt: The user's text prompt
            image_path: Optional path to an image file
            should_save_results_to_file: Whether to save results to file
            output_file_path: Optional path for output file
            
        Returns:
            The processed response as a string
            
        Raises:
            Exception: If the MCP client fails to process the query
        """
        try:
            return await self.mcp_client.process_query(
                prompt, image_path, should_save_results_to_file, output_file_path
            )
        except Exception as e:
            # Log the error and re-raise with context
            print(f"Error processing LLM query: {e}", exc_info=True)
            raise