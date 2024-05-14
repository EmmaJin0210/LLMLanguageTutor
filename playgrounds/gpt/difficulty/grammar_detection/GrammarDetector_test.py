from GrammarDetector import GrammarDetector
from openai import OpenAI
from utils import *
import datetime

def get_grammar_level(grammar_dict, grammar_point):
    # TODO: if grammar_point doesn't exist? need to throw error
    return grammar_dict[grammar_point]["level"]

log = []

detector = GrammarDetector("japanese", ["n5"])
grammar_dict = detector.grammar_dict

test_set = read_json_to_dict("testset-2024-04-03-15-37-30.json")

total_count = len(test_set)
accurate_count = 0
consistent_count = 0

for label, sentence in test_set.items():
    result = detector.detect_grammar(sentence)
    log = print_and_save("Sentence: "+sentence, log)
    log = print_and_save("Correct label: "+label, log)
    log = print_and_save("Detector result: "+str(result), log)
    if label in result:
        accurate_count += 1
    else:
        print_and_save("Label "+label+" is not in result.", log)
    not_in_dict = []
    for gp in result:
        if gp not in grammar_dict:
            not_in_dict.append(gp)
    if len(not_in_dict) == 0:
        consistent_count += 1
    else:
        log = print_and_save("The grammar points "+str(not_in_dict)+"are not in the original dictionary.", log)
    log = print_and_save("", log)

accuracy = accurate_count / total_count
consistency = consistent_count / total_count

print_and_save("Accuracy: "+str(accuracy), log)
print_and_save("Consistency: "+str(consistency), log)

current_time = datetime.datetime.now()
timestamp = current_time.strftime("%Y-%m-%d-%H-%M-%S")
filename = f"results-{timestamp}.txt"
with open(filename, 'w', encoding='utf-8') as file:
    for line in log:
        file.write(line+'\n')