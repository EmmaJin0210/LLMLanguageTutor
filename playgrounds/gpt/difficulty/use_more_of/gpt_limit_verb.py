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


def construct_prompt(filepath):
    prompt_front = """
You are a helpful and patient Japanese language tutor. Your student wants to improve their Japanese conversation skills.
Be mindful that you are speaking to your student in Japanese.
You should aim to go with the flow of the conversation and go with what the student wants to talk about, but you should ALWAYS follow the rules below:
"""
    # 1. You should only use EXTREMELY simple vocabulary and grammar. If you are deciding between words, always choose the most elementary one.
    prompt_end = """
2. You should keep your sentences short and NOT use compound sentences.
3. You should remind the student to speak in full sentences, as well as use です・ます form when they don't.
4. If your student makes mistakes, you should correct them right away patiently.
5. You should speak in the です・ます form.
6. Try not to quiz your student on translations.
7. Since your student is interested in Anime, so you should try to use examples from Anime whenever possible.
"""
    vocab_pool = read_vocab_list(filepath)
    # instruction = "1. You should only use words in this list and their conjugations: " + str(vocab_pool)
    instruction = "1. You should your verbs to those in this list and their conjugations: " + str(vocab_pool)
    system_prompt = prompt_front + instruction + prompt_end
    print(system_prompt)
    return system_prompt


def read_vocab_list(filepath):
    vocab = []
    with open(filepath) as infile:
        for line in infile.readlines():
            vocab.append(line.strip())
    return vocab


def main():
    my_key = set_api_key()
    system_prompt = construct_prompt("elementary_vocab_100.txt")
    chat_history = [ChatMessage.system(system_prompt)]

    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = Kani(engine, chat_history=chat_history)
    asyncio.run(language_chat(tutor))


if __name__ == "__main__":
    main()