#!/usr/bin/env python3
import sqlite3
import json
import re
import os
from collections import defaultdict

TARGET_FOLDER = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/jisho_anki/hardest"
DB_PATH       = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/sources_jisho_anki/vocab/collection.anki21"

def parse_reading(expression: str, raw_reading: str) -> str:
    """
    If expression is all katakana (plus 長音符), return it unchanged.
    Otherwise, extract kana inside […] and standalone hiragana outside.
    """
    if re.fullmatch(r'[\u30A0-\u30FFー]+', expression):
        return expression

    result = []
    i = 0
    while i < len(raw_reading):
        ch = raw_reading[i]
        if ch == '[':
            j = raw_reading.find(']', i)
            if j != -1:
                result.append(raw_reading[i+1:j])
                i = j + 1
                continue
        if '\u3040' <= ch <= '\u309F':
            result.append(ch)
        i += 1
    return "".join(result)

def get_hardest_level(deck_name: str) -> str:
    levels = re.findall(r'JLPT N[1-5]', deck_name)
    if not levels:
        return None
    # pick the hardest (lowest number)
    return sorted(levels, key=lambda s: int(s[-1]))[0]

def jlpt_tag_to_filename(jlpt_tag: str) -> str:
    # "JLPT N3" → "n3"
    return f"n{jlpt_tag[-1]}"

def load_deck_map(cursor) -> dict:
    cursor.execute("SELECT decks FROM col")
    decks = json.loads(cursor.fetchone()[0])
    return {int(k): v["name"] for k, v in decks.items()}

def main():
    os.makedirs(TARGET_FOLDER, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    deck_map = load_deck_map(cur)

    vocab = defaultdict(dict)
    cur.execute("""
        SELECT n.flds, c.did
        FROM notes n
        JOIN cards c ON n.id = c.nid
    """)
    for flds, did in cur.fetchall():
        fields      = flds.split('\x1f')
        if len(fields) < 3:
            continue
        expression  = fields[0].strip()
        meaning     = fields[1].strip()
        raw_reading = fields[2].strip()
        deck_name   = deck_map.get(did, "")
        jlpt        = get_hardest_level(deck_name)
        if not jlpt:
            continue
        fn = jlpt_tag_to_filename(jlpt)

        # add the surface form
        if expression not in vocab[fn]:
            vocab[fn][expression] = {"meaning": meaning}

        # parse and add the reading if distinct
        reading = parse_reading(expression, raw_reading)
        if reading and reading != expression and reading not in vocab[fn]:
            vocab[fn][reading] = {"meaning": meaning}

    conn.close()

    # write out n1.json … n5.json
    for level in ["n1", "n2", "n3", "n4", "n5"]:
        data = vocab.get(level, {})
        path = os.path.join(TARGET_FOLDER, f"{level}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
