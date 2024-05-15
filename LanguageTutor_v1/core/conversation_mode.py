import os
import warnings
import asyncio
from kani import ChatMessage, ChatRole
from kani.engines.openai import OpenAIEngine
from core.kanis.ConversationKani import ConversationKani
from core.modules.GrammarDetector import GrammarDetectorLevel
from core.modules.VocabDetector import VocabDetector
from core.modules.SentenceSimplifier import SentenceSimplifier
# from modules.DifficultyCalculator import DifficultyCalculator
from core.modules.SentenceTokenizer import SentenceTokenizer
from core.utils.utils import *
from core.utils.profile_utils import *
from core.utils.frontend_utils import *
from core.utils.speech_utils import *

# TODO: How about I try to group phrases that mean similar things into groups:
# meaning : {level1 : [], level2 : []}

async def language_chat(tutor, user_profile, language, target_level, mode, 
                        gd_above, vd_above, ss, tokenizer, gp_target,
                        track_usage = False):
    # TODO: keep all chat history here? Keep all summarized checkpoints here?
    # TODO: maybe need to keep a counter here and do checkpointing every 8 rounds
    rounds = 0
    all_user_input = ""
    all_bot_output = ""
    user_interests = [user_profile["interests"]]
    user_info = [user_profile["personal-info"]]
    while (True):
        if rounds % 16 == 0 and rounds != 0:
            history_to_summarize = format_chat_history_for_summary(
                tutor.chat_history[:len(tutor.chat_history-4)])
            chat_summary = summarize_rounds_history(history_to_summarize, language)
            new_chat_history = [ChatMessage(role=ChatRole.ASSISTANT, content=chat_summary)] +\
                                tutor.chat_history[len(tutor.chat_history-4):]
            tutor.chat_history = new_chat_history
            
        user_input = input("You: ")
        # user_input = await speech_to_text()
        all_user_input += user_input
        if user_input.lower() in ["quit", "q"]:
            if user_interests:
                user_profile["interests"] = summarize_user_interests(user_interests, language)
            
            if user_info:
                user_profile["personal-info"] = summarize_user_personal_info(user_info, language)
            # summarize topics talked about
            history_to_summarize = format_chat_history_for_summary(tutor.chat_history)
            topics_talked_about = summarize_rounds_history(history_to_summarize, language)
            user_profile["past-topics"].append(topics_talked_about)
            # TODO: summarize mistakes the user made (all_user_input?)

            await clean_up(tutor.engine)
            break
        # if track_usage:
        #     gp = gd_plain.detect_grammar(user_input)
        #     print("Grammar points: ", gp)
        #     vp = vd_plain.detect_vocab(user_input)
        #     print("Vocab points: ", vp)
        async for msg in tutor.full_round(user_input):
            if msg.content is None and msg.role == ChatRole.ASSISTANT:
                continue
            if msg.role == ChatRole.FUNCTION:
                if msg.name == "store_user_interest":
                    user_interests.append(msg.content)
                elif msg.name == "store_user_personal_info":
                    user_info.append(msg.content)
                continue
            print("orgininal text: ", msg.text)
            tokens = tokenizer.tokenize_sentence(msg.text)
            gp_above = await gd_above.detect_grammar(msg.text)
            for gp in gp_above:
                if gp in gp_target or gp not in gd_above.grammar_points:
                    gp_above.remove(gp)
            print("above grammar: ", gp_above)
            vp_above = vd_above.detect_vocab(tokens)
            for i, vp in enumerate(vp_above):
                if vp in all_user_input:
                    vp_above.pop(i)
            print("above vocab: ", vp_above)
            print(len(gp_above), len(vp_above))
            if len(gp_above) != 0 or len(vp_above) != 0:
                print("Simplifying...")
                if mode == "formal":
                    text = ss.swap_hard_expressions_formal(gp_above + vp_above, msg.text)
                else:
                    text = ss.swap_hard_expressions_casual(gp_above + vp_above, msg.text)
            else:
                text = msg.text
            # vocab_target = vd_target.detect_vocab(msg.text)
            # print("target vocab: ", vocab_target)
            # dc = DifficultyCalculator(gp_target, gp_above, [])
            # dc.at_target_difficulty(msg.text, target_level)
            # if dc.at_target_difficulty(msg.text, target_level):
            #     text = msg.text
            # else:
            #     print("Simplifying...")
            #     if mode == "formal":
            #         text = ss.swap_hard_expressions_formal(gp_above, msg.text)
            #     else:
            #         text = ss.swap_hard_expressions_casual(gp_above, msg.text)
            tutor.chat_history[-1] = ChatMessage.assistant(text)
            # text_to_speech(text)
            print("Tutor: ", text)
        rounds += 1
    # TODO: summarize what we talked about, write to user profile.
    # should we return just the summary here or the entire user profile?
    return user_profile

async def clean_up(engine):
    await engine.client.close()
    await engine.close()


def construct_sys_prompt_conversation(language, language_b, name, level, interests, user_info, past_topics, good_grammar):
    # TODO: add past topics that you have talked about with the user, and where you left off last time.
    sys_prompt = f"""You are a chatbot for language learning. Your user is learning {language} and wants to improve their {language} conversation skills.
To this end, imagine that you are a friendly native {language} speaker. You are at the same age level as the user, and you are the user's language partner.
Your job is to help the user improve their {language} conversation skills through simple and friendly conversations.
The user's name is {name}, and their {language} level is {level}. Their preferred backup language for explanationing unfamiliar words and phrases is {language_b}.
Here is some more personal info about them: {user_info}.
The user's interests are {interests}.
The past topics you have talked about are: {past_topics}.

Since you are having a chat with the user, you should keep your sentences as concise, short, and simple as possible.
Be mindful that you are speaking in {language};
also be mindful that the text you generate will be converted to audio to simulate a real conversation, so try to make it sound more natural.

Start the conversation following these guidelines:
1. Start by greeting the user and asking how their day is going.
2. Talk a bit about their day with the user. This should be around 5 to 8 rounds.
3. Then, conclude the greetings with something like "let's start our discussion for today?" and wait for the user's reply.
4. After the user indicates they are ready to start the discussion, look at the user's interests provided above and suggest a topic that the user might be interested in.
For example, you can say something like "I remember you mentioned you like <some_user_interest>, let's talk more about <some_user_interest>!"
If the user's interests are unknown, you should ask the user what they want to talk about and go from there.
For example, you can say something like "I don't know what you are interested in yet. What topic do you want to talk about today?"

You should ALWAYS follow the rules below:
1. Remember, the user is a language learner, not a native speaker. Your are here to help the user practice.
Therefore, you should always talk with very beginner-friendly expressions.
Only convey one thing in one round. Only ask one question in one round.
2. You should try to match the user's abilities of understanding and speaking: if the user only uses simple expressions, you should only use simple expressions as well.
3. Even when you are talking about complicated topics, you should still make sure to use simple expressions so that the user understands you.
4. If the user asks you what a word or phrase means, JUST give the {language_b.upper()} translation of that word or phrase. Don't try to explain it in {language}.
5. During the conversation, don't pick on small mistakes the user makes, but rather summarize them so you can tell the user at the end of the entire conversation.
If the user makes a really big grammar mistake, remind the user in a friendly way by saying the corrected version of the sentence.
6. If the user mentions something they are interested in, store that interest as a full sentence.
7. Although you are friendly, do not offer help to the user in subjects other than practicing their {language} conversation skills.

Also, try to use these grammar points as much as possible to help the user better remember them:
{good_grammar}
"""
    return sys_prompt

def summarize_conversation(conversation_history):
    # TODO: another KANI? depends on the format of the conversation history
    pass

def main():
    language, target_level = get_target_language(), get_chatbot_target_level()
    levels_below = get_levels_below_inclusive(language, target_level)
    levels_above = get_levels_above_exclusive(language, target_level)
    backup_lanaguage = get_chatbot_backup_language()
    mode = get_chatbot_conversation_formality()
    ## TODO: actually, should have a separate prompt (or sth in the prompt) that controls the mode
    track_usage =  get_track_user_usage_flag_chat()

    grammar_dict_target = load_grammar_file_to_dict(language, levels_below)
    grammar_points_target = get_grammar_keys(grammar_dict_target)
    # gd_target = GrammarDetectorLevel(language, grammar_points_target)
    grammar_dict_above = load_grammar_file_to_dict(language, levels_above)
    grammar_points_above = get_grammar_keys(grammar_dict_above)
    gd_above = GrammarDetectorLevel(language, grammar_points_above)
    # gd_plain = GrammarDetectorPlain(language)
    tokenizer = SentenceTokenizer(language)

    vocab_dict_target =  load_vocab_file_to_dict(language, levels_below)
    vocab_points_target = get_vocab_keys_w_category(vocab_dict_target)
    vocab_keys_target = get_vocab_keys(vocab_points_target)
    # vd_target = VocabDetectorLevel(language, vocab_points_target, vocab_keys_target)
    vocab_dict_above =  load_vocab_file_to_dict(language, levels_above)
    vocab_points_above = get_vocab_keys_w_category(vocab_dict_above)
    vocab_keys_above = get_vocab_keys(vocab_points_above)
    vd_above = VocabDetector(language, vocab_points_above, vocab_keys_above)
    # vd_above = VocabDetectorLevel(language, vocab_points_above, vocab_keys_above)
    # vd_plain = VocabDetectorPlain(language)

    ss = SentenceSimplifier(language, backup_lanaguage, grammar_points_target, grammar_points_above, vocab_keys_target, vocab_keys_above)

    username = retrieve_username()
    profile_path = retrieve_profile_path_from_username(username)
    user_profile = read_json_to_dict(profile_path)
    name = retrieve_user_name(user_profile)
    user_interests = retrieve_user_interests_from_profile(user_profile)
    user_info = retrieve_user_info_from_profile(user_profile)
    past_topics = retrieve_past_topics_from_profile(user_profile)
    good_grammar = retrieve_recent_grammar_learnt(user_profile)
    system_prompt = construct_sys_prompt_conversation(language, backup_lanaguage, name, "elementary", user_interests, user_info, past_topics, good_grammar)

    my_key = os.getenv("OPENAI_API_KEY")
    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = ConversationKani(user_profile=user_profile, engine=engine, system_prompt=system_prompt, desired_response_tokens=15)
    user_profile = asyncio.run(language_chat(tutor, user_profile, language, target_level, mode, gd_above, vd_above, ss, tokenizer, grammar_points_target, track_usage))

    write_updated_profile_to_file(user_profile, profile_path)



if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    main()