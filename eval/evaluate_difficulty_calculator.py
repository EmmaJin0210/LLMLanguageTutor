import os
import json
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels, \
    get_levels_above_exclusive, get_levels_below_inclusive
from LanguageTutor_v1.core.modules.TokenDetectorMatcher import TokenDetectorMatcher
from LanguageTutor_v1.appstuff.app_constants import ROOT_STATIC_DB
from LanguageTutor_v1.core.modules.DifficultyCalculator import DifficultyCalculator

TARGET_LANGUAGE = "japanese"
ALL_LEVELS = get_all_levels(TARGET_LANGUAGE)

def evaluate_test_files():
    word_dict = {}
    for level in ALL_LEVELS:
        filepath = os.path.join(ROOT_STATIC_DB, TARGET_LANGUAGE, "sentences", f"{level}_bagofwords.txt")
        with open(filepath, "r", encoding="utf-8") as f:
            words = {line.strip() for line in f if line.strip()}
        word_dict[level] = words

    grammar_dict = {}
    tdm = TokenDetectorMatcher(word_dict, grammar_dict, language=TARGET_LANGUAGE)
    dc = DifficultyCalculator()

    results = {}

    for level in ALL_LEVELS:
        test_filepath = os.path.join(ROOT_STATIC_DB, TARGET_LANGUAGE, "sentences", f"test_{level}.txt")
        with open(test_filepath, "r", encoding="utf-8") as f:
            sentences = [line.strip() for line in f if line.strip()]

        total_sentences = len(sentences)
        at_target_count = 0

        for sentence in sentences:
            tokens = tdm.tokenize(sentence, tokenizer='Sudachi', sudachi_mode='C')
            detected, undetected = tdm.detect_tokens_at_levels(tokens, ALL_LEVELS, scope=['v'])
            
            above_levels = get_levels_above_exclusive(TARGET_LANGUAGE, level)
            below_levels = get_levels_above_exclusive(TARGET_LANGUAGE, level)
            above = {level: tokens for level, tokens in detected.items() if level in above_levels}
            below = {level: tokens for level, tokens in detected.items() if level in below_levels}
            is_at_target = dc.at_target_level(above, below)

            if is_at_target:
                at_target_count += 1

        results[level] = {
            "total_sentences": total_sentences,
            "at_target_count": at_target_count,
            "percentage": (at_target_count / total_sentences) * 100 if total_sentences > 0 else 0
        }
        print(f"Level {level}: {at_target_count} / {total_sentences} sentences ({results[level]['percentage']:.2f}%) are at target level.")

    results_filepath = os.path.join(ROOT_STATIC_DB, TARGET_LANGUAGE, "sentences", "evaluation_results.json")
    with open(results_filepath, "w", encoding="utf-8") as outfile:
        json.dump(results, outfile, indent=2, ensure_ascii=False)
    print("Evaluation results saved to:", results_filepath)

def main():
    evaluate_test_files()

if __name__ == "__main__":
    main()
