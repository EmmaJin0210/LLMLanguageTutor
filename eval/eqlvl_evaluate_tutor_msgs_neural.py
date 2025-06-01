import os
import torch
import argparse
from datetime import datetime
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json
from LanguageTutor_v1.core.core_utils.language_utils import get_levels_above_exclusive
from eval.eval_constants import CONVERSATION_LOGS_FOLDER, EvalType


# e_filename -> e_filename
num_rounds = 10
JLPT2NUM = {"n5": 1, "n4": 2, "n3": 3, "n2": 4, "n1": 5}

language = "japanese"
DC_NEURAL_ID = "bennexx/cl-tohoku-bert-base-japanese-v3-jlpt-classifier"

model = AutoModelForSequenceClassification.from_pretrained(
    DC_NEURAL_ID,
    trust_remote_code=True
)
tokenizer = AutoTokenizer.from_pretrained(
    DC_NEURAL_ID,
    trust_remote_code=True
)
if tokenizer.pad_token_id is None or tokenizer.pad_token_id == tokenizer.eos_token_id:
    tokenizer.pad_token = tokenizer.eos_token
model.eval()
id2label = model.config.id2label
label2id = {v.lower(): k for k, v in id2label.items()}
print("LOADED MODEL!")


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
        file_path = os.path.join(folder_path, filename)
        if os.path.isdir(file_path):
            continue
        if filename.startswith("e_"):
            evaluate_tutor_msgs_for_file(folder_path, filename)
            print(f"Completed difficulty evaluation for {file_path}")


def evaluate_tutor_msgs_for_file(folder_path, filename):
    file_path = os.path.join(folder_path, filename)
    print(f"evaluating for {file_path}...")
    logs = read_json_to_dict(file_path)

    total_err  = 0.0      # squared-error over the whole file
    total_utts = 0

    for i, conv in enumerate(logs.get("conversations", [])):
        # TODO: should only do this for tutor_level == student_level
        target_level = conv.get("tutor_level", "")
        student_level = conv.get("student_level", "")
        if target_level == student_level:
            conv, conv_err, conv_utts = calc_difficulty_for_conversation(conv)
            logs["conversations"][i] = conv

            total_err  += conv_err
            total_utts += conv_utts
            print(f"Completed for conversation {i + 1}")

    # single metric: mean ControlError across *all* tutor utterances in the file
    logs["eqlvl_mean_control_error_neural"] = total_err / max(total_utts, 1)

    write_dict_to_json(logs, file_path)
    print(f"Computed ControlError for {file_path}")


def calc_difficulty_for_conversation(conversation):
    target = conversation.get("tutor_level", "").lower()
    err_sum = 0.0                           # total squared-error in this conversation
    utt_cnt = 0                             # number of tutor utterances

    for ind, rnd in enumerate(conversation.get("script", [])):
        utt = rnd.get("tutor", "").strip()
        det_lvl, err = calc_difficulty_for_text(utt, target)

        conversation["script"][ind]["detected_level_neural"] = det_lvl
        conversation["script"][ind]["control_error"]         = err     # keep per-utterance value

        err_sum += err
        utt_cnt += 1

    return conversation, err_sum, utt_cnt      #  <── CHANGED


def calc_difficulty_for_text(text, target_level):
    device = next(model.parameters()).device
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probs = torch.softmax(logits, dim=-1)
    predicted_class_id = torch.argmax(probs, dim=-1).item()
    probs_list = probs.squeeze().tolist()
    detected_level = id2label[predicted_class_id].lower()
    # NEW ─────────────────────────────────────────────────────────
    pred_num   = JLPT2NUM[detected_level]
    target_num = JLPT2NUM[target_level]
    control_err = (pred_num - target_num) ** 2         # (s(x) - t)^2
    # ─────────────────────────────────────────────────────────────

    return detected_level, control_err                 # CHANGED


def main():
    args = parse_args()
    eval_type = args.T

    folder_path = get_folder_path(eval_type)
    evaluate_tutor_msgs_for_all_files(folder_path)

if __name__ == "__main__":
    main()
