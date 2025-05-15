import logging
from typing import Tuple

from google import genai
from google.genai import types

class GeminiAgent:
    API_KEY_NAME = "gemini"
    
    def __init__(self, key: str):
        self.gemin_client: genai.Client = genai.Client(api_key=key)
        self.generation_config = {
            "temperature": 0,   # Creativity (0: deterministic, 1: high variety)
            "top_p": 0.95,       # Focus on high-probability words
            "top_k": 64,        # Consider top-k words for each step
            "max_output_tokens": 8192,  # Limit response length
            "response_mime_type": "text/plain",  # Output as plain text
        }

        self.safety_settings = [
            # Gemini's safety settings for blocking harmful content
            # (Set to "BLOCK_NONE" for no blocking)
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        self.chat = self.gemin_client.chats.create(
                    model="gemini-2.0-flash",
                    history= [],
                    config=self.generation_config
        )


    def chat_with_gemini(self, prompt, file_path = None) -> Tuple[bool, str]:
        try:
            if not (file_path is None or file_path == ""):
                part = self.get_files_to_attach(file_path)
                generatedResponse: types.GenerateContentResponse  = self.chat.send_message([
                    types.Part(text=prompt),
                    part
                ])
            else:
                generatedResponse: types.GenerateContentResponse = self.chat.send_message(prompt)
            response = generatedResponse._get_text()
            return True, response                    
        except Exception as ex:
            logging.error("error communicating with gemini", exc_info=True)
            return False, "error"
    

    def stream_chat_with_gemini(self, prompt, file_path = None):        
        if not file_path is None or file_path == "":
            part =  self.get_files_to_attach(file_path)
            response = self.chat.send_message_stream([
                types.Part(text=prompt),
                part
            ])
        else:
            response = self.chat.send_message_stream(prompt)
        for chunk in response:            
            yield chunk.text
        # response = chat.send_message_stream("How many paws are in my house?")
        # for chunk in response:
        #     print(chunk.text, end="")
        # for message in chat._curated_history:
        #     print(f'role - ', message.role, end=": ")
        #     print(message.parts[0].text)

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