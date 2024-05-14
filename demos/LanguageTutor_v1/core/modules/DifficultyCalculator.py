from core.utils.utils import *

class DifficultyCalculator:
    def __init__(self, grammar_target, grammar_above, vocab_target): # , vocab_above
        self.grammar_target = grammar_target
        self.grammar_above = grammar_above
        self.vocab_target = vocab_target
        # self.vocab_above = vocab_above

    def at_target_difficulty(self, sentence, target_level):
        if len(self.grammar_above) > 0:
            return False
        return True
    def overall_difficulty(self, sentence):
        pass
    def grammar_difficulty(self, sentence):
        pass
    def vocab_difficulty(self, sentence):
        pass