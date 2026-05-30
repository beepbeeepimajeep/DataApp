"""Aggregate Opus production results into the 3 deliverable CSVs.

Reads dataapp_outputs/opus/items.jsonl (535 complete rows) and the 151B
source files. Uses 151B scripts/gold_equiv.gold_equiv for value-equality.

Outputs (all gitignored under dataapp_outputs/opus/):
  1. opus_results.csv            — all 535
  2. anchor_v2_candidates.csv    — 316 anchor rows, opus vs anchor verdict
  3. opus_5th_teacher.csv        — 219 set-B rows, opus vs 4 teachers

qtype derivation (for gold_equiv): MCQ if is_mcq; else free_multi if
n_ans_slots_q>1; else free_single.
"""
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
C = Path.home() / "cse151b/151B_SP26_Competition"
OUT = REPO / "dataapp_outputs/opus"
sys.path.insert(0, str(C))
sys.path.insert(0, str(C / "scripts"))
import gold_equiv as ge

import pandas as pd

# ---- load opus items ----
items = {r["id"]: r for r in (json.loads(l) for l in open(OUT / "items.jsonl") if l.strip())}
target = json.load(open(OUT / "target_535.json"))

# ---- master: qtype derivation ----
master = pd.read_csv(C / "data/master_item_tracker.csv", dtype={"id": str},
                     usecols=["id", "is_mcq", "n_ans_slots_q"])
master["id"] = master["id"].apply(lambda x: str(x).zfill(4))
qtype = {}
for _, row in master.iterrows():
    if row["is_mcq"] == True:  # noqa: E712
        qtype[row["id"]] = "MCQ"
    else:
        try:
            slots = int(float(row["n_ans_slots_q"]))
        except Exception:
            slots = 1
        qtype[row["id"]] = "free_multi" if slots > 1 else "free_single"


def qt(i):
    return qtype.get(i, "free_single")


# ---- 1. opus_results.csv ----
with open(OUT / "opus_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "opus_answer", "n_tokens_output", "wall_time_s",
                "cost_usd", "finish_reason", "caphit_forced", "error"])
    for i in target:
        r = items[i]
        w.writerow([i, r["extracted_raw"] or "", r["usage"]["output"],
                    r["wall_time_s"], r["cost_usd"], r["finish_reason"],
                    r.get("caphit_forced", False), r["error"] or ""])
print("wrote opus_results.csv (%d rows)" % len(target))

# ---- 2. anchor_v2_candidates.csv ----
anchor = pd.read_csv(C / "data/search/teachers/anchor_set_FINAL.csv", dtype={"id": str})
anchor["id"] = anchor["id"].apply(lambda x: str(x).zfill(4))
verdict_counts = {"corroborate": 0, "contradict": 0, "inconclusive": 0}
with open(OUT / "anchor_v2_candidates.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "anchor_answer", "opus_answer", "agree",
                "anchor_tier", "anchor_source", "opus_verdict", "caphit_forced"])
    for _, a in anchor.iterrows():
        i = a["id"]
        opus = items[i]["extracted_raw"] or ""
        agree = ge.gold_equiv(opus, a["answer"], qt(i))
        if agree is True:
            verdict = "corroborate"
        elif agree is False:
            verdict = "contradict"
        else:
            verdict = "inconclusive"
        verdict_counts[verdict] += 1
        w.writerow([i, a["answer"], opus, agree, a["tier"], a["source"],
                    verdict, items[i].get("caphit_forced", False)])
print("wrote anchor_v2_candidates.csv (%d rows)" % len(anchor))
print("  verdicts:", verdict_counts)

# ---- 3. opus_5th_teacher.csv ----
teachers = {}
for t in ["sonnet", "gpt4", "oss", "xhigh"]:
    df = pd.read_csv(C / f"data/search/teachers/{t}/answers.csv", dtype={"id": str})
    df["id"] = df["id"].apply(lambda x: str(x).zfill(4))
    # answers may be NaN (teacher had no answer) -> coerce to "" so gold_equiv is safe
    df["answer"] = df["answer"].apply(lambda x: "" if pd.isna(x) else str(x))
    teachers[t] = dict(zip(df["id"], df["answer"]))

set_b = [i for i in target if i not in set(anchor["id"])]
with open(OUT / "opus_5th_teacher.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "opus_answer", "sonnet_answer", "gpt4_answer",
                "oss_answer", "xhigh_answer", "opus_matches_majority",
                "qtype", "caphit_forced"])
    for i in set_b:
        opus = items[i]["extracted_raw"] or ""
        tans = {t: teachers[t].get(i, "") for t in ["sonnet", "gpt4", "oss", "xhigh"]}
        # majority among teacher answers that opus matches via gold_equiv
        matches = sum(1 for t in tans.values() if ge.gold_equiv(opus, t, qt(i)) is True)
        matches_majority = matches >= 2  # >=2 of 4 teachers agree with opus
        w.writerow([i, opus, tans["sonnet"], tans["gpt4"], tans["oss"],
                    tans["xhigh"], matches_majority, qt(i),
                    items[i].get("caphit_forced", False)])
print("wrote opus_5th_teacher.csv (%d rows)" % len(set_b))
