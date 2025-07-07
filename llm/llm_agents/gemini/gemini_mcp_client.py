import logging
import os
import json
from google import genai
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from google.genai import types
from google.genai.types import GenerateContentResponse

from llm.llm_agents.agent_services.resume_saver_service import ResumeSaverService 


class SmartMCPClient:
    """An intelligent client that uses Gemini to decide when to use MCP tools."""

    def __init__(self, mcp_server_url=None, ):
        # MCP server settings
        self.mcp_server_url = mcp_server_url or "http://127.0.0.1:8765/mcp"
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        self.gemin_client: genai.Client = genai.Client(api_key=self.api_key)        
        self.chat = self.gemin_client.chats.create(
                    model="gemini-2.0-flash",
                    history= []
        )
        config = {
            "temperature": 0,   # Creativity (0: deterministic, 1: high variety)
            "top_p": 0.95,       # Focus on high-probability words
            "top_k": 64,        # Consider top-k words for each step
            "max_output_tokens": 8192,  # Limit response length
            "response_mime_type": "application/json",  # Output as plain text
        }
        self.chat._config = config
        self.resume_saver_service: ResumeSaverService  = ResumeSaverService()

    async def decide_tool_usage(self, query, available_tools):
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
            print("Query appears to be a simple greeting or too short - not using tools")
            return None, None
            
        if not self.api_key:
            # More selective rule-based logic if no API key
            relevant_terms = ['resume', 'ATS']
            
            # Only use the tool if query has specific relevant keywords
            if 'get_resume_files' in available_tools and any(term in query.lower() for term in relevant_terms):
                return 'get_resume_files', {'query': query}
            return None, None
            
        try:         
            messages = await self.init_messages(query, available_tools)
            self.chat._config["response_mime_type"] = "application/json"
            generated_response: GenerateContentResponse = self.chat.send_message(messages)
            decision = json.loads(generated_response.model_dump_json())
            tools_text = decision.get('candidates')[0].get('content').get('parts')[0].get('text')
            tools_json = json.loads(tools_text)
            selected_tool = tools_json.get("tool")
            args = tools_json.get("args", {})
            
            if selected_tool and selected_tool in available_tools:
                print(f"Gemini decided to use tool: {selected_tool}")
                return selected_tool, args
            else:
                print("Gemini decided not to use any tools")
                return None, None                
        except Exception as e:
            logging.error(f"Error using Gemini for tool decision: {e}")
            # Fall back to direct tool usage if error occurs
            if 'get_resume_files' in available_tools:
                return 'get_resume_files', {'query': query}
            return None, None
        
    async def init_messages(self, query, available_tools):
        tool_descriptions = {
            'get_resume_files': "create a resume and a cover letter based on the job description and raw resume"
        }
        # Prepare descriptions for available tools
        available_descriptions = {tool: tool_descriptions.get(tool, f"Tool: {tool}") 
                                    for tool in available_tools}
        
        system_prompt = self.init_system_prompt(available_descriptions, query)
        return system_prompt
    
    def init_system_prompt(self, available_descriptions, query):
        return f"""You are a tool selection assistant. 
Based on the user's query, determine if any of these available tools should be used:
{json.dumps(available_descriptions, indent=2)}

IMPORTANT: Only use a tool if the query is SPECIFICALLY asking about adjust resume to job description


For general greetings, chitchat, or questions unrelated to Internet Israel content, 
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

If no tool should be used and you should answer the query directly, respond with:
{{
  "tool": null,
  "args": null
}}

Be selective and conservative with tool usage. Be concise. Only output valid JSON.
Query: {query}
"""
    
    async def process_query(self, query: str, output_file_path = "", should_save_results_to_file = False) -> str:
        """
        Process a user query using a combination of Gemini and MCP server.
        
        Args:
            query: The user's question or request
        Returns:
            The response as a string
        """
        try:
            logging.debug(f"Connecting to MCP server at {self.mcp_server_url}...")
            async with streamablehttp_client(self.mcp_server_url) as (read_stream, write_stream, _):
                logging.debug("Established streamable_http connection")
                
                async with ClientSession(read_stream, write_stream) as session:
                    logging.debug("Created MCP client session")
                    
                    # Initialize the session
                    await session.initialize()
                    logging.debug("Successfully initialized MCP session")
                    
                    # Get available tools
                    try:
                        tools_response = await session.list_tools()
                        available_tools = [tool.name for tool in tools_response.tools]
                        logging.debug(f"Available tools: {available_tools}")
                    except Exception as e:
                        logging.debug(f"Could not list tools: {e}")
                        available_tools = []
                    
                    # Use Gemini to decide if a tool should be used
                    selected_tool, tool_args = await self.decide_tool_usage(query, available_tools)
                    
                    # If Gemini decided to use a tool, call it
                    if selected_tool:
                        logging.debug(f"Using tool: {selected_tool} with args: {tool_args}")
                        response = await session.call_tool(selected_tool, tool_args)
                        if response == None:
                            return None
                        tool_result = response.content[0].text
                        logging.debug(f"Tool response received ({len(tool_result)} characters)")
                        
                        if self.api_key:
                                try:
                                    resume_data_dict = json.loads(tool_result)
                                except ValueError:
                                    logging.error("error with json structure of tool")
                                    return None
                                prompt = self.format_prompts_for_resume(resume_data_dict)
                                self.chat._config["response_mime_type"] = "text/plain"
                                gemini_response = self.chat.send_message(prompt)
                                resume_text = gemini_response._get_text()
                                if should_save_results_to_file:
                                   resume_highlighted_sections = self.convert_none_to_empy_string(resume_data_dict.get('resume_highlighted_sections', ''))
                                   applicant_name = resume_data_dict.get('applicant_name', '')
                                   self.resume_saver_service.save_resume(resume_text, output_file_path, applicant_name, resume_highlighted_sections)
                                cover_letter_guidelines = resume_data_dict.get('cover_letter_guidelines', '')
                                if (cover_letter_guidelines != None):
                                    gemini_response = self.chat.send_message(cover_letter_guidelines)
                                    cover_letter_text = gemini_response._get_text()
                                if (should_save_results_to_file):
                                     self.resume_saver_service.save_cover_letter(cover_letter_text, output_file_path, applicant_name)
                                return resume_text +"\n\n" + cover_letter_text
                        else:
                            return tool_result
                    else:
                        if self.api_key:
                            try:
                                gemini_response = self.chat.send_message(query)
                                gemini_text = gemini_response._get_text()
                                return gemini_text
                            except Exception as e:
                                logging.debug(f"Error using Gemini: {e}")
                                return "Sorry, I couldn't process your request with Gemini or MCP tools."
                        else:
                            return "No suitable tool found and Gemini API key not provided."
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            logging.error("error communicating with gemini", e)
            return None
        
    def format_prompts_for_resume(self, resume_data_dict):       
        general_guidleines = resume_data_dict.get('general_guidelines', '')
        resume = resume_data_dict.get('resume', '')        
        jobs_desc = self.convert_none_to_empy_string(resume_data_dict.get('job_description', ''))
     
        prompt = f"{general_guidleines}\n\n{resume}\n\n\n"
        prompt += jobs_desc
        return prompt 

    def convert_none_to_empy_string(self, text):
        if text == None:
            return ""
        return text



    def get_files_to_attach(self, image_file_paths):
        logging.debug("got file to upload")
        self.delete_files()
        file = self.upload_to_gemini(image_file_paths)
        file_data : types.FileData = types.FileData(file_uri=file.uri, mime_type="image/png")
        return types.Part(file_data=file_data)
    
    def upload_to_gemini(self, path, mime_type=None):
        """Uploads a file to Gemini for use in prompts."""
        file = self.gemin_client.files.upload(file=path)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file    

    def delete_files(self):
        for f in self.gemin_client.files.list():
            self.gemin_client.files.delete(name=f.name)