import json
import ast


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

def read_txt_file_to_string(file_path):
    """
    Reads a text file and returns its contents as a single string.

    Parameters:
        file_path (str): The path to the text file.

    Returns:
        str: The contents of the file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file at {file_path} does not exist.")
    except IOError as e:
        raise IOError(f"An error occurred while reading the file: {e}")