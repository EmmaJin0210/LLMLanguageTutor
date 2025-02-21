from LanguageTutor_v1.core.core_utils.misc_utils import *
from LanguageTutor_v1.core.core_utils.language_utils import load_grammar_file_to_dict, load_vocab_file_to_dict, \
    flatten_dict_for_tokenization
from LanguageTutor_v1.core.modules.TokenDetectorMatcher import TokenDetectorMatcher
from collections import defaultdict


# full JLPT lists?
# 5 examples for each level
# run script
# if not, change database for n1 - n4
# -----
# regex (optional)
# for fuzzy matching, distribution
# find a package to do kanji -> hiragana


levels = ["n5", "n4", "n3", "n2", "n1"] # 
# EXAMPLES = read_json_to_dict("difficulty_test_examples/examples.json")
# NEWS_EXAMPLES = read_json_to_dict("difficulty_test_examples/news_examples.json")
JLPT_EXAMPLES = read_json_to_dict("difficulty_test_examples/jlpt_examples.json")

grammar_dict = load_grammar_file_to_dict("japanese", levels)
vocab_dict = load_vocab_file_to_dict("japanese", levels)
grammar_dict = flatten_dict_for_tokenization(grammar_dict)
vocab_dict = flatten_dict_for_tokenization(vocab_dict)


detector = TokenDetectorMatcher(vocab_dict, grammar_dict, language = "japanese")
undetected_counts = defaultdict(int)
token_counts = defaultdict(int)
accurate_label_counts = defaultdict(int)
overestimate_label_counts = defaultdict(int)
total_label_counts = sum([len(examples) for _, examples in JLPT_EXAMPLES.items()])

def update_hit_rates(level, tokenizer):
    for sentence in JLPT_EXAMPLES[level]:
        print()
        print(f"    Sentence: {sentence}")
        print()
        tokens = detector.tokenize(sentence, tokenizer=tokenizer)
        token_counts[tokenizer] += len(tokens)
        print(f"        --- Using Tokenizer {tokenizer} ---")
        print(f"        Tokens: {tokens}")
        not_detected = set(tokens)
        detected_dict = detector.detect_tokens_at_levels(tokens, levels)
        for l, detected in detected_dict.items():
            print(f"        Tokens at Level {l}: {detected}")
            not_detected -= detected
        fuzzy_matched = detector.fuzzy_match(not_detected)
        print(f"        Fuzzy matched: {fuzzy_matched}")
        not_detected -= fuzzy_matched
        print(f"        Not detected: {not_detected}")
        undetected_counts[tokenizer] += len(not_detected)

def calc_accuracies(level, tokenizer):
    for sentence in JLPT_EXAMPLES[level]:
        tokens = detector.tokenize(sentence, tokenizer=tokenizer)
        detected_dict, _ = detector.detect_tokens_at_levels(tokens, levels)
        not_detected = set(tokens)
        print(detected_dict)
        for l, detected in detected_dict.items():
            if len(detected) > 0:
                label = l
            not_detected -= detected
        if label == level:
            accurate_label_counts[tokenizer] += 1
        else:
            print(f"--- Using Tokenizer {tokenizer} ---")
            print(f"    wrong level for: {sentence}")
            print(f"        Tokens: {tokens}")
            print(f"        Correct level: {level} | Detected level: {label}")
            for l, detected in detected_dict.items():
                print(f"            Tokens at Level {l}: {detected}")
            print(f"        Not detected: {not_detected}")
            if label > level:
                overestimate_label_counts[tokenizer] += 1
        
for level in levels:
    print(f"--- At level {level} ---")
    for tokenizer in ['MeCab', 'Janome', 'Sudachi']:#
        # update_hit_rates(level, tokenizer)
        calc_accuracies(level, tokenizer)

for tokenizer, correct_count in accurate_label_counts.items():

    print(f"{tokenizer} has accuracy of {correct_count/total_label_counts} ({correct_count} out of {total_label_counts}) | overestimate accuracy of {overestimate_label_counts[tokenizer]/total_label_counts} ({overestimate_label_counts[tokenizer]} out of {total_label_counts})")

# for tokenizer, undetected in undetected_counts.items():
#     print(f"{tokenizer} : {undetected / token_counts[tokenizer]} undetected ({undetected} out of {token_counts[tokenizer]}) | HIT RATE: {1 - undetected / token_counts[tokenizer]}")

