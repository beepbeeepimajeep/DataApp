"""Rerun cap-hit items via constrained continuation.

The 13 cap-hit items maxed 32K output with no \\boxed and high reasoning churn
(cut off mid-exploration). 32K is the model max, so we cannot raise the cap.
Fix: feed the original prompt + the truncated reasoning back as an assistant
turn, then a user message instructing Opus to STOP reasoning and commit to its
single best answer as \\boxed{...}. Small max_tokens (2048) so it can't re-cap.

Updates the cap-hit rows in items.jsonl in place:
  - response_truncated  = the original 32K truncated trace (preserved for SFT)
  - response_full       = the continuation's boxed answer text
  - extracted_raw       = last_boxed/remove_boxed of the continuation
  - finish_reason       = continuation's stop_reason
  - caphit_forced       = True  (downstream should treat as lower-confidence)
  - usage/cost          = original + continuation summed

Run: ~/cse151b/151B_SP26_Competition/.venv/bin/python scripts/rerun_caphits.py
"""
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from dotenv import load_dotenv
load_dotenv(REPO / ".env")
from src.api_clients import OpusClient
from src.extraction import last_boxed_only_string, remove_boxed

C = Path.home() / "cse151b/151B_SP26_Competition"
TEACHER_DIR = C / "data/search/teachers/sonnet"
OUT = REPO / "dataapp_outputs/opus"
ITEMS = OUT / "items.jsonl"
PRICE_IN = 5.0 / 1_000_000
PRICE_OUT = 25.0 / 1_000_000

CONTINUE_MSG = (
    "Your reasoning above was cut off before you finished. Do NOT start over "
    "and do NOT continue exploring. Based on the work you have already done, "
    "commit to your single best final answer now. Output ONLY the final answer "
    "as \\boxed{...} with nothing else."
)


def extract_raw(t):
    return remove_boxed(last_boxed_only_string(t))


def read_prompt(item_id):
    text = (TEACHER_DIR / f"item_{item_id}.md").read_text()
    after = text.split("## Prompt", 1)[1]
    fo = after.index("```") + 3
    nl = after.index("\n", fo)
    fc = after.index("```", nl)
    return after[nl + 1:fc].rstrip("\n")


def main():
    caps = json.load(open(OUT / "caphit_ids.json"))
    rows = [json.loads(l) for l in open(ITEMS) if l.strip()]
    by_id = {r["id"]: r for r in rows}
    client = OpusClient(model="claude-opus-4-7")

    for iid in caps:
        orig = by_id[iid]
        if orig.get("caphit_forced"):
            print(f"{iid}: already rerun, skip")
            continue
        prompt = read_prompt(iid)
        truncated = orig["response_full"]
        msgs = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": truncated},
            {"role": "user", "content": CONTINUE_MSG},
        ]
        t0 = time.time()
        res = client.call(messages=msgs, max_tokens=2048)
        raw = extract_raw(res["response"])
        cont_cost = res["input_tokens"] * PRICE_IN + res["output_tokens"] * PRICE_OUT

        orig["response_truncated"] = truncated
        orig["response_full"] = res["response"]
        orig["extracted_raw"] = raw
        orig["finish_reason"] = res["finish_reason"]
        orig["caphit_forced"] = True
        orig["usage"] = {
            "input": orig["usage"]["input"] + res["input_tokens"],
            "output": orig["usage"]["output"] + res["output_tokens"],
        }
        orig["cost_usd"] = round(orig["cost_usd"] + cont_cost, 6)
        orig["wall_time_s"] = round(orig["wall_time_s"] + (time.time() - t0), 2)
        orig["request_id_continuation"] = res["request_id"]
        orig["error"] = res["error"]
        print(f"{iid}: raw={raw!r} finish={res['finish_reason']} "
              f"cont_out={res['output_tokens']} cost+=${cont_cost:.4f} err={res['error']}")

    # rewrite items.jsonl atomically, preserving original order
    tmp = ITEMS.with_suffix(".jsonl.tmp")
    with open(tmp, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    tmp.replace(ITEMS)
    still_empty = [r["id"] for r in rows if not r["extracted_raw"]]
    print(f"\nrewrote {ITEMS} ({len(rows)} rows). still empty: {len(still_empty)} {still_empty}")


if __name__ == "__main__":
    main()
