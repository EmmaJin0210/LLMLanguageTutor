import os
import torch
from openai import AsyncOpenAI as OpenAIClient
from kani.engines.openai import OpenAIEngine
from transformers import AutoModelForCausalLM, AutoTokenizer
from LanguageTutor_v1.core.engines.ControlledGenFudgeEngine import ControlledGenFudgeEngine
from LanguageTutor_v1.core.engines.SharedHFModelEngine import SharedHFModelEngine
from LanguageTutor_v1.core.engines.OvergenerationEngine import OvergenerationEngine
from LanguageTutor_v1.core.engines.HFOvergenerationEngine import HFOvergenerationEngine
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
from LanguageTutor_v1.core.sysprompts import get_sysprompt_eval_baseline, get_sysprompt_eval_detailed
from LanguageTutor_v1.core.core_utils.language_utils import load_vocab_file_to_dict
from LanguageTutor_v1.core.core_constants import ENGINE_ID_OPENAI_OG, ENGINE_ID_DEEPSEEK, ENGINE_ID_OPENAI
from LanguageTutor_v1.core.models.model_constants import MODEL_ID_HF_DEFAULT, MODEL_ID_OPENAI_DEFAULT, \
    LAMBDA, MODEL_ID_LM_TINY, MODEL_ID_LM_SMALL

###### imports for typing purposes ######
from kani.engines.base import BaseEngine
#########################################


# # engine consts
class EngineTypes:
    FUDGE_ENGINE = "fudge"
    OVERGEN_ENGINE = "overgen"
    HFOVERGEN_ENGINE = "hfovergen"
    SHAREDHFMODEL_ENGINE = "sharedhfmodel" # serves as base hf engine
    OPENAI_ENGINE = "openai"

# # prompt versions
# class PromptVersions:
#     BASELINE = "baseline"
#     DETAILED = "detailed"

class ChatbotLevel:
    N1 = "n1"
    N2 = "n2"
    N3 = "n3"
    N4 = "n4"
    N5 = "n5"

# # if model is not specified, fall to default model of the engine
# engine_to_default_model = {
#     # "fudge" : MODEL_ID_HF_DEFAULT,
#     "fudge" : MODEL_ID_HF_DEFAULT,
#     "overgen" : MODEL_ID_OPENAI_DEFAULT,
#     "hfovergen" : MODEL_ID_HF_DEFAULT,
#     "sharedhfmodel" : MODEL_ID_HF_DEFAULT,
#     "openai" : MODEL_ID_OPENAI_DEFAULT
# }

# username = "emma"
# student_level = "n5"
# track_usage = False
# target_language = "japanese"
# all_levels = get_all_levels(target_language)
# my_openai_key = os.getenv("OPENAI_API_KEY")

# load_dotenv()


# def parse_args():
#     parser = argparse.ArgumentParser(description="Language Tutor Eval Options")

#     parser.add_argument(
#         "-P", choices=["baseline", "detailed"], required=True,
#         help="System prompt style"
#     )

#     parser.add_argument(
#         "-TE", choices=["fudge", "overgen", "hfovergen", "sharedhfmodel", "openai"], required=True,
#         help="Tutor engine (fudge or overgen or hfovergen or sharedhfmodel or openai)"
#     )

#     parser.add_argument(
#         "-LEVEL", choices=["n1", "n2", "n3", "n4", "n5"], required=True,
#         help="Chatbot level (n1 - n5)"
#     )

#     parser.add_argument(
#         "-TM", type=str, required=False,
#         help="Tutor model. Have paired defaults with Tutor engine. Can specify none-default model here if wanted."
#     )

#     parser.add_argument(
#         "-LAMBDA", type=float, required=False,
#         help="Interpolation weight for FUDGE (0.0 = pure LM, 1.0 = pure predictor)"
#     )

#     return parser.parse_args()


# def prep_overgen_engine(model_id, target_level):
#     vocab_dict = load_vocab_file_to_dict(
#         language = target_language,
#         levels = all_levels,
#         vocab_dir = os.path.join("vocab_lists", "jpwac")
#     )
#     client = OpenAIClient(api_key = my_openai_key)
#     return OvergenerationEngine(
#         language = target_language, 
#         target_level = target_level, 
#         vocab_dict = vocab_dict,
#         grammar_dict = {},
#         client = client,
#         model = model_id
#     )

# def prep_hfovergen_engine(model_id, target_level):
#     vocab_dict = load_vocab_file_to_dict(
#         language = target_language,
#         levels = all_levels,
#         vocab_dir = os.path.join("vocab_lists", "jpwac")
#     )
#     return HFOvergenerationEngine(
#         language = target_language, 
#         target_level = target_level, 
#         vocab_dict = vocab_dict,
#         grammar_dict = {},
#         model_id = model_id
#     )

# def setup_tutor_engine(engine_id, model_id, bot_level, lamda):
#     return set_up_engine(
#         engine_id = engine_id,
#         model_id = model_id,
#         bot_level = bot_level,
#         lamda = lamda
#     )

# def set_up_engine(engine_id, model_id,
#                   bot_level = None, lamda = LAMBDA):
#     SAMPLE_KW = {}

#     match engine_id:

#         case EngineTypes.FUDGE_ENGINE:
#             return ControlledGenFudgeEngine(
#                 model_id = model_id,
#                 target_difficulty = bot_level,
#                 lamda = lamda
#             )
        
#         case EngineTypes.SHAREDHFMODEL_ENGINE:
#             return SharedHFModelEngine(
#                 model_id = model_id,
#                 **SAMPLE_KW
#             )
        
#         case EngineTypes.OVERGEN_ENGINE:
#             return prep_overgen_engine(
#                 model_id = model_id,
#                 target_level = bot_level
#             )
        
#         case EngineTypes.HFOVERGEN_ENGINE:
#             return prep_hfovergen_engine(
#                 model_id = model_id,
#                 target_level = bot_level
#             )
        
#         case EngineTypes.OPENAI_ENGINE:
#             return OpenAIEngine(
#                 my_openai_key, 
#                 model = model_id,
#                 **SAMPLE_KW
#             )

# def setup_tutor_system_prompt(bot_level, student_level, version):
#     match version:
#         case PromptVersions.BASELINE:
#             return get_sysprompt_eval_baseline(
#                 language = target_language,
#                 level = bot_level
#             )
#         case PromptVersions.DETAILED:
#             return get_sysprompt_eval_detailed(
#                 language = target_language,
#                 tutor_level = bot_level,
#                 student_level = student_level
#             )


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

def prep_hfovergen_engine(model_id, target_level, shared_model, shared_tokenizer):
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
        model_id = model_id,
        model = shared_model,
        tokenizer = shared_tokenizer
    )


def set_up_engine(engine_id, model_id, shared_model, shared_tokenizer, 
                  bot_level = None, lamda = LAMBDA, for_student = False):
    SAMPLE_KW = {}
    if for_student:
        if engine_id == EngineTypes.SHAREDHFMODEL_ENGINE:
            SAMPLE_KW = dict(temperature = 0.7, top_p = 1.0, do_sample = True)
        elif engine_id == EngineTypes.OPENAI_ENGINE:
            SAMPLE_KW = dict(temperature = 0.7, top_p = 1.0)
        else:
            SAMPLE_KW = {}

    match engine_id:

        case EngineTypes.FUDGE_ENGINE:
            return ControlledGenFudgeEngine(
                model = shared_model, 
                tokenizer = shared_tokenizer,
                model_id = model_id,
                target_difficulty = bot_level,
                lamda = lamda
            )
        
        case EngineTypes.SHAREDHFMODEL_ENGINE:
            return SharedHFModelEngine(
                model = shared_model,
                tokenizer = shared_tokenizer,
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
                target_level = bot_level,
                shared_model = shared_model,
                shared_tokenizer = shared_tokenizer
            )
        
        case EngineTypes.OPENAI_ENGINE:
            return OpenAIEngine(
                my_openai_key, 
                model = model_id,
                **SAMPLE_KW
            )
        

def setup_tutor_engine(engine_id, model_id, shared_model, shared_tokenizer, bot_level, lamda):
    return set_up_engine(
        engine_id = engine_id,
        model_id = model_id,
        shared_model = shared_model,
        shared_tokenizer = shared_tokenizer,
        bot_level = bot_level,
        lamda = lamda
    )



# TODO: don't use this anymore
def create_engine(engine_id: str, model_id: str, **kwargs) -> BaseEngine:
    model_id = MODEL_ID_LM_SMALL
    # if engine_id == ENGINE_ID_OPENAI_OG:
    #     my_key = os.getenv("OPENAI_API_KEY")
    #     client = OpenAIClient(api_key = my_key)
    #     engine = OvergenerationEngine(language = kwargs.get("language"), 
    #                                     target_level = kwargs.get("target_level"), 
    #                                     vocab_dict = kwargs.get("vocab_dict"),
    #                                     grammar_dict = kwargs.get("grammar_dict"),
    #                                     client = client,
    #                                     model = model_id)
    # elif engine_id == ENGINE_ID_OPENAI:
    #     my_key = os.getenv("OPENAI_API_KEY")
    #     engine = OpenAIEngine(api_key = my_key, model = model_id)
    # TODO: CHANGE THIS COMPLETELY
    shared_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code = True,
        device_map = "balanced_low_0",
        torch_dtype=torch.float16
    )
    shared_tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        trust_remote_code = True
    )

    if shared_tokenizer.pad_token_id is None or shared_tokenizer.pad_token_id == shared_tokenizer.eos_token_id:
        shared_tokenizer.pad_token = shared_tokenizer.eos_token


    return ControlledGenFudgeEngine(
        model=shared_model,
        tokenizer=shared_tokenizer,
        model_id = model_id,
        target_difficulty = "n4",
        lamda = 0.8
    )
    # my_key = os.getenv("OPENAI_API_KEY")
    # engine = OpenAIEngine(api_key = my_key, model = model_id)
    # return engine


async def clean_up(engine: BaseEngine) -> None:
    # if engine:
    #     await engine.client.close()
    await engine.close()