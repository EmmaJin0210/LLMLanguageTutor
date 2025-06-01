#!/usr/bin/env python3
import os
import re
import sqlite3
import json
from collections import defaultdict

# Paths
BASE_DIR    = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/sources_jlpt_anki"
LEVEL       = "n4"
DB_PATH     = os.path.join(BASE_DIR, LEVEL, "collection.anki2")
OUTPUT_DIR  = BASE_DIR.replace("sources_jlpt_anki", "jlpt_anki")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"{LEVEL}.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_field(fld: str) -> str:
    """
    Convert <br> to newline, strip HTML tags, and trim whitespace.
    """
    # Replace <br> or <br/> with newline
    t = re.sub(r'(?i)<br\s*/?>', '\n', fld)
    # Remove all other HTML tags
    t = re.sub(r'<[^>]+>', '', t)
    return t.strip()

def split_pieces(raw: str):
    """
    Remove all tildes and split on semicolons, slashes, or Japanese commas.
    """
    s = raw.replace('～', '').replace('~', '')
    return [p.strip() for p in re.split(r'[;\/、]', s) if p.strip()]

def extract_n4():
    vocab = {}
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT flds FROM notes")
    for (flds,) in cur.fetchall():
        raw_fields = flds.split('\x1f')
        # Clean HTML from each field
        fields = [clean_field(f) for f in raw_fields]
        if len(fields) < 2:
            continue

        expr_field = fields[0]
        # Determine meaning: use field[2] if non-empty, else fall back to second field's second line
        if len(fields) > 2 and fields[2].strip():
            meaning = fields[2].strip()
        else:
            parts = [line.strip() for line in fields[1].splitlines() if line.strip()]
            meaning = parts[1] if len(parts) > 1 else ""
        if not expr_field or not meaning:
            continue

        # Split expression into multiple forms if needed
        for expr in split_pieces(expr_field):
            if expr not in vocab:
                vocab[expr] = {"meaning": meaning}

    conn.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=4)
    print(f"Wrote {len(vocab)} entries to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_n4()
