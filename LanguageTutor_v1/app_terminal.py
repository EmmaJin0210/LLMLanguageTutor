import warnings
import asyncio
# # OpenAI engine stuff
# import os
# from dotenv import load_dotenv
# from kani.engines.openai import OpenAIEngine
from kani import ChatMessage, ChatRole
from LanguageTutor_v1.core.kanis.ConversationKani import ConversationKani

from LanguageTutor_v1.core.core_utils.profile_utils import retrieve_profile_path_from_username, \
    retrieve_user_name, retrieve_user_interests_from_profile, retrieve_user_info_from_profile, \
    retrieve_past_topics_from_profile, retrieve_recent_grammar_learnt, write_updated_profile_to_file

from LanguageTutor_v1.core.core_utils.chat_utils import format_chat_history_for_summary, \
    summarize_rounds_history, summarize_user_interests, summarize_user_personal_info

from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels, filter_katakana, \
    load_grammar_file_to_dict, load_vocab_file_to_dict, flatten_dict_for_tokenization, \
    get_desired_tokens_count

from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict

from LanguageTutor_v1.core.sysprompts import get_sysprompt_chat_mode
from LanguageTutor_v1.core.engines.ControlledGenFudgeEngine import ControlledGenFudgeEngine

from LanguageTutor_v1.core.core_constants import KANI_F_STORE_INTEREST, KANI_F_STORE_PERSONAL_INFO

TARGET_LANGUAGE = "japanese"
BACKUP_LANGUAGE = "english"
CHATBOT_LEVEL = "n5"
TRACK_USAGE = False

USERNAME = "emma"


async def language_chat(tutor, user_profile, language, track_usage = False):
    rounds = 0
    all_user_input = ""
    user_interests = [user_profile["interests"]]
    user_info = [user_profile["personal-info"]]
    while (True):
        if rounds % 16 == 0 and rounds != 0:
            history_to_summarize = format_chat_history_for_summary(
                                                    tutor.chat_history[:len(tutor.chat_history - 4)])
            chat_summary = summarize_rounds_history(history_to_summarize, language)
            new_chat_history = [ChatMessage(role = ChatRole.ASSISTANT, content = chat_summary)] +\
                                tutor.chat_history[len(tutor.chat_history - 4):]
            tutor.chat_history = new_chat_history
            
        user_input = input("You: ")
        # user_input = await speech_to_text()
        all_user_input += user_input
        if user_input.lower() in ["quit", "q"]:
            if user_interests:
                user_profile["interests"] = summarize_user_interests(user_interests, language)
            
            if user_info:
                user_profile["personal-info"] = summarize_user_personal_info(user_info, language)
            # summarize topics talked about
            history_to_summarize = format_chat_history_for_summary(tutor.chat_history)
            topics_talked_about = summarize_rounds_history(history_to_summarize, language)
            user_profile["past-topics"].append(topics_talked_about)
            await clean_up(tutor.engine)
            break

        async for msg in tutor.full_round(user_input):
            if msg.content is None and msg.role == ChatRole.ASSISTANT:
                continue
            if msg.role == ChatRole.FUNCTION:
                if msg.name == KANI_F_STORE_INTEREST:
                    user_interests.append(msg.content)
                elif msg.name == KANI_F_STORE_PERSONAL_INFO:
                    user_info.append(msg.content)
                continue
            text = msg.text
            tutor.chat_history[-1] = ChatMessage.assistant(text)
            # text_to_speech(text)
            print("Tutor: ", text)
        rounds += 1
    return user_profile

async def clean_up(engine):
    await engine.client.close()
    await engine.close()

def main():
    track_usage = TRACK_USAGE
    language = TARGET_LANGUAGE
    backup_language = BACKUP_LANGUAGE
    target_level = CHATBOT_LEVEL
    username = USERNAME
    all_levels = get_all_levels(language)
    profile_path = retrieve_profile_path_from_username(username)
    user_profile = read_json_to_dict(profile_path)
    first_name = retrieve_user_name(user_profile)

    # load grammar and vocab db
    grammar_dict = load_grammar_file_to_dict(language, all_levels)
    vocab_dict = load_vocab_file_to_dict(language, all_levels)
    if backup_language == "english":
        grammar_dict = filter_katakana(grammar_dict)
        vocab_dict = filter_katakana(vocab_dict)
    grammar_dict = flatten_dict_for_tokenization(grammar_dict)
    vocab_dict = flatten_dict_for_tokenization(vocab_dict)

    # construct system prompt
    user_interests = retrieve_user_interests_from_profile(user_profile)
    user_info = retrieve_user_info_from_profile(user_profile)
    past_topics = retrieve_past_topics_from_profile(user_profile)
    good_grammar = retrieve_recent_grammar_learnt(user_profile)
    desired_tokens = get_desired_tokens_count(language, target_level)
    system_prompt = get_sysprompt_chat_mode(language, backup_language, first_name, 
                                            target_level, user_interests, user_info, 
                                            past_topics, good_grammar, desired_tokens)

    # load_dotenv()
    # my_key = os.getenv("OPENAI_API_KEY")
    engine = ControlledGenFudgeEngine(target_difficulty=target_level)
    tutor = ConversationKani(user_profile=user_profile, 
                             engine=engine, 
                             system_prompt=system_prompt, 
                             desired_response_tokens=15)
    user_profile = asyncio.run(language_chat(tutor, user_profile, language, track_usage))

    write_updated_profile_to_file(user_profile, profile_path)



# import os
# import asyncio
# from kani import ChatMessage, ChatRole
# from kani.engines.openai import OpenAIEngine
# from core.kanis.LearningKani import LearningKani
# from core.utils.utils import *
# from core.utils.profile_utils import *
# from core.utils.frontend_utils import *


# async def language_chat(tutor, user_profile):
#     while (True):
#         user_input = input("You: ")
#         if user_input.lower() in ["quit", "q"]:
#             await clean_up(tutor.engine)
#             break
#         async for msg in tutor.full_round(user_input):
#             if msg.content is None and msg.role == ChatRole.ASSISTANT:
#                 continue
#             if msg.role == ChatRole.FUNCTION:
#                 continue
#             print("Tutor: ", msg.text)
    

# async def clean_up(engine):
#     await engine.client.close()
#     await engine.close()

# def main():
#     target_language = get_target_language()
#     instruction_language = get_learning_instruction_language()
#     target_level = get_learning_target_level()
#     learning_schema = get_learning_schema()

#     username = retrieve_username()
#     profile_path = retrieve_profile_path_from_username(username)
#     user_profile = read_json_to_dict(profile_path)
#     name = retrieve_user_name(user_profile)

#     grammar_dict_target = load_grammar_file_to_dict(target_language, [target_level])
#     grammar_to_teach = pick_grammars_to_teach(learning_schema, grammar_dict_target, user_profile)

#     system_prompt = construct_learning_sys_prompt(name, "elementary", target_language, instruction_language, grammar_to_teach)


#     my_key = os.getenv("OPENAI_API_KEY")
#     engine = OpenAIEngine(my_key, model="gpt-4")
#     tutor = LearningKani(user_profile=user_profile, engine=engine, system_prompt=system_prompt)
#     asyncio.run(language_chat(tutor, user_profile))

#     # update learning log
#     user_profile = update_learning_log_in_profile(grammar_to_teach, user_profile)

#     write_updated_profile_to_file(user_profile, profile_path)
#     return

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    main()