from llm.llm_agents.gemini.gemini_mcp_client import SmartMCPClient

class LLMService():

    def __init__(self):
        self.mcp_client = SmartMCPClient()

 
    async def chat_with_bot(self, prompt: str, image_path:str, should_save_results_to_file: bool, output_file_path: str ) -> str:
       return await self.mcp_client.process_query(prompt, image_path, should_save_results_to_file, output_file_path)
    

        