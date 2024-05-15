from kani import Kani, AIParam, ai_function
from typing import Annotated
from core.utils.utils import *

class LearningKani(Kani):

    def __init__(self, user_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_profile = user_profile