from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
from LanguageTutor_v1.appstuff.app_constants import ROOT_STATIC_DB
from LanguageTutor_v1.core.core_utils.misc_utils import write_dict_to_json

levels = get_all_levels("japanese")

for level in levels:
    bow_path = f"{ROOT_STATIC_DB}japanese/sentences/{level}_bagofwords.txt"
    vocab_path = f"{ROOT_STATIC_DB}japanese/vocab_lists/jpwac/{level}.json"


    with open(bow_path, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

        vocab_dict = {word: {} for word in words}

        # Write to JSON
        write_dict_to_json(vocab_dict, vocab_path)