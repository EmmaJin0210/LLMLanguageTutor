# from collections import Counter

# from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
# from LanguageTutor_v1.core.modules.TokenTokenizer import TokenTokenizer
# from LanguageTutor_v1.appstuff.app_constants import ROOT_STATIC_DB

# language = "japanese"

# tt = TokenTokenizer(language)
# sentence = "私は夜学生で,学生結婚をしました。"

# tokens = tt.sentence_to_tokens(
#                 sentence=sentence,
#                 base_form=True,
#                 filter_punctuation=True
#             )

# print(tokens)
import re
from collections import Counter
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
from LanguageTutor_v1.core.modules.TokenTokenizer import TokenTokenizer
from LanguageTutor_v1.appstuff.app_constants import ROOT_STATIC_DB
import math

language = "japanese"
jp_only_re = re.compile(r'^[\u3040-\u30FF\u31F0-\u31FF\u4E00-\u9FFF]+$')

tt = TokenTokenizer(language)

all_levels = get_all_levels(language)

level_word_freq = {}
word_level_freq = {}

total_tokens_db = 0

for level in all_levels:
    print(f"creating maps for {level}")
    level_word_freq[level] = Counter()
    infilepath = f"{ROOT_STATIC_DB}{language}/sentences/{level}.txt"
    with open(infilepath, "r", encoding="utf-8") as f:
        for line in f:
            sentence = line.strip()
            tokens = tt.sentence_to_tokens(
                sentence=sentence,
                base_form=True,
                filter_punctuation=True
            )
            for token in tokens:
                if not jp_only_re.fullmatch(token):
                    continue
                total_tokens_db += 1        
                level_word_freq[level][token] += 1
                if token not in word_level_freq:
                    word_level_freq[token] = {}
                word_level_freq[token][level] = word_level_freq[token].get(level, 0) + 1

print(total_tokens_db)


TOTAL_TOKENS = total_tokens_db
GLOBAL_FRAC  = 1e-6
LEVEL_FRAC   = 1e-6
global_min   = math.ceil(TOTAL_TOKENS * GLOBAL_FRAC)

print("removing singleton words...")
words_to_remove = []
for word, freq_dict in word_level_freq.items():
    total_freq = sum(freq_dict.values())
    if total_freq <= global_min:
        words_to_remove.append(word)

for word in words_to_remove:
    del word_level_freq[word]
    for level in all_levels:
        if word in level_word_freq[level]:
            del level_word_freq[level][word]

print("removing singleton occurrences in each level...")

for level in all_levels:
    for word in list(level_word_freq[level].keys()):
        LEVEL_TOKENS = sum(list(level_word_freq[level].values()))
        if level_word_freq[level][word] <= math.ceil(LEVEL_TOKENS * LEVEL_FRAC):
            del level_word_freq[level][word]
            if word in word_level_freq and level in word_level_freq[word]:
                del word_level_freq[word][level]
            if word in word_level_freq and not word_level_freq[word]:
                del word_level_freq[word]

# Total words per level
total_words = {}
total_unique_words = {}
for level, counter in level_word_freq.items():
    total_words[level] = sum(counter.values())
    total_unique_words[level] = len(list(counter.keys()))
print("total words: ", total_words)
print("total unique words: ", total_unique_words)


print("assigning each word to the best level")
word_best_level = {}
done_count = 0
for word, freq_dict in word_level_freq.items():
    if done_count % 100 == 0:
        print(f"finished assigning {done_count} words")
    best_level = None
    best_norm = 0.0
    for level, freq in freq_dict.items():
        norm = freq / total_words[level] if total_words[level] > 0 else 0.0
        if norm > best_norm:
            best_norm = norm
            best_level = level
    if best_level is not None:
        word_best_level[word] = best_level
    done_count += 1

level_to_words = {}
for level in all_levels:
    level_to_words[level] = {word for word in level_word_freq[level] 
                             if word in word_best_level and word_best_level[word] == level}

level_to_words_unique = {}
accumulated = set()

for level in all_levels:
    print(f"making level {level} exclusive")
    current_vocab = level_to_words[level]
    unique_vocab = current_vocab - accumulated
    level_to_words_unique[level] = unique_vocab
    accumulated.update(current_vocab)


for level, vocab in level_to_words_unique.items():
    print(f"writing to level {level} bagofwords")
    outfilepath = f"{ROOT_STATIC_DB}{language}/sentences/{level}_bagofwords.txt"
    with open(outfilepath, "w", encoding="utf-8") as f:
        for word in vocab:
            f.write(word + "\n")