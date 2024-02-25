"""
GPT playground
"""
import os
from getpass import getpass
import asyncio
from kani import Kani, ChatMessage #, chat_in_terminal
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
            await clean_up(tutor.engine)
            break
        response = await tutor.chat_round_str(user_input)
        print("Tutor: ", response)


async def clean_up(engine):
    await engine.client.close()
    await engine.close()


def read_prompt(filepath):
    prompt = ""
    with open(filepath) as infile:
        for line in infile.readlines():
            prompt += line
    return prompt


def main():
    my_key = set_api_key()
    system_prompt = read_prompt("testprompt.txt")
    chat_history = [ChatMessage.system(system_prompt)]

    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = Kani(engine, chat_history=chat_history)
    asyncio.run(language_chat(tutor))


if __name__ == "__main__":
    main()
