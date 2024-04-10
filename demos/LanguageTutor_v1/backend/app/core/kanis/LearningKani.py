from kani import Kani, AIParam, ai_function
from typing import Annotated
from demos.LanguageTutor_v1.backend.app.core.utils import *
from GrammarDetector import GrammarDetector

class LearningKani(Kani):
    @ai_function()
    def call_every_round(
        self,
        user_input: Annotated[str, AIParam(desc="The entire input from the user")],
    ):
        """In every single round, get the entire input from the user.
        Then, use the grammar detector to detect what grammar points are used in the input
        """
        return user_input