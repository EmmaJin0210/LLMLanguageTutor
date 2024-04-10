import os
import asyncio
from kani import ChatMessage
from kani.engines.openai import OpenAIEngine
from kanis.ConversationKani import ConversationKani
from GrammarDetector import GrammarDetectorLevel, GrammarDetectorPlain
from VocabDetector import VocabDetectorLevel, VocabDetectorPlain
from SentenceSimplifier import SentenceSimplifier
from utils import *

language = "Japanese"
target_level = "n5"
mode = "formal"

grammar_dict_target = load_grammar_file_to_dict(language, [target_level])
grammar_points_target = get_grammar_keys(grammar_dict_target)
gd_target = GrammarDetectorLevel(language, grammar_points_target)

grammar_dict_above = load_grammar_file_to_dict(language, ["n1", "n2", "n3", "n4"])
grammar_points_above = get_grammar_keys(grammar_dict_above)
gd_above = GrammarDetectorLevel(language, grammar_points_above)

gd_plain = GrammarDetectorPlain(language)

ss = SentenceSimplifier()

vocab_dict_target =  load_vocab_file_to_dict(language, [target_level])
vocab_points_target = get_vocab_keys_w_category(vocab_dict_target)
vocab_keys_target = get_vocab_keys(vocab_points_target)
vd_target = VocabDetectorLevel(language, vocab_points_target, vocab_keys_target)

vd_plain = VocabDetectorPlain(language)

async def language_chat(tutor):
    while (True):
        user_input = input("You: ")
        gp = gd_plain.detect_grammar(user_input)
        print("Grammar points: ", gp)
        vp = vd_plain.detect_vocab(user_input)
        print("Vocab points: ", vp)
        if user_input.lower() in ["quit", "q"]:
            await clean_up(tutor.engine)
            break
        async for msg in tutor.full_round(user_input):
            #TODO: if sentence exceeds certain threshold, call simplifier
            print("orgininal text: ", msg.text)
            gp_target = gd_target.detect_grammar(msg.text)
            print("target grammar: ", gp_target)
            gp_above = gd_above.detect_grammar(msg.text)
            print("above grammar: ", gp_above)
            vocab_target = vd_target.detect_vocab(msg.text)
            print("target vocab: ", vocab_target)
            if len(msg.text) > 40:
                print("Simplifying...")
                text = ss.simplify_sentence_formal(msg.text)
            else:
                text = msg.text
            print("Tutor: ", text)


async def clean_up(engine):
    await engine.client.close()
    await engine.close()


def construct_sys_prompt(language, language_b, name, level, grammar, vocab):
    sys_prompt = f"""Your user is trying to learn {language} wants to improve their {language} conversation skills.
To this end, imagine that you are a friendly native {language} speaker, who is the language partner for the user.
Your job is to help the user improve their {language} conversation skills through simple, casual, and friendly conversations.
The user's name is {name}, and their {language} level is {level}.

Remember, your goal is to keep the flow of the conversation, so you need to make sure the user understands what you are saying.
Be mindful that you are speaking in {language}.
Be mindful that the text you generate will be converted to audio to simulate a real conversation, so try to make it sound more natural.

Start by greeting the user and asking how their day is going.

You should ALWAYS follow the rules below:
1. Remember, the user is a language learner, not a native speaker. Your are here to help the user practice.
Therefore, you should adjust to and match the user's level of understanding and speaking.
2. At any time, if you want to use any words that seem a bit hard, you should substitute it with a word in {language_b}.
3. During the conversation, don't pick on small mistakes the user makes, but rather summarize them so you can tell the user at the end of the entire conversation.
If the user makes a really big grammar mistake, remind the user in a friendly way by saying the corrected version of the sentence.
4. If the user asks you what a word or phrase means, give the {language_b} translation of that word or phrase.
8. Although you are friendly, do not offer help to the user in subjects other than practicing their {language} conversation skills.
"""
    print(sys_prompt)
    return sys_prompt

def main():
    name = "エマ"
    language, levels = "Japanese", ["n5"]
    backup_lanaguage = "Chinese"
    grammar_dict = load_grammar_file_to_dict(language, levels)
    grammar_prompt = unpack_grammar_dict_for_prompting(grammar_dict)
    vocab_dict = load_vocab_file_to_dict(language, levels)
    vocab_prompt = unpack_vocab_dict_for_prompting(vocab_dict)
    system_prompt = construct_sys_prompt(language, backup_lanaguage, name, "elementary", grammar_prompt, vocab_prompt)
    # chat_history = [ChatMessage.system(system_prompt)]
    my_key = os.getenv("OPENAI_API_KEY")
    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = ConversationKani(engine, system_prompt=system_prompt, desired_response_tokens=60)
    asyncio.run(language_chat(tutor))


if __name__ == "__main__":
    main()