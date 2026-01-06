import json, aiohttp, logging, asyncio


from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession

from llm.gemini.models import LLMResponse, LLMResponseCode, LLMToolResponse, LLMToolResponseCode
from llm.gemini.gemini_client_wrapper import GeminiClientWrapper

from llm.llm_client.models import MCPResponse, MCPResponseCode
from llm.llm_client.services.job_unifier_service import JobUnifierService
from llm.llm_client.services.resume_refiner_service import ResumeRefinerService


class SmartMCPClient:
    """An intelligent client that uses LLM to decide when to use MCP tools."""

    def __init__(self, mcp_server_url=None):
        # MCP server settings
        self.mcp_server_url = mcp_server_url or "http://127.0.0.1:8765/mcp"
       
        self.gemini_client_wrapper: GeminiClientWrapper = GeminiClientWrapper()
        self.resume_chat = self.gemini_client_wrapper.init_chat()
        self.resume_refiner_service = ResumeRefinerService(self.resume_chat, self.gemini_client_wrapper)
        self.job_unifier_service = JobUnifierService(self.gemini_client_wrapper)
        
        # List of MCP tools with only their name
        self.available_tools_names = []

        # List of MCP tools with their name and parameters
        self.available_tools_descriptions = {}

    async def process_query( self,  query: str, base64_decoded: str = None, output_file_path: str = None, user_id: str = None) -> MCPResponse:
        """
        Process a user query using a combination of Gemini and MCP server.

        Args:
            user_id: The user's id
            query: The user's question or request
            base64_decoded: Base64 encoded image data (optional)
            output_file_path: Path to save output files
        Returns:
            The response as a MCPResponse
        """
        try:
            if not await self._is_mcp_server_ready():
                llm_response = await self.gemini_client_wrapper.get_response_from_gemini(query, self.resume_chat, base64_decoded)
                return self._convert_llm_response_to_mcp_response(llm_response)

            async with streamable_http_client(self.mcp_server_url) as ( read_stream, write_stream, _,), ClientSession(read_stream, write_stream) as session:
                
                logging.debug("Established streamable_http and Created MCP client session")

                await session.initialize()
                logging.debug("Successfully initialized MCP session")

                # Use Gemini to decide if a tool should be used
                tool_response = await self._decide_tool_usage(query, user_id, session)

                if tool_response.code == LLMToolResponseCode.USING_TOOL:
                    if tool_response.selected_tool is None:
                        logging.error("Error with tool seletion")
                        return MCPResponse(code=MCPResponseCode.ERROR_WITH_TOOL_RESPONSE,text="Error with tool selection")
                    selected_tool,tool_args = tool_response.selected_tool, tool_response.args
                    return await self._use_tool(selected_tool, tool_args, session, output_file_path)
                elif tool_response.code == LLMToolResponseCode.MODEL_OVERLOADED:
                    return MCPResponse(tool_response.error_message, MCPResponseCode.ERROR_MODEL_OVERLOADED)
                else:
                    agent_response = await self.gemini_client_wrapper.get_response_from_gemini(query, self.resume_chat, base64_decoded)
                    return self._convert_llm_response_to_mcp_response(agent_response)                
        except asyncio.CancelledError:
            logging.debug("MCP query was cancelled")
            return MCPResponse("Operation was cancelled", MCPResponseCode.OPERATION_CANCELLED)
        except Exception as e:
            logging.exception(f"Error communicating with Gemini or MCP server {e}")
            return MCPResponse("An error occurred while processing your request. Please try again.", MCPResponseCode.ERROR_COMMUNICATING_WITH_LLM)
        
    def _convert_llm_response_to_mcp_response(self, llm_response: LLMResponse) -> MCPResponse:
        match llm_response.code:
            case LLMResponseCode.OK:
                return MCPResponse(llm_response.text, MCPResponseCode.OK)
            case LLMResponseCode.MODEL_OVERLOADED:
                return MCPResponse(llm_response.text, MCPResponseCode.ERROR_MODEL_OVERLOADED)
            case LLMResponseCode.RESOURCE_EXHAUSTED:
                return MCPResponse(llm_response.text, MCPResponseCode.ERROR_MODEL_QUOTA_EXCEEDED)
            case _:
                return MCPResponse(llm_response.text, MCPResponseCode.ERROR_COMMUNICATING_WITH_LLM)

    async def _is_mcp_server_ready(self, timeout=2):
        try:
            async with aiohttp.ClientSession() as session, \
                       session.get(self.mcp_server_url, timeout=timeout) as resp:
                # You can check for a specific status code if needed
                return resp.status == 406 # (= Not Accepatable) Server is probably reacheable.
        except Exception as e:
            logging.exception(f"MCP server not ready {e}")
            return False
        
    def _is_greeting_query(self, query: str) -> bool:
        """Check if query is a simple greeting that shouldn't use tools"""
        if not query:
            return False
        
        single_word_greetings = ["hello", "hi", "hey", "greetings", "howdy"]
        multi_word_greetings = ["good morning", "good afternoon", "how are you", "what's up"]
        
        query_lower = query.lower().strip()
        query_words = query_lower.split()
        
        # Check single-word greetings
        if query_words and query_words[0] in single_word_greetings and len(query_words) <= 3:
            return True
        
        # Check multi-word greetings
        if any(query_lower.startswith(greeting) for greeting in multi_word_greetings) and len(query_words) <= 4:
            return True
            
        return False
    
    async def _decide_tool_usage(self, query:str, user_id:str, session:ClientSession) -> LLMToolResponse:
        """
        Use LLM to decide which tool to use based on the query
        
        Args:
            query: The user's question
            
        Returns:
            LLMToolResponse
        """
        # Quick filter for common greetings and chitchat - never use tools for these
        if self._is_greeting_query(query):
            logging.debug("Query appears to be a simple greeting or too short - not using tools")
            return LLMToolResponse(code=LLMToolResponseCode.NOT_USING_TOOL, selected_tool=None, args=None , error_message="Query is greetings query")
        
        response =  self._get_tool_and_params_using_keywords(query)
        
        if response.code == LLMToolResponseCode.USING_TOOL:
            return response
        
        await self._init_available_tools_descriptions(session)
            
        message = self._init_system_prompt(query, user_id)
        
        return self.gemini_client_wrapper.get_mcp_tool_response(prompt=message,
                                                            chat=self.resume_chat,
                                                            available_tools=self.available_tools_names)
   
    def _get_tool_and_params_using_keywords(self, query:str) -> LLMToolResponse:
        query = query.lower().strip()
        if "resume" in query and "job" in query:
            return LLMToolResponse(code=LLMToolResponseCode.USING_TOOL, selected_tool="get_resume_files", args=None)
        if ("search" in query or "find" in query) and ("jobs" in query or "job" in query) and "internet" in query:
            return LLMToolResponse(code=LLMToolResponseCode.USING_TOOL, selected_tool="search_jobs_from_the_internet", args=None)
        return LLMToolResponse(code=LLMToolResponseCode.NOT_USING_TOOL, selected_tool=None, args=None)
        
         
    async def _init_available_tools_descriptions(self, session: ClientSession):
        if (self.available_tools_names != []):
            return 
        
        session_tools = await self._init_session_tools(session)
        if session_tools == None:
            return
        
        self.available_tools_names = [tool.name for tool in session_tools.tools]
        logging.debug(f"Available tools: {self.available_tools_names}")
        
        for tool in session_tools.tools:
            if tool.name in self.available_tools_names:
                # Include parameter info in description
                params = tool.inputSchema.get('properties', {}) if tool.inputSchema else {}
                param_info = f" (Parameters: {list(params.keys())})" if params else " (No parameters)"
                self.available_tools_descriptions[tool.name] = f"{tool.description}{param_info}"        

    
    async def _init_session_tools(self, session: ClientSession):
        try:
            session_tools = await session.list_tools()        
        except Exception as e:
            logging.debug(f"Could not list tools: {e}")
            return None
        return session_tools
            
    
    def _init_system_prompt(self, query:str, user_id:str) -> str:
        return f"""You are a tool selection assistant. 
Based on the user's query, determine if any of the available tools should be used.
{json.dumps(self.available_tools_descriptions, indent=2)}
IMPORTANT: Use a tool if the query is asking about one of the following:
 1. Adjust resume to job description.
 2. Searching for jobs on the internet.
 3. Getting information about jobs I have already applied to. Infer the company name if possible.

If a tool should be used, respond in JSON format:
{{
  "tool": "tool_name",
  "args": {{"param_name": "param_value"}}
}}
If the tool definition has no parameters respond in JSON format:
{{
  "tool": "tool_name",
  "args": {{}}
}}
For tools that require user_id use: {user_id}
Be selective and conservative with tool usage. Be concise. Only output valid JSON.
If no tool should be selected, respond to the query directly. Query: {query}
"""
    
    async def _use_tool(self, selected_tool, tool_args, session: ClientSession, output_file_path: str):
        logging.debug(f"Using tool: {selected_tool} with args: {tool_args}")
        try:
            response = await session.call_tool(selected_tool, tool_args)
            
            if response is None:
                return MCPResponse(f"Tool execution failed to return an answer", MCPResponseCode.ERROR_TOOL_RETURNED_NO_RESULT)
            if not response.content or len(response.content) == 0:
                return MCPResponse("Tool execution returned empty response", MCPResponseCode.ERROR_TOOL_RETURNED_NO_RESULT)
            if response.isError:
                error_msg = response.content[0].text if response and response.content and len(response.content) > 0  else "Unknown error"
                logging.error(f"Tool execution returned error: {error_msg}")
                return MCPResponse(f"Tool execution returned error: {error_msg}", MCPResponseCode.ERROR_TOOL_RETURNED_NO_RESULT)

            tool_result = response.content[0].text
            logging.debug(f"Tool response received ({len(tool_result)} characters)")

            return await self._use_tool_result(selected_tool, tool_result, output_file_path)
            
        except Exception as e:
            logging.exception(f"Error using tool: {e}")
            return MCPResponse("Sorry, I couldn't execute tool.", MCPResponseCode.ERROR_COMMUNICATING_WITH_TOOL)
        
    async def _use_tool_result(self, selected_tool, tool_result, output_file_path) -> MCPResponse:
        if selected_tool == 'get_resume_files':
            return await self.resume_refiner_service.refine_resume(tool_result, output_file_path)
        if selected_tool == 'search_jobs_from_the_internet':
            return await self.job_unifier_service.get_unified_jobs()
        return MCPResponse(tool_result, MCPResponseCode.OK)