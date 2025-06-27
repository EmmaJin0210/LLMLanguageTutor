#!/usr/bin/env python3
import os, re, sqlite3, json
from collections import defaultdict

BASE_DIR   = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/sources_jlpt_anki"
OUTPUT_DIR = BASE_DIR.replace("sources_jlpt_anki", "jlpt_anki_with_reading")

KANJI_RE             = re.compile(r'[\u4E00-\u9FFF]')
HIRAGANA_RE          = re.compile(r'[\u3040-\u309F]')
SINGLE_HIRA_RE       = re.compile(r'^[\u3040-\u309F]$')
TWO_HIRA_RE          = re.compile(r'^[\u3040-\u309F]{2}$')
EXACTLY_ONE_KANJI_RE = re.compile(r'^[\u4E00-\u9FFF]$')

PAREN_MAP = str.maketrans({"（": "(", "）": ")", "\uFE59": "(", "\uFE5A": ")"})
TILDE_RE  = re.compile(r"[\u007E\uFF5E\u301C\u02DC\u3030]")

def expand_parentheses(s: str) -> list[str]:
    s = TILDE_RE.sub("", s.translate(PAREN_MAP)).strip()
    o = s.find("(")
    c = s.find(")", o + 1)
    if o == -1 or c == -1:
        return [s]
    before, inside, after = s[:o].strip(), s[o+1:c].strip(), s[c+1:].strip()
    outside     = f"{before} {after}".strip()
    inside_full = f"{before}{inside}{after}".strip()
    return [outside, inside_full]

def split_pieces(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;/、]", s) if p.strip()]

def extract_level(level: str):
    level_dir = os.path.join(BASE_DIR, level)
    cur = sqlite3.connect(os.path.join(level_dir, "collection.anki2")).cursor()
    cur.execute("SELECT flds FROM notes")

    vocab = defaultdict(dict)
    for (flds,) in cur.fetchall():
        expr_raw, read_raw, meaning, *_ = flds.split('\x1f') + ["", "", ""]
        if not expr_raw.strip() or not meaning.strip():
            continue

        # expressions
        exprs = []
        for v in expand_parentheses(expr_raw):
            exprs.extend(split_pieces(v))

        # readings  (← NEW: expand parens here too)
        readings = []
        for rd in split_pieces(read_raw):
            readings.extend(expand_parentheses(rd))

        for expr in exprs:
            vocab.setdefault(expr, {"meaning": meaning})
            if not KANJI_RE.search(expr):
                continue

            mixed  = bool(HIRAGANA_RE.search(expr))
            onekan = bool(EXACTLY_ONE_KANJI_RE.fullmatch(expr))

            for rd in readings:
                if (rd == expr or rd in vocab or
                    SINGLE_HIRA_RE.fullmatch(rd) or
                    (mixed and TWO_HIRA_RE.fullmatch(rd)) or
                    (onekan and len(HIRAGANA_RE.findall(rd)) <= 2)):
                    continue
                vocab[rd] = {"meaning": meaning}

    out = os.path.join(OUTPUT_DIR, f"{level}.json")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=4, sort_keys=True)
    print(f"[{level}] wrote {len(vocab):,} entries → {out}")

def main():
    for lv in sorted(os.listdir(BASE_DIR)):
        if re.fullmatch(r"n[1-5]", lv):
            extract_level(lv)

if __name__ == "__main__":
    main()
