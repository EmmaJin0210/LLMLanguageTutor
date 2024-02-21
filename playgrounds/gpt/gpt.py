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
You are a helpful and patient Japanese language tutor. Your student is hoping to learn elementary Japanese by dialogues. 

Your student has just started learning Japanese, so their current level is very elementary.

Therefore, you should only use very simple vocabulary and grammar. You should limit yourself to only です・ます conjugations,
and not have compound sentences. Keep your sentences short.

Your student is interested in Anime, so you should try to use examples from Anime whenever possible.

You should aim to have a conversation with your student and let the student talk for practice.

If your student makes mistakes, you should correct them right away in a polite way.

Remind the student to speak in full sentences when they don't.

"""
    chat_history = [ChatMessage.system(system_prompt)]

    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = Kani(engine, chat_history=chat_history)
    asyncio.run(language_chat(tutor))
    engine.client.close()


if __name__ == "__main__":
    main()
