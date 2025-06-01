import json
import re
from LanguageTutor_v1.core.core_utils.language_utils import get_all_levels
from LanguageTutor_v1.core.modules.TokenTokenizer import TokenTokenizer
from LanguageTutor_v1.appstuff.app_constants import ROOT_STATIC_DB

language    = "japanese"
jp_only_re  = re.compile(r'^[\u3040-\u30FF\u31F0-\u31FF\u4E00-\u9FFF]+$')

tt          = TokenTokenizer(language)
all_levels  = get_all_levels(language)

for level in all_levels:
    inpath  = f"{ROOT_STATIC_DB}{language}/sentences/{level}.txt"
    outpath = f"{ROOT_STATIC_DB}{language}/sentences/{level}_tokens.jsonl"
    with open(inpath,  encoding="utf-8") as inf, \
         open(outpath, "w", encoding="utf-8") as outf:
        for line in inf:
            sentence = line.strip()
            toks = tt.sentence_to_tokens(
                sentence=sentence,
                base_form=True,
                filter_punctuation=True
            )
            # filter out any non-JP tokens
            toks = [t for t in toks if jp_only_re.fullmatch(t)]
            json.dump(toks, outf, ensure_ascii=False)
            outf.write("\n")
    print(f"→ cached tokens for {level} → {outpath}")
