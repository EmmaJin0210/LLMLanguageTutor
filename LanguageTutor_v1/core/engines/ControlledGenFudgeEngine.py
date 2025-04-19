import re
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from kani.models import ChatMessage
from kani.engines import Completion
from kani.ai_function import AIFunction

from LanguageTutor_v1.core.engines.SharedHFModelEngine import SharedHFModelEngine
from LanguageTutor_v1.core.engines.FudgeLogitsProcessor import FudgeLogitsProcessor
from LanguageTutor_v1.core.models.model_constants import MODEL_ID_PREDICTOR, LAMBDA



class ControlledGenFudgeEngine(SharedHFModelEngine):
    def __init__(self, model, tokenizer, model_id: str, target_difficulty: str, lamda: float = LAMBDA, **kwargs):
        super().__init__(
            model_id=model_id,
            model=model,
            tokenizer=tokenizer,
            **kwargs
        )
        self.target_difficulty = target_difficulty
        self.difficulty_map = {"n1": 0, "n2": 1, "n3": 2, "n4": 3, "n5": 4}
        # Load the binary predictor (BP) separately.
        self.bp_model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID_PREDICTOR)
        self.bp_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID_PREDICTOR)
        # Assign BP to a specific GPU: if more than one GPU is available, use "cuda:1"
        self.bp_device = torch.device("cuda:0") if torch.cuda.device_count() > 1 else torch.device("cuda")
        self.bp_model.to(self.bp_device)
        self.lamda = lamda

    async def predict(self, messages: list, functions: list[AIFunction] = None,
                      top_k: int = 50, max_new_tokens: int = 256, **kwargs) -> Completion:
        
        prompt = self.build_prompt(messages, functions)
        # Encode prompt as input IDs.
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        prompt_token_len = input_ids.size(1)
        attention_mask = torch.ones_like(input_ids)
        
        # Create the custom logits processor.
        fudge_processor = FudgeLogitsProcessor(
            bp_model = self.bp_model,
            bp_tokenizer = self.bp_tokenizer,
            bp_device = self.bp_device,
            target_idx = self.difficulty_map[self.target_difficulty],
            lamda = self.lamda,
            base_tokenizer = self.tokenizer,
            prompt_token_len = prompt_token_len,
            top_p = 0.7,
            top_k = top_k
        )
        
        logits_processor = [fudge_processor]
        
        
        outputs = self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            logits_processor=logits_processor,
            max_new_tokens = max_new_tokens,
            do_sample = True
        )
        # Decode the generated tokens.
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        # Remove the original prompt from the generated text.
        final_text = generated_text[len(prompt):].strip()
        final_message = ChatMessage.assistant(final_text)
        return Completion(message=final_message, prompt_tokens=None, completion_tokens=None)


################### OLD CODE WITHOUT THE LOGITS PROCESSOR ########################
# class ControlledGenFudgeEngine(SharedHFModelEngine):
#     def __init__(self, model, tokenizer, model_id: str, target_difficulty: str, lamda: float = LAMBDA, **kwargs):
#         super().__init__(
#             model_id = model_id,
#             model = model,
#             tokenizer = tokenizer,
#             **kwargs
#         )

#         self.target_difficulty = target_difficulty
#         self.difficulty_map = {"n1": 0, "n2": 1, "n3": 2, "n4": 3, "n5": 4}
#         # Load the binary predictor (BP) separately.
#         self.bp_model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID_PREDICTOR)
#         self.bp_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID_PREDICTOR)
#         # Assign BP to a specific GPU: if more than one GPU is available, use "cuda:1", else use the same device.
#         self.bp_device = torch.device("cuda:1") if torch.cuda.device_count() > 1 else torch.device("cuda")
#         self.bp_model.to(self.bp_device)
#         self.lamda = lamda
    
#     async def predict(self, messages: list, functions: list[AIFunction] = None, 
#                       max_new_tokens: int = 50, top_k: int = 50, **kwargs) -> Completion:
        
#         prompt = self.build_prompt(messages, functions)
#         generated = prompt
#         # print("INITIAL PROMPT: ", generated)
#         # old_generated = generated
#         # Generate tokens until end condition
#         for _ in range(max_new_tokens):
#             next_token = self.predict_next_token(generated, len(prompt), top_k=top_k, **kwargs)
#             # print("NEXT TOKEN PREDICTED: ", next_token)
#             # old_generated = generated
#             # Check for end-of-sequence token
#             if next_token.strip() == self.tokenizer.eos_token:
#                 # print("NEXT TOKEN: ", next_token, "|||GENERATED:", old_generated, '\n')
#                 break
#             generated += next_token

#         print("FINAL UTTERANCE: ", generated[len(prompt):])
#         final_message = ChatMessage.assistant(generated[len(prompt):].strip())
#         return Completion(message=final_message, prompt_tokens=None, completion_tokens=None)

#     def predict_next_token(self, prompt: str, orig_prompt_len: int, top_k: int = 50, **kwargs) -> str:
#         # Encode prompt for model_G
#         # print(f"PREDICTING NEXT TOKEN WITH GENERATED: ", prompt)
#         input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
#         attention_mask = torch.ones_like(input_ids, dtype=torch.long)
#         # Get logits for next token from model_G
#         with torch.no_grad():
#             outputs = self.model(input_ids, attention_mask=attention_mask)
#         logits = outputs.logits[:, -1, :]
        
#         # Select top-k candidate tokens from model_G
#         topk_logits, topk_indices = torch.topk(logits, top_k)
#         probs_G = F.softmax(topk_logits, dim = -1).squeeze()  # (top_k,)
        
#         combined_probs = []
#         target_idx = self.difficulty_map[self.target_difficulty]
#         # prefix = prompt[orig_prompt_len:]
        
#         # For each candidate token, adjust log-probability
#         for i, candidate_token_idx in enumerate(topk_indices.squeeze()):
#             # Decode candidate token
#             candidate_token = self.tokenizer.decode([candidate_token_idx],
#                                                     skip_special_tokens=True,
#                                                     errors="replace").strip()
#             new_prefix = prompt + candidate_token
#             # Split on terminal tokens "。？！"
#             new_prefix = new_prefix[orig_prompt_len:]
#             pieces = re.split(r'[。？！]+', new_prefix)
#             print("PIECES: ", pieces)
#             # pieces = new_prefix.split("<|im_start|>assistant")
#             # # Take the final piece
#             new_prefix = pieces[-1]
#             print("TRIMMED NEW PREFIX: ", new_prefix)
#             # Encode new prefix
#             bp_input_ids = self.bp_tokenizer(new_prefix, return_tensors="pt").to(self.bp_device)
#             # print(bp_input_ids)
#             with torch.no_grad():
#                 bp_outputs = self.bp_model(**bp_input_ids)
#                 bp_logits = bp_outputs.logits  # (1, num_labels)
#                 bp_probs = F.softmax(bp_logits, dim=-1).squeeze()
#                 # Current probability of target difficulty
#                 difficulty_prob = bp_probs[target_idx].to(self.device)
            
#             # linear interpolation
#             combined_prob = (1 - self.lamda) * probs_G[i] + self.lamda * difficulty_prob
#             # combined_log_prob = torch.log(probs_G[i]) + 2 * torch.log(difficulty_prob)
#             combined_probs.append(combined_prob)
        
#         combined_probs = torch.tensor(combined_probs, device=self.device)
#         combined_probs /= combined_probs.sum()
#         # INFLUENCE FUTURE PREDICTS, AND THE STUDENT MODEL
#         # Sample the next token
#         sampled_idx = torch.multinomial(combined_probs, num_samples=1)
#         final_token_idx = topk_indices[0, sampled_idx].item()
#         final_token = self.tokenizer.decode([final_token_idx])
#         print("FINAL TOKEN: ", final_token)
#         return final_token
