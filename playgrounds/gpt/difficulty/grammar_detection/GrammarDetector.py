from openai import OpenAI
from utils import *

def detect_grammar_sys_prompt(grammar_keys):
    system_prompt = "You are a helpful grammar detection assistant."
    system_prompt += "Given a sentence from the user, your job is to detect whether the sentence uses "
    system_prompt += "a grammar point that is in the list of grammar points below: \n"
    system_prompt += str(grammar_keys) + "\n"
    system_prompt += "If the detection is positive, output the grammar points used in the sentence that are also in the above list, "
    system_prompt += "in the EXACT SAME WORDING/FORMAT as the grammar point appears in the list above. "
    system_prompt += "If the detection is negative, output the word 'NONE'."
    system_prompt += "If there are multiple grammar points that matches with something in the list detected, "
    system_prompt += "output them separated by ||, like this: grammar_1||grammar_2||grammar_3||...."
    system_prompt += "Remember, each grammar point you output needs to EXACTLY match an item in the list provided, not a character more or less."
    system_prompt += "Do not output anything that does not match EXACTLY with an item in the list."
    return system_prompt


class GrammarDetector:
    def __init__(self, language, levels):
        self.grammar_dict = load_grammar_file_to_dict(language, levels)
        self.grammar_points = get_grammar_keys(self.grammar_dict)
        self.system_prompt = detect_grammar_sys_prompt(self.grammar_points)
        print(self.system_prompt)
        self.model = OpenAI()
    
    def detect_grammar(self, sentence):
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": "その花はとても美しいです。"},
                {"role": "assistant", "content": "だ / です||とても||は||い-adjectives"},
                {"role": "user", "content": "一緒にします。"},
                {"role": "assistant", "content": "一緒に（いっしょに）"},
                # {"role": "user", "content": "友達はまだ家に帰っていません。"},
                # {"role": "assistant", "content": "は||まだ||まだ～ていません||ている"},
                # {"role": "user", "content": "もう11時だ。今寝なければなりません。"},
                # {"role": "assistant", "content": "もう||だ / です"},
                # {"role": "user", "content": "しなくてもいいです。"},
                # {"role": "assistant", "content": "なくてもいい||だ / です"},
                {"role": "user", "content": sentence}
            ]
        )
        model_output = completion.choices[0].message.content
        gp_detected = model_output.split("||")
        return gp_detected

