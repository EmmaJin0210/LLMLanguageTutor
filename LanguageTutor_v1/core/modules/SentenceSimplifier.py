from openai import OpenAI

language = "Japanese"

simplify_formal_sys_prompt = """You are a helpful sentence simplifier for language learners.
Given a sentence in any language from the user, your job is to simplify the sentence and make it easier to understand.
Preserve the main meaning of the original sentence but use easier expressions.
However, the sentence should still be non-casual.
Note that the simplified sentence should be in the same language as the original sentence.
"""

simplify_casual_sys_prompt = """You are a helpful sentence simplifier for language learners.
Given a sentence in any language from the user, your job is to simplify the sentence and make it more casual and easier to understand.
Note that the simplified sentence should be in the same language as the original sentence.
"""

def get_swap_formal_sys_prompt(language, backup_language):
    prompt = f"""You are a helpful {language} expression swapper for language learners.
    Given a sentence in any language from the user, as well as a don't-use list of expressions that are present in the current sentence but shouldn't be used, you should:
    For each expression in the don't-use list,
    first, locate where that expression is in the sentence provided;
    then, sububstitute that expression for a more beginner-level expression.

    Leave everything else in the sentence EXACTLY THE SAME as before. ONLY swap out expressions in the don't-use list provided.

    Before outputting, make sure AGAIN that the simplified sentence doesn't contain expressions in the don't-use list.
    Note that the simplified sentence should be in the same language as the original sentence.
    """
    return prompt
#     If the expression to swap out is a noun or if you can't find a simpler way to put it, swap the expression with the same expression said in {backup_language}.
# Althought you should also shorten the sentence if it's relatively long for chatting,
# the sentence form should still be non-casual.
#     If the expression to swap out is a noun, or if you can't find a simpler way to put it, swap the expression with the same expression said in {backup_language}.

substitute_casual_sys_prompt = """You are a helpful sentence simplifier for language learners.
Given a sentence in any language from the user, your job is to make the sentence easier to understand by substituting expressions from the lists that the user provides for easier expressions,
while preserving the meaning of the original sentence.
You should also make the sentence more casual.
Note that the simplified sentence should be in the same language as the original sentence.
"""

class SentenceSimplifier:

    def __init__(self, language, backup_language, grammar_target, grammar_above, vocab_target, vocab_above):
        self.language = language
        self.backup_language = backup_language
        
        self.init_formal_sys_prompt = simplify_formal_sys_prompt
        self.init_casual_sys_prompt = simplify_casual_sys_prompt
        self.swap_formal_sys_prompt = get_swap_formal_sys_prompt(language, backup_language)
        self.swap_casual_sys_prompt = substitute_casual_sys_prompt

        self.grammar_target = grammar_target
        self.grammar_above = grammar_above
        self.vocab_target = vocab_target
        self.vocab_above = vocab_above
        self.model = OpenAI()

    def simplify_sentence_formal(self, sentence):
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":  self.init_formal_sys_prompt},
                {"role": "user", "content": sentence},
            ]
        )
        model_output = completion.choices[0].message.content
        return model_output
    

    def simplify_sentence_casual(self, sentence):
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":  self.init_casual_sys_prompt},
                {"role": "user", "content": sentence},
            ]
        )
        model_output = completion.choices[0].message.content
        return model_output

    def swap_hard_expressions_formal(self, to_swap, sentence):
        def create_shot():
            user = "Sentence to simplify: J-POPと推理小説ですか。それはとてもいいですね。そのトピックで話しましょう。あなたのお気に入りの歌手やバンドは何ですか?"
            user += "\ndon't-use list: ['気に入る','歌手']"
            assistant = "J-POPと推理小説ですか。それはとてもいいですね。そのトピックで話しましょう。あなたの好きな歌う人やバンドは何ですか?"
            return user, assistant
        shot_u, shot_a = create_shot()
        user = "Sentence to simplify: 大変でしたね。数学は得意ですか？それともちょっと難しいですか？"
        user += "\ndon't-use list: ['それとも','得意']"
        assistant = "大変でしたね。数学は簡単ですか、ちょっと難しいですか。"
        
        user_prompt = "Sentence to simplify: " + sentence + "\n"
        user_prompt += "\ndon't-use list: " + str(to_swap) + "\n"
        print("no use: ", user_prompt)
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":  self.swap_formal_sys_prompt},
                {"role": "user", "content": shot_u},
                {"role": "assistant", "content": shot_a},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
                {"role": "user", "content": user_prompt}
            ]
        )
        model_output = completion.choices[0].message.content
        return model_output
    
    def swap_hard_expressions_casual(self, to_swap, sentence):
        def create_shot():
            user = "Sentence to simplify: J-POPと推理小説ですか。それはとてもいいですね。そのトピックで話しましょう。あなたのお気に入りの歌手やバンドは何ですか?"
            user += "Grammar in the sentence that's too hard: [気に入る]"
            user += "Words in the sentence that are too hard: [歌手]"
            assistant = "J-POPと推理小説、いいね!その話題で話そうよ。好きなうたうひとやバンドは何?"
            return user, assistant
        shot_u, shot_a = create_shot()
        user_prompt = "Sentence to simplify: " + sentence + "\n"
        user_prompt += "Grammar in the sentence that's too hard: " + str(to_swap) + "\n"
        user_prompt += "Words in the sentence that are too hard: " +  str(to_swap)
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":  self.swap_casual_sys_prompt},
                {"role": "user", "content": shot_u},
                {"role": "assistant", "content": shot_a},
                {"role": "user", "content": user_prompt}
            ]
        )
        model_output = completion.choices[0].message.content
        return model_output

    def translate_hard_expressions(self, backup_language):
        pass
        