import os
import asyncio
from random import sample
from copy import deepcopy
from kani import ChatMessage, ChatRole
from kani.engines.openai import OpenAIEngine
from core.kanis.LearningKani import LearningKani
from core.utils.utils import *
from core.utils.profile_utils import *
from core.utils.frontend_utils import *


async def language_chat(tutor, user_profile):
    while (True):
        user_input = input("You: ")
        if user_input.lower() in ["quit", "q"]:
            await clean_up(tutor.engine)
            break
        async for msg in tutor.full_round(user_input):
            if msg.content is None and msg.role == ChatRole.ASSISTANT:
                continue
            if msg.role == ChatRole.FUNCTION:
                continue
            print("Tutor: ", msg.text)
    

async def clean_up(engine):
    await engine.client.close()
    await engine.close()

# TODO: add instructions for teaching vocabulary before teaching grammar, as well as choosing vocabulary
# TODO: add in instructions for letting the user indicate they already know some grammar point and skip to the role-play.
# TODO: maybe add in a kani function to draw more expressions to teach from the database if the user wants to learn more
def construct_learning_sys_prompt(name, level_general, language, instruction_lang, grammar_to_teach):
    sys_prompt = f"""You are a helpful and patient 1-on-1 {language} language tutor.
Your instruction language is {instruction_lang}.
Your student is {name}, who is learning {language} and currently at the {level_general} level.

Today, you are having a lesson with your student,
and the grammar points you need to teach to the user are {grammar_to_teach}.

First, greet the user and ask if they have any questions before you begin today's lesson. This should be a pure
greeting and asking for questions, don't dive into the material just yet.

If the user has questions or anything else to say, address those first; if not, then you can start with the material you will be teaching.

For each grammar point, follow these steps to teach it to the user:

1. Present the grammar point in {language}.
Look at the meaning of the grammar point and explain the grammar point to the user in {instruction_lang}.
When you are explaining, list a few example phrases or very short sentences to facilitate your explanation of how to use the grammar point.
Ask the user if the meaning makes sense.

2. Give 3 simple example sentences in {language} that uses the grammar point, and ask the user to translate it into {instruction_lang}.
Give the examples sentences ONE-BY-ONE.

3. Ask the user if they now understand what the grammar point means. If they don't, ask them what is confusing to them and explain more.

4. If the user thinks they understand, construct a short {language}-speaking activity that would require the user to use the grammar point when speaking during the activity.
This could be question-answering, role-play, etc. Be imaginative about the proposed scenario of the activity.
For example, if the grammar point is more commonly used in questions, you could make the user construct questions using the grammar point and ask those questions to you, and you will role-play the person answer the questions.
Or, if it is hard to ask a question with the grammar point, you could come up with a few questions in {language} that would make the user use the grammar point learnt when they answer the question in {language}.

Be very specific about what the user should do in the activity. The level of detailed-ness should be similar to this: "I will be playing the role of your good friend, and you want to learn more about my music tastes. Ask me questions using the grammar point <grammar_point>".
Note that during the activity, you should be role-playing with the user and simulating a real conversation. Be sure to keep everything you say limited to ONE SIMPLE SENTENCE, no matter if it is a question, an answer to the user's question, or just a reply to what the user is saying.
DO NOT say anything that's outside of the role you are playing. This includes telling the user their sentence is correct, pointing out the user's mistakes, asking the user for their next question, etc.
Carry on the activity such that the user will be able to only speak one sentence at a time.

When the activity is done, evaluate whether the user used the grammar point taught and if what they said grammatically correct for everything the user said during the activity, and give feedback to the user.

5. After going through the activity in {language}, move on to the next grammar point.

Repeat until you have taught all the grammar points given to you.

After you have taught all the grammar points given, ask the user one more time if they have any questions.
If yes, patiently answer the user's questions. If not, say goodbye to the user and conclude the lesson.
"""
    return sys_prompt

def pick_words_to_teach():
    pass

def pick_grammars_to_teach(schema, grammar_dict, user_profile):
    to_teach = []
    taught = user_profile["taught-log"]["grammar"]
    to_teach_keys = []
    if schema == "random-sample":
        trimmed = deepcopy(grammar_dict)
        for gp in taught:
            del trimmed[gp]
        to_teach_keys = sample(list(trimmed.keys()), 3)
    for key in to_teach_keys:
        to_teach.append({ key : grammar_dict[key]})
    return to_teach


def generate_practice_example():
    pass

def update_learning_log_in_profile(grammar_taught, user_profile):
    old_grammar_log = user_profile["taught-log"]["grammar"]
    for dic in grammar_taught:
        updated_grammar_log = {**dic, **old_grammar_log}
        old_grammar_log = updated_grammar_log

    user_profile["taught-log"]["grammar"] = updated_grammar_log
    return user_profile

def create_tutor(user_profile, system_prompt):
    my_key = os.getenv("OPENAI_API_KEY")
    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = LearningKani(user_profile=user_profile, engine=engine, system_prompt=system_prompt)


def main():
    target_language = get_target_language()
    instruction_language = get_learning_instruction_language()
    target_level = get_learning_target_level()
    learning_schema = get_learning_schema()

    username = retrieve_username()
    profile_path = retrieve_profile_path_from_username(username)
    user_profile = read_json_to_dict(profile_path)
    name = retrieve_user_name(user_profile)

    grammar_dict_target = load_grammar_file_to_dict(target_language, [target_level])
    grammar_to_teach = pick_grammars_to_teach(learning_schema, grammar_dict_target, user_profile)

    system_prompt = construct_learning_sys_prompt(name, "elementary", target_language, instruction_language, grammar_to_teach)


    my_key = os.getenv("OPENAI_API_KEY")
    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = LearningKani(user_profile=user_profile, engine=engine, system_prompt=system_prompt)
    asyncio.run(language_chat(tutor, user_profile))

    # update learning log
    user_profile = update_learning_log_in_profile(grammar_to_teach, user_profile)

    write_updated_profile_to_file(user_profile, profile_path)
    return

if __name__ == "__main__":
    main()