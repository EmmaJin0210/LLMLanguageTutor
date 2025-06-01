# 1. tokenize each tutor utterance, keep two variables:
# 1) all tutor utterances joined together, string, for each file -> MDD
# 2) all tokens of tutor utterances joined together, list, for each file -> N-gram diversity
# -> maybe JReadability?

# write the 2 vars to each e_ script

import os
import argparse
from LanguageTutor_v1.core.modules.TokenDetectorMatcher import TokenDetectorMatcher
from LanguageTutor_v1.core.modules.DifficultyCalculator import DifficultyCalculator
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
from LanguageTutor_v1.core.core_utils.language_utils import load_vocab_file_to_dict
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json
from eval.eval_constants import CONVERSATION_LOGS_FOLDER, EvalType

# filename -> e_filename
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


def join_utterances_for_all_files(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isdir(file_path):
            continue
        if filename.startswith("e_"):
            join_utterances_for_file(file_path)


def join_utterances_for_file(file_path):
    logs = read_json_to_dict(file_path)
    conversations = logs.get("conversations", [])
    
    joined_utterances = ""
    joined_tokens = []

    for ind, conversation in enumerate(conversations):
        # tutor_text = joined tutor utterances for one whole conversation
        tutor_text = "".join([rnd.get("tutor", "") for rnd in conversation.get("script", [])])
        joined_utterances += tutor_text
        tokens = tdm.tokenize(sentence = tutor_text, strip=True, jpn_only=True)
        joined_tokens += tokens

    logs["joined_utterances"] = joined_utterances
    logs["joined_tokens"] = joined_tokens
    write_dict_to_json(logs, file_path)
    print(f"Completed join utterances for {file_path}")



def main():
    args = parse_args()
    eval_type = args.T

    folder_path = get_folder_path(eval_type)
    join_utterances_for_all_files(folder_path)


if __name__ == "__main__":
    main()
