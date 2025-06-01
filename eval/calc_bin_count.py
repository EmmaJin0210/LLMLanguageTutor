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

source_folder = "jlpt_anki_with_reading"


target_language = "japanese"
all_levels = get_all_levels(target_language)

vocab_dict = load_vocab_file_to_dict(
    language = target_language,
    levels = all_levels,
    vocab_dir = os.path.join("vocab_lists", source_folder)
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


def calc_bin_rate_for_all_files(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isdir(file_path):
            continue
        if filename.startswith("e_"):
            calc_bin_rate_for_file(folder_path, filename)


def calc_bin_rate_for_file(folder_path, filename):
    raw_detected_cnts, raw_undetected_cnts = 0, 0
    file_path = os.path.join(folder_path, filename)
    logs = read_json_to_dict(file_path)
    conversations = logs.get("conversations", [])
    for ind, conversation in enumerate(conversations):
        updated_conversation, detected_cnts, undetected_cnts = \
            calc_difficulty_for_conversation(conversation)
        raw_detected_cnts += detected_cnts
        raw_undetected_cnts += undetected_cnts
        logs["conversations"][ind] = updated_conversation
    logs[f"total_detected_counts"] = raw_detected_cnts
    logs[f"total_counts"] = raw_detected_cnts + raw_undetected_cnts
    new_file_path = file_path if filename.startswith("e_") else os.path.join(folder_path, f"e_{filename}")
    write_dict_to_json(logs, new_file_path)


def calc_difficulty_for_conversation(conversation):
    target_level = conversation.get("tutor_level", "")
    for ind, rnd in enumerate(conversation.get("script", [])):
        tutor_utterance = rnd.get("tutor", "").strip()
        detected, undetected = \
            calc_difficulty_for_text(tutor_utterance, target_level)
        detected_cnts_to_log = {level : len(toks) for level, toks in detected.items()}
        detected_cnts_total = sum(detected_cnts_to_log.values())
        undetected_cnts = len(undetected)
    return conversation, detected_cnts_total, undetected_cnts


def calc_difficulty_for_text(text, target_level):
    tokens = tdm.tokenize(text, tokenizer='Sudachi', sudachi_mode='C', strip = True)
    detected, undetected = tdm.detect_tokens_at_levels(tokens, all_levels, scope = ['v'])
    return detected, undetected


def main():
    args = parse_args()
    eval_type = args.T

    folder_path = get_folder_path(eval_type)
    calc_bin_rate_for_all_files(folder_path)


if __name__ == "__main__":
    main()
