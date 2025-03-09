import logging
from typing import Tuple

from google import genai




class GeminiAgent:
    API_KEY_NAME = "gemini"
    
    def __init__(self, key: str):
        self.gemin_client = genai.Client(api_key=key)
        self.chat = self.gemin_client.chats.create(model="gemini-2.0-flash")

    def chat_with_gemini(self, prompt) -> Tuple[bool, str]:
        try:
            response = self.gemin_client.models.generate_content(
                model='gemini-2.0-flash-001', contents=prompt
            )
            return True, response.text
        except Exception as ex:
            logging.log(logging.ERROR, "error communicating with gemini", ex)
            return False, "error"
    

    def stream_chat_with_gemini(self, prompt):
        response = self.chat.send_message_stream(prompt)
        for chunk in response:            
            yield chunk.text
        # response = chat.send_message_stream("How many paws are in my house?")
        # for chunk in response:
        #     print(chunk.text, end="")
        # for message in chat._curated_history:
        #     print(f'role - ', message.role, end=": ")
        #     print(message.parts[0].text)