import os
import argparse
from datetime import datetime
from LanguageTutor_v1.core.modules.TokenDetectorMatcher import TokenDetectorMatcher
from LanguageTutor_v1.core.modules.DifficultyCalculator import DifficultyCalculator
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels, \
    get_levels_above_exclusive, get_levels_below_inclusive
from LanguageTutor_v1.core.core_utils.language_utils import load_vocab_file_to_dict
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json
from eval.eval_constants import CONVERSATION_LOGS_FOLDER, EvalType


target_language = "japanese"
all_levels = get_all_levels(target_language)

vocab_dict = load_vocab_file_to_dict(
    language = target_language,
    levels = all_levels,
    vocab_dir = os.path.join("vocab_lists", "jpwac")
)

tdm = TokenDetectorMatcher(word_dict = vocab_dict,
                           grammar_dict = {},
                           language = target_language)
dc = DifficultyCalculator()


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Tutor Difficulty Options")

    parser.add_argument(
        "-T", 
        choices = [EvalType.BASELINE, EvalType.PROMPTING, EvalType.OVERGEN, EvalType.FUDGE], 
        required = True,
        help = "Evaluation Type: baseline or prompting or overgen or fudge"
    )

    return parser.parse_args()


def get_folder_path(eval_type):
    return os.path.join(CONVERSATION_LOGS_FOLDER, eval_type)


def evaluate_tutor_msgs_for_all_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.startswith("e_"):
            file_path = os.path.join(folder_path, filename)
            evaluate_tutor_msgs_for_file(folder_path, filename)
            print(f"Completed difficulty evaluation for {file_path}")


def evaluate_tutor_msgs_for_file(folder_path, filename):
    num_valid_rounds = 0
    total_score = 0.0
    raw_above_cnts, raw_total_cnts = 0, 0
    file_path = os.path.join(folder_path, filename)
    start_time = datetime.now()
    logs = read_json_to_dict(file_path)
    conversations = logs.get("conversations", [])
    for ind, conversation in enumerate(conversations):
        updated_conversation, valid_rnds, sum_score_conv, above_cnts, total_cnts = \
            calc_difficulty_for_conversation(conversation)
        num_valid_rounds += valid_rnds
        total_score += sum_score_conv
        raw_above_cnts += above_cnts
        raw_total_cnts += total_cnts
        logs["conversations"][ind] = updated_conversation
    ave_diff_score_by_utterance = total_score / num_valid_rounds
    logs["ave_diff_score_by_utterance"] = ave_diff_score_by_utterance
    logs["ave_diff_score_overall"] = raw_above_cnts / raw_total_cnts
    end_time = datetime.now()
    runtime = end_time - start_time
    logs["runtime_difficulty_eval"] = str(runtime)
    new_file_path = os.path.join(folder_path, f"e_{filename}")
    write_dict_to_json(logs, new_file_path)


def calc_difficulty_for_conversation(conversation):
    at_target_cnt = 0
    valid_rounds = 0
    sum_score = 0.0
    raw_above_cnts, raw_total_cnts = 0, 0
    target_level = conversation.get("tutor_level", "")
    levels_above = get_levels_above_exclusive(target_language, target_level)
    for ind, rnd in enumerate(conversation.get("script", [])):
        tutor_utterance = rnd.get("tutor", "").strip()
        utt_at_target, utt_difficulty, detected, undetected = \
            calc_difficulty_for_text(tutor_utterance, target_level)
        detected_cnts_to_log = {level : len(toks) for level, toks in detected.items()}
        detected_cnts_total = sum(detected_cnts_to_log.values())
        above_cnts_total = sum(len(toks) for level, toks in detected.items() if level in levels_above)
        undetected_cnts = len(undetected)
        conversation["script"][ind]["difficulty_score"] = utt_difficulty
        conversation["script"][ind]["at_target_level"] = utt_at_target
        conversation["script"][ind]["detected_counts"] = detected_cnts_to_log
        conversation["script"][ind]["detected_counts_total"] = detected_cnts_total
        conversation["script"][ind]["undetected_counts"] = undetected_cnts
        # conversation["script"][ind]["detected"] = {
        #                                                 lvl: sorted(list(toks))
        #                                                 for lvl, toks in detected.items()
        #                                             }
        # conversation["script"][ind]["undetected"] = list(undetected)
        at_target_cnt = (at_target_cnt + 1) if utt_at_target else at_target_cnt
        # if utt_difficulty is none or not enough is detected,
        # this round shouldn't be included for utterance-level
        if utt_difficulty and \
            detected_cnts_total / (detected_cnts_total + undetected_cnts) > 0.25:
            valid_rounds += 1
            sum_score += utt_difficulty
            raw_above_cnts += above_cnts_total
            raw_total_cnts += detected_cnts_total + undetected_cnts

    # only detected_cnts_total should be included for the token-level averaging
    tutor_utterances_joined = " ".join([rnd.get("tutor", "").strip() 
                                        for rnd in conversation.get("script", [])])
    conv_at_target, conv_difficulty, detected, undetected = \
        calc_difficulty_for_text(tutor_utterances_joined, target_level)
    conversation["difficulty_score"] = conv_difficulty
    conversation["at_target_level"] = conv_at_target
    conversation["num_rounds_at_target_level"] = at_target_cnt
    # return the updated conversation dict
    return conversation, valid_rounds, sum_score, raw_above_cnts, raw_total_cnts


def calc_difficulty_for_text(text, target_level):
    tokens = tdm.tokenize(text, tokenizer='Sudachi', sudachi_mode='C', strip = True)
    detected, undetected = tdm.detect_tokens_at_levels(tokens, all_levels, scope = ['v'])
    print("Detected tokens by level:")
    for level in all_levels:
        print(f"  {level}: {sorted(detected.get(level, []))}")
    print("Undetected tokens:", sorted(undetected))
    
    above_levels = get_levels_above_exclusive(target_language, target_level)
    below_levels = get_levels_below_inclusive(target_language, target_level)
    above = {level: tokens for level, tokens in detected.items() if level in above_levels}
    below = {level: tokens for level, tokens in detected.items() if level in below_levels}
    is_at_target = dc.at_target_level(above, below)
    difficulty_score = dc.calc_difficulty_score(above, below)
    print(f"At target level ({target_level})? {is_at_target}")
    return is_at_target, difficulty_score, detected, undetected


def main():
    args = parse_args()
    eval_type = args.T

    folder_path = get_folder_path(eval_type)
    evaluate_tutor_msgs_for_all_files(folder_path)


if __name__ == "__main__":
    main()
