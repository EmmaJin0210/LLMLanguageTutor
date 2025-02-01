from core.utils.language_utils import *

class DifficultyCalculator:

    def at_target_difficulty(self, above, below):
        if above / (above + below) < 0.1:
            return True
        return False

    def calc_difficulty_score(self, language, above, below):
        score = 0
        for level, tokens in above.items():
            score += get_level_difficulty_score(language, level) * len(tokens)
        for level, tokens in below.items():
            score -= len(tokens) / 5
        return score

    def grammar_difficulty(self, sentence):
        pass
    def vocab_difficulty(self, sentence):
        pass