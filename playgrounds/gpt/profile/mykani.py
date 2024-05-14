from kani import Kani, AIParam, ai_function
from typing import Annotated


class MyKani(Kani):
    @ai_function()
    def store_user_info(
        self,
        info: Annotated[str, AIParam(desc="any info about the user that you think will be useful or relavant for future lessons, in a key: value format")],
    ):
        """Store any information about the user that you think will be useful or relavant in future conversations, such as their name,
        topics that they are interested in, etc. Store things in a key: value format.
        """
        print("info: ", info)

    @ai_function()
    def store_general_interests(
        self,
        interest: Annotated[str, AIParam(desc="An interest that the user mentioned, in a format that you think will be easy to store and look up in the future")],
    ):
        """Store the user's general interest when they mention it in a conversation.
        Return it in a format that you think will be easy to store and look up in the future.
        """
        return "User's general interest stored: " + interest
    
    @ai_function()
    def store_specific_interests(
        self,
        general_interest: Annotated[str, AIParam(desc="A general interest category that the specific interest belongs to")],
        specific_interest: Annotated[str, AIParam(desc="User's specific interests")],
    ):
        """If the user mentions a more specific interest, store the user's more specific interests under a general interest.
        For example, if they say "I like Taylor Swift's Love Story", then store "Taylor Swift's Love Story"
        under the general interest "music"
        """
        return specific_interest + " in " + general_interest
    # TODO:
    # how does function call return get incorporated into context
    # Evaluate grammar correctness
    # subkani that checks for sentence correctness
    @ai_function
    def detect_grammar_mistake(
        self,
        mistake_made: Annotated[str, AIParam(desc="description of the exact mistake the user made")],
        grammar_point: Annotated[str, AIParam(desc="the grammar point corresponding to the mistake the user made")],
    ):
        """ If a grammar mistake is detected, put into words what mistake the user made.
        """
        return "mistake made: " + mistake_made + "\ngrammar point: " + grammar_point
    

    # @ai_function
    # def retrieve_info_from_user_profile(
    #     self,
    #     info_to_retrieve: Annotated[str, AIParam(desc="info you want to retrieve, such as the user's interests, grammar mistakes the user made in the past, etc.")],
    # ):
    #     """retrieve user info when you and the user are moving on to a new topic!
    #     You have access to the profile of the user that can provide info about the user. If you want to retrieve some info about the user that you think would be useful to the conversation,
    #     specify the info you want to retrieve and call this function.
    #     """
    #     return "info to retrieve: " + info_to_retrieve

    @ai_function
    def move_to_new_topic(
        self,
        old_topic: Annotated[str, AIParam(desc="old topic that you and the user were discussing")],
        new_topic: Annotated[str, AIParam(desc="new topic that you and the user are discussing or are going to discuss")]
    ):
        """When transitioning to a new topic, print out both the old topic and new topic
        """
        return "old topic: " + old_topic + "\nnew topic: " + new_topic
    ### few-shot prompting function-calling

