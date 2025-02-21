import functools
import threading
from kani.engines.base import BaseEngine, Completion
from kani.models import ChatMessage, ChatRole
from kani.ai_function import AIFunction
import core.modules.function_calling as function_calling
from core.engines.engine_constants import OPENAI_MODELS_CONTEXT_SIZES
from core.modules.TokenDetectorMatcher import TokenDetectorMatcher
from core.modules.DifficultyCalculator import DifficultyCalculator
from core.core_utils.language_utils import get_levels_below_inclusive, get_levels_above_exclusive

try:
    import tiktoken
except ImportError as e:
    raise ImportError('The DifficultyEstimationEngine requires OpenAI dependencies. Install with "pip install openai".') from None



class DifficultyEstimationEngine(BaseEngine):
    def __init__(self, language, target_level, vocab_dict, grammar_dict, client=None, model="gpt-4", tokenizer=None, **hyperparams):
        self.language = language
        self.target_level = target_level
        self.vocab_dict = vocab_dict
        self.grammar_dict = grammar_dict
        self.client = client
        self.model = model
        self.tokenizer = tokenizer or self._load_tokenizer()
        self.hyperparams = hyperparams

        max_context_size = next(size for prefix, size in OPENAI_MODELS_CONTEXT_SIZES if model.startswith(prefix))
        self.max_context_size = max_context_size

        self.levels_below = get_levels_below_inclusive(self.language, self.target_level)
        self.levels_above = get_levels_above_exclusive(self.language, self.target_level)

    def _load_tokenizer(self):
        """
        Initialize the tokenizer for the model.
        """
        try:
            return tiktoken.encoding_for_model(self.model)
        except ImportError:
            raise ImportError("The tiktoken library is required to use the tokenizer. Install it with 'pip install tiktoken'.")
        except KeyError:
            raise ValueError(f"No tokenizer found for the model '{self.model}'. Please specify a valid model or provide a tokenizer.")

    @property
    def token_reserve(self):
        """
        Returns the number of tokens reserved by the engine.
        """
        return self.function_token_reserve([])

    def message_len(self, message: ChatMessage) -> int:
        """
        Calculate the length of a message in tokens.
        """
        return len(message.content.split())

    def function_token_reserve(self, functions: list[AIFunction]) -> int:
        if not functions:
            return 0
        return self._function_token_reserve_impl(frozenset(functions))

    @functools.lru_cache(maxsize=256)
    def _function_token_reserve_impl(self, functions):
        # openai doesn't tell us exactly how their function prompt works, so
        # we rely on community reverse-engineering to build the right prompt
        # hopefully OpenAI releases a utility to calculate this in the future, this seems kind of fragile
        prompt = function_calling.prompt(functions)
        return len(self.tokenizer.encode(prompt)) + 16  # internal MD headers, namespace {} delimiters


    async def predict(self, messages, functions=None, **kwargs):
        """
        Generate a single response.
        """
        responses = []
        while not responses:
            responses = await self.generate_responses(messages, functions=functions, **kwargs)
        return self.pick_response(responses)

    async def generate_responses(self, messages, functions=None, n=5, **kwargs):
        translated_messages = [
            {"role": msg.role.value, "content": msg.content} for msg in messages
        ]

        if functions:
            # Validate and translate functions
            translated_functions = []
            for func in functions:
                if not hasattr(func, "parameters") or func.parameters is None:
                    func.parameters = {}  # Default to empty JSON Schema
                translated_functions.append({
                    "name": func.name,
                    "description": func.desc,
                    "parameters": func.parameters,
                })
        else:
            translated_functions = None

        payload = {
            "model": self.model,
            "messages": translated_messages,
            "n": n,
            "functions": translated_functions,
            **self.hyperparams,
            **kwargs,
        }

        response = await self.client.chat.completions.create(**payload)
        return [choice.message.content for choice in response.choices if choice.message.content]

    def pick_response(self, responses):
        """
        Select a response based on difficulty estimation using threading.
        Responses are scored based on difficulty and sorted (higher score first, fewer tokens as a tiebreaker).
        """
        token_matcher = TokenDetectorMatcher(self.vocab_dict, self.grammar_dict, language=self.language)
        difficulty_calculator = DifficultyCalculator()
        scored_responses = []
        threads = []

        def evaluate_response(response):
            """
            Evaluate a single response and append its score and token count to scored_responses.
            """
            tokens = token_matcher.tokenize(response)
            levels_below_to_matched, undetected = token_matcher.detect_tokens_at_levels(tokens, self.levels_below)
            levels_above_to_matched, _ = token_matcher.detect_tokens_at_levels(undetected, self.levels_above)
            difficulty_score = difficulty_calculator.calc_difficulty_score(
                self.language, levels_above_to_matched, levels_below_to_matched
            )

            scored_responses.append({
                "response": response,
                "score": difficulty_score,
                "token_count": len(tokens)
            })

        # Start threads to evaluate responses
        for response in responses:
            thread = threading.Thread(target=evaluate_response, args=(response,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        if not scored_responses:
            raise ValueError("No valid responses were scored.")

        # Sort responses: higher score first, then fewer tokens
        scored_responses.sort(key=lambda x: (x["score"], x["token_count"]))
        print(scored_responses)
        # Pick the top response
        best_response = scored_responses[0]["response"]

        # Wrap the selected response in a Completion object
        message = ChatMessage(role=ChatRole.ASSISTANT, content=best_response)
        return Completion(message=message, prompt_tokens=None, completion_tokens=None)



    async def close(self):
        """
        Close the client.
        """
        await self.client.close()
