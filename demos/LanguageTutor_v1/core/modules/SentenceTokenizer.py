import JapaneseTokenizer


class SentenceTokenizer():
    def __init__(self, language):
        self.language = language.lower()
        if self.language == "japanese":
            self.tokenizer = self.init_japanese_tokenizer()

    def init_japanese_tokenizer(self):
        dict_type = "ipadic"
        return JapaneseTokenizer.MecabWrapper(dictType=dict_type)

    def tokenize_sentence(self, sentence):
        if self.language == "japanese":
            tokens = self.tokenizer.tokenize(sentence, return_list=True)
            # tokenized_sentence = mecab_wrapper.tokenize(text)
            # for i, obj in enumerate(tokenized_sentence.tokenized_objects):
            #     print(tokens[i], obj.tuple_pos)
            return tokens