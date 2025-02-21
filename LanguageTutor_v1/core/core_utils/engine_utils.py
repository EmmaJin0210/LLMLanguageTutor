import os
from openai import AsyncOpenAI as OpenAIClient
from kani.engines.openai import OpenAIEngine

from core.engines.DifficultyEstimationEngine import DifficultyEstimationEngine
from core.engines.DeepSeekEngine import get_deepseek_engine
from core.core_constants import ENGINE_ID_OPENAI_DC, ENGINE_ID_DEEPSEEK, ENGINE_ID_OPENAI

###### imports for typing purposes ######
from kani.engines.base import BaseEngine
#########################################

def create_engine(engine_id: str, model_id: str, **kwargs) -> BaseEngine:
    if engine_id == ENGINE_ID_OPENAI_DC:
        my_key = os.getenv("OPENAI_API_KEY")
        client = OpenAIClient(api_key = my_key)
        engine = DifficultyEstimationEngine(language = kwargs.get("language"), 
                                            target_level = kwargs.get("target_level"), 
                                            vocab_dict = kwargs.get("vocab_dict"),
                                            grammar_dict = kwargs.get("grammar_dict"),
                                            client = client,
                                            model = model_id)
    elif engine_id == ENGINE_ID_DEEPSEEK:
        engine = get_deepseek_engine(model = model_id)
    elif engine_id == ENGINE_ID_OPENAI:
        my_key = os.getenv("OPENAI_API_KEY")
        engine = OpenAIEngine(api_key = my_key, model = model_id)

    return engine


async def clean_up(engine: BaseEngine) -> None:
    await engine.client.close()
    await engine.close()