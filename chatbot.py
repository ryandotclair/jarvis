import os
import openai

openai.api_key = os.environ.get('OPENAI_KEY')

#debug
print("chatbot started")
completion = openai.Completion()

start_chat_log = '''Human: Hello, isn't it just a lovely day?
AI: It is! A very lovely day. My name is Jarvis, by the way.
Human: How should I address you?
AI: My name is Jarvis. I'm your personal AI helper for Azure Spring Apps Enterprise.
'''

def ask(question, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    prompt = f'{chat_log}Human: {question}\nAI:'
    response = completion.create(
        prompt=prompt, engine="davinci", stop=['\nHuman'], temperature=0.9,
        top_p=1, frequency_penalty=0, presence_penalty=0.6, best_of=1,
        max_tokens=150)
    answer = response.choices[0].text.strip()

    return answer

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    return f'{chat_log}Human: {question}\nAI: {answer}\n'

