
from LanguageTutor_v1.core.modules.SentenceTokenizer import SentenceTokenizer
from LanguageTutor_v1.core.models.model_constants import ROOT_SENTENCES_JPN, \
    LIST_FILENAMES_SENTENCES_JPN

# function to: 
# 1. read each sentence from a file, map all prefixes to corresponding level
# 2. write (prefix -> level) data to new .txt file for each level
def generate_and_store_prefixes(filename: str, n_filename: str) -> None:
    with open(f"{ROOT_SENTENCES_JPN}{filename}", "r", encoding = "utf-8") as infile, \
        open(f"{ROOT_SENTENCES_JPN}{n_filename}", "w", encoding = "utf-8") as outfile:
        for line in infile:
            sentence = line.strip()
            tokens = st.tokenize_sentence(sentence)
            for i in range(1, len(tokens) + 1):
                outfile.write("".join(tokens[:i]) + "\n")
    infile.close()
    outfile.close()


# take least number of prefixes, randomly sample from other levels
# write sample data to new file for each level


# prepare training data into json file (do we need to separate things out by batches?)

st = SentenceTokenizer(language = "japanese")
for filename in LIST_FILENAMES_SENTENCES_JPN:
    generate_and_store_prefixes(filename = filename, 
                                n_filename = f"prefix_{filename}")