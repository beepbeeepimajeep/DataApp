"""
Re-run the 14 xhigh refusal items with a modified MCQ suffix that nudges
the model to pick the closest option rather than refuse.

Safeguards (per CLAUDE.md "Silent provider failures" history):
- Concurrency capped at 4
- Per-request 600s wall-clock timeout
- Output validated: non-zero output_tokens AND contains \boxed{...}
- Smoke 1 item before fan-out

Usage:
    python3 scripts/rerun_xhigh_refusals.py --smoke   # 1 item only
    python3 scripts/rerun_xhigh_refusals.py --all     # remaining 13
"""

import argparse
import concurrent.futures
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.api_clients import GPT55Client
from src.prompts import SYSTEM_PROMPT, SINGLE_ANSWER_SUFFIX, MULTI_ANSWER_SUFFIX, detect_question_type

REFUSAL_IDS = [68, 112, 141, 211, 259, 290, 443, 561, 690, 786, 801, 810, 904, 918]

MCQ_SUFFIX_V2 = """Problem type: multiple choice.

Solve the problem and identify the correct option letter.
If you believe none of the options are exactly correct, pick the one most likely to be graded correct.
End with: \\boxed{Letter}"""

OUT_DIR = "dataapp_outputs/gpt55_rerun_refusals"
os.makedirs(OUT_DIR, exist_ok=True)


def load_items() -> dict:
    items = {}
    with open("private.jsonl") as f:
        for line in f:
            d = json.loads(line)
            iid = int(d.get("id", d.get("item_id", -1)))
            if iid in REFUSAL_IDS:
                items[iid] = d
    return items


def build_messages(item: dict) -> list[dict]:
    qtype = detect_question_type(item)
    q = item.get("question", "")
    if qtype == "mcq":
        opts = item.get("options", []) or []
        labels = [chr(65 + i) for i in range(len(opts))]
        opts_text = "\n".join(f"{lbl}. {opt.strip()}" for lbl, opt in zip(labels, opts))
        user_content = f"{q}\n\nOptions:\n{opts_text}\n\n{MCQ_SUFFIX_V2}"
    elif qtype == "multi_free":
        user_content = f"{q}\n\n{MULTI_ANSWER_SUFFIX}"
    else:
        user_content = f"{q}\n\n{SINGLE_ANSWER_SUFFIX}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ], qtype


def extract_boxed(text: str) -> str:
    matches = list(re.finditer(r"\\boxed\{", text))
    if not matches:
        return ""
    start = matches[-1].end()
    depth, j = 1, start
    while j < len(text) and depth > 0:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[start:j - 1].strip() if depth == 0 else ""


def run_one(iid: int, item: dict, client: GPT55Client) -> dict:
    messages, qtype = build_messages(item)
    t0 = time.time()
    try:
        resp = client.call(
            messages=messages,
            temperature=1.0,
            max_tokens=16000,
            reasoning_effort="xhigh",
        )
    except Exception as e:
        return {"iid": iid, "qtype": qtype, "ok": False, "error": str(e),
                "elapsed_s": time.time() - t0}

    text = resp.get("response", "") or ""
    out_tok = resp.get("output_tokens", 0)
    boxed = extract_boxed(text)
    valid = bool(text) and out_tok > 0 and bool(boxed)

    # Persist full response
    md_path = os.path.join(OUT_DIR, f"item_{iid:04d}_gpt5_5_rerun.md")
    with open(md_path, "w") as f:
        f.write(text)
    meta_path = os.path.join(OUT_DIR, f"item_{iid:04d}_gpt5_5_rerun_meta.json")
    with open(meta_path, "w") as f:
        json.dump({
            "iid": iid,
            "qtype": qtype,
            "input_tokens": resp.get("input_tokens"),
            "output_tokens": out_tok,
            "reasoning_tokens": resp.get("reasoning_tokens"),
            "finish_reason": resp.get("finish_reason"),
            "elapsed_s": time.time() - t0,
            "error": resp.get("error"),
            "boxed": boxed,
            "valid": valid,
        }, f, indent=2)

    return {
        "iid": iid, "qtype": qtype, "ok": valid,
        "boxed": boxed, "out_tok": out_tok,
        "input_tok": resp.get("input_tokens"),
        "reasoning_tok": resp.get("reasoning_tokens"),
        "elapsed_s": time.time() - t0,
        "error": resp.get("error") if not valid else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="Run smoke item only (id 290)")
    ap.add_argument("--all", action="store_true", help="Run remaining items")
    ap.add_argument("--only", type=str, default="", help="Comma-separated item ids")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    if not (args.smoke or args.all or args.only):
        ap.error("Specify --smoke, --all, or --only=ID[,ID...]")

    items = load_items()
    if args.smoke:
        target_ids = [290]  # T1 MCQ refusal — clean test of new MCQ suffix
    elif args.only:
        target_ids = [int(x) for x in args.only.split(",")]
    else:
        target_ids = [i for i in REFUSAL_IDS if i != 290]

    print(f"Running {len(target_ids)} items, concurrency={args.concurrency}")
    print(f"Target IDs: {target_ids}")

    client = GPT55Client()
    results = []
    t_start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        future_to_iid = {ex.submit(run_one, iid, items[iid], client): iid for iid in target_ids}
        for fut in concurrent.futures.as_completed(future_to_iid, timeout=900):
            try:
                r = fut.result(timeout=10)
                results.append(r)
                status = "OK" if r["ok"] else "FAIL"
                print(f"  [{status}] id={r['iid']:>4} qtype={r['qtype']:<11} "
                      f"out_tok={r['out_tok']:>5} elapsed={r['elapsed_s']:>5.1f}s  "
                      f"boxed={r['boxed'][:60]!r}"
                      + (f"  ERROR: {r['error']}" if r.get("error") else ""))
            except Exception as e:
                iid = future_to_iid[fut]
                print(f"  [FUTURE-ERROR] id={iid}: {e}")
                results.append({"iid": iid, "ok": False, "error": f"future: {e}"})

    elapsed = time.time() - t_start
    ok = sum(1 for r in results if r.get("ok"))
    print(f"\nDone: {ok}/{len(results)} valid in {elapsed:.1f}s")

    # Token totals
    total_in = sum(r.get("input_tok") or 0 for r in results)
    total_out = sum(r.get("out_tok") or 0 for r in results)
    total_reason = sum(r.get("reasoning_tok") or 0 for r in results)
    print(f"Tokens: input={total_in}, output={total_out}, reasoning={total_reason}")

    # Save summary
    summary_path = os.path.join(OUT_DIR, "rerun_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            prior = json.load(f)
    else:
        prior = {"runs": []}
    prior["runs"].append({
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "smoke" if args.smoke else "all",
        "results": results,
        "elapsed_s": elapsed,
        "totals": {"input_tokens": total_in, "output_tokens": total_out,
                   "reasoning_tokens": total_reason},
    })
    with open(summary_path, "w") as f:
        json.dump(prior, f, indent=2)
    print(f"Summary saved → {summary_path}")


if __name__ == "__main__":
    main()
