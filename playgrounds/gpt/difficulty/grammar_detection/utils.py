import json

def load_grammar_file_to_dict(language, levels):
    dic = {}
    for level in levels:
        file_path = "../grammar_lists/" + language.lower() + "/" + level + ".json"
        json_obj = read_json_to_dict(file_path)
        dic.update(json_obj)
    return dic

def get_grammar_keys(json_obj):
    grammar_keys = []
    for grammar_point in json_obj:
        grammar_keys.append(grammar_point)
    return grammar_keys

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