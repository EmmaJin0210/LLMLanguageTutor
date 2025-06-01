#!/usr/bin/env python3
import os
import re
import sqlite3
import json
from collections import defaultdict

BASE_DIR    = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/sources_jlpt_anki"
LEVEL       = "n4"
DB_PATH     = os.path.join(BASE_DIR, LEVEL, "collection.anki2")
OUTPUT_DIR  = BASE_DIR.replace("sources_jlpt_anki", "jlpt_anki_with_reading")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"{LEVEL}.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────── regex helpers ───────────
KANJI_RE             = re.compile(r'[\u4E00-\u9FFF]')
HIRAGANA_RE          = re.compile(r'[\u3040-\u309F]')
SINGLE_HIRAGANA_RE   = re.compile(r'^[\u3040-\u309F]$')
TWO_HIRAGANA_RE      = re.compile(r'^[\u3040-\u309F]{2}$')
EXACTLY_ONE_KANJI_RE = re.compile(r'^[\u4E00-\u9FFF]$')

# full-width → ASCII parens
PAREN_MAP = str.maketrans({"（": "(", "）": ")"})

# ─────────── tiny helpers ───────────
def clean_field(fld: str) -> str:
    fld = re.sub(r'(?i)<br\s*/?>', '\n', fld)
    fld = re.sub(r'<[^>]+>', '', fld)
    return fld.strip()

def split_pieces(raw: str):
    """Remove tildes (~, ～) and split on ; / 、."""
    s = raw.replace('～', '').replace('~', '')
    return [p.strip() for p in re.split(r'[;/、]', s) if p.strip()]

def expand_parentheses(s: str):
    """
    If one '( … )' exists anywhere, return [outside, inside_full],
    else [s] as-is.  No tilde handling here – split_pieces will do that.
    """
    s = s.translate(PAREN_MAP).strip()
    o, c = s.find("("), s.find(")", s.find("(") + 1)
    if o == -1 or c == -1:
        return [s]
    before, inside, after = s[:o].strip(), s[o+1:c].strip(), s[c+1:].strip()
    outside     = f"{before} {after}".strip()
    inside_full = f"{before}{inside}{after}".strip()
    return [outside, inside_full]

# ─────────── main extraction ───────────
def extract_n4():
    vocab = defaultdict(dict)
    conn  = sqlite3.connect(DB_PATH)
    cur   = conn.cursor()
    cur.execute("SELECT flds FROM notes")

    for (flds,) in cur.fetchall():
        fields = [clean_field(f) for f in flds.split('\x1f')]
        if len(fields) < 2:
            continue

        expr_field, reading_field = fields[:2]
        # pick out meaning & raw_reading
        if len(fields) > 2 and fields[2].strip():
            raw_reading = reading_field
            meaning     = fields[2].strip()
        else:
            parts = [ln.strip() for ln in reading_field.splitlines() if ln.strip()]
            if len(parts) < 2:
                continue
            raw_reading, meaning = parts[:2]

        # ── apply paren-expansion FIRST, then the original split_pieces
        exprs = []
        for v in expand_parentheses(expr_field):
            exprs.extend(split_pieces(v))

        readings = []
        for v in expand_parentheses(raw_reading):
            readings.extend(split_pieces(v))

        for expr in exprs:
            vocab.setdefault(expr, {"meaning": meaning})

            if not KANJI_RE.search(expr):
                continue  # only attach readings to Kanji-containing exprs

            is_mixed     = bool(HIRAGANA_RE.search(expr))
            is_one_kanji = bool(EXACTLY_ONE_KANJI_RE.match(expr))

            for rd in readings:
                if (rd == expr or rd in vocab or SINGLE_HIRAGANA_RE.match(rd) or
                    (is_mixed and TWO_HIRAGANA_RE.match(rd)) or
                    (is_one_kanji and len(HIRAGANA_RE.findall(rd)) <= 2)):
                    continue
                vocab[rd] = {"meaning": meaning}

    conn.close()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=4)
    print(f"Wrote {len(vocab)} entries to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_n4()
