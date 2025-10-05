import io
import logging
from google import genai
from google.genai.chats import Chat
from google.genai.types import FileData
from google.genai.types import Part
from PIL import Image

class GeminiUtils:
    GEMINI_MODEL = "gemini-2.5-flash"

    CONFIG_RESPONSE_MIME_TYPE = "response_mime_type"
    MIME_TYPE_JSON = "application/json"
    MIME_TYPE_TEXT = "text/plain"

    def __init__(self, gemini_client: genai.Client):
        self.gemini_client: genai.Client = gemini_client

    def init_chat(self) -> Chat:
        config = {
            "temperature": 0,   # Creativity (0: deterministic, 1: high variety)
            "top_p": 0.95,       # Focus on high-probability words
            "top_k": 64,        # Consider top-k words for each step
            "max_output_tokens": 8192,  # Limit response length
            self.CONFIG_RESPONSE_MIME_TYPE: self.MIME_TYPE_JSON,
        }
        chat  = self.gemini_client.chats.create(
            model= self.GEMINI_MODEL,
            config=config,
            history=[]
        )

        return chat
    
    def get_response_from_gemini(self, prompt: str,  chat: Chat, base64_decoded : str = None, file_paths : list[str] = None) -> str:
            try:
                chat._config[self.CONFIG_RESPONSE_MIME_TYPE] = self.MIME_TYPE_TEXT           
                if base64_decoded:
                    image = Image.open(io.BytesIO(base64_decoded))
                    gemini_response = chat.send_message([prompt, image])
                elif file_paths:
                    gemini_text = ""
                    for file in file_paths:
                        file_part = self.upload_large_file_to_google_cloud(file,  self.MIME_TYPE_TEXT)
                        gemini_response = chat.send_message(file_part)
                        gemini_text = f"{gemini_text}\n{gemini_response.text}"
                    gemini_response = chat.send_message(prompt)
                    gemini_text = f"{gemini_text}\n{gemini_response.text}"
                    return gemini_text
                else:
                    gemini_response = chat.send_message(prompt)                   
                gemini_text = gemini_response.text
                return gemini_text
            except Exception as e:
                logging.error(f"Error using Gemini {e}", exc_info=True)
                return "Sorry, I couldn't process your request with Gemini or MCP tools."

    def upload_large_file_to_google_cloud(self, file_path, mime_type) -> Part:
        if not mime_type:
            raise ValueError("mime_type parameter is required")
        logging.debug("got a file to upload")
        file = self.gemini_client.files.upload(file=file_path)        
        logging.debug(f"Uploaded file '{file.display_name}' as: {file.uri}")
        file_data : FileData = FileData(file_uri=file.uri, mime_type=mime_type)
        return Part(file_data=file_data)  
    
    def delete_all_files(self):
        """
        WARNING: Deletes ALL files from the Gemini client.
        Use with caution in shared environments.
        Consider using selective deletion instead.
        """
        for f in self.gemini_client.files.list():
            try:
                self.gemini_client.files.delete(name=f.name)
            except Exception as ex:
                logging.error(f"Error deleting file {f.name}: {ex}", exc_info=True)