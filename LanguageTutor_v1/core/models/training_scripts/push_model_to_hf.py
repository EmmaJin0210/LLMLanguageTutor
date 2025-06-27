import os
from huggingface_hub import upload_folder
from dotenv import load_dotenv
from LanguageTutor_v1.core.models.model_constants import ROOT_MODELS

model_output_dir = f"{ROOT_MODELS}modernbert-predictor/checkpoint-280710"
repo_id = "anon/modernbert-predictor"

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

upload_folder(
    folder_path = model_output_dir,
    repo_id=repo_id,
    repo_type = "model",
    token = hf_token
)

print("Pushed model to HuggingFace!")
