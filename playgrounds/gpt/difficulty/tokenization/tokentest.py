import JapaneseTokenizer
import Levenshtein as lev


def calc_levenshtein_similarity(self, word1, word2):
    distance = lev.distance(word1, word2)
    similarity = 1 - distance / max(len(word1), len(word2))
    return similarity

# Choose a dictionary type, for example 'ipadic'
dict_type = 'ipadic'

# Initialize Mecab tokenizer with specified dictionary type
mecab_wrapper = JapaneseTokenizer.MecabWrapper(dictType=dict_type)

# Example text
text = '推理小説、面白い選択ですね！それなら、日本の作家である東野圭吾さんの作品を読んだことはありますか？彼の推理小説はとても人気がありますよ。'

# Tokenize text
tokens = mecab_wrapper.tokenize(text, return_list=True)
print(tokens)
tokenized_sentence = mecab_wrapper.tokenize(text)
for i, obj in enumerate(tokenized_sentence.tokenized_objects):
    print(tokens[i], obj.tuple_pos)

# import JapaneseTokenizer

# # Initialize your chosen tokenizer, for example Juman++
# tokenizer_wrapper = JapaneseTokenizer.JumanppWrapper()

# # Example text
# text = '今日は非常に良い日です。'

# # Tokenize text
# tokenized_sentence = tokenizer_wrapper.tokenize(text)
# tokens = tokenized_sentence.convert_list_object()
# for i, obj in enumerate(tokenized_sentence.tokenized_objects):
#     print(tokens[i], obj.tuple_pos)







