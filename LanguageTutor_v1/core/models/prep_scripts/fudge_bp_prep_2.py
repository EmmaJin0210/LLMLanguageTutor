from LanguageTutor_v1.core.modules.TokenTokenizer import TokenTokenizer
from LanguageTutor_v1.core.models.model_constants import MODEL_ID_LM_TINY
from LanguageTutor_v1.core.core_constants import JPN

tt = TokenTokenizer(language=JPN, tokenizer_id=MODEL_ID_LM_TINY)
tokens = tt.tokenizer.tokenize("たまたまこの冷凍生地を開発したのがこのタカギベーカリーさんだそうです。<|im_end|>")
print(tokens)  # Expect something like ['<|im_end|>'] if it's one token.
print(len(tokens))
for i in range(1, len(tokens) + 1):
    # Use convert_tokens_to_string to correctly join tokens.
    prefix_text = tt.tokenizer.convert_tokens_to_string(tokens[:i])
    print(prefix_text)
tokens = tt.tokenizer.convert_tokens_to_string(tokens)
print(tokens)  # Expect something like ['<|im_end|>'] if it's one token.
print(len(tokens))


# import json
# import random
# from collections import Counter
# from LanguageTutor_v1.core.modules.TokenTokenizer import TokenTokenizer
# from LanguageTutor_v1.core.core_utils.misc_utils import write_dict_to_json
# from LanguageTutor_v1.core.models.model_constants import MODEL_ID_LM, LIST_FILENAMES_SENTENCES_JPN, \
#     LIST_FILENAMES_PREFIX_JPN, LIST_LEVELS_LABEL_JPN, ROOT_SENTENCES_JPN, FILENAME_TRAIN_DATA, FILENAME_TEST_DATA
# from LanguageTutor_v1.core.core_constants import JPN

# # Initialize the TokenTokenizer (using the HF model for Japanese)
# tt = TokenTokenizer(language=JPN, tokenizer_id=MODEL_ID_LM)


# #############################################
# # Step 1: Split Sentences into Train and Test Files
# #############################################
# def count_sentences(filename: str) -> int:
#     filepath = f"{ROOT_SENTENCES_JPN}{filename}"
#     with open(filepath, "r", encoding="utf-8") as f:
#         return sum(1 for line in f if line.strip())

# # Determine the minimum number of sentences across all sentence files.
# min_count = min(count_sentences(filename) for filename in LIST_FILENAMES_SENTENCES_JPN)
# print("Minimum sentence count across levels:", min_count)

# def split_sentences_train_test(filename: str, train_ratio: float = 0.8) -> None:
#     """
#     Reads sentences from the input file, randomly samples exactly min_count sentences,
#     splits them into training and testing sets, and writes out two files:
#       - train_{filename}
#       - test_{filename}
#     """
#     infilepath = f"{ROOT_SENTENCES_JPN}{filename}"
#     with open(infilepath, "r", encoding="utf-8") as f:
#         sentences = [line.strip() for line in f if line.strip()]
#     # Randomly sample exactly min_count sentences to balance across levels.
#     sampled_sentences = random.sample(sentences, k=min_count)
#     split_idx = int(min_count * train_ratio)
#     train_sentences = sampled_sentences[:split_idx]
#     test_sentences = sampled_sentences[split_idx:]
    
#     train_filepath = f"{ROOT_SENTENCES_JPN}train_{filename}"
#     test_filepath = f"{ROOT_SENTENCES_JPN}test_{filename}"
    
#     with open(train_filepath, "w", encoding="utf-8") as f:
#         for sentence in train_sentences:
#             f.write(sentence + "\n")
#     with open(test_filepath, "w", encoding="utf-8") as f:
#         for sentence in test_sentences:
#             f.write(sentence + "\n")

# # Apply train-test split on each original sentence file.
# for filename in LIST_FILENAMES_SENTENCES_JPN:
#     split_sentences_train_test(filename, train_ratio=0.8)

# #############################################
# # Step 2: Generate Prefixes from the Split Sentence Files
# #############################################
# def generate_and_store_prefixes(filename: str, n_filename: str) -> None:
#     """
#     Reads each sentence from the input file, appends the <|im_end|> token to the end,
#     then generates every possible prefix from that sentence and writes them to a new file.
#     """
#     infilepath = f"{ROOT_SENTENCES_JPN}{filename}"
#     outfile_path = f"{ROOT_SENTENCES_JPN}{n_filename}"
#     with open(infilepath, "r", encoding="utf-8") as infile, \
#         open(outfile_path, "w", encoding="utf-8") as outfile:
#         for line in infile:
#             sentence = line.strip()
#             # Append the <|im_end|> token.
#             sentence_with_end = sentence + "<|im_end|>"
#             tokens = tt.sentence_to_tokens(sentence=sentence_with_end)
#             # Generate every prefix (from 1 token up to full sentence tokens)
#                         # Generate every prefix by reassembling the tokens into text.
#             # for i in range(1, len(tokens) + 1):
#             #     # Use convert_tokens_to_string to correctly join tokens.
#             #     prefix_text = tt.tokenizer.convert_tokens_to_string(tokens[:i])
#             #     outfile.write(prefix_text + "\n")
#             for i in range(1, len(tokens) + 1):
#                 outfile.write("".join(tokens[:i]) + "\n")

# # Generate prefix files from the training sentence files.
# for filename in LIST_FILENAMES_SENTENCES_JPN:
#     train_filename = f"train_{filename}"
#     # Write prefixes to file, naming it with "sampled_prefix_" prefix.
#     generate_and_store_prefixes(filename=train_filename, n_filename=f"sampled_prefix_{filename}")

# # Optionally, you can also generate prefixes from the test files if needed:
# for filename in LIST_FILENAMES_SENTENCES_JPN:
#     test_filename = f"test_{filename}"
#     generate_and_store_prefixes(filename=test_filename, n_filename=f"sampled_testprefix_{filename}")

# #############################################
# # Step 3: Create Train/Test Data for FUDGE Training
# #############################################
# def load_all_prefix_data():
#     prefix_label_pairs = []
#     # For each level in your label list (e.g., LIST_LEVELS_LABEL_JPN contains "n5", "n4", etc.)
#     for level in LIST_LEVELS_LABEL_JPN:
#         filepath = f"{ROOT_SENTENCES_JPN}sampled_prefix_{level}.txt"
#         with open(filepath, "r", encoding="utf-8") as f:
#             prefixes = [line.strip() for line in f if line.strip()]
#             # Associate each prefix with its level.
#             prefix_label_pairs.extend([{"prefix": p, "label": level} for p in prefixes])
#     return prefix_label_pairs

# def split_balanced_train_test(prefix_label_pairs, train_ratio=0.8):
#     # Group prefixes by label.
#     label_to_prefixes = {}
#     for item in prefix_label_pairs:
#         label_to_prefixes.setdefault(item["label"], []).append(item["prefix"])
    
#     train_data, test_data = [], []
#     # Here we assume that each level has the same total number of prefixes because the sentences were balanced.
#     for label, prefixes in label_to_prefixes.items():
#         random.shuffle(prefixes)
#         split_idx = int(len(prefixes) * train_ratio)
#         train_data.extend([{"prefix": p, "label": label} for p in prefixes[:split_idx]])
#         test_data.extend([{"prefix": p, "label": label} for p in prefixes[split_idx:]])
#     return train_data, test_data

# prefix_label_pairs = load_all_prefix_data()
# train_data, test_data = split_balanced_train_test(prefix_label_pairs, train_ratio=0.8)
# train_filepath = f"{ROOT_SENTENCES_JPN}{FILENAME_TRAIN_DATA}"
# test_filepath = f"{ROOT_SENTENCES_JPN}{FILENAME_TEST_DATA}"

# write_dict_to_json(train_data, train_filepath)
# write_dict_to_json(test_data, test_filepath)
