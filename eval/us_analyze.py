import os
import json
import matplotlib.pyplot as plt

# -----------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------
LOG_DIR = "eval/user_study_logs"        # folder with your *_tok.json logs
OUT_DIR = LOG_DIR                       # where to save summary + graphs
METRICS = [
    "percent_not_understood",
    "ave_num_tokens",
    "ave_hard_tokens",
    "percent_hard_tokens",
]

# -----------------------------------------------------------------
# Small helpers (no external package dependence)
# -----------------------------------------------------------------
def read_json_to_dict(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def new_stats() -> dict:
    return {
        "rounds": 0,
        "understood_false_cnt": 0,
        "sum_tokens_per_round": 0,
        "sum_hard_per_round": 0,
        "total_tokens": 0,
        "total_hard_tokens": 0,
    }

def add_round(stats: dict, rnd: dict) -> None:
    understood = rnd.get("understood", False)
    n_tokens = len(rnd.get("student_tokens", [])) + len(rnd.get("tutor_tokens", []))
    n_hard   = len(rnd.get("hard_tokens", []))

    stats["rounds"]               += 1
    stats["understood_false_cnt"] += int(not understood)
    stats["sum_tokens_per_round"] += n_tokens
    stats["sum_hard_per_round"]   += n_hard
    stats["total_tokens"]         += n_tokens
    stats["total_hard_tokens"]    += n_hard

def finalize(raw: dict) -> dict:
    rounds = max(raw["rounds"], 1)
    tot    = max(raw["total_tokens"], 1)
    return {
        "percent_not_understood":  raw["understood_false_cnt"] / rounds,
        "ave_num_tokens":      raw["sum_tokens_per_round"] / rounds,
        "ave_hard_tokens":     raw["sum_hard_per_round"]  / rounds,
        "percent_hard_tokens": raw["total_hard_tokens"] / tot,
    }

def plot_bar(labels, values, title, ylabel, fname):
    plt.figure(figsize=(8, 4))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, fname), dpi=300)
    plt.close()

# -----------------------------------------------------------------
# AGGREGATION
# -----------------------------------------------------------------
summary: dict[str, dict] = {}

for file in os.listdir(LOG_DIR):
    if not file.endswith(".json"):
        continue

    data    = read_json_to_dict(os.path.join(LOG_DIR, file))
    engine  = data.get("engine", "unknown")
    level   = data.get("level",  "unknown").lower()

    eng = summary.setdefault(
        engine,
        {"error_cnt_major": 0, "error_cnt_minor": 0, "_TOTAL": new_stats()},
    )
    eng.setdefault(level, new_stats())

    for rnd in data.get("script", []):
        eflag = rnd.get("error", "").lower()
        if eflag == "major":
            eng["error_cnt_major"] += 1
            continue          # skip metrics
        if eflag == "minor":
            eng["error_cnt_minor"] += 1

        add_round(eng[level], rnd)
        add_round(eng["_TOTAL"], rnd)

# convert raw counters to final metrics
for eng_dict in summary.values():
    for key, raw in list(eng_dict.items()):
        if isinstance(raw, dict) and "rounds" in raw:
            eng_dict[key] = finalize(raw)

# -----------------------------------------------------------------
# SAVE + PRINT SUMMARY
# -----------------------------------------------------------------
summary_path = os.path.join(OUT_DIR, "engine_level_summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# Pretty-print to console (unchanged behaviour)
print(json.dumps(summary, ensure_ascii=False, indent=2))

# -----------------------------------------------------------------
# PLOT GRAPHS
# -----------------------------------------------------------------
# 1. Metric by engine (all levels combined)
for metric in METRICS:
    engines = list(summary.keys())
    vals    = [summary[e]["_TOTAL"][metric] for e in engines]
    plot_bar(
        engines, vals,
        f"{metric} by engine (all levels)",
        metric,
        f"{metric}_by_engine.png",
    )

# 2. Metric by level for each engine
for eng, eng_dict in summary.items():
    levels = [k for k in eng_dict if k not in ("_TOTAL", "error_cnt_major", "error_cnt_minor")]
    for metric in METRICS:
        vals = [eng_dict[lvl][metric] for lvl in levels]
        if not vals:
            continue
        plot_bar(
            levels, vals,
            f"{metric} for {eng} by level",
            metric,
            f"{metric}_{eng}_by_level.png",
        )

print("Summary written to:", summary_path)
print("Graphs saved in   :", OUT_DIR)
