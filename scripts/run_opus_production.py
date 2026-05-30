"""Opus 4.7 production pass — 535 targeted items, streaming, resumable.

Locked config: claude-opus-4-7, no thinking, no temperature forwarded,
max_tokens=32768, streaming, max_workers=10, tenacity 3x retry (in OpusClient).

Resumable: appends one JSONL line per completed item to items.jsonl; on
restart, skips ids already present. Live tracking: prints a progress line
periodically and writes progress.json heartbeat.

Auto-STOP gates (spec): running cost > $50; error rate > 10% after retries;
empty extracted_raw rate > 5%; diamond mismatch (0041!=2112 or 0285!=735);
persistent rate-limit (reduce workers once, then stop).

NO aggregation here — opus_results.csv / anchor_v2 / 5th_teacher are built by
a separate step that uses 151B gold_equiv.

Run: ~/cse151b/151B_SP26_Competition/.venv/bin/python scripts/run_opus_production.py
"""

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
OUT.mkdir(parents=True, exist_ok=True)
ITEMS = OUT / "items.jsonl"
PROGRESS = OUT / "progress.json"

MAX_WORKERS = 10
PRICE_IN = 5.0 / 1_000_000
PRICE_OUT = 25.0 / 1_000_000

COST_HARD_STOP = 50.0
ERR_RATE_STOP = 0.10
EMPTY_RATE_STOP = 0.05
DIAMONDS = {"0041": "2112", "0285": "735"}

_lock = threading.Lock()
_stop = threading.Event()
_stop_reason = [None]


def extract_raw(text):
    return remove_boxed(last_boxed_only_string(text))


def read_prompt(item_id):
    text = (TEACHER_DIR / f"item_{item_id}.md").read_text()
    after = text.split("## Prompt", 1)[1]
    fo = after.index("```") + 3
    nl = after.index("\n", fo)
    fc = after.index("```", nl)
    return after[nl + 1:fc].rstrip("\n")


def load_done():
    done = {}
    if ITEMS.exists():
        for line in ITEMS.read_text().splitlines():
            if line.strip():
                try:
                    d = json.loads(line)
                    done[d["id"]] = d
                except Exception:
                    pass
    return done


def run_item(client, item_id):
    prompt = read_prompt(item_id)
    res = client.call(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=32768,
    )
    raw = extract_raw(res["response"])
    cost = res["input_tokens"] * PRICE_IN + res["output_tokens"] * PRICE_OUT
    return {
        "id": item_id,
        "response_full": res["response"],
        "extracted_raw": raw,
        "usage": {"input": res["input_tokens"], "output": res["output_tokens"]},
        "finish_reason": res["finish_reason"],
        "wall_time_s": round(res["generation_time_s"], 2),
        "cost_usd": round(cost, 6),
        "request_id": res["request_id"],
        "prompt_source": "teacher_md",
        "error": res["error"],
    }


def main():
    target = json.load(open(OUT / "target_535.json"))
    done = load_done()
    todo = [i for i in target if i not in done]
    print(f"target={len(target)} done={len(done)} todo={len(todo)} workers={MAX_WORKERS}")

    # running stats seeded from already-done items
    stats = {
        "completed": len(done),
        "errors": sum(1 for d in done.values() if d.get("error")),
        "empty_raw": sum(1 for d in done.values() if not d.get("extracted_raw")),
        "cost": sum(d.get("cost_usd", 0) for d in done.values()),
        "total": len(target),
    }
    diamond_seen = {k: done[k]["extracted_raw"] for k in DIAMONDS if k in done}

    if not todo:
        print("nothing to do — all target items already present.")
        return

    fout = open(ITEMS, "a")
    t0 = time.time()

    def gate_check():
        if stats["cost"] > COST_HARD_STOP:
            return f"cost ${stats['cost']:.2f} > ${COST_HARD_STOP}"
        n = stats["completed"]
        if n >= 30:  # don't trip on tiny denominators
            if stats["errors"] / n > ERR_RATE_STOP:
                return f"error rate {stats['errors']}/{n} > {ERR_RATE_STOP:.0%}"
            if stats["empty_raw"] / n > EMPTY_RATE_STOP:
                return f"empty extracted_raw {stats['empty_raw']}/{n} > {EMPTY_RATE_STOP:.0%}"
        return None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        client = OpusClient(model="claude-opus-4-7")
        futs = {ex.submit(run_item, client, i): i for i in todo}
        for fut in as_completed(futs):
            iid = futs[fut]
            try:
                rec = fut.result()
            except Exception as e:
                rec = {"id": iid, "response_full": "", "extracted_raw": None,
                       "usage": {"input": 0, "output": 0}, "finish_reason": None,
                       "wall_time_s": 0, "cost_usd": 0, "request_id": None,
                       "prompt_source": "teacher_md", "error": f"runner: {e}"}
            with _lock:
                fout.write(json.dumps(rec) + "\n")
                fout.flush()
                stats["completed"] += 1
                if rec["error"]:
                    stats["errors"] += 1
                if not rec["extracted_raw"]:
                    stats["empty_raw"] += 1
                stats["cost"] += rec["cost_usd"]
                if iid in DIAMONDS:
                    diamond_seen[iid] = rec["extracted_raw"]

                n = stats["completed"]
                wall = time.time() - t0
                if n % 10 == 0 or n == stats["total"]:
                    msg = (f"[{n}/{stats['total']}] cost=${stats['cost']:.2f} "
                           f"err={stats['errors']} empty={stats['empty_raw']} "
                           f"wall={wall:.0f}s last={iid}:{rec['extracted_raw']!r}")
                    print(msg, flush=True)
                    PROGRESS.write_text(json.dumps({**stats, "wall_s": round(wall, 1),
                                                    "diamonds": diamond_seen}, indent=2))

                # diamond mismatch
                for d, exp in DIAMONDS.items():
                    if d in diamond_seen and diamond_seen[d] not in (None,) and diamond_seen[d] != exp:
                        # tolerance not applied here; flag exact-string drift from smoke
                        _stop_reason[0] = f"diamond {d}={diamond_seen[d]!r} != {exp}"
                        _stop.set()
                reason = gate_check()
                if reason:
                    _stop_reason[0] = reason
                    _stop.set()

            if _stop.is_set():
                print(f"STOP gate tripped: {_stop_reason[0]} — cancelling remaining", flush=True)
                for f in futs:
                    f.cancel()
                break

    fout.close()
    wall = time.time() - t0
    final = {**stats, "wall_s": round(wall, 1), "diamonds": diamond_seen,
             "stopped": _stop_reason[0]}
    PROGRESS.write_text(json.dumps(final, indent=2))
    print("DONE" if not _stop_reason[0] else f"HALTED: {_stop_reason[0]}")
    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()
