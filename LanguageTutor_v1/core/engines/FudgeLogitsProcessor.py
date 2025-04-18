import re
import torch
import torch.nn.functional as F
from transformers import LogitsProcessor

class FudgeLogitsProcessor(LogitsProcessor):
    def __init__(self, bp_model, bp_tokenizer, bp_device, target_idx, lamda, base_tokenizer, prompt_token_len: int, top_k: int = 50):
        self.bp_model = bp_model
        self.bp_tokenizer = bp_tokenizer
        self.bp_device = bp_device
        self.target_idx = target_idx
        self.lamda = lamda
        self.base_tokenizer = base_tokenizer
        self.prompt_token_len = prompt_token_len
        self.top_k = top_k
        self._terminal_re = re.compile(r'。+$')
        self._splitter    = re.compile(r'。+')

    def __call__(self, input_ids, scores):
        if self.lamda == 0:
            return scores

        device = scores.device
        topk_logits, topk_indices = torch.topk(scores, self.top_k, dim=-1)
        probs_G = F.softmax(topk_logits, dim=-1).squeeze(0)   # (k,)

        bp_texts = []
        for tok_id in topk_indices[0]:
            cand_ids = torch.cat([input_ids[0], tok_id.unsqueeze(0)], dim=0)
            decoded  = self.base_tokenizer.decode(
                cand_ids[self.prompt_token_len:], skip_special_tokens=True
            )

            pieces = self._splitter.split(decoded)
            # if it ends in “。” drop that final empty piece
            if self._terminal_re.search(decoded) and len(pieces) >= 2:
                bp_text = pieces[-2]
            else:
                bp_text = pieces[-1]
            bp_texts.append(bp_text)

        # BP forward pass
        bp_in = self.bp_tokenizer(
            bp_texts, return_tensors="pt", padding=True, truncation=True
        ).to(self.bp_device)
        with torch.no_grad():
            bp_logits = self.bp_model(**bp_in).logits
            p_bp      = F.softmax(bp_logits, dim=-1)[:, self.target_idx].to(device)
        # FUDGE
        fudge = torch.log((1 - self.lamda) +
                          self.lamda * (p_bp / probs_G + 1e-9))

        new_scores = scores.clone()
        new_scores[0, topk_indices[0]] = topk_logits + fudge
        return new_scores