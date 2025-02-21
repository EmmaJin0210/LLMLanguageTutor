from core.core_utils.language_utils import load_grammar_file_to_dict, load_vocab_file_to_dict, \
    filter_katakana, flatten_dict_for_tokenization, \
    get_desired_tokens_count, get_level_desc_word
from core.core_utils.profile_utils import retrieve_user_interests_from_profile, \
    retrieve_user_info_from_profile, retrieve_past_topics_from_profile, \
    retrieve_recent_grammar_learnt, write_updated_profile_to_file, \
    retrieve_profile_path_from_username, update_learning_log_in_profile
from core.core_utils.chat_utils import summarize_user_interests, summarize_user_personal_info, \
    summarize_rounds_history, format_chat_history_for_summary
from core.core_utils.learning_utils import pick_grammars_to_teach
from core.core_utils.speech_utils import text_to_speech
from core.core_utils.engine_utils import create_engine
from core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json

from core.sysprompts import get_sysprompt_chat_mode, get_sysprompt_learning_mode
from appstuff.data_classes import ConversationEndpointInfo, LearningEndpointInfo, GlobalSessionData
from openai import OpenAI
from kani import ChatMessage, ChatRole
import json

from core.core_constants import KANI_F_STORE_INTEREST, KANI_F_STORE_PERSONAL_INFO, \
    ENGINE_ID_OPENAI_DC, \
    TRANSCRIPTION_MODEL
from appstuff.app_constants import MOUNT_TEMP_DATA, SERVER_ADDR, \
    ROOT_USER_PROFILES, ROOT_TEMP_DATA, \
    FILENAME_AUDIO_INPUT, FILENAME_USERS_DB, FILENAME_PROFILE_TEMPLATE, \
    MSG_PROGRESS_SAVE_SUCCESS, MSG_PROGRESS_SAVE_FAIL, MSG_TRANSCRIBE_AUDIO_FAIL
    
###### imports for typing purposes ######
from typing import Union, Dict
from kani import Kani
from kani.engines.base import BaseEngine 
from fastapi import WebSocket
#########################################

def get_conversation_endpoint_info(session_data: GlobalSessionData) \
    -> ConversationEndpointInfo:

    track_usage = False
    language = session_data.language
    backup_language = session_data.backup_language
    target_level = session_data.current_level
    all_levels = session_data.all_levels
    user_profile = session_data.profile
    first_name = session_data.firstname

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

    return ConversationEndpointInfo(track_usage = track_usage, 
                                    language = language, 
                                    target_level = target_level, 
                                    grammar_dict = grammar_dict, 
                                    vocab_dict = vocab_dict, 
                                    system_prompt = system_prompt,
                                    desired_response_tokens = desired_tokens)


def get_learning_endpoint_info(session_data: GlobalSessionData) -> LearningEndpointInfo:
    name = session_data.firstname
    target_level = session_data.target_level
    level_in_profile_desc = session_data.profile["comprehension-level"]
    language = session_data.language
    instruction_language = session_data.instruction_language
    learning_schema = session_data.learning_schema
    user_profile = session_data.profile

    level_desc = level_in_profile_desc if level_in_profile_desc \
        else get_level_desc_word(language = language, level = target_level)
    grammar_dict_target = load_grammar_file_to_dict(language = language,
                                                    levels = [target_level])
    grammar_to_teach = pick_grammars_to_teach(learning_schema = learning_schema, 
                                              grammar_dict = grammar_dict_target,
                                              user_profile = user_profile)
    system_prompt = get_sysprompt_learning_mode(name, level_desc, language, 
                                               instruction_language, grammar_to_teach)
    
    return LearningEndpointInfo(grammar_to_teach = grammar_to_teach,
                                system_prompt = system_prompt)
    

def get_engine(info: Union[LearningEndpointInfo, ConversationEndpointInfo], 
               engine_id: str, 
               model_id: str) \
    -> BaseEngine:
    extra_kwargs = {}
    if engine_id == ENGINE_ID_OPENAI_DC:
        extra_kwargs = {
            "language": getattr(info, "language", None),
            "target_level": getattr(info, "target_level", None),
            "vocab_dict": getattr(info, "vocab_dict", None),
            "grammar_dict": getattr(info, "grammar_dict", None),
        }
    return create_engine(engine_id = engine_id, model_id = model_id, **extra_kwargs)


async def handle_websocket_input(websocket: WebSocket) -> Dict:
    data = await websocket.receive()
    try:
        print(f"Websocket received data: \n {data}")
        data = json.loads(data["text"])
        datatype, datadata = data["type"], data["data"]
    except:
        datatype, datadata = "text", data["text"]

    user_input = "NO USER INPUT"
    if datatype == "text":
        user_input = datadata
    elif datatype == "audio":
        res = await transcribe_audio(filepath = f"{ROOT_TEMP_DATA}{FILENAME_AUDIO_INPUT}")
        if not res["success"]:
            return {"success" : False,
                    "error": res["error"]}
        user_input = res["transcription"]
        print(f"Audio transcription: \n {user_input}")
        await websocket.send_text(f"You: {user_input}")
    return {"success" : True, 
            "user_input": user_input}


async def transcribe_audio(filepath: str) -> Dict: ###
    try:
        client = OpenAI()
        with open(filepath, "rb") as audiofile:
            transcription = client.audio.transcriptions.create(
                model = TRANSCRIPTION_MODEL,
                file = audiofile
            )
            return {"success" : True, 
                    "transcription": transcription.text}
    except Exception as e:
        print(f"Error in transcription: {e}")
        return {"success" : False, 
                "error": MSG_TRANSCRIBE_AUDIO_FAIL}
    

async def generate_audio_response(text: str) -> str:
    audio_filename = text_to_speech(text)
    return f"http://{SERVER_ADDR}/{MOUNT_TEMP_DATA}{audio_filename}"


async def handle_chat_round(websocket: WebSocket, 
                            session_data: GlobalSessionData,
                            tutor: Kani, 
                            user_input: str) \
    -> GlobalSessionData: ### TODO: is_web
    async for msg in tutor.full_round(user_input):
        if msg.content is None and msg.role == ChatRole.ASSISTANT:
            continue
        if msg.role == ChatRole.FUNCTION:
            if msg.name == KANI_F_STORE_INTEREST:
                session_data.user_interests.append(msg.content)
            elif msg.name == KANI_F_STORE_PERSONAL_INFO:
                session_data.user_info.append(msg.content)
            continue
        
        tutor.chat_history[-1] = ChatMessage.assistant(content = msg.text)
        await websocket.send_text(f"Tutor: {msg.text}")

        audio_url = await generate_audio_response(text = msg.text)
        await websocket.send_text(audio_url)
    return session_data


async def handle_learning_round(websocket: WebSocket, 
                                tutor: Kani, 
                                user_input: str) \
    -> None: ### TODO: is_web

    async for msg in tutor.full_round(user_input):
        if msg.content is None and msg.role == ChatRole.ASSISTANT:
            continue
        if msg.role == ChatRole.FUNCTION:
            continue
        await websocket.send_text(f"Tutor: {msg.text}")
        audio_url = await generate_audio_response(text = msg.text)
        await websocket.send_text(audio_url)


def save_chat_info_to_profile(session_data: GlobalSessionData) -> Dict:
    try:
        language = session_data.language
        tutor = session_data.tutor
        user_profile = session_data.profile
        profile_path = session_data.profile_path
        if session_data.user_interests:
            user_profile["interests"] = summarize_user_interests(
                                            interests_list = session_data.user_interests,
                                            language = language
                                        )
        if session_data.user_info:
            user_profile["personal-info"] = summarize_user_personal_info(
                                                info_list = session_data.user_info,
                                                language = language
                                            )
        # summarize topics talked about
        history_to_summarize = format_chat_history_for_summary(tutor.chat_history)
        topics_talked_about = summarize_rounds_history(history_to_summarize, language)
        user_profile["past-topics"].append(topics_talked_about)
        write_updated_profile_to_file(user_profile, profile_path)

        return {"success" : True, 
                "message": MSG_PROGRESS_SAVE_SUCCESS}
    
    except Exception as e:
        return {"success" : False, 
                "message": MSG_PROGRESS_SAVE_FAIL}
    

def save_learning_info_to_profile(session_data: GlobalSessionData) -> Dict:
    try:
        grammar_to_teach = session_data.grammar_to_teach
        user_profile = session_data.profile
        profile_path = session_data.profile_path
        user_profile = update_learning_log_in_profile(grammar_to_teach, user_profile)
        # TODO: this can prob become a more general helper func
        write_updated_profile_to_file(user_profile, profile_path)

        return {"success" : True, 
                "message": MSG_PROGRESS_SAVE_SUCCESS}
    
    except Exception as e:
        return {"success" : False, 
                "message": MSG_PROGRESS_SAVE_FAIL}
    

def handle_user_login(session_data: GlobalSessionData, 
                      username: str) \
    -> GlobalSessionData:

    profile = read_json_to_dict(f"{ROOT_USER_PROFILES}{username}.json")
    session_data.username = username.lower()
    session_data.profile_path = retrieve_profile_path_from_username(username)
    session_data.profile = profile
    session_data.firstname = profile["name"]

    return session_data


def handle_user_signup(session_data: GlobalSessionData,
                       username: str, 
                       firstname: str) \
    -> GlobalSessionData:
    
    username = username.lower()
    session_data.users[username] = {"username": username, "firstname": firstname}
    write_dict_to_json(session_data.users, f"{ROOT_USER_PROFILES}{FILENAME_USERS_DB}")
    user_template = read_json_to_dict(f"{ROOT_USER_PROFILES}{FILENAME_PROFILE_TEMPLATE}")
    user_template["name"] = firstname
    write_dict_to_json(user_template, f"{ROOT_USER_PROFILES}{username}.json")

    return session_data