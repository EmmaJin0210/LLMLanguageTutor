#!/usr/bin/env python3
import os, re, sqlite3, json
from collections import defaultdict

BASE_DIR   = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/sources_shin_kanzen_master"
OUTPUT_DIR = BASE_DIR.replace("sources_shin_kanzen_master", "shin_kanzen_master")

# ───────── regex helpers for the reading filter ─────────
KANJI_RE             = re.compile(r'[\u4E00-\u9FFF]')
HIRAGANA_RE          = re.compile(r'[\u3040-\u309F]')
SINGLE_HIRA_RE       = re.compile(r'^[\u3040-\u309F]$')
TWO_HIRA_RE          = re.compile(r'^[\u3040-\u309F]{2}$')
EXACTLY_ONE_KANJI_RE = re.compile(r'^[\u4E00-\u9FFF]$')

def should_keep_reading(expr: str, rd: str, vocab: dict) -> bool:
    """
    Apply the same ‘no single-hiragana / two-hiragana / etc.’ rules.
    """
    if rd == expr or rd in vocab or SINGLE_HIRA_RE.fullmatch(rd):
        return False

    if not KANJI_RE.search(expr):          # expr has no Kanji → keep any rd
        return True

    mixed   = bool(HIRAGANA_RE.search(expr))
    onekan  = bool(EXACTLY_ONE_KANJI_RE.fullmatch(expr))

    if mixed   and TWO_HIRA_RE.fullmatch(rd):
        return False
    if onekan  and len(HIRAGANA_RE.findall(rd)) <= 2:
        return False
    return True
# ─────────────────────────────────────────────────────────

def parse_reading(expression: str, raw_reading: str) -> str:
    if re.fullmatch(r'[\u30A0-\u30FFー]+', expression):
        return expression

    res, i = [], 0
    while i < len(raw_reading):
        ch = raw_reading[i]
        if ch == '[':
            j = raw_reading.find(']', i)
            if j != -1:
                res.append(raw_reading[i+1:j]); i = j + 1; continue
        if '\u3040' <= ch <= '\u309F':     # hiragana
            res.append(ch)
        i += 1
    return "".join(res)

def extract_level(level: str):
    level_dir = os.path.join(BASE_DIR, level)
    db_path   = os.path.join(level_dir, "collection.anki21")

    vocab = defaultdict(dict)
    cur   = sqlite3.connect(db_path).cursor()
    cur.execute("SELECT flds FROM notes")

    for (flds,) in cur.fetchall():
        fields = flds.split('\x1f')
        if len(fields) < 3:        continue
        expr, raw_read, meaning = (f.strip() for f in fields[:3])
        if not expr or not meaning: continue

        full_rd = parse_reading(expr, raw_read)

        # ── handle expressions with '（…）'
        m = re.search(r'（(.*?)）', expr)
        if m:
            inner = m.group(1)
            expr_base  = re.sub(r'（.*?）', '', expr).strip()
            expr_full  = re.sub(r'[（）]', '', expr).strip()
            rd_base    = full_rd.replace(inner, '', 1)

            # add each expr-form & its reading with filtering
            for e, r in [(expr_base, rd_base), (expr_full, full_rd)]:
                if e and e not in vocab:
                    vocab[e] = {"meaning": meaning}
                if r and should_keep_reading(e, r, vocab):
                    vocab[r] = {"meaning": meaning}
        else:
            # no parentheses
            if expr not in vocab:
                vocab[expr] = {"meaning": meaning}
            if should_keep_reading(expr, full_rd, vocab):
                vocab[full_rd] = {"meaning": meaning}

    # ── dump JSON
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{level}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=4)
    print(f"Wrote {len(vocab)} entries → {out_path}")

def main():
    for name in sorted(os.listdir(BASE_DIR)):
        if re.fullmatch(r"n[1-4]", name):
            extract_level(name)

if __name__ == "__main__":
    main()
