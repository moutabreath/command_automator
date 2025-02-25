import openai

class LLMLogicHanlder():
    def __init__(self):
        self.load_api_key()

    def load_api_key(self):
        try:
            f = open('configs\\openapi_key.txt')
        except IOError:
            return
        key = f.readline()
        openai.api_key = key

    def chat_with_gpt(self, prompt):
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].text.strip()

