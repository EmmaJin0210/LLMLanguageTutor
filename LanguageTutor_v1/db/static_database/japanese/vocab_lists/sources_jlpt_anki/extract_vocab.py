#!/usr/bin/env python3
import os
import re
import sqlite3
import json
from collections import defaultdict

BASE_DIR   = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/sources_jlpt_anki"
OUTPUT_DIR = BASE_DIR.replace("sources_jlpt_anki", "jlpt_anki")

def split_pieces(raw: str):
    """
    Remove all tildes and split on semicolons, commas, slashes, or Japanese commas.
    """
    s = raw.replace('～', '').replace('~', '')
    return [p.strip() for p in re.split(r'[;、/]', s) if p.strip()]

def extract_level(level: str):
    level_dir = os.path.join(BASE_DIR, level)
    db_path   = os.path.join(level_dir, "collection.anki2")  # or .anki21

    vocab = {}
    conn  = sqlite3.connect(db_path)
    cur   = conn.cursor()
    cur.execute("SELECT flds FROM notes")
    for (flds,) in cur.fetchall():
        fields      = flds.split('\x1f')
        if len(fields) < 3:
            continue
        raw_expr    = fields[0].strip()
        meaning     = fields[2].strip()
        if not raw_expr or not meaning:
            continue

        # split the expression into pieces
        exprs = split_pieces(raw_expr)
        for expr in exprs:
            # add each expr only once
            if expr not in vocab:
                vocab[expr] = {"meaning": meaning}

    conn.close()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{level}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=4)
    print(f"Wrote {len(vocab)} entries to {out_path}")

def main():
    for name in sorted(os.listdir(BASE_DIR)):
        if re.fullmatch(r"n[1-5]", name):
            extract_level(name)

if __name__ == "__main__":
    main()
