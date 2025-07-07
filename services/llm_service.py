from tabs.llm.llm_agents.gemini.gemini_mcp_client import SmartMCPClient
from tabs.llm.llm_agents.gpt.gpt_agent import GptAgent

class LLMService():

    def __init__(self):
        self.mcp_client = SmartMCPClient()

 
    async def chat_with_bot(self, prompt, file_path = None, applicant_name = "", output_file_path = "", should_save_results_to_file = False ) -> str:
       return await self.mcp_client.process_query(prompt, applicant_name, output_file_path, should_save_results_to_file)
    

        