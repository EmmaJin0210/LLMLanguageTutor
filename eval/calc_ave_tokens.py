import os
import argparse
from eval.eval_constants import CONVERSATION_LOGS_FOLDER, EvalType
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json


def parse_args():
    parser = argparse.ArgumentParser(description="Perplexity Calculation Options")

    parser.add_argument(
        "-T", 
        choices = [EvalType.BASELINE, EvalType.PROMPTING, EvalType.OVERGEN, EvalType.FUDGE], 
        required = True,
        help = "Evaluation Type: baseline or prompting or overgen or fudge"
    )

    return parser.parse_args()


def get_folder_path(eval_type):
    return os.path.join(CONVERSATION_LOGS_FOLDER, eval_type)


def calc_ave_tokens_for_all_files(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isdir(file_path):
            continue
        if filename.startswith("e_"):
            calc_ave_tokens_for_file(file_path)


def calc_ave_tokens_for_file(file_path):
    logs = read_json_to_dict(file_path)
    conversations = logs.get("conversations", [])
    total_tokens = 0
    for ind, conversation in enumerate(conversations):
        scripts = conversation.get("script", [])
        for rnd in scripts:
            tokens_cnt = rnd.get("jlpt_anki_with_reading_detected_counts_total", 0) + \
                        rnd.get("jlpt_anki_with_reading_undetected_counts", 0)
            total_tokens += tokens_cnt

    logs["ave_tokens_per_utterance"] = total_tokens / (len(conversations) * 10)
    write_dict_to_json(logs, file_path)
    print(f"Completed ave length calculation for {file_path}")


def main():
    args = parse_args()
    eval_type = args.T

    folder_path = get_folder_path(eval_type)
    calc_ave_tokens_for_all_files(folder_path)


if __name__ == "__main__":
    main()
