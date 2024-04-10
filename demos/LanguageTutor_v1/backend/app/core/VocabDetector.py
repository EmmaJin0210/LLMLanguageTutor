from openai import OpenAI
from utils import *

# TODO: pass in JSON instead; or just the index? (other)

def detect_vocab_level_sys_prompt(vocab, language):
    system_prompt = f"You are a helpful {language} vocabulary detection assistant."
    system_prompt += "Given a sentence from the user, your job is to detect whether the sentence uses "
    system_prompt += "a vocabulary that is in the list of vocabulary below: \n"
    system_prompt += str(vocab) + "\n"
    system_prompt += "Keep in mind that using a direct conjugation of a word also counts as using that word."
    system_prompt += "If the detection is positive, output the vocabulary used in the sentence that are also in the above list, "
    system_prompt += "in the EXACT SAME WORDING/FORMAT as the vocabulary appears in the list above. "
    system_prompt += "If the detection is negative, output the word 'NONE'."
    system_prompt += "If there are multiple vocabulary that matches with something in the list detected, "
    system_prompt += "output them separated by ||, like this: vocabulary_1||vocabulary_2||vocabulary_3||...."
    system_prompt += "Remember, each vocabulary you output needs to EXACTLY match an item in the list provided, not a character more or less."
    system_prompt += "Do not output anything that does not match EXACTLY with an item in the list."
    return system_prompt

def detect_vocab_plain_sys_prompt(language):
    system_prompt = f"You are a helpful {language} vocabulary detection assistant."
    system_prompt += "Given a sentence from the user, your job is to detect whether the sentence uses a vocabulary, "
    system_prompt += "and if yes, what vocabulary point(s) it uses."
    system_prompt += "If the detection is negative, output the word 'NONE'."
    system_prompt += "If there are multiple vocabularies used, "
    system_prompt += "output them separated by ||, like this: vocabulary_1||vocabulary_2||vocabulary_3||...."
    system_prompt += f"Output the vocabularies in {language}."
    system_prompt += "Keep in mind that using a direct conjugation of a word also counts as using that word."
    return system_prompt


class VocabDetectorLevel:
    def __init__(self, language, vocab_points, keys):
        self.vocab_points = vocab_points
        self.vocab_keys = keys
        self.system_prompt = detect_vocab_level_sys_prompt(self.vocab_points, language)
        self.model = OpenAI()
    
    def detect_vocab(self, sentence):
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": "その花はとても美しいです。"},
                {"role": "assistant", "content": "だ / です||とても||は||い-adjectives"},
                {"role": "user", "content": "一緒にします。"},
                {"role": "assistant", "content": "一緒に（いっしょに）"},
                {"role": "user", "content": sentence}
            ]
        )
        model_output = completion.choices[0].message.content
        vp_detected = model_output.split("||")
        to_check = vp_detected
        for vp in to_check:
            if vp not in self.vocab_points:
                vp_detected.remove(vp)
        return vp_detected


class VocabDetectorPlain:
    def __init__(self, language):
        self.system_prompt = detect_vocab_plain_sys_prompt(language)
        self.model = OpenAI()
    
    def detect_vocab(self, sentence):
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": sentence}
            ]
        )
        model_output = completion.choices[0].message.content
        vp_detected = model_output.split("||")
        return vp_detected
