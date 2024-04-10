from openai import OpenAI

simplify_formal_sys_prompt = """You are a helpful sentence simplifier for language learners.
Given a sentence in any language from the user, your job is to simplify the sentence and make it easier to understand.
However, the sentence should still be relatively formal and polite.
Note that the simplified sentence should be in the same language as the original sentence.
"""

class SentenceSimplifier:
    def __init__(self):
        self.simplify_formal_sys_prompt = simplify_formal_sys_prompt
        self.model = OpenAI()

    def simplify_sentence_formal(self, sentence):
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":  self.simplify_formal_sys_prompt},
                {"role": "user", "content": sentence},
            ]
        )
        model_output = completion.choices[0].message.content
        return model_output

    def substitute_hard_words(self):
        pass