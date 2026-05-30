"""
Opus 4.7 client smoke test. Standalone — does NOT invoke the orchestrator.

Extraction convention (151B RAW, NOT DataApp normalize-during-extract):
  - pull response text
  - apply last_boxed_only_string + remove_boxed ONLY
  - do NOT call normalize_answer() at any point
  - store the raw extracted string

Agreement check uses normalize_for_comparison ONLY for comparison
(never stored). Item passes if
normalize_for_comparison(extracted_raw) == normalize_for_comparison(expected).

Usage:
    python scripts/smoke_opus.py --phase 0      # hello-world
    python scripts/smoke_opus.py --phase 3      # 5-item serial
    python scripts/smoke_opus.py --phase 4      # 5-item concurrent
    python scripts/smoke_opus.py --phase 5      # forced-error retry
    python scripts/smoke_opus.py --phase all --out results.json
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv
load_dotenv(REPO / ".env")

from src.api_clients import OpusClient
from src.extraction import (
    last_boxed_only_string,
    remove_boxed,
    normalize_for_comparison,
)

MODEL = "claude-opus-4-7"
# Opus 4.7 deprecated `temperature` (any value -> HTTP 400 with no thinking).
# OpusClient does not forward this arg; kept only for cross-client signature
# compatibility. LOCKED Option 1: no thinking, no temperature, 32K, streaming.
TEMP = None
MAX_TOKENS = 32768

# Anthropic Opus 4.x pricing (per A6): input $5/M, output $25/M
PRICE_IN = 5.0 / 1_000_000
PRICE_OUT = 25.0 / 1_000_000

TEACHER_DIR = Path.home() / "cse151b/151B_SP26_Competition/data/search/teachers/sonnet"

ITEMS = [
    ("0017", "MCQ_single", "A+", "C"),
    ("0019", "MCQ_single", "A", "E"),
    ("0041", "FREE_num", "A+", "2112"),
    ("0285", "FREE_num", "A", "735"),
    ("0451", "FREE_multi-6", "A",
     "0.1290,0.1935,0.2097,14,0.1774,0.06452"),
]


def extract_raw(response_text: str):
    """151B raw convention: last_boxed_only_string + remove_boxed ONLY.
    No normalize_answer. Returns raw inner string or None."""
    boxed = last_boxed_only_string(response_text)
    return remove_boxed(boxed)


def read_prompt(item_id: str) -> str:
    """Pull the ## Prompt fenced block from a teacher file, strip fences."""
    text = (TEACHER_DIR / f"item_{item_id}.md").read_text()
    after = text.split("## Prompt", 1)[1]
    fence_open = after.index("```") + 3
    nl = after.index("\n", fence_open)          # skip optional lang token
    fence_close = after.index("```", nl)
    return after[nl + 1:fence_close].rstrip("\n")


def cost_of(result: dict) -> float:
    return result["input_tokens"] * PRICE_IN + result["output_tokens"] * PRICE_OUT


def run_item(client: OpusClient, item_id: str, expected: str) -> dict:
    prompt = read_prompt(item_id)
    res = client.call(
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMP,
        max_tokens=MAX_TOKENS,
    )
    raw = extract_raw(res["response"])
    agree = (
        raw is not None
        and normalize_for_comparison(raw) == normalize_for_comparison(expected)
    )
    return {
        "id": item_id,
        "expected": expected,
        "extracted_raw": raw,
        "agree": agree,
        "input_tokens": res["input_tokens"],
        "output_tokens": res["output_tokens"],
        "hit_token_cap": res["hit_token_cap"],
        "finish_reason": res["finish_reason"],
        "generation_time_s": res["generation_time_s"],
        "error": res["error"],
        "cost": cost_of(res),
        "response": res["response"],
    }


def phase0(client):
    print("=== PHASE 0: hello-world ===")
    res = client.call(
        messages=[{"role": "user", "content": "What is 2+2? Just the number."}],
        temperature=TEMP, max_tokens=100,
    )
    ok = "4" in res["response"]
    print(f"  response={res['response']!r}  pass={ok}  err={res['error']}")
    print(f"  cost=${cost_of(res):.6f}")
    return {"phase": 0, "pass": ok, "response": res["response"],
            "cost": cost_of(res), "error": res["error"]}


def phase3(client):
    print("=== PHASE 3: 5-item serial ===")
    t0 = time.time()
    rows = [run_item(client, i, exp) for i, _t, _tier, exp in ITEMS]
    wall = time.time() - t0
    for r in rows:
        print(f"  {r['id']} exp={r['expected']!r} raw={r['extracted_raw']!r} "
              f"agree={r['agree']} cap={r['hit_token_cap']} "
              f"out_tok={r['output_tokens']} t={r['generation_time_s']:.1f}s")
    n_agree = sum(r["agree"] for r in rows)
    print(f"  serial wall={wall:.1f}s  agree={n_agree}/5  "
          f"cost=${sum(r['cost'] for r in rows):.4f}")
    return {"phase": 3, "wall_s": wall, "n_agree": n_agree, "rows": rows}


def phase4(client):
    print("=== PHASE 4: 5-item concurrent (max_workers=5) ===")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(run_item, client, i, exp)
                for i, _t, _tier, exp in ITEMS]
        rows = [f.result() for f in futs]
    wall = time.time() - t0
    rows.sort(key=lambda r: r["id"])
    for r in rows:
        print(f"  {r['id']} raw={r['extracted_raw']!r} agree={r['agree']} "
              f"err={r['error']}")
    n_done = sum(r["error"] is None for r in rows)
    print(f"  concurrent wall={wall:.1f}s  completed={n_done}/5  "
          f"cost=${sum(r['cost'] for r in rows):.4f}")
    return {"phase": 4, "wall_s": wall, "n_done": n_done, "rows": rows}


def phase5():
    print("=== PHASE 5: forced-error retry ===")
    client = OpusClient(model="claude-opus-4-doesnotexist")
    t0 = time.time()
    res = client.call(
        messages=[{"role": "user", "content": "hi"}],
        temperature=TEMP, max_tokens=100,
    )
    elapsed = time.time() - t0
    clean = (res["error"] is not None and res["response"] == ""
             and res.get("route") == "anthropic")
    print(f"  elapsed={elapsed:.1f}s  error_present={res['error'] is not None}  "
          f"clean_dict={clean}")
    print(f"  error_msg={str(res['error'])[:160]}")
    return {"phase": 5, "pass": clean, "elapsed_s": elapsed,
            "error": str(res["error"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    client = OpusClient(model=MODEL)
    results = {}
    phases = ["0", "3", "4", "5"] if args.phase == "all" else [args.phase]
    for p in phases:
        if p == "0":
            results["phase0"] = phase0(client)
        elif p == "3":
            results["phase3"] = phase3(client)
        elif p == "4":
            results["phase4"] = phase4(client)
        elif p == "5":
            results["phase5"] = phase5()

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(results, indent=2))
        print(f"\nwrote {args.out}")
    return results


if __name__ == "__main__":
    main()
