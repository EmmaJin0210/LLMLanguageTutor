import json
import ast

difficulty_map = {
    "japanese" : ["n5", "n4", "n3", "n2", "n1"]
}

level_to_desc_map = {
    "n5" : "beginner",
    "n4" : "beginner",
    "n3" : "intermediate",
    "n2" : "intermediate",
    "n1" : "advanced"
}

def get_desc(level):
    return level_to_desc_map[level]

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
        file_path = f"static_database/{language.lower()}/grammar_lists/{level}.json"
        json_obj = read_json_to_dict(file_path)
        dic.update(json_obj)
    return dic

def load_vocab_file_to_dict(language, levels):
    to_return = {"nouns": {}, "verbs": {}, "adverbs": {}, "adjectives": {}}
    categories = ["nouns", "verbs", "adverbs", "adjectives"]
    for level in levels:
        file_path = f"static_database/{language.lower()}/vocab_lists/{level}.json"
        json_obj = read_json_to_dict(file_path)
        for c in categories:
            to_return[c].update(json_obj[c])
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

def write_dict_to_json(dic, file_path):
    with open(file_path, "w", encoding="utf-8") as outfile:
        json.dump(dic, outfile, indent=4, ensure_ascii=False)

def read_json_to_dict(file_path):
    with open(file_path, "r", encoding="utf-8") as infile:
        dic = json.load(infile)
    return dic
    
def print_and_save(to_print, save_to):
    print(to_print)
    save_to.append(to_print)
    return save_to

def list_str_to_list(list_string):
    return ast.literal_eval(list_string)


def retrieve_shots(language, function):
    path = f"static_database/{language.lower()}/few_shots/{function}.json"
    return read_json_to_dict(path)