import logging
import os
import json
import aiohttp
import logging
import os
import json
from google import genai
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from google.genai import types
from google.genai.types import GenerateContentResponse
from PIL import Image
import io

from commands_automator.llm.llm_agents.agent_services.resume_refiner_service import ResumeRefinerService
from commands_automator.llm.llm_agents.agent_services.resume_saver_service import ResumeSaverService


class SmartMCPClient:
    """An intelligent client that uses Gemini to decide when to use MCP tools."""

    def __init__(self, mcp_server_url=None, ):
        # MCP server settings
        self.mcp_server_url = mcp_server_url or "http://127.0.0.1:8765/mcp"
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        self.gemini_client: genai.Client = genai.Client(api_key=self.api_key)
        self.resume_chat = self.gemini_client.chats.create(
            model="gemini-2.5-flash",
            history=[]
        )
        config = {
            "temperature": 0,   # Creativity (0: deterministic, 1: high variety)
            "top_p": 0.95,       # Focus on high-probability words
            "top_k": 64,        # Consider top-k words for each step
            "max_output_tokens": 8192,  # Limit response length
            "response_mime_type": "application/json",  # Output as plain text
        }

        self.resume_chat._config = config
        self.resume_refiner_service = ResumeRefinerService(self.resume_chat)

    async def decide_tool_usage(self, query, available_tools, session):
        """
        Use Gemini to decide which tool to use based on the query
        
        Args:
            query: The user's question
            available_tools: List of available tools from the MCP server
            
        Returns:
            tuple: (tool_name, tool_args) or (None, None) if no tool should be used
        """
        # Quick filter for common greetings and chitchat - never use tools for these
        common_greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", 
                           "how are you", "what's up", "howdy"]
        
        # If query is just a simple greeting, don't use a tool
        if query.lower() in common_greetings:
            logging.debug("Query appears to be a simple greeting or too short - not using tools")
            return None, None
            
        if not self.api_key:
            # More selective rule-based logic if no API key
            relevant_terms = ['resume', 'ATS']
            
            # Only use the tool if query has specific relevant keywords
            if 'get_resume_files' in available_tools and any(term in query.lower() for term in relevant_terms):
                return 'get_resume_files', {}
            return None, None
            
        try:
            messages = await self.init_messages(query, available_tools, session)
            self.resume_chat._config["response_mime_type"] = "application/json"
            generated_response: GenerateContentResponse = self.resume_chat.send_message(messages)
            decision = json.loads(generated_response.model_dump_json())
            tools_text = decision.get('candidates')[0].get('content').get('parts')[0].get('text')
            tools_json = json.loads(tools_text)
            selected_tool = tools_json.get("tool")
            args = tools_json.get("args", {})
            if selected_tool and selected_tool in available_tools:
                logging.debug(f"Gemini decided to use tool: {selected_tool}")
                return selected_tool, args
            else:
                logging.debug("Gemini decided not to use any tools")
                return None, None
        except Exception as e:
            logging.error(f"Error using Gemini for tool decision {e}", exc_info=True)
            # Fall back to direct tool usage if error occurs
            if 'get_resume_files' in available_tools:
                return 'get_resume_files', {'query': query}
            return None, None
        
    async def init_messages(self, query, available_tools, session):
    # Get tool schemas from MCP server
        tools_response = await session.list_tools()
        tool_descriptions = {}
        
        for tool in tools_response.tools:
            if tool.name in available_tools:
                # Include parameter info in description
                params = tool.inputSchema.get('properties', {}) if tool.inputSchema else {}
                param_info = f" (Parameters: {list(params.keys())})" if params else " (No parameters)"
                tool_descriptions[tool.name] = f"{tool.description}{param_info}"
        
        available_descriptions = tool_descriptions
        system_prompt = self.init_system_prompt(available_descriptions, query)
        return system_prompt
    
    def init_system_prompt(self, available_descriptions, query):
        return f"""You are a tool selection assistant. 
Based on the user's query, determine if any of these available tools should be used:
{json.dumps(available_descriptions, indent=2)}

IMPORTANT: Only use a tool if the query is asking about one of the following:
 1. Adjust resume to job description.
 2. Searching jobs from the internet.
If you have already used a tool before, infer if you should use it again. For example if the user query is
'again', and you have used a tool in the previous query, you may decide to use the tool you previously
used just before this query.


For general greetings, chitchat, or questions unrelated to resume content, 
DO NOT use any tools. Examples where NO tool should be used:
- "Hello"
- "How are you?"
- "What's the weather like?"
- "Tell me about Python"
- "What time is it?"

If a tool should be used, respond in JSON format:
{{
  "tool": "tool_name",
  "args": {{
    "query": "user query or relevant part"
  }}
}}
If the tool definition has no paramters respond in JSON fomrat:
{{
  "tool": "tool_name",
  "args": {{}}
}}
If no tool should be used and you should answer the query directly, respond with:
{{
  "tool": null,
  "args": null
}}

Be selective and conservative with tool usage. Be concise. Only output valid JSON.
If no tool should be selected, respond the query directly.
Query: {query}
"""
    

    async def is_mcp_server_ready(self, timeout=2):
        try:
            async with aiohttp.ClientSession() as session, \
                       session.get(self.mcp_server_url, timeout=timeout) as resp:
                # You can check for a specific status code if needed
                return resp.status == 406 # (= NOt Accepatable) Server is probably reacheable.
        except Exception as e:
            logging.error(f"MCP server not ready {e}", exc_info=True)
            return False
    
    async def process_query(
        self,
        query: str,
        base64_decoded: str,
        output_file_path: str,
    ) -> str:
        """
        Process a user query using a combination of Gemini and MCP server.

        Args:
            query: The user's question or request
            base64_decoded: Base64 encoded image data (optional)
            output_file_path: Path to save output files
        Returns:
            The response as a string
        """
        try:
            if not await self.is_mcp_server_ready():
                return self.call_gemini_api_directly(query, base64_decoded)

            logging.debug(f"Connecting to MCP server at {self.mcp_server_url}...")

            async with streamablehttp_client(self.mcp_server_url) as (
                read_stream,
                write_stream,
                _,
            ), ClientSession(read_stream, write_stream) as session:
                logging.debug("Established streamable_http and Created MCP client session")

                await session.initialize()
                logging.debug("Successfully initialized MCP session")

                available_tools = await self.get_available_tools(session)

                # Use Gemini to decide if a tool should be used
                selected_tool, tool_args = await self.decide_tool_usage(
                    query, available_tools, session
                )

                # If Gemini decided to use a tool, call it
                if selected_tool:
                    return await self.use_tool(
                        selected_tool,
                        tool_args,
                        session,
                        output_file_path,
                    )
                else:
                    return self.call_gemini_api_directly(query, base64_decoded)

        except Exception as e:
            logging.error(f"Error communicating with Gemini or MCP server {e}", exc_info=True)
            return "An error occurred while processing your request. Please try again."
        
    async def use_tool(self, selected_tool, tool_args, session, output_file_path):
        logging.debug(f"Using tool: {selected_tool} with args: {tool_args}")
        try:
            response = await session.call_tool(selected_tool, tool_args)
           
            if response is None or response.isError:
                raise Exception("Tool execution failed with error")        
        except Exception as e:
            logging.error(f"Error using tool: {e}", exc_info=True)
            return "Sorry, I couldn't execute tool."
      
        tool_result = response.content[0].text
        logging.debug(f"Tool response received ({len(tool_result)} characters)")
        
        if selected_tool == 'get_resume_files':
            return self.refine_resume(tool_result, output_file_path)
        return tool_result
    
    def refine_resume(self, tool_result, output_file_path):
        if self.api_key:
            try:
                return self.resume_refiner_service.refine_resume(tool_result, output_file_path)
            except Exception as e:
                logging.error(f"Error refining resume: {e}", exc_info=True)
                return tool_result  # Fallback to raw result
        else:
            return tool_result

        
    def call_gemini_api_directly(self, query, base64_decoded):
        if self.api_key:
            try:
                self.resume_chat._config["response_mime_type"] = "text/plain"
                if base64_decoded:
                    image = Image.open(io.BytesIO(base64_decoded))
                    gemini_response = self.resume_chat.send_message([query, image])
                else:
                    gemini_response = self.resume_chat.send_message(query)
                gemini_text = gemini_response.text()
                return gemini_text
            except Exception as e:
                logging.error(f"Error using Gemini {e}", exc_info=True)
                return "Sorry, I couldn't process your request with Gemini or MCP tools."

    async def get_available_tools(self, session):
        try:
            tools_response = await session.list_tools()
            available_tools = [tool.name for tool in tools_response.tools]
            logging.debug(f"Available tools: {available_tools}")
        except Exception as e:
            logging.debug(f"Could not list tools: {e}")
            available_tools = []
        return available_tools


    def convert_none_to_empty_string(self, text):
        if text == None:
            return ""
        return text



    def get_files_to_attach(self, image_file_path):
        logging.debug("got file to upload")
        self.delete_files()
        file = self.upload_to_gemini(image_file_path)
        file_data : types.FileData = types.FileData(file_uri=file.uri, mime_type="image/png")
        return types.Part(file_data=file_data)
    
    def upload_to_gemini(self, path, mime_type=None):
        """Uploads a file to Gemini for use in prompts."""
        file = self.gemini_client.files.upload(file=path)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file    

    def delete_files(self):
        for f in self.gemini_client.files.list():
            self.gemini_client.files.delete(name=f.name)