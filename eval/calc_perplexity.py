import os
import math
import torch
import argparse
from datetime import datetime
from dotenv import load_dotenv
from huggingface_hub import login
from transformers import AutoTokenizer, AutoModelForCausalLM
from eval.eval_constants import CONVERSATION_LOGS_FOLDER, PERPLEXITY_MODEL_ID, EvalType
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json


load_dotenv()

hf_token = os.getenv("HF_TOKEN")
if hf_token is None:
    raise ValueError("Please set your HF_TOKEN environment variable with your Hugging Face token.")
login(token = hf_token)

tokenizer = AutoTokenizer.from_pretrained(PERPLEXITY_MODEL_ID, trust_remote_code = True)
model = AutoModelForCausalLM.from_pretrained(PERPLEXITY_MODEL_ID,
                                             trust_remote_code = True,
                                             device_map = "auto")
model.eval()


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


def calc_perplexity_for_all_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.startswith("e_"):
            file_path = os.path.join(folder_path, filename)
            calc_perpleixity_for_file(file_path)


def calc_perpleixity_for_file(file_path):
    start_time = datetime.now()
    logs = read_json_to_dict(file_path)
    conversations = logs.get("conversations", [])
    
    total_loss = 0.0
    total_tokens = 0

    for ind, conversation in enumerate(conversations):
        tutor_text = "".join([rnd.get("tutor", "") for rnd in conversation.get("script", [])])
        conv_loss, conv_tokens, conv_perplexity = calc_perplexity(tutor_text)
        conversations[ind]["perplexity"] = conv_perplexity
        total_loss += conv_loss
        total_tokens += conv_tokens

    # overall perplexity of file
    if total_tokens > 0:
        avg_loss = total_loss / total_tokens
        overall_perplexity = math.exp(avg_loss)
    else:
        overall_perplexity = float("inf")
    
    end_time = datetime.now()
    runtime = end_time - start_time

    logs["overall_perplexity"] = overall_perplexity
    logs["runtime_perplexity"] = str(runtime)
    write_dict_to_json(logs, file_path)
    print(f"Completed perplexity calculation for {file_path}")


def calc_perplexity(text, max_length = 1024):
    encodings = tokenizer(text, return_tensors = "pt", truncation = True, max_length = max_length)
    input_ids = encodings.input_ids.to(model.device)
    # in case input_ids is too short or empty
    if input_ids.size(1) == 0:
        return 0.0, 0, float("inf")
    with torch.no_grad():
        outputs = model(input_ids, labels=input_ids)
    loss_per_token = outputs.loss.item()
    num_tokens = input_ids.size(1)
    total_loss = loss_per_token * num_tokens
    perplexity = math.exp(loss_per_token)
    return total_loss, num_tokens, perplexity


def main():
    args = parse_args()
    eval_type = args.T

    folder_path = get_folder_path(eval_type)
    calc_perplexity_for_all_files(folder_path)


if __name__ == "__main__":
    main()
