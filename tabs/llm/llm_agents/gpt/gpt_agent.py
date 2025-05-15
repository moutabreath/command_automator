import logging

from openai import OpenAI

class GptAgent:

    API_KEY_NAME = "openai"
        
    def __init__(self, key: str):
        self.gpt_client = OpenAI(
        api_key=key,)



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
            logging.log(logging.DEBUG, chat_completion)
        except Exception as ex:
            logging.log(logging.ERROR, "error with gtp", ex)