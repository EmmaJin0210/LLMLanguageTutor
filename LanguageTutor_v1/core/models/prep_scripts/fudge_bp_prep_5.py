import random
from LanguageTutor_v1.core.modules.TokenTokenizer import TokenTokenizer
from LanguageTutor_v1.core.core_utils.misc_utils import write_dict_to_json
from LanguageTutor_v1.core.models.model_constants import MODEL_ID_LM, LIST_FILENAMES_SENTENCES_JPN, \
    LIST_FILENAMES_PREFIX_JPN, LIST_LEVELS_LABEL_JPN, ROOT_SENTENCES_JPN, \
    FILENAME_TRAIN_DATA, FILENAME_EVAL_DATA, FILENAME_TEST_DATA
from LanguageTutor_v1.core.core_constants import JPN


tt = TokenTokenizer(language=JPN, tokenizer_id=MODEL_ID_LM)


def count_sentences(filename: str) -> int:
    filepath = f"{ROOT_SENTENCES_JPN}{filename}"
    with open(filepath, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())

min_count = min(count_sentences(filename) for filename in LIST_FILENAMES_SENTENCES_JPN)
print("Minimum sentence count across levels:", min_count)


def split_sentences_train_eval_test(filename: str, train_ratio: float = 0.8, eval_ratio: float = 0.1) -> None:

    infilepath = f"{ROOT_SENTENCES_JPN}{filename}"
    with open(infilepath, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]
    sampled_sentences = random.sample(sentences, k=min_count)
    train_end = int(min_count * train_ratio)
    eval_end = train_end + int(min_count * eval_ratio)
    train_sentences = sampled_sentences[:train_end]
    eval_sentences = sampled_sentences[train_end:eval_end]
    test_sentences = sampled_sentences[eval_end:]
    
    train_filepath = f"{ROOT_SENTENCES_JPN}train_{filename}"
    eval_filepath = f"{ROOT_SENTENCES_JPN}eval_{filename}"
    test_filepath = f"{ROOT_SENTENCES_JPN}test_{filename}"
    
    with open(train_filepath, "w", encoding="utf-8") as f:
        for sentence in train_sentences:
            f.write(sentence + "\n")
    with open(eval_filepath, "w", encoding="utf-8") as f:
        for sentence in eval_sentences:
            f.write(sentence + "\n")
    with open(test_filepath, "w", encoding="utf-8") as f:
        for sentence in test_sentences:
            f.write(sentence + "\n")

for filename in LIST_FILENAMES_SENTENCES_JPN:
    split_sentences_train_eval_test(filename, train_ratio=0.8, eval_ratio=0.1)


def generate_and_store_prefixes(filename: str, n_filename: str) -> None:
    infilepath = f"{ROOT_SENTENCES_JPN}{filename}"
    outfile_path = f"{ROOT_SENTENCES_JPN}{n_filename}"
    with open(infilepath, "r", encoding="utf-8") as infile, \
         open(outfile_path, "w", encoding="utf-8") as outfile:
        for line in infile:
            sentence = line.strip()
            token_ids = tt.tokenizer.encode(sentence, add_special_tokens=False)
            for i in range(1, len(token_ids) + 1):
                prefix_ids = token_ids[:i]
                # Now decode back to text
                prefix_str = tt.tokenizer.decode(prefix_ids, skip_special_tokens=False)
                outfile.write(prefix_str + "\n")


for filename in LIST_FILENAMES_SENTENCES_JPN:
    train_filename = f"train_{filename}"
    generate_and_store_prefixes(filename=train_filename, n_filename=f"sampled_prefix_{filename}")

for filename in LIST_FILENAMES_SENTENCES_JPN:
    eval_filename = f"eval_{filename}"
    generate_and_store_prefixes(filename=eval_filename, n_filename=f"sampled_evalprefix_{filename}")
    
for filename in LIST_FILENAMES_SENTENCES_JPN:
    test_filename = f"test_{filename}"
    generate_and_store_prefixes(filename=test_filename, n_filename=f"sampled_testprefix_{filename}")


def load_all_prefix_data(prefix_type="sampled_prefix_"):
    prefix_label_pairs = []
    for level in LIST_LEVELS_LABEL_JPN:
        filepath = f"{ROOT_SENTENCES_JPN}{prefix_type}{level}.txt"
        with open(filepath, "r", encoding="utf-8") as f:
            prefixes = [line.strip() for line in f if line.strip()]
            prefix_label_pairs.extend([{"prefix": p, "label": level} for p in prefixes])
    return prefix_label_pairs


def split_balanced_train_eval_test(prefix_label_pairs, train_ratio=0.8, eval_ratio=0.1):
    label_to_prefixes = {}
    for item in prefix_label_pairs:
        label_to_prefixes.setdefault(item["label"], []).append(item["prefix"])
    
    train_data, eval_data, test_data = [], [], []
    for label, prefixes in label_to_prefixes.items():
        random.shuffle(prefixes)
        n = len(prefixes)
        train_end = int(n * train_ratio)
        eval_end = train_end + int(n * eval_ratio)
        train_data.extend([{"prefix": p, "label": label} for p in prefixes[:train_end]])
        eval_data.extend([{"prefix": p, "label": label} for p in prefixes[train_end:eval_end]])
        test_data.extend([{"prefix": p, "label": label} for p in prefixes[eval_end:]])
    return train_data, eval_data, test_data


prefix_label_pairs_train = load_all_prefix_data(prefix_type="sampled_prefix_")
train_data, eval_data, test_data = split_balanced_train_eval_test(prefix_label_pairs_train, train_ratio=0.8, eval_ratio=0.1)

train_filepath = f"{ROOT_SENTENCES_JPN}{FILENAME_TRAIN_DATA}"
eval_filepath = f"{ROOT_SENTENCES_JPN}{FILENAME_EVAL_DATA}"
test_filepath = f"{ROOT_SENTENCES_JPN}{FILENAME_TEST_DATA}"

write_dict_to_json(train_data, train_filepath)
write_dict_to_json(eval_data, eval_filepath)
write_dict_to_json(test_data, test_filepath)
