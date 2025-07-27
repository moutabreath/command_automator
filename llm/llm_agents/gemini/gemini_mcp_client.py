import logging
import os
import json
import aiohttp
from google import genai
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from google.genai import types
from google.genai.types import GenerateContentResponse
from PIL import Image
import io

from llm.llm_agents.agent_services.resume_saver_service import ResumeSaverService 


class SmartMCPClient:
    """An intelligent client that uses Gemini to decide when to use MCP tools."""

    def __init__(self, mcp_server_url=None, ):
        # MCP server settings
        self.mcp_server_url = mcp_server_url or "http://127.0.0.1:8765/mcp"
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        self.gemini_client: genai.Client = genai.Client(api_key=self.api_key)        
        self.resume_chat = self.gemini_client.chats.create(
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
        self.resume_chat._config = config    
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
            self.resume_chat._config["response_mime_type"] = "application/json"
            generated_response: GenerateContentResponse = self.resume_chat.send_message(messages)
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
            logging.error(f"Error using Gemini for tool decision {e}", exc_info=True)
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

If no tool should be used and you should answer the query directly, respond with:
{{
  "tool": null,
  "args": null
}}

Be selective and conservative with tool usage. Be concise. Only output valid JSON.
Query: {query}
"""
    

    async def is_mcp_server_ready(self, timeout=2):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.mcp_server_url, timeout=timeout) as resp:
                    # You can check for a specific status code if needed
                    return resp.status == 406 # (= NOt Accepatable) Server is probably reacheable.
        except Exception as e:
            logging.error(f"MCP server not ready", exc_info=True)
            return False
    
    async def process_query(
        self,
        query: str,
        base64_decoded: str,
        should_save_results_to_file: bool,
        output_file_path: str,
    ) -> str:
        """
        Process a user query using a combination of Gemini and MCP server.

        Args:
            query: The user's question or request
            base64_decoded: Base64 encoded image data (optional)
            should_save_results_to_file: Whether to save results to files
            output_file_path: Path to save output files
        Returns:
            The response as a string
        """
        try:
            # TODO: Implement image upload functionality if needed
            if not await self.is_mcp_server_ready():
                return self.call_gemini_api_directly(query)

            logging.debug(f"Connecting to MCP server at {self.mcp_server_url}...")

            async with streamablehttp_client(self.mcp_server_url) as (
                read_stream,
                write_stream,
                _,
            ), ClientSession(read_stream, write_stream) as session:
                logging.debug("Established streamable_http connection")
                logging.debug("Created MCP client session")

                await session.initialize()
                logging.debug("Successfully initialized MCP session")

                available_tools = await self.get_available_tools(session)

                # Use Gemini to decide if a tool should be used
                selected_tool, tool_args = await self.decide_tool_usage(
                    query, available_tools
                )

                # If Gemini decided to use a tool, call it
                if selected_tool:
                    return await self.use_tool(
                        selected_tool,
                        tool_args,
                        session,
                        should_save_results_to_file,
                        output_file_path,
                    )
                else:
                    return self.call_gemini_api_directly(query, base64_decoded)

        except Exception as e:
            logging.error(
                "Error communicating with Gemini or MCP server", exc_info=True
            )
            return "An error occurred while processing your request. Please try again."
    async def use_tool(self, selected_tool, tool_args, session, should_save_results_to_file, output_file_path):
        logging.debug(f"Using tool: {selected_tool} with args: {tool_args}")
        response = await session.call_tool(selected_tool, tool_args)
        if response == None:
            return ""
        tool_result = response.content[0].text
        logging.debug(f"Tool response received ({len(tool_result)} characters)")
        
        if self.api_key:
                try:
                    resume_data_dict = json.loads(tool_result)
                except ValueError:
                    logging.error("error with json structure of tool")
                    return ""
                
                resume_text = self.get_refined_resume(resume_data_dict)                                
                cover_letter_text = self.get_cover_letter(resume_data_dict)

                self.save_files_if_needed(should_save_results_to_file, output_file_path, resume_data_dict, resume_text, cover_letter_text)
                return resume_text +"\n\n" + cover_letter_text
        else:
            return tool_result
        
    def call_gemini_api_directly(self, query, base64_decoded):
        if self.api_key:
            try:
                image = Image.open(io.BytesIO(base64_decoded))
                self.resume_chat._config["response_mime_type"] = "text/plain"
                text_prompt = "Now answer the query with text "+ query
                gemini_response = self.resume_chat.send_message([text_prompt, image])
                gemini_text = gemini_response._get_text()
                return gemini_text
            except Exception as e:
                logging.error(f"Error using Gemini {e}", exc_info=True)
                return "Sorry, I couldn't process your request with Gemini or MCP tools."
        else:
            return "No suitable tool found and Gemini API key not provided."

    def save_files_if_needed(self, should_save_results_to_file, output_file_path, resume_data_dict, resume_text, cover_letter_text):
        if should_save_results_to_file:
           resume_highlighted_sections = self.convert_none_to_empty_string(resume_data_dict.get('resume_highlighted_sections', ''))
           applicant_name = resume_data_dict.get('applicant_name', '')
           resume_file_name = self.resume_saver_service.get_resume_file_name(resume_text, applicant_name)
           self.resume_saver_service.save_resume(resume_text, output_file_path, applicant_name, resume_file_name, resume_highlighted_sections)
           if (cover_letter_text != ''):
               self.resume_saver_service.save_cover_letter(cover_letter_text, output_file_path, applicant_name, resume_file_name)

    async def get_available_tools(self, session):
        try:
            tools_response = await session.list_tools()
            available_tools = [tool.name for tool in tools_response.tools]
            logging.debug(f"Available tools: {available_tools}")
        except Exception as e:
            logging.debug(f"Could not list tools: {e}")
            available_tools = []
        return available_tools

    def get_cover_letter(self, resume_data_dict):
        cover_letter_guidelines = resume_data_dict.get('cover_letter_guidelines', '')
        cover_letter_text = ''
        if (cover_letter_guidelines != None):
            gemini_response = self.resume_chat.send_message(cover_letter_guidelines)
            cover_letter_text = gemini_response._get_text()
        return cover_letter_text

    def get_refined_resume(self, resume_data_dict):
        prompt = self.format_prompts_for_resume(resume_data_dict)
        self.resume_chat._config["response_mime_type"] = "text/plain"
        gemini_response = self.resume_chat.send_message(prompt)
        resume_text = gemini_response._get_text()
        return resume_text
        
    def format_prompts_for_resume(self, resume_data_dict):       
        general_guidleines = resume_data_dict.get('general_guidelines', '')
        resume = resume_data_dict.get('resume', '')        
        jobs_desc = self.convert_none_to_empty_string(resume_data_dict.get('job_description', ''))
     
        prompt = f"""You have finished using the mcp tool. Now output text according to the following guidelines.\n\n
                    {general_guidleines}\n\n{resume}\n\n\n"""
        prompt += jobs_desc
        return prompt 

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