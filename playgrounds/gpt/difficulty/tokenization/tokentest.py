import JapaneseTokenizer
import Levenshtein as lev
from sudachipy import tokenizer
from sudachipy import dictionary
import konoha
import subprocess
import sentencepiece as spm

def calc_levenshtein_similarity(word1, word2):
    distance = lev.distance(word1, word2)
    similarity = 1 - distance / max(len(word1), len(word2))
    return similarity

# Example text
text = '昨日の夜、友達と渋谷駅で待ち合わせして、一緒にラーメンを食べました。'

# MeCab Tokenizer
print("\nMeCab Tokenizer:")
dict_type = 'ipadic'
mecab_wrapper = JapaneseTokenizer.MecabWrapper(dictType=dict_type)
mecab_tokens = mecab_wrapper.tokenize(text, return_list=True)
print(mecab_tokens)

# Sudachi Tokenizer
print("\nSudachi Tokenizer:")
sudachi_tokenizer = dictionary.Dictionary().create()
mode = tokenizer.Tokenizer.SplitMode.C
sudachi_tokens = [m.surface() for m in sudachi_tokenizer.tokenize(text, mode)]
print(sudachi_tokens)

# Juman++ Tokenizer
print("\nJuman++ Tokenizer:")
tokenizer_wrapper = JapaneseTokenizer.JumanppWrapper()
juman_tokens = tokenizer_wrapper.tokenize(text).convert_list_object()
print(juman_tokens)

# KyTea Tokenizer
print("\nKyTea Tokenizer:")
try:
    # Use shell=True to handle input redirection like in a terminal
    result = subprocess.check_output(f"echo '{text}' | kytea", shell=True, text=True)
    kytea_tokens = [token.split('/')[0] for token in result.strip().split()]
    print(kytea_tokens)
except subprocess.CalledProcessError:
    print("KyTea encountered an error.")
except FileNotFoundError:
    print("KyTea not found. Ensure it’s installed and accessible from the command line.")

# Konoha Tokenizers (MeCab, Janome, Sudachi with mode)
konoha_tokenizers = [
    ('MeCab', {}),
    ('Janome', {}),
    ('Sudachi', {"mode": "C"})
]

for tokenizer_name, params in konoha_tokenizers:
    try:
        print(f"\n{tokenizer_name} Tokenizer:")
        tokenizer = konoha.WordTokenizer(tokenizer_name, **params)
        konoha_tokens = [token.surface for token in tokenizer.tokenize(text)]
        print(konoha_tokens)
    except ValueError as ve:
        print(f"Error with {tokenizer_name}: {ve}")
    except Exception as e:
        print(f"Unexpected error with {tokenizer_name}: {e}")

# # Sentencepiece Tokenizer
# print("\nSentencepiece Tokenizer:")
# try:
#     # Load a Sentencepiece model, replace 'sentencepiece.model' with actual model path
#     sp = spm.SentencePieceProcessor(model_file='sentencepiece.model')
#     sentencepiece_tokens = sp.encode(text, out_type=str)
#     print(sentencepiece_tokens)
# except FileNotFoundError:
#     print("Sentencepiece model file not found. Download a model and update `model_file` path.")
# except Exception as e:
#     print(f"Unexpected error with Sentencepiece: {e}")
