import requests
from bs4 import BeautifulSoup
import json
import os
import re

# Levels in order N5 → N1
LEVELS   = ["N5", "N4", "N3", "N2", "N1"]
BASE_URL = "https://en.wiktionary.org/wiki/Appendix:JLPT/{}"
OUT_DIR  = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/wiki"
os.makedirs(OUT_DIR, exist_ok=True)

# ───────────── reading-filter helpers (same rules as before) ─────────────
KANJI_RE             = re.compile(r'[\u4E00-\u9FFF]')
HIRAGANA_RE          = re.compile(r'[\u3040-\u309F]')
SINGLE_HIRA_RE       = re.compile(r'^[\u3040-\u309F]$')
TWO_HIRA_RE          = re.compile(r'^[\u3040-\u309F]{2}$')
EXACTLY_ONE_KANJI_RE = re.compile(r'^[\u4E00-\u9FFF]$')

def keep_reading(expr: str, rd: str, vocab: dict) -> bool:
    if rd == expr or rd in vocab or SINGLE_HIRA_RE.fullmatch(rd):
        return False
    if not KANJI_RE.search(expr):                # expr has no Kanji
        return True
    mixed  = bool(HIRAGANA_RE.search(expr))
    onekan = bool(EXACTLY_ONE_KANJI_RE.fullmatch(expr))
    if mixed  and TWO_HIRA_RE.fullmatch(rd):
        return False
    if onekan and len(HIRAGANA_RE.findall(rd)) <= 2:
        return False
    return True
# ────────────────────────────────────────────────────────────────────────

for lvl in LEVELS:
    url  = BASE_URL.format(lvl)
    soup = BeautifulSoup(requests.get(url).text, "lxml")

    vocab = {}
    for table in soup.find_all("table", class_="wikitable"):
        header = table.find("tr")
        cols   = [th.get_text(strip=True) for th in header.find_all("th")]
        if cols[:3] != ["Kanji", "Reading", "Meaning"]:
            continue

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            kanji   = cells[0].get_text(strip=True)
            reading = cells[1].get_text(strip=True)
            meaning = cells[2].get_text(strip=True)
            if not kanji or not meaning:
                continue

            # add the kanji form
            vocab.setdefault(kanji, {"meaning": meaning})

            # add reading only if it passes the filter
            if reading and keep_reading(kanji, reading, vocab):
                vocab[reading] = {"meaning": meaning}

    filename = f"n{lvl[1].lower()}.json"
    with open(os.path.join(OUT_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)
    print(f"{lvl}: {len(vocab)} entries → {os.path.join(OUT_DIR, filename)}")
