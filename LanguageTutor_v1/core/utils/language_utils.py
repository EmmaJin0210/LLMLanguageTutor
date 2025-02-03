import re
import json
from core.utils.utils import *

STATIC_ROOT_DIR = "static_database"

difficulty_map = {
    "japanese" : ["n5", "n4", "n3", "n2", "n1"]
}

language_level_to_desc_map = {
    "japanese": {
        "n5" : "beginner",
        "n4" : "beginner",
        "n3" : "intermediate",
        "n2" : "intermediate",
        "n1" : "advanced"
    }
}

language_level_to_desired_tokens_map = {
    "japanese": {
        "n5" : 10,
        "n4" : 15,
        "n3" : 20,
        "n2" : 30,
        "n1" : 50
    }
}

language_level_to_difficulty_score_map = {
    "japanese": {
        "n5" : 1,
        "n4" : 3,
        "n3" : 8,
        "n2" : 15,
        "n1" : 30
    }
}


def get_desc(language, level):
    return language_level_to_desc_map[language][level]

def get_levels(language):
    return difficulty_map[language.lower()]

def get_levels_below_inclusive(language, target_level):
    index = difficulty_map[language.lower()].index(target_level.lower())
    return difficulty_map[language.lower()][:index+1]

def get_levels_above_exclusive(language, target_level):
    index = difficulty_map[language.lower()].index(target_level.lower())
    return difficulty_map[language.lower()][index+1:]

def load_grammar_file_to_dict(language, levels):
    dic = {}
    for level in levels:
        dic[level] = {}
        file_path = f"static_database/{language.lower()}/grammar_lists/{level}.json"
        json_obj = read_json_to_dict(file_path)
        dic[level].update(json_obj)
    return dic

def load_grammar_file_to_dict(language, levels):
    dic = {}
    for level in levels:
        dic[level] = {}
        file_path = f"static_database/{language.lower()}/grammar_lists/{level}.json"
        json_obj = read_json_to_dict(file_path)
        dic[level].update(json_obj)
    return dic

def flatten_grammar_dict_for_tokenization(g_dict):
    to_return = {}
    for level, words in g_dict.items():
        to_return[level] = {}
        for word, inner_dict in words.items():
            if word in to_return[level]:
                to_return[level][word] += "; " + inner_dict["meaning"]
            else:
                to_return[level][word] = inner_dict["meaning"]
    return to_return

def load_vocab_file_to_dict(language, levels):
    to_return = {}
    for level in levels:
        to_return[level] = {}
        file_path = f"static_database/{language.lower()}/vocab_lists/{level}.json"
        json_obj = read_json_to_dict(file_path)
        to_return[level].update(json_obj)
    return to_return

def flatten_vocab_dict_for_tokenization(v_dict):
    to_return = {}
    for level, words in v_dict.items():
        to_return[level] = {}
        for word, inner_dict in words.items():
            if word in to_return[level]:
                to_return[level][word] += "; " + inner_dict["meaning"]
            else:
                to_return[level][word] = inner_dict["meaning"]
    return to_return

def get_grammar_keys(json_obj):
    grammar_keys = []
    for grammar_point in json_obj:
        grammar_keys.append(grammar_point)
    return grammar_keys

def get_vocab_keys_w_category(json_obj):
    to_return = {}
    for c, dic in json_obj.items():
        keys = list(dic.keys())
        to_return[c] = keys
    return to_return

def get_vocab_keys(json_obj):
    to_return = []
    for _ , keys in json_obj.items():
        to_return += list(keys)
    return to_return

def unpack_grammar_dict_for_prompting(json_obj):
    to_return = {}
    for gp, dict2 in json_obj.items():
        to_return[gp] = dict2["meaning"]
    return to_return

def unpack_vocab_dict_for_prompting(json_obj):
    to_return = {}
    for category, dict2 in json_obj.items():
        key = "only use these " + category
        value = {}
        for word, dict3 in dict2.items():
            value[word] = dict3["meaning"]
        to_return[key] = value
    return to_return

def unpack_vocab_list_to_str_for_prompt(vocab_dict):
    to_return = ""
    for k, v in vocab_dict.items():
        to_return += k + ":\n"
        to_return += str(list(v.keys())) + "\n"
    return to_return

def get_all_levels_of_language(language):
    return difficulty_map[language]

def filter_katakana(db):
    # Regex pattern to match words that are entirely in Katakana
    katakana_pattern = re.compile(r'^[\u30A0-\u30FF]+$')
    for level, words_dict in db.items():
        # Filter out words that are entirely Katakana
        db[level] = {word: details for word, details in words_dict.items() if not katakana_pattern.match(word)}
    return db

def get_detailed_description(language, level):
    path = f"{STATIC_ROOT_DIR}/{language.lower()}/level_descs/{level}.txt"
    return read_txt_file_to_string(path)

def retrieve_shots(language, function):
    path = f"{STATIC_ROOT_DIR}/{language.lower()}/few_shots/{function}.json"
    return read_json_to_dict(path)

def get_level_guidelines(language, level):
    path = f"{STATIC_ROOT_DIR}/{language.lower()}/level_guidelines/{level}.txt"
    return read_txt_file_to_string(path)

def get_level_example(language, level):
    path = f"{STATIC_ROOT_DIR}/{language.lower()}/level_examples/{level}.txt"
    return read_txt_file_to_string(path)

def get_desired_tokens_count(language, level):
    return language_level_to_desired_tokens_map[language][level]

def get_level_difficulty_score(language, level):
    return language_level_to_difficulty_score_map[language][level]