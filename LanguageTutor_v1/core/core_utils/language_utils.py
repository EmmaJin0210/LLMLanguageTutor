import re
from core.core_utils.misc_utils import read_json_to_dict, read_txt_file_to_string
from core.language_constants import MAP_LEVEL_TO_DESC_WORD, LIST_ALL_LEVELS, \
    MAP_LEVEL_TO_NUM_DESIRED_TOKENS, MAP_LEVEL_TO_DIFFICULTY_SCORE, \
    DIRNAME_GRAMMAR, DIRNAME_VOCAB, DIRNAME_FEWSHOTS, DIRNAME_LEVEL_DESCS, \
    DIRNAME_LEVEL_GUIDES, DIRNAME_LEVEL_EX
from appstuff.app_constants import ROOT_STATIC

###### imports for typing purposes ######
from typing import List, Dict
#########################################



def get_level_desc_word(language: str, level: str) -> str:
    return MAP_LEVEL_TO_DESC_WORD[language][level]


def get_all_levels(language: str) -> List[str]:
    return LIST_ALL_LEVELS[language]


def get_levels_below_inclusive(language: str, target_level: str) \
    -> List[str]:
    index = LIST_ALL_LEVELS[language].index(target_level)
    return LIST_ALL_LEVELS[language][:index + 1]


def get_levels_above_exclusive(language: str, target_level: str) \
    -> List[str]:
    index = LIST_ALL_LEVELS[language].index(target_level)
    return LIST_ALL_LEVELS[language][index + 1:]


def load_grammar_file_to_dict(language: str, levels: List[str]) -> Dict:
    dic = {}
    for level in levels:
        dic[level] = {}
        file_path = f"{ROOT_STATIC}{language}/{DIRNAME_GRAMMAR}/{level}.json"
        json_obj = read_json_to_dict(file_path)
        dic[level].update(json_obj)
    return dic


def flatten_dict_for_tokenization(dic: Dict) -> Dict:
    to_return = {}
    for level, words in dic.items():
        to_return[level] = {}
        for word, inner_dict in words.items():
            if word in to_return[level]:
                to_return[level][word] += "; " + inner_dict["meaning"]
            else:
                to_return[level][word] = inner_dict["meaning"]
    return to_return


def load_vocab_file_to_dict(language: str, levels: List[str]) -> Dict:
    to_return = {}
    for level in levels:
        to_return[level] = {}
        file_path = f"{ROOT_STATIC}{language}/{DIRNAME_VOCAB}/{level}.json"
        json_obj = read_json_to_dict(file_path)
        to_return[level].update(json_obj)
    return to_return


def get_all_levels_of_language(language: str) -> List[str]:
    return LIST_ALL_LEVELS[language]


def filter_katakana(dic: Dict) -> Dict:
    katakana_pattern = re.compile(r'^[\u30A0-\u30FF]+$')
    for level, words_dict in dic.items():
        dic[level] = {word: details for word, details in words_dict.items() 
                      if not katakana_pattern.match(word)}
    return dic


def get_level_desc_detailed(language: str, level: str) -> str:
    path = f"{ROOT_STATIC}{language}/{DIRNAME_LEVEL_DESCS}/{level}.txt"
    return read_txt_file_to_string(path)


def retrieve_shots(language: str, function: str) -> Dict:
    path = f"{ROOT_STATIC}{language}/{DIRNAME_FEWSHOTS}/{function}.json"
    return read_json_to_dict(path)


def get_level_guidelines(language: str, level: str) -> str:
    path = f"{ROOT_STATIC}{language}/{DIRNAME_LEVEL_GUIDES}/{level}.txt"
    return read_txt_file_to_string(path)


def get_level_example(language: str, level: str) -> str:
    path = f"{ROOT_STATIC}{language}/{DIRNAME_LEVEL_EX}/{level}.txt"
    return read_txt_file_to_string(path)


def get_desired_tokens_count(language: str, level: str) -> int:
    return MAP_LEVEL_TO_NUM_DESIRED_TOKENS[language][level]


def get_level_difficulty_score(language: str, level: str) -> int:
    return MAP_LEVEL_TO_DIFFICULTY_SCORE[language][level]