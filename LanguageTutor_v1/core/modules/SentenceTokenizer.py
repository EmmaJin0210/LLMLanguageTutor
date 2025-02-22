import sudachipy

class SentenceTokenizer():
    def __init__(self, language):
        self.language = language.lower()
        if self.language == "japanese":
            self.tokenizer = self.init_japanese_tokenizer()

    def init_japanese_tokenizer(self):
        return sudachipy.Dictionary().create()

    def tokenize_sentence(self, sentence):
        if self.language == "japanese":
            tokens = [m.surface() for m in self.tokenizer.tokenize(sentence)]
            return tokens
