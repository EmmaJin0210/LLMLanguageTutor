import os
import re
from LanguageTutor_v1.core.modules.TokenDetectorMatcher import TokenDetectorMatcher
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels, load_vocab_file_to_dict
from LanguageTutor_v1.core.core_utils.misc_utils import read_json_to_dict, write_dict_to_json

# Configuration
source_folder = "jlpt_anki_with_reading"
input_dir = "eval/user_study_logs"
target_language = "japanese"

# Regex to filter Japanese-only tokens
jp_only_re = re.compile(r'^[\u3005\u303B\u309D\u309E\u30FC\u3040-\u30FF\u31F0-\u31FF\u4E00-\u9FFF]+$')

# Load vocab and initialize tokenizer
all_levels = get_all_levels(target_language)
vocab_dict = load_vocab_file_to_dict(
    language=target_language,
    levels=all_levels,
    vocab_dir=os.path.join("vocab_lists", source_folder)
)
tdm = TokenDetectorMatcher(word_dict=vocab_dict, grammar_dict={}, language=target_language)


for filename in os.listdir(input_dir):

    input_path = os.path.join(input_dir, filename)
    data = read_json_to_dict(input_path)

    for round_entry in data["script"]:
        for speaker in ["student", "tutor"]:
            if speaker in round_entry:
                sentence = round_entry[speaker].strip()
                tokens = tdm.tokenize(sentence, tokenizer='Sudachi', sudachi_mode='C', strip=True)
                tokens = [t for t in tokens if jp_only_re.fullmatch(t)]
                round_entry[f"{speaker}_tokens"] = tokens
                round_entry["hard_tokens"] = []
                round_entry["understood"] = True

    base_name = os.path.splitext(filename)[0]
    output_path = os.path.join(input_dir, f"{base_name}.json")
    write_dict_to_json(data, output_path)