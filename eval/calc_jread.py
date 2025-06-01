# TODO: do the correlation for conversation-level instead of utterance
import os
import argparse
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json
from eval.eval_constants import CONVERSATION_LOGS_FOLDER, EvalType
from jreadability import compute_readability
from scipy.stats import spearmanr
import numpy as np 


target_language = "japanese"
all_levels = get_all_levels(target_language)

JLPT_TO_INT = {"n1": 1, "n2": 2, "n3": 3, "n4": 4, "n5": 5}

def make_level_map():
    return [
        (float('-inf'), 3.0, "n1"),
        (3.0, 4.0, "n2"),
        (4.0, 5.0, "n3"),
        (5.0, 5.5, "n4"),
        (5.5, float('inf'), "n5"),
    ]

JREAD_TO_JLPT = make_level_map()

def get_jlpt_level(score, level_map):
    for low, high, level in level_map:
        if low <= score < high:
            return level
    return "Unknown"

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


def calc_jread_for_all_files(folder_path):
    filenames = os.listdir(folder_path)
    for filename in filenames:
        file_path = os.path.join(folder_path, filename)
        if os.path.isdir(file_path):
            continue
        if filename.startswith("e_"):
            calc_jread_for_file(folder_path, filename)
            print(f"Completed jread evaluation for {file_path}")


def calc_jread_for_file(folder_path, filename):
    at_target_counts = 0
    jread_scores = []          # --- NEW  (collect per-conversation scores)
    target_levels = []         # --- NEW
    file_path = os.path.join(folder_path, filename)
    logs = read_json_to_dict(file_path)
    conversations = logs.get("conversations", [])
    for ind, conversation in enumerate(conversations):
        updated_conversation = \
            calc_jread_for_conversation(conversation)
        at_target_counts += updated_conversation["jread_at_target_cnt"]
        logs["conversations"][ind] = updated_conversation
        # --- CHANGED: accumulate for correlation
        score_conv = updated_conversation.get("jread")
        jlpt_label = updated_conversation.get("tutor_level", "").lower()
        lvl_int = JLPT_TO_INT.get(jlpt_label)
        if score_conv is not None and lvl_int is not None:
            jread_scores.append(score_conv)
            target_levels.append(lvl_int)
    logs["jread_at_target_percentage"] = at_target_counts / (len(conversations) * 10)
    # --- NEW: compute Spearman ρ for this file ----------------------------
    if len(jread_scores) > 1 and len(set(target_levels)) > 1:
        rho, p = spearmanr(jread_scores, target_levels)
        logs["spearman_rho"] = float(rho)
        logs["spearman_p"] = float(p)
        print(f"Spearman ρ for {filename}: {rho:.4f}  (p={p:.4g})")
    else:
        print(f"Not enough variability to compute Spearman ρ for {filename}")
    new_file_path = file_path if filename.startswith("e_") else os.path.join(folder_path, f"e_{filename}")
    write_dict_to_json(logs, new_file_path)


def calc_jread_for_conversation(conversation):
    at_target_cnt = 0
    target_level = conversation.get("tutor_level", "")
    for ind, rnd in enumerate(conversation.get("script", [])):
        tutor_utterance = rnd.get("tutor", "").strip()
        jread_score, at_target_level = \
            calc_jread_for_text(tutor_utterance, target_level)
        conversation["script"][ind]["jread"] = jread_score
        conversation["script"][ind]["jread_at_target"] = at_target_level
        at_target_cnt = (at_target_cnt + 1) if at_target_level else at_target_cnt

    tutor_utterances_joined = " ".join([rnd.get("tutor", "").strip() 
                                        for rnd in conversation.get("script", [])])
    jread_score_conv, at_target_level_conv = \
        calc_jread_for_text(tutor_utterances_joined, target_level)
    conversation["jread"] = jread_score_conv
    conversation["jread_at_target_level"] = at_target_level_conv
    conversation["jread_at_target_cnt"] = at_target_cnt

    return conversation


def calc_jread_for_text(text, target_level):
    score = compute_readability(text)
    level = get_jlpt_level(score, JREAD_TO_JLPT)
    return score, (level == target_level)


def main():
    args = parse_args()
    eval_type = args.T

    folder_path = get_folder_path(eval_type)
    calc_jread_for_all_files(folder_path)


if __name__ == "__main__":
    main()
