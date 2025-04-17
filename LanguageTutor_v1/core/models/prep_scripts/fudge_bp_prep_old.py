
import json
import random
from LanguageTutor_v1.core.modules.TokenTokenizer import TokenTokenizer
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, \
    write_dict_to_json
from LanguageTutor_v1.core.models.model_constants import MODEL_ID_LM, \
    LIST_FILENAMES_SENTENCES_JPN, LIST_FILENAMES_PREFIX_JPN, LIST_LEVELS_LABEL_JPN, \
    ROOT_SENTENCES_JPN, FILENAME_TRAIN_DATA, FILENAME_TEST_DATA
from  LanguageTutor_v1.core.core_constants import JPN


# TODO: 1. train-test split should be on sentences not prefixes
# TODO: 2. add <|im_end|> to the end of each sentence as a token. (first verify that it is indeed one entire token in qwen)

# function to: 
# 1. read each sentence from a file, map all prefixes to corresponding level
# 2. write (prefix -> level) data to new .txt file for each level
def generate_and_store_prefixes(filename: str, n_filename: str) -> None:
    infile_path = f"{ROOT_SENTENCES_JPN}{filename}"
    outfile_path = f"{ROOT_SENTENCES_JPN}{n_filename}"
    with open(infile_path, "r", encoding = "utf-8") as infile, \
        open(outfile_path, "w", encoding = "utf-8") as outfile:
        for line in infile:
            sentence = line.strip()
            tokens = tt.sentence_to_tokens(sentence)
            for i in range(1, len(tokens) + 1):
                outfile.write("".join(tokens[:i]) + "\n")
    infile.close()
    outfile.close()


def get_smallest_samples_count() -> int:
    smallest_count, smallest_filename = float('inf'), None
    for filename in LIST_FILENAMES_PREFIX_JPN:
        filepath = f"{ROOT_SENTENCES_JPN}{filename}"
        with open(filepath, "r", encoding = "utf-8") as infile:
            count = sum([1 for line in infile if line.strip()])
            if count < smallest_count:
                smallest_count = count
                smallest_filename = filename
    print(f"File with least number of samples is {smallest_filename}:{smallest_count} samples")
    return smallest_count

# take least number of prefixes, randomly sample from other levels
# write sample data to new file for each level
def sample_file(filename: str, smallest_count: int) -> None:
    infile_path = f"{ROOT_SENTENCES_JPN}{filename}"
    with open(infile_path, "r", encoding = "utf-8") as infile:
        lines = infile.readlines()
    infile.close()

    sampled_lines = random.sample(lines, k = smallest_count)

    n_filename = f"sampled_{filename}"
    outfile_path = f"{ROOT_SENTENCES_JPN}{n_filename}"
    with open(outfile_path, "w", encoding = "utf-8") as outfile:
        for line in sampled_lines:
            outfile.write(line)
    outfile.close()

# divide data into train and test set (probably 80/20?)
# make sure train and test set are both balanced in the number of sentences from each level

def load_all_prefix_data():
    prefix_label_pairs = []
    
    for level in LIST_LEVELS_LABEL_JPN:
        filepath = f"{ROOT_SENTENCES_JPN}sampled_prefix_{level}.txt"
        with open(filepath, "r", encoding = "utf-8") as f:
            prefixes = [line.strip() for line in f if line.strip()]
            prefix_label_pairs.extend([{"prefix": p, "label": level} 
                                       for p in prefixes])

    return prefix_label_pairs

def split_balanced_train_test(prefix_label_pairs, train_ratio=0.8):
    # Group prefixes by label
    label_to_prefixes = {}
    for item in prefix_label_pairs:
        label_to_prefixes.setdefault(item["label"], []).append(item["prefix"])

    train_data, test_data = [], []
    
    for label, prefixes in label_to_prefixes.items():
        random.shuffle(prefixes)
        split_idx = int(len(prefixes) * train_ratio)
        
        train_data.extend([{"prefix": p, "label": label} 
                           for p in prefixes[:split_idx]])
        test_data.extend([{"prefix": p, "label": label} 
                          for p in prefixes[split_idx:]])

    return train_data, test_data



tt = TokenTokenizer(language = JPN, tokenizer_id = MODEL_ID_LM)
for filename in LIST_FILENAMES_SENTENCES_JPN:
    generate_and_store_prefixes(filename = filename, 
                                n_filename = f"prefix_{filename}")


smallest_count = get_smallest_samples_count()  # 257013


for filename in LIST_FILENAMES_PREFIX_JPN:
    sample_file(filename, smallest_count)


prefix_label_pairs = load_all_prefix_data()
train_data, test_data = split_balanced_train_test(prefix_label_pairs)
train_filepath = f"{ROOT_SENTENCES_JPN}{FILENAME_TRAIN_DATA}"
test_filepath = f"{ROOT_SENTENCES_JPN}{FILENAME_TEST_DATA}"

write_dict_to_json(train_data, train_filepath)
write_dict_to_json(test_data, test_filepath)

