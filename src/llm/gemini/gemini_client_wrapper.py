from enum import Enum
import io
import json
import logging
import mimetypes
import os
from google import genai
from google.genai.chats import Chat
from google.genai.types import FileData
from google.genai.types import File
from google.genai.types import Part
from PIL import Image

from utils import file_utils


class LLMResponseCode(Enum):
    """Enumeration of possible Gemini API operation results"""
    OK = 1
    ERROR_USING_GEMINI_API = 2
    GEMINI_UNAVAILABLE = 3
    MODEL_OVERLOADED = 4
    
class LLMAgentResponse:
    def __init__(self, text: str, code: LLMResponseCode):
        self.text = text
        self.code = code
        

class GeminiClientWrapper:
    GEMINI_MODEL = "gemini-2.5-flash"

    CONFIG_RESPONSE_MIME_TYPE = "response_mime_type"

    def __init__(self, cleanup_files: bool = False):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        self.gemini_client: genai.Client = genai.Client(api_key=api_key)
        if cleanup_files:
            self._delete_all_files()
            
    def init_chat(self) -> Chat:
        self.base_config = {
            "temperature": 0,   # Creativity (0: deterministic, 1: high variety)
            "top_p": 0.95,       # Focus on high-probability words
            "top_k": 64,        # Consider top-k words for each step
            "max_output_tokens": 8192,  # Limit response length
            self.CONFIG_RESPONSE_MIME_TYPE: mimetypes.types_map['.json'],
        }
        chat = self.gemini_client.chats.create(
            model=self.GEMINI_MODEL,
            config=self.base_config.copy(),
            history=[]
        )

        return chat

    async def get_response_from_gemini(self, prompt: str,
                                 chat: Chat,
                                 response_mime_type: str = mimetypes.types_map['.txt'],
                                 base64_decoded: str = None,
                                 file_paths: list[str] = None,
                                 ) -> LLMAgentResponse:

        config = self.base_config.copy()
        config[self.CONFIG_RESPONSE_MIME_TYPE] = response_mime_type
        parts = [Part(text=prompt)]

        if file_paths:
            prompt = f"{prompt} \n\n\n {await self._get_json_files_content_for_prompt(file_paths)}"
            parts = [Part(text=prompt)]
        # Handle single image from base64
        elif base64_decoded:
            try:
                image = Image.open(io.BytesIO(base64_decoded))
                parts.append(Part(inline_data=image))
            except Exception as e:
                logging.error(f"Error processing image data: {e}", exc_info=True)
                return LLMAgentResponse(
                    f"Failed to process image: {str(e)}", 
                    LLMResponseCode.ERROR_USING_GEMINI_API
                )
        try:
            response = chat.send_message(message=parts, config=config)
            if response:
                return LLMAgentResponse(response.text, LLMResponseCode.OK)
            return LLMAgentResponse(f"Couldn't get result from gemini Api", LLMResponseCode.ERROR_USING_GEMINI_API)
        except Exception as e:
            logging.error(f"Error using Gemini: {e}", exc_info=True)
            status = getattr(e, 'status_code', None) or (e.args[0] if e.args else None)
            if status == 503:
                message = getattr(e, 'message', str(e))
                if 'overloaded' in message.lower():
                    return LLMAgentResponse(message, LLMResponseCode.MODEL_OVERLOADED)
                return LLMAgentResponse(message, LLMResponseCode.GEMINI_UNAVAILABLE)
            return LLMAgentResponse(f"Sorry, I couldn't process your request with Gemini", LLMResponseCode.ERROR_USING_GEMINI_API)
        
    def get_mcp_tool_json(self, prompt: str,
                                 chat: Chat, available_tools):
        config = self.base_config.copy()
        config[self.CONFIG_RESPONSE_MIME_TYPE] = mimetypes.types_map['.json']
        try:
            tool_response = chat.send_message(message=prompt, config=config)
            decision = json.loads(tool_response.model_dump_json())
            candidates = decision.get('candidates', [])
            if not candidates:
                return None, None
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                return None, None
            tools_text = parts[0].get('text')
            if not tools_text:
                return None, None
            tools_json = json.loads(tools_text)    
            selected_tool = tools_json.get("tool")
            args = tools_json.get("args", {})
            if selected_tool and selected_tool in available_tools:
                logging.debug(f"Gemini decided to use tool: {selected_tool}")
                return selected_tool, args
        except Exception as ex:
            logging.error(f"Error using Gemini: {ex}", exc_info=True)
            return None, None
        
    async def _get_json_files_content_for_prompt(self, file_paths: list[str]) -> str:
        result = ""
        for file_path in file_paths:
            content = await file_utils.read_text_file(file_path)
            if content:
                result = f"{result}\n\n\n{content}"
        return result
    
    def _get_json_file_parts(self, file_paths: list[str]) -> list[Part]:
        parts = []
        # Upload files
        for file_path in file_paths:            
            file = self._upload_large_file_to_google_cloud(file_path)            
            if file:
                file_data = self._get_file_data_from_uploaded_files(file, file_path)
                if file_data:
                    parts.append(Part(file_data=file_data))
            else:
                logging.warning(f"Skipping file that failed to upload: {file_path}")        

        return parts      

    def _upload_large_file_to_google_cloud(self, file_path: str) -> File:
        logging.debug(f"Uploading file: {file_path}")
        try:
            file: File = self.gemini_client.files.upload(file=file_path)       
            logging.debug(f"Successfully uploaded '{file.display_name}' as: {file.uri}")
            return file      
        except Exception as e:
            logging.error(f"Couldn't upload file {file_path}: {e}", exc_info=True)
            return None
            
    def _get_file_data_from_uploaded_files(self, file: File, file_path: str) -> FileData:        
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        if file and file.uri:            
            logging.debug(f"Uploaded file '{file.display_name}' as: {file.uri}")
            file_data: FileData = FileData(file_uri=file.uri, mime_type=mime_type)
            return file_data
        
        return None
    
    def _delete_all_files(self):
        """
        WARNING: Deletes ALL files from the Gemini client.
        Use with caution in shared environments.
        Consider using selective deletion instead.
        """
        if self.gemini_client.files:
            try:
                for f in self.gemini_client.files.list():
                    try:
                        self.gemini_client.files.delete(name=f.name)
                    except Exception as ex:
                        logging.error(f"Error deleting file {f.name}: {ex}", exc_info=True)
            except Exception as e:
                logging.error(f"Error listing files: {e}", exc_info=True)
