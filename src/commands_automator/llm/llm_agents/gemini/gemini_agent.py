import io
import logging
import mimetypes
from google import genai
from google.genai.chats import Chat
from google.genai.types import FileData
from google.genai.types import File
from google.genai.types import Part
from PIL import Image

from commands_automator.utils import file_utils

class GeminiAgent:
    GEMINI_MODEL = "gemini-2.5-flash"

    CONFIG_RESPONSE_MIME_TYPE = "response_mime_type"

    def __init__(self, gemini_client: genai.Client):
        self.gemini_client: genai.Client = gemini_client
        self.delete_all_files()

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
                                 ) -> str:

        self.base_config[self.CONFIG_RESPONSE_MIME_TYPE] = response_mime_type
        parts = [Part(text=prompt)]

        if file_paths:            
            parts.extend(await self.get_json_files_content_as_parts(file_paths))
            for part in parts:                
                response = chat.send_message(message=part, config=self.base_config)
            if response:
                return response.text 
            
        # Handle single image from base64
        elif base64_decoded:
            try:
                image = Image.open(io.BytesIO(base64_decoded))
                parts.append(Part(inline_data=image))
            except Exception as e:
                logging.error(f"Error processing image data: {e}", exc_info=True)

        try:
            response = chat.send_message(message=parts, config=self.base_config)
            if response:
                return response.text

        except Exception as e:
            logging.error(f"Error using Gemini: {e}", exc_info=True)
            return f"Sorry, I couldn't process your request with Gemini: {str(e)}"    

    async def get_json_files_content_as_parts(self, file_paths: list[str]) -> list[Part]:
        parts = []
        for file_path in file_paths:
            content = await file_utils.read_text_file(file_path)
            parts.append(Part(text=content))
        return parts
        
    
    def get_json_file_parts(self, file_paths: list[str]) -> list[Part]:
        parts = []
        # Upload files
        for file_path in file_paths:            
            file = self.upload_large_file_to_google_cloud(file_path)            
            if file:
                file_data = self.get_file_data_from_uploaded_files(file, file_path)
                parts.append(Part(file_data=file_data))
            else:
                logging.warning(f"Skipping file that failed to upload: {file_path}")        

        return parts      

    def upload_large_file_to_google_cloud(self, file_path: str) -> File:
        logging.debug(f"Uploading file: {file_path}")
        try:
            file: File = self.gemini_client.files.upload(file=file_path)       
            logging.debug(f"Successfully uploaded '{file.display_name}' as: {file.uri}")
            return file      
        except Exception as e:
            logging.error(f"Couldn't upload file {file_path}: {e}", exc_info=True)
            return None
            
    def get_file_data_from_uploaded_files(self, file: File, file_path: str) -> FileData:        
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        if file and file.uri:            
            logging.debug(f"Uploaded file '{file.display_name}' as: {file.uri}")
            file_data: FileData = FileData(file_uri=file.uri, mime_type=mime_type)
            return file_data
        
        return None
    
    def delete_all_files(self):
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


