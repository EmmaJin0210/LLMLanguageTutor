import JapaneseTokenizer
import konoha
import subprocess
import regex as re

from core.utils.utils import *

def is_punctuation(token):
    return re.match(r'^\p{P}+$', token)

class TokenDetectorMatcher:
    def __init__(self, word_dict, grammar_dict, language = "japanese"):
        self.language = language
        self.level_to_words = word_dict
        self.level_to_grammars = grammar_dict

    def tokenize(self, sentence, tokenizer = 'Sudachi', sudachi_mode = 'A'):
        konoha_tokenizers = {
            'MeCab': {},
            'Janome': {},
            'Sudachi': {"mode": sudachi_mode}
        }
        if tokenizer in konoha_tokenizers:
            self.tokenizer = konoha.WordTokenizer(tokenizer, **konoha_tokenizers[tokenizer])
            tokens = [token.base_form for token in self.tokenizer.tokenize(sentence)]
        elif tokenizer == 'juman':
            self.tokenizer = JapaneseTokenizer.JumanppWrapper()
            tokens = self.tokenizer.tokenize(sentence).convert_list_object()
        elif tokenizer == 'kytea':
            result = subprocess.check_output(f"echo '{sentence}' | kytea", shell=True, text=True)
            tokens = [token.split('/')[0] for token in result.strip().split()]

        tokens = [token for token in tokens if token and not is_punctuation(token)]
        return tokens

    def detect_tokens_at_level(self, tokens, level, scope=['v', 'g']):
        to_return = set()
        for token in tokens:
            if 'v' in scope and token in self.level_to_words[level]:
                to_return.add(token)
            if 'g' in scope and token in self.level_to_grammars[level]:
                to_return.add(token)
        return to_return


    def detect_tokens_at_levels(self, tokens, levels, scope=['v', 'g']):  # return a level : [tokens] map
        level_to_detected = {}
        tokens = set(tokens)
        # print(levels)
        for level in levels:
            level_to_detected[level] = set()
            detected = self.detect_tokens_at_level(tokens, level, scope)
            level_to_detected[level].update(detected)
            tokens -= detected
        undetected = tokens
        return level_to_detected, undetected

    # def fuzzy_match(self, to_match, levels=[], scope=['v', 'g']):
    #     matched = set()
    #     if not levels:
    #         levels = self.levels
    #     if levels != self.levels:
    #         self.load_db_as_dicts(levels=levels)
    #     for token in to_match:
    #         variations = [token + "る"]
    #         for level in levels:
    #             for variation in variations:
    #                 if 'v' in scope and variation in self.level_to_words[level]:
    #                     matched.add(token)
    #                 if 'g' in scope and variation in self.level_to_grammars[level]:
    #                     matched.add(token)
    #     return matched





def main():
    levels = ["n2", "n3", "n4", "n5"]
    n5_ex1 = "これは本です。"
    n5_ex2 = "一緒に映画を見ませんか。"
    n5_ex3 = "日本へ行きたいです。"
    detector = TokenDetectorMatcher(language="Japanese", levels=levels)
    tokens = detector.tokenize(n5_ex1)
    print(f"Tokens: {tokens}")
    at_level = detector.detect_tokens_at_level(tokens)
    print(f"At Levels {levels}: {at_level}")

if __name__ == "__main__":
    main()