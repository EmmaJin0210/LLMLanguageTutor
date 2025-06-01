#!/usr/bin/env python3
import sqlite3
import re

# Path to your Anki database
DB_PATH = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/sources_jisho_anki/vocab/collection.anki21"

def parse_reading(expression: str, raw_reading: str) -> str:
    """
    If the expression is all katakana (plus long-vowel mark), return it unchanged.
    Otherwise, extract the kana inside […] and any standalone hiragana outside the brackets.
    """
    # Regex for “all katakana” (U+30A0–U+30FF) plus long vowel mark ー
    if re.fullmatch(r'[\u30A0-\u30FFー]+', expression):
        return expression

    result = []
    i = 0
    while i < len(raw_reading):
        ch = raw_reading[i]
        if ch == '[':
            # capture until the next ]
            j = raw_reading.find(']', i)
            if j != -1:
                result.append(raw_reading[i+1:j])
                i = j + 1
                continue
        # if it's hiragana, keep it
        if '\u3040' <= ch <= '\u309F':
            result.append(ch)
        i += 1

    return "".join(result)

def print_readings():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # notes.flds: Expression\x1fEnglish definition\x1fReading…
    cur.execute("SELECT flds FROM notes")
    for (flds,) in cur.fetchall():
        fields     = flds.split('\x1f')
        expression = fields[0].strip()
        raw_reading= fields[2].strip() if len(fields) > 2 else ""
        reading    = parse_reading(expression, raw_reading)
        print(f"{expression}\t→\t{reading}")
    conn.close()

if __name__ == "__main__":
    print_readings()
