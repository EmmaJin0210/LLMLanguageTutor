import json
import math
from collections import Counter, defaultdict
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
from LanguageTutor_v1.appstuff.app_constants import ROOT_STATIC_DB

language    = "japanese"
all_levels  = get_all_levels(language)

level_word_freq = {lvl: Counter() for lvl in all_levels}
word_level_freq = defaultdict(lambda: defaultdict(int))
TOTAL_TOKENS    = 0

for level in all_levels:
    cache_path = f"{ROOT_STATIC_DB}{language}/sentences/{level}_tokens.jsonl"
    with open(cache_path, "r", encoding="utf-8") as f:
        for line in f:
            toks = json.loads(line)
            for tok in toks:
                TOTAL_TOKENS += 1
                level_word_freq[level][tok] += 1
                word_level_freq[tok][level] += 1


GLOBAL_FRAC = 1e-6
LEVEL_FRAC  = 1e-6
global_min  = math.ceil(TOTAL_TOKENS * GLOBAL_FRAC)

# remove globally rare
for word, freqs in list(word_level_freq.items()):
    if sum(freqs.values()) <= global_min:
        del word_level_freq[word]
        for lvl in all_levels:
            level_word_freq[lvl].pop(word, None)

# remove per‐level rare
for lvl in all_levels:
    lvl_total = sum(level_word_freq[lvl].values())
    level_min = math.ceil(lvl_total * LEVEL_FRAC)
    for word, cnt in list(level_word_freq[lvl].items()):
        if cnt <= level_min:
            del level_word_freq[lvl][word]
            if word in word_level_freq and lvl in word_level_freq[word]:
                del word_level_freq[word][lvl]
    # clean up any now‑empty entries
    for w in list(word_level_freq):
        if not word_level_freq[w]:
            del word_level_freq[w]

# compute best‐level
total_words = {lvl: sum(c.values()) for lvl, c in level_word_freq.items()}
word_best_level = {}
threshold = 0
for w, freqs in word_level_freq.items():
    for lvl, cnt in freqs.items():
        score = cnt / total_words[lvl]
        if score > threshold:
            word_best_level[w] = lvl
            break


# total_words = {lvl: sum(c.values()) for lvl, c in level_word_freq.items()}
# word_best_level = {}
# for w, freqs in word_level_freq.items():
#     best, best_score = None, 0.0
#     for lvl, cnt in freqs.items():
#         score = cnt / total_words[lvl]
#         if score > best_score:
#             best_score, best = score, lvl
#     if best:
#         word_best_level[w] = best

# build per‐level vocab
level_to_words = {lvl: set() for lvl in all_levels}
for w, lvl in word_best_level.items():
    level_to_words[lvl].add(w)

accum = set()
level_to_words_unique = {}
for lvl in all_levels:
    unique = level_to_words[lvl] - accum
    level_to_words_unique[lvl] = unique
    accum |= level_to_words[lvl]

# write bag‐of‐words
for lvl, vocab in level_to_words_unique.items():
    outpath = f"{ROOT_STATIC_DB}{language}/sentences/{lvl}_bagofwords.txt"
    with open(outpath, "w", encoding="utf-8") as f:
        for w in sorted(vocab):
            f.write(w + "\n")
    print(f"→ wrote {len(vocab)} words for level {lvl} to {outpath}")
