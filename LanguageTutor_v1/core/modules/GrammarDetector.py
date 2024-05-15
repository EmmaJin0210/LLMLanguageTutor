from openai import OpenAI
import os
import asyncio
from kani import Kani, ChatMessage
from kani.engines.openai import OpenAIEngine
from core.utils.utils import *

# TODO: pass in JSON instead; or just the index? (other)
# TODO: maybe integrate the two API calls into one? Chain-of_thoughts prompting?
# TODO: maybe it will be better if we take in the tokenized sentence as input, instead of just the sentence itself?
# TODO: !!! Maybe we could do a matching first with some token matcher and then ask GPT to select from the potential grammar points

def detect_grammar_level_sys_prompt(grammar_keys, language):
    system_prompt = f"You are a helpful {language} grammar detection assistant."
    system_prompt += "Given a sentence from the user, your job is to detect whether the sentence uses "
    system_prompt += "a grammar point that is in the list of grammar points below: \n"
    system_prompt += str(grammar_keys) + "\n"
    system_prompt += "If the detection is positive, output the grammar points used in the tokens that are also in the above list, "
    system_prompt += "in the EXACT SAME WORDING/FORMAT as the grammar point appears in the list above. "
    system_prompt += "If the detection is negative, output the word 'NONE'."
    system_prompt += "If there are multiple grammar points that matches with something in the list detected, "
    system_prompt += "output them separated by ||, like this: grammar_1||grammar_2||grammar_3||...."
    system_prompt += "Remember, each grammar point you output needs to EXACTLY match an item in the list provided, not a character more or less."
    system_prompt += "Do not output anything that does not match EXACTLY with an item in the list."
    system_prompt += "Before you return the output, check again that every grammar point you are outputting is actually used in the sentence given by the user."
    return system_prompt

def detect_grammar_plain_sys_prompt(language):
    system_prompt = f"You are a helpful {language} grammar detection assistant."
    system_prompt += "Given a sentence from the user, your job is to detect whether the sentence uses a grammar point, "
    system_prompt += "and if yes, what grammar point(s) it uses."
    system_prompt += "If the detection is negative, output the word 'NONE'."
    system_prompt += "If there are multiple grammar points, "
    system_prompt += "output them separated by ||, like this: grammar_1||grammar_2||grammar_3||...."
    system_prompt += f"Output the grammar points in {language}."
    return system_prompt


def detect_grammar_verify_sys_prompt(language):
    system_prompt = f"You are a helpful {language} grammar detection verification assistant."
    system_prompt += "Given a sentence and a list of grammar points from the user, your job is to determine whether the given sentences really uses each grammar point in the list or not."
    system_prompt += "Take any grammar points that are not used in the sentence out of the list, and output the resulting list as a string."
    system_prompt += "If all grammar points in the list are used in the given sentence, output the original list as a string."
    return system_prompt

class GrammarDetector:
    def __init__(self, language, grammar_points):
        self.language = language
        self.grammar_points = grammar_points

    def filter_by_similarity(self, tokens):
        pass

    def detect_grammar(self, tokens):
        pass


class GrammarDetectorLevel:
    def __init__(self, language, grammar_points):
        self.language = language
        self.grammar_points = grammar_points
        self.system_prompt = detect_grammar_level_sys_prompt(self.grammar_points, language)
        my_key = os.getenv("OPENAI_API_KEY")
        self.engine = OpenAIEngine(my_key, model="gpt-4")
        few_shot = [ChatMessage.user("その花はとても美しいです。"),
                    ChatMessage.assistant("だ / です||とても||は||い-adjectives")]
        self.ai = Kani(self.engine, system_prompt=self.system_prompt, chat_history=few_shot)
        self.model = OpenAI()
        self.verification_prompt = detect_grammar_verify_sys_prompt(language)
    
    async def detect_grammar(self, sentence):
        shots = retrieve_shots(self.language, "grammardetector")
        async for msg in self.ai.full_round(sentence):
            model_output = msg.text
            gp_detected = model_output.split("||")
            print("gp_detected:", gp_detected)
            to_check = gp_detected[:]
            for item in to_check:
                if item not in self.grammar_points:
                    gp_detected.remove(item)
            to_return = gp_detected
            if gp_detected:
                user_msg = "Sentence: " + sentence + "\n list: " + str(gp_detected)
                messages = [{"role": "system", "content":  self.verification_prompt}]
                messages += shots
                messages += [{"role": "user", "content": user_msg}]
                completion = self.model.chat.completions.create(
                    model="gpt-4",
                    messages=messages
                )
                model_output = completion.choices[0].message.content
                to_return = list_str_to_list(model_output)
            return to_return


class GrammarDetectorPlain:
    def __init__(self, language):
        self.language = language
        self.system_prompt = detect_grammar_plain_sys_prompt(language)
        self.model = OpenAI()
    
    def detect_grammar(self, sentence):
        completion = self.model.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": sentence}
            ]
        )
        model_output = completion.choices[0].message.content
        gp_detected = model_output.split("||")
        return gp_detected

