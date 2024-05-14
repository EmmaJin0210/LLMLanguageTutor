from core.utils.utils import *
from kani import ChatMessage, ChatRole
from openai import OpenAI

def retrieve_username():
    return "emma"

def retrieve_recent_grammar_learnt(user_profile, n=5):
    return list(user_profile["taught-log"]["grammar"].items())[:n]

def write_updated_profile_to_file(user_profile, filepath):
    write_dict_to_json(user_profile, filepath)

def retrieve_user_name(user_profile):
    return user_profile["name"]

def retrieve_profile_path_from_username(username):
    return f"user_profiles/{username}.json"

def retrieve_user_interests_from_profile(user_profile):
    interests = user_profile["interests"]
    if len(interests) != 0:
        return str(interests)
    return "UNKNOWN"

def retrieve_user_info_from_profile(user_profile):
    info = user_profile["personal-info"]
    if len(info) != 0:
        return str(info)
    return "UNKNOWN"

def retrieve_past_topics_from_profile(user_profile):
    past_topics_list = user_profile["past-topics"]
    if len(past_topics_list) != 0:
        return str(past_topics_list)
    return "NONE"

def format_chat_history_for_summary(history):
    to_return = []
    valid_roles = [ChatRole.ASSISTANT, ChatRole.USER]
    for msg in history:
        if msg.role not in valid_roles or not msg.content:
            continue
        flattened = "user: " if msg.role == ChatRole.USER else "tutor: "
        flattened += msg.content
        to_return.append(flattened)
    return to_return


def summarize_user_interests(interests_list, language):
    sys_prompt = f"""You are a helpful topic summarizer for a language learning chatbot. 
Given a list of the user's interests, your job is to organize and summarize these interests into
concise sentences in their original language.
"""
    shots = retrieve_shots(language, "summarize_user_interests")
    messages = [{"role": "system", "content":  sys_prompt}]
    messages += shots
    messages += [{"role": "user", "content": str(interests_list)}]
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    return completion.choices[0].message.content

def summarize_user_personal_info(info_list, language):
    shots = retrieve_shots(language, "summarize_user_personal_info")
    sys_prompt = f"""You are a helpful topic summarizer for a language learning chatbot. 
Given a list of the user's personal information, your job is to organize and summarize these information into
concise sentences in their original language.
"""
    messages = [{"role": "system", "content":  sys_prompt}]
    messages += shots
    messages += [{"role": "user", "content":  str(info_list)}]
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    return completion.choices[0].message.content

def summarize_user_mistakes(user_profile, language):
    pass

def summarize_rounds_history(history, language):
    shots = retrieve_shots(language, "summarize_rounds_history")
    sys_prompt = f"""You are a helpful topic summarizer for a language learning chatbot.
The user is having a conversation with the language tutor. Given the list of
conversations they are having, your job is to summarize the conversation into a few very short, beginner-level sentences,
in the language used for each sentence.
Focus on what topics are being covered in the conversation.
"""
    messages = [{"role": "system", "content":  sys_prompt}]
    messages += shots
    messages += [{"role": "user", "content": str(history)}]
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    return completion.choices[0].message.content
