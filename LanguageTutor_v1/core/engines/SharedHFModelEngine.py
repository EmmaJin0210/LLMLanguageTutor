import torch
from kani.engines.huggingface import HuggingEngine
from kani.engines.huggingface.chat_template_pipeline import ChatTemplatePromptPipeline
from LanguageTutor_v1.core.engines.engine_constants import DEFAULT_TOKENIZER_KWARGS, \
    DEFAULT_MODEL_LOAD_KWARGS

class SharedHFModelEngine(HuggingEngine):
    def __init__(self, model_id, 
                 model = None, tokenizer = None,
                 tokenizer_kwargs = DEFAULT_TOKENIZER_KWARGS,
                 model_load_kwargs = DEFAULT_MODEL_LOAD_KWARGS,
                 device = "cuda",
                 prompt_pipeline = None, 
                 max_context_size = None,
                 token_reserve = 0,
                 **kwargs):
        # If model and tokenizer are already provided, bypass parent's loading
        if model is not None and tokenizer is not None:
            self.model = model
            self.tokenizer = tokenizer
            self.model_id = model_id
            self.device = device

            # Patch pad_token_id
            if self.tokenizer.pad_token_id is None or self.tokenizer.pad_token_id == self.tokenizer.eos_token_id:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            
            if prompt_pipeline is None:
                prompt_pipeline = ChatTemplatePromptPipeline(self.tokenizer)
            self.pipeline = prompt_pipeline

            if max_context_size is None:
                max_context_size = getattr(
                    self.model.config, "model_max_len",
                    getattr(self.model.config, "max_position_embeddings", None)
                )
                if max_context_size is None:
                    raise ValueError(
                        "Could not infer model's max context size from config. Pass `max_context_size`."
                    )
            self.max_context_size = max_context_size

            if self.model.device.type != self.device:
                self.model.to(self.device)

            # If token_reserve isn't given
            if token_reserve == 0 and self.pipeline:
                prompt = self.pipeline.execute([], for_measurement=True)
                if isinstance(prompt, torch.Tensor):
                    token_reserve = len(prompt[0])
                else:
                    tokenized = self.tokenizer.encode(prompt, add_special_tokens=False)
                    token_reserve = len(tokenized)
            self.token_reserve = token_reserve
            self.hyperparams = kwargs
        else:
            super().__init__(
                model_id = model_id,
                device = device,
                tokenizer_kwargs = tokenizer_kwargs,
                model_load_kwargs = model_load_kwargs,
                **kwargs
            )

            # Patch pad_token_id
            if self.tokenizer.pad_token_id is None or self.tokenizer.pad_token_id == self.tokenizer.eos_token_id:
                self.tokenizer.pad_token = self.tokenizer.eos_token



    def _get_generate_args(self, prompt: str | torch.Tensor, **hyperparams):
        if isinstance(prompt, str):
            tokenized = self.tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
            input_toks = tokenized
            input_len = len(tokenized[0])
        elif isinstance(prompt, torch.Tensor):
            input_toks = prompt
            input_len = len(input_toks[0])
        else:
            raise TypeError("build_prompt should either return a str or a Tensor.")

        if input_toks.device.type != self.device:
            input_toks = input_toks.to(self.device)

        attention_mask = torch.ones_like(input_toks)
        hyperparams["attention_mask"] = attention_mask

        hyperparams = {**self.hyperparams, **hyperparams}
        hyperparams.setdefault("max_length", self.max_context_size)

        return input_toks, input_len, hyperparams

