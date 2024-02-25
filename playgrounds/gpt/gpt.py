"""
GPT playground
"""
import os
from getpass import getpass
import asyncio
from kani import Kani, chat_in_terminal, ChatMessage
from kani.engines.openai import OpenAIEngine

def set_api_key():
    if 'OPENAI_API_KEY' not in os.environ:
        print("You didn't set your OPENAI_API_KEY on the command line.")
        os.environ['OPENAI_API_KEY'] = getpass("Please enter your OpenAI API Key: ")
    return os.environ['OPENAI_API_KEY']

async def language_chat(tutor):
    while (True):
        user_input = input("You: ")
        if user_input.lower() in ["quit", "q"]:
            break
        response = await tutor.chat_round_str(user_input)
        print("Tutor: ", response)

def main():
    my_key = set_api_key()
    system_prompt = """
You are a helpful and patient Japanese language tutor. Your student wants to improve their Japanese conversation skills.

Be mindful that you are speaking to your student in Japanese.
You should aim to go with the flow of the conversation and go with what the student wants to talk about, but you should ALWAYS follow the rules below:
1. You should only use EXTREMELY simple vocabulary and grammar. If you are deciding between words, always choose the most elementary one.
2. You should keep your sentences short and NOT use compound sentences.
3. You should remind the student to speak in full sentences, as well as use です・ます form when they don't.
4. If your student makes mistakes, you should correct them right away patiently.
5. You should speak in the です・ます form.
6. Try not to quiz your student on translations.
7. Since your student is interested in Anime, so you should try to use examples from Anime whenever possible.
"""
    chat_history = [ChatMessage.system(system_prompt)]

    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = Kani(engine, chat_history=chat_history)
    asyncio.run(language_chat(tutor))
    engine.client.close()


if __name__ == "__main__":
    main()
