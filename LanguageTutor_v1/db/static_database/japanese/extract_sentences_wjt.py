from datasets import load_dataset
import os

# 1) Load the dataset
ds = load_dataset("bennexx/WJTSentDiL", "main_data", split="train")

# 2) Prepare output directory & file handles
os.makedirs("sentences", exist_ok=True)
levels = ["n1","n2","n3","n4","n5"]
files = {
    lvl: open(f"sentences/wjt_{lvl}.txt", "w", encoding="utf-8")
    for lvl in levels
}

# 3) Iterate and write
for ex in ds:
    lvl = ex["level"].lower()
    sent = ex["sentence"].strip()
    if lvl in files:
        files[lvl].write(sent + "\n")

# 4) Clean up
for f in files.values():
    f.close()
