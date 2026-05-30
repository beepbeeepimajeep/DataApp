#!/usr/bin/env python3
"""
Build data/teacher_answers_compact.json from raw teacher response files.

Keys: "0".."942" (UNPADDED). Values: {"s":..., "g":..., "o":..., "x":...}.
Extracts the LAST \boxed{...} from each raw response (matches grader rule).
For xhigh refusals: uses data/xhigh_refusal_recovery.json "integrate" entries;
excluded items get "x": "" with a logged note.
"""

import json
import os
import re
import glob
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUTPUTS_DIR = os.path.join(ROOT, "dataapp_outputs")
OUT_FILE = os.path.join(DATA_DIR, "teacher_answers_compact.json")
REFUSAL_FILE = os.path.join(DATA_DIR, "xhigh_refusal_recovery.json")
NUM_ITEMS = 943


def extract_last_boxed(text):
    """Extract content of the last \\boxed{...} in text, handling nested braces."""
    matches = list(re.finditer(r'\\boxed\{', text))
    if not matches:
        return None
    start = matches[-1].end()
    depth = 1
    pos = start
    while pos < len(text) and depth > 0:
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
        pos += 1
    return text[start:pos - 1]


def load_refusal_recovery():
    with open(REFUSAL_FILE) as f:
        d = json.load(f)
    return d.get("integrate", {}), d.get("excluded_with_reason", {})


def main():
    integrate, excluded = load_refusal_recovery()
    print(f"Refusal recovery: {len(integrate)} integrate, {len(excluded)} excluded")

    result = {}
    xhigh_histogram = {"ok": 0, "recovered": 0, "excluded": 0, "no_box": 0}
    failures = []

    for item_idx in range(NUM_ITEMS):
        padded = f"{item_idx:04d}"
        key = str(item_idx)  # unpadded

        # --- sonnet ---
        sonnet_file = os.path.join(OUTPUTS_DIR, f"item_{padded}", "sonnet_response.md")
        s_ans = None
        if os.path.exists(sonnet_file):
            with open(sonnet_file) as f:
                s_ans = extract_last_boxed(f.read())
        if s_ans is None:
            failures.append(f"item_{padded}: sonnet no \\boxed")

        # --- gpt4 ---
        gpt4_file = os.path.join(OUTPUTS_DIR, f"item_{padded}", "gpt5_4_response.md")
        g_ans = None
        if os.path.exists(gpt4_file):
            with open(gpt4_file) as f:
                g_ans = extract_last_boxed(f.read())
        if g_ans is None:
            failures.append(f"item_{padded}: gpt4 no \\boxed")

        # --- oss ---
        oss_file = os.path.join(OUTPUTS_DIR, f"item_{padded}", "gpt_oss_response.md")
        o_ans = None
        if os.path.exists(oss_file):
            with open(oss_file) as f:
                o_ans = extract_last_boxed(f.read())
        if o_ans is None:
            failures.append(f"item_{padded}: oss no \\boxed")

        # --- xhigh ---
        xhigh_file = os.path.join(OUTPUTS_DIR, "gpt55_full", f"item_{padded}_gpt5_5_response.md")
        x_ans = None
        x_status = "ok"

        str_idx = str(item_idx)
        if str_idx in integrate:
            # Recovered from refusal
            x_ans = integrate[str_idx]
            x_status = "recovered"
            xhigh_histogram["recovered"] += 1
        elif str_idx in excluded:
            # Excluded - leave empty
            x_ans = ""
            x_status = "excluded"
            xhigh_histogram["excluded"] += 1
            failures.append(f"item_{padded}: xhigh excluded ({excluded[str_idx]})")
        elif os.path.exists(xhigh_file):
            with open(xhigh_file) as f:
                x_ans = extract_last_boxed(f.read())
            if x_ans is None:
                x_status = "no_box"
                x_ans = ""
                xhigh_histogram["no_box"] += 1
                failures.append(f"item_{padded}: xhigh no \\boxed")
            else:
                xhigh_histogram["ok"] += 1
        else:
            x_ans = ""
            x_status = "no_box"
            xhigh_histogram["no_box"] += 1
            failures.append(f"item_{padded}: xhigh file missing")

        result[key] = {
            "s": s_ans if s_ans is not None else "",
            "g": g_ans if g_ans is not None else "",
            "o": o_ans if o_ans is not None else "",
            "x": x_ans,
        }

    # Write output
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\nWrote {OUT_FILE}")

    # Summary
    print(f"\n=== Summary ===")
    print(f"Total items: {len(result)}")
    all4 = sum(1 for v in result.values() if v["s"] and v["g"] and v["o"] and v["x"])
    print(f"Items with all 4 keys filled: {all4}")
    print(f"\nxhigh histogram:")
    for k, v in xhigh_histogram.items():
        print(f"  {k}: {v}")
    total_xhigh = sum(xhigh_histogram.values())
    print(f"  TOTAL: {total_xhigh}")

    if failures:
        print(f"\nFailures / warnings ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
    else:
        print("\nNo failures.")

    # Spot-check 5 items: 0, 1, 100, 500, 942
    print("\n=== Spot-checks ===")
    checks = [0, 1, 100, 500, 942]
    for idx in checks:
        key = str(idx)
        v = result[key]
        print(f"item_{idx:04d} (key={repr(key)}): s={repr(v['s'][:30])} g={repr(v['g'][:30])} o={repr(v['o'][:30])} x={repr(v['x'][:30])}")

    return len(failures) == 0 or all(
        "excluded" in f or "recovered" in f for f in failures
    )


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
