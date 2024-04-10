from kani import Kani, AIParam, ai_function
from typing import Annotated
from utils import *


class ConversationKani(Kani):
    @ai_function()
    def stub_function(
        self,
        user_input: Annotated[str, AIParam(desc="The entire input from the user")],
    ):
        """In every single round, get the entire input from the user.
        Then, use the grammar detector to detect what grammar points are used in the input
        """
        pass