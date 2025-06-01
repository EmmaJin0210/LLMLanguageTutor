import asyncio
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from kani.engines.huggingface import HuggingEngine
from kani import ChatMessage, ChatRole
from LanguageTutor_v1.core.kanis.ConversationKani import ConversationKani
from LanguageTutor_v1.core.models.model_constants import MODEL_ID_LM, MODEL_ID_LM_SMALL


# Define the student system prompt.
STUDENT_SYSTEM_PROMPT = (
    "You are a beginner-level student learning Japanese and only know basic expressions. "
    "You are practicing Japanese conversation with a language tutor. "
    "You will have a back-and-forth Japanese conversation with the tutor (user)."
    "You should start by greeting the tutor."
    f"Then, you will talk about your favorite food."
    "Speak one sentence at a time."
)

def main():
    # Load the student model using HuggingEngine.
    # We use half-precision and device_map="auto" to optimize GPU usage.
    engine = HuggingEngine(
        MODEL_ID_LM_SMALL,
        device="cuda",
        tokenizer_kwargs={"trust_remote_code": True},
        model_load_kwargs={
            "trust_remote_code": True,
            "device_map": "auto",
            "torch_dtype": torch.float16,
        }
    )
    # Create a ConversationKani instance for the student.
    # (Here we provide a minimal user profile; adjust as needed.)
    user_profile = {"name": "TestUser"}
    student_conversation = ConversationKani(
        user_profile=user_profile,
        engine=engine,
        system_prompt=STUDENT_SYSTEM_PROMPT,
        desired_response_tokens=15
    )
    # Initialize chat history with the system prompt.
    student_conversation.chat_history = [ChatMessage(role=ChatRole.SYSTEM, content=STUDENT_SYSTEM_PROMPT)]
    
    print("Interactive chat with the student model. Type 'quit' or 'exit' to end.")
    
    loop = asyncio.get_event_loop()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        # Append your input to the chat history.
        student_conversation.chat_history.append(ChatMessage(role=ChatRole.USER, content=user_input))
        # Get the model's response asynchronously.
        response = loop.run_until_complete(engine.predict(messages=student_conversation.chat_history))
        student_reply = response.message.content
        print("Student:", student_reply)
        # Append the model's reply to the history.
        student_conversation.chat_history.append(ChatMessage(role=ChatRole.ASSISTANT, content=student_reply))

if __name__ == "__main__":
    main()
