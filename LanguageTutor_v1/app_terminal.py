import warnings
import asyncio
import importlib
from kani import ChatMessage, ChatRole

from LanguageTutor_v1.core.kanis.ConversationKani import ConversationKani

from LanguageTutor_v1.core.core_utils.profile_utils import retrieve_profile_path_from_username, \
    write_updated_profile_to_file

from LanguageTutor_v1.core.core_utils.chat_utils import format_chat_history_for_summary, \
    summarize_rounds_history, summarize_user_interests, summarize_user_personal_info

from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels, load_vocab_file_to_dict

from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict

from LanguageTutor_v1.core.engines.ControlledGenFudgeEngine import ControlledGenFudgeEngine

from LanguageTutor_v1.core.core_constants import KANI_F_STORE_INTEREST, KANI_F_STORE_PERSONAL_INFO
import asyncio
import os
import torch
import argparse
from dotenv import load_dotenv
from openai import AsyncOpenAI as OpenAIClient
from transformers import AutoModelForCausalLM, AutoTokenizer
from kani.engines.openai import OpenAIEngine
from LanguageTutor_v1.core.kanis.LogTruncationKani import LogTruncationKani
from LanguageTutor_v1.core.engines.ControlledGenFudgeEngine import ControlledGenFudgeEngine
from LanguageTutor_v1.core.engines.SharedHFModelEngine import SharedHFModelEngine
from LanguageTutor_v1.core.engines.OvergenerationEngine import OvergenerationEngine
from LanguageTutor_v1.core.engines.HFOvergenerationEngine import HFOvergenerationEngine
from LanguageTutor_v1.core.sysprompts import get_sysprompt_eval_baseline, get_sysprompt_eval_detailed
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
from LanguageTutor_v1.core.models.model_constants import MODEL_ID_HF_DEFAULT, MODEL_ID_OPENAI_DEFAULT, \
    LAMBDA
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict
from LanguageTutor_v1.core.core_utils.language_utils import load_vocab_file_to_dict


# engine consts
class EngineTypes:
    FUDGE_ENGINE = "fudge"
    OVERGEN_ENGINE = "overgen"
    HFOVERGEN_ENGINE = "hfovergen"
    SHAREDHFMODEL_ENGINE = "sharedhfmodel" # serves as base hf engine
    OPENAI_ENGINE = "openai"

# prompt versions
class PromptVersions:
    BASELINE = "baseline"
    DETAILED = "detailed"

class ChatbotLevel:
    N1 = "n1"
    N2 = "n2"
    N3 = "n3"
    N4 = "n4"
    N5 = "n5"

# if model is not specified, fall to default model of the engine
engine_to_default_model = {
    "fudge" : MODEL_ID_HF_DEFAULT,
    "overgen" : MODEL_ID_OPENAI_DEFAULT,
    "hfovergen" : MODEL_ID_HF_DEFAULT,
    "sharedhfmodel" : MODEL_ID_HF_DEFAULT,
    "openai" : MODEL_ID_OPENAI_DEFAULT
}

username = "anon"
student_level = "n5"
track_usage = False
target_language = "japanese"
all_levels = get_all_levels(target_language)
my_openai_key = os.getenv("OPENAI_API_KEY")

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description="Language Tutor Eval Options")

    parser.add_argument(
        "-P", choices=["baseline", "detailed"], required=True,
        help="System prompt style"
    )

    parser.add_argument(
        "-TE", choices=["fudge", "overgen", "hfovergen", "sharedhfmodel", "openai"], required=True,
        help="Tutor engine (fudge or overgen or hfovergen or sharedhfmodel or openai)"
    )

    parser.add_argument(
        "-LEVEL", choices=["n1", "n2", "n3", "n4", "n5"], required=True,
        help="Chatbot level (n1 - n5)"
    )

    parser.add_argument(
        "-TM", type=str, required=False,
        help="Tutor model. Have paired defaults with Tutor engine. Can specify none-default model here if wanted."
    )

    parser.add_argument(
        "-LAMBDA", type=float, required=False,
        help="Interpolation weight for FUDGE (0.0 = pure LM, 1.0 = pure predictor)"
    )

    parser.add_argument(
        "--engine",
        type=str,
        required=False,
        help="Engine as <module>:<Class>"
    )

    return parser.parse_args()


def load_engine(engine_spec: str):
    module_path, class_name = engine_spec.split(":")
    module = importlib.import_module(f"LanguageTutor_v1.core.engines.{module_path}")
    engine_class = getattr(module, class_name)
    return engine_class()

def prep_overgen_engine(model_id, target_level):
    vocab_dict = load_vocab_file_to_dict(
        language = target_language,
        levels = all_levels,
        vocab_dir = os.path.join("vocab_lists", "jpwac")
    )
    client = OpenAIClient(api_key = my_openai_key)
    return OvergenerationEngine(
        language = target_language, 
        target_level = target_level, 
        vocab_dict = vocab_dict,
        grammar_dict = {},
        client = client,
        model = model_id
    )

def prep_hfovergen_engine(model_id, target_level):
    vocab_dict = load_vocab_file_to_dict(
        language = target_language,
        levels = all_levels,
        vocab_dir = os.path.join("vocab_lists", "jpwac")
    )
    return HFOvergenerationEngine(
        language = target_language, 
        target_level = target_level, 
        vocab_dict = vocab_dict,
        grammar_dict = {},
        model_id = model_id
    )

def setup_tutor_engine(engine_id, model_id, bot_level, lamda):
    return set_up_engine(
        engine_id = engine_id,
        model_id = model_id,
        bot_level = bot_level,
        lamda = lamda
    )

def set_up_engine(engine_id, model_id,
                  bot_level = None, lamda = LAMBDA):
    SAMPLE_KW = {}

    match engine_id:

        case EngineTypes.FUDGE_ENGINE:
            return ControlledGenFudgeEngine(
                model_id = model_id,
                target_difficulty = bot_level,
                lamda = lamda
            )
        
        case EngineTypes.SHAREDHFMODEL_ENGINE:
            return SharedHFModelEngine(
                model_id = model_id,
                **SAMPLE_KW
            )
        
        case EngineTypes.OVERGEN_ENGINE:
            return prep_overgen_engine(
                model_id = model_id,
                target_level = bot_level
            )
        
        case EngineTypes.HFOVERGEN_ENGINE:
            return prep_hfovergen_engine(
                model_id = model_id,
                target_level = bot_level
            )
        
        case EngineTypes.OPENAI_ENGINE:
            return OpenAIEngine(
                my_openai_key, 
                model = model_id,
                **SAMPLE_KW
            )

def setup_tutor_system_prompt(bot_level, student_level, version):
    match version:
        case PromptVersions.BASELINE:
            return get_sysprompt_eval_baseline(
                language = target_language,
                level = bot_level
            )
        case PromptVersions.DETAILED:
            return get_sysprompt_eval_detailed(
                language = target_language,
                tutor_level = bot_level,
                student_level = student_level
            )


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
    if engine.client:
        await engine.client.close()
    await engine.close()

def main():
    args = parse_args()
    prompt_version = args.P
    t_engine_id = args.TE
    t_model_id = args.TM if args.TM else engine_to_default_model[t_engine_id]
    lamda = args.LAMBDA
    target_level = args.LEVEL

    profile_path = retrieve_profile_path_from_username(username)
    user_profile = read_json_to_dict(profile_path)

    tutor_engine = setup_tutor_engine(
        engine_id = t_engine_id,
        model_id = t_model_id,
        bot_level = target_level,
        lamda = lamda
    )
    tutor_system_prompt = setup_tutor_system_prompt(
        bot_level = target_level,
        student_level = student_level,
        version = prompt_version
    )

    tutor = ConversationKani(user_profile=user_profile, 
                             engine=tutor_engine, 
                             system_prompt=tutor_system_prompt, 
                             desired_response_tokens=15)
    
    user_profile = asyncio.run(language_chat(tutor, user_profile, target_language, track_usage))

    write_updated_profile_to_file(user_profile, profile_path)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    main()
