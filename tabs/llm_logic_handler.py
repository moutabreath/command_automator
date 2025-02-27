from openai import OpenAI
from google import genai

from python_utils.logger import Logger

class LLMLogicHanlder():
    def __init__(self):
        self.load_api_keys()

    def load_api_keys(self):
        try:
            f = open('configs\\chat_bot_keys.txt')
        except IOError:
            return
        
        self.init_gpt_client(f)
        self.init_gemini_client(f)
        
       
    def init_gpt_client(self, f):
        key_line = f.readline()
        key_line_parts = key_line.split("=")
        key = key_line_parts[1]
        self.gpt_client = OpenAI(
        api_key=key,)

    def init_gemini_client(self, f):
        key_line = f.readline()
        key_line_parts = key_line.split("=")
        key = key_line_parts[1]
        self.gemin_client = genai.Client(api_key=key)


    def chat_with_gpt(self, prompt):
    #     response = self.client.chat.completions.create(
    #         model="gpt-4o-mini",
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": [
    #                     {"type": "text", "text": prompt},
    #                     {
    #                         "type": "image_url",
    #                         "image_url": {"url": f"{img_url}"},
    #                     },
    #                 ],
    #             }
    # ],)
        try:
            chat_completion = self.gpt_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            model="gpt-4o-mini",
            )
            Logger.print_log(chat_completion)
        except Exception:
            Logger.print_error_message(f"Error with gpt", Exception)


    def chat_with_gemini(self, prompt):
        response = self.gemin_client.models.generate_content(
            model='gemini-2.0-flash-001', contents=prompt
        )
        return response.text