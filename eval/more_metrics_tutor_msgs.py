from dotenv import load_dotenv
load_dotenv()

import os
import argparse
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json
from eval.eval_constants import CONVERSATION_LOGS_FOLDER, EvalType, \
    STANZA_RESOURCES_DIR

import stanza
from stanza import DownloadMethod
# stanza.download('ja')
nlp = stanza.Pipeline(
    lang="ja",
    processors="tokenize,pos,lemma,depparse",   # or just "tokenize,depparse"
    use_gpu=True,                               # set True if you have a CUDA GPU
    dir=STANZA_RESOURCES_DIR,
    download_method=DownloadMethod.REUSE_RESOURCES
)

from jreadability import compute_readability

METRICS = ["mdd", "ngram", "readability"]


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Tutor Difficulty Options")

    parser.add_argument(
        "-T", 
        choices = [EvalType.BASELINE, EvalType.PROMPTING, EvalType.OVERGEN, EvalType.FUDGE], 
        required = True,
        help = "Evaluation Type: baseline or prompting or overgen or fudge"
    )

    parser.add_argument(
        "-M", 
        choices = METRICS, 
        required = True,
        help = "Metric: mdd or ngram or readability"
    )

    return parser.parse_args()


def get_folder_path(eval_type):
    return os.path.join(CONVERSATION_LOGS_FOLDER, eval_type)


def calc_metric_for_all_files(folder_path, metric):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isdir(file_path):
            continue
        if filename.startswith("e_"):
            calc_metric_for_file(file_path, metric)


def calc_metric_for_file(file_path, metric):
    logs = read_json_to_dict(file_path)
    match metric:
        case "mdd":
            mdd = calc_mdd(logs["joined_utterances"])
            logs["mdd"] = mdd
        case "ngram":
            for n in [1, 2, 3]:
                ngram_d = calc_ngram_diversity(logs["joined_tokens"], n)
                logs[f"{n}_gram_diversity"] = ngram_d
        case "readability":
            jread = compute_readability(logs["joined_utterances"])
            logs["jreadability"] = jread

    write_dict_to_json(logs, file_path)
    print(f"Completed calculation of {metric} for {file_path}")


def calc_mdd(text):
    doc = nlp(text)
    distances = []

    for sent in doc.sentences:
        for word in sent.words:
            if word.head == 0:
                continue  # skip the root
            distance = abs(word.id - word.head)
            distances.append(distance)

    if distances:
        return sum(distances) / len(distances)
    else:
        return 0.0
    

from itertools import islice

def calc_ngram_diversity(tokens, n):
    grams = list(zip(*(islice(tokens, i, None) for i in range(n))))
    total = len(grams)
    if total == 0:
        return 0.0
    unique = len(set(grams))
    return unique / total


def main():
    args = parse_args()
    eval_type = args.T
    metric = args.M

    folder_path = get_folder_path(eval_type)
    calc_metric_for_all_files(folder_path, metric)


if __name__ == "__main__":
    main()





# argparse

# MDD



# N-gram diversity


# JReadability?