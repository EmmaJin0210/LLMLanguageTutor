import functools
from kani.engines.huggingface import HuggingEngine
from kani.models import ChatMessage, ChatRole
from transformers import AutoTokenizer

class DeepSeekEngine(HuggingEngine):
    def __init__(self, model_id, cache_directory, device="cpu", **hyperparams):
        super().__init__(
            model_id=model_id,
            device=device,
            model_load_kwargs={"cache_dir": cache_directory},
            **hyperparams
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_directory)

    def build_prompt(self, messages, functions=None):
        formatted_messages = []
        for msg in messages:
            if msg.role == ChatRole.USER:
                formatted_messages.append(f"[USER]: {msg.content}\n")
            elif msg.role == ChatRole.ASSISTANT:
                formatted_messages.append(f"[ASSISTANT]: {msg.content}\n")

        return "".join(formatted_messages)

    def message_len(self, message: ChatMessage) -> int:
        return len(self.tokenizer.encode(message.content, add_special_tokens=False))


def get_deepseek_engine(model_id):
    cache_directory = "/Users/emmajin0210/Desktop/LLMLanguageTutor/LanguageTutor_v1/core/models"

    return DeepSeekEngine(
        model_id=model_id,
        cache_directory=cache_directory,
        device="cpu",
        max_context_size=4096,
        temperature=0.7
    )
