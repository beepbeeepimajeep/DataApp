"""
Opus 4.7 API probe matrix — reconnaissance only, NO OpusClient, NO smoke.

Determines empirically the (model_id, thinking_shape, temperature) combos
that Anthropic's installed SDK (anthropic 0.97.0) accepts, and whether the
winning combo ACTUALLY emits `thinking` content blocks.

Each cell: hello-world "What is 2+2? Just the number.", max_tokens=1024.
Writes a full report to dataapp_outputs/smoke_tests/opus_probe_matrix_report.md
(gitignored). Records exact Anthropic error JSON per failing cell.

Run: ~/cse151b/151B_SP26_Competition/.venv/bin/python scripts/probe_opus_matrix.py
"""

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from dotenv import load_dotenv
load_dotenv(REPO / ".env")
from anthropic import Anthropic

HELLO = [{"role": "user", "content": "What is 2+2? Just the number."}]
PRICE_IN = 5.0 / 1_000_000
PRICE_OUT = 25.0 / 1_000_000

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
rows = []
total_cost = 0.0


def cell(label, model, max_tokens=1024, **kw):
    global total_cost
    rec = {"cell": label, "model": model, "params": kw, "max_tokens": max_tokens}
    t0 = time.time()
    try:
        r = client.messages.create(
            model=model, system="", messages=HELLO, max_tokens=max_tokens, **kw
        )
        n_think = sum(1 for b in r.content if getattr(b, "type", None) == "thinking")
        txt = "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
        cost = r.usage.input_tokens * PRICE_IN + r.usage.output_tokens * PRICE_OUT
        total_cost += cost
        rec.update(
            ok=True, http=200, stop=r.stop_reason,
            blocks=[getattr(b, "type", "?") for b in r.content],
            n_thinking=n_think, text=txt,
            in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens,
            cost=cost, elapsed=round(time.time() - t0, 2),
        )
    except Exception as e:
        # capture full error JSON if present
        body = None
        for attr in ("response", "body"):
            v = getattr(e, attr, None)
            if v is not None:
                try:
                    body = v.json() if hasattr(v, "json") else v
                except Exception:
                    body = str(v)
                break
        rec.update(ok=False, etype=type(e).__name__, emsg=str(e)[:400],
                   ebody=body, elapsed=round(time.time() - t0, 2))
    rows.append(rec)
    flag = "OK" if rec["ok"] else "FAIL"
    extra = f"n_thinking={rec.get('n_thinking')}" if rec["ok"] else rec.get("emsg", "")[:90]
    print(f"[{label}] {flag} {extra}")
    return rec


def main():
    wall0 = time.time()

    # ── TIER M: model identifiers, NO thinking ──
    print("== TIER M (no thinking) ==")
    m_results = {}
    for mid in ["claude-opus-4-7", "claude-opus-4-6",
                "claude-opus-4-5-20251101", "claude-opus-4-8"]:
        m_results[mid] = cell(f"M:{mid}", mid).get("ok", False)
    working_m = next((m for m, ok in m_results.items() if ok), None)
    if working_m is None:
        print("STOP: all model identifiers failed (no-thinking).")
        write_report(time.time() - wall0)
        return
    print(f"-> working model: {working_m}")

    # ── TIER T: thinking shapes on working_m ──
    print("== TIER T (thinking shapes) ==")
    cell("T1:none", working_m)
    cell("T2:enabled-budget4096", working_m,
         thinking={"type": "enabled", "budget_tokens": 4096})
    cell("T3:enabled-budget8192", working_m,
         thinking={"type": "enabled", "budget_tokens": 8192})
    cell("T4:extended_thinking-via-extra_body", working_m,
         extra_body={"extended_thinking": {"type": "enabled", "budget_tokens": 8192}})
    cell("T5:enabled-budget8192-max32768", working_m, max_tokens=32768,
         thinking={"type": "enabled", "budget_tokens": 8192})
    # T6 — the shape the API error told us to use
    t6 = cell("T6:adaptive+effort:high", working_m,
              thinking={"type": "adaptive"}, output_config={"effort": "high"})
    working_thinking = ({"thinking": {"type": "adaptive"},
                         "output_config": {"effort": "high"}}
                        if t6["ok"] else None)

    # ── TIER TE: temperature on working_m + working thinking ──
    print("== TIER TE (temperature) ==")
    base = working_thinking or {}
    cell("TE1:temp0.6", working_m, temperature=0.6, **base)
    cell("TE2:temp1.0", working_m, temperature=1.0, **base)
    cell("TE3:temp-omitted", working_m, **base)

    # ── EFFORT sweep — does ANY effort level produce a thinking block? ──
    print("== EFFORT sweep (thinking-block presence) ==")
    if working_thinking:
        for eff in ["low", "medium", "high"]:
            cell(f"EFF:{eff}", working_m, max_tokens=2048,
                 thinking={"type": "adaptive"}, output_config={"effort": eff})

    write_report(time.time() - wall0)


def write_report(wall):
    out = REPO / "dataapp_outputs/smoke_tests/opus_probe_matrix_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Opus 4.7 API Probe Matrix Report",
        "",
        f"- SDK: anthropic 0.97.0",
        f"- Total cost: ${total_cost:.4f}",
        f"- Total wall: {wall:.1f}s",
        f"- Cells: {len(rows)}",
        "",
        "## Per-cell results",
        "",
        "| cell | model | ok | http/err | n_thinking | text | in/out tok | cost |",
        "|------|-------|----|----------|-----------|------|-----------|------|",
    ]
    for r in rows:
        if r["ok"]:
            lines.append(
                f"| {r['cell']} | {r['model']} | ✓ | 200 {r['stop']} | "
                f"{r['n_thinking']} | `{r['text']}` | "
                f"{r['in_tok']}/{r['out_tok']} | ${r['cost']:.5f} |"
            )
        else:
            lines.append(
                f"| {r['cell']} | {r['model']} | ✗ | {r['etype']} | - | "
                f"{r.get('emsg','')[:60]} | - | - |"
            )
    lines += ["", "## Full error JSON (failing cells)", ""]
    for r in rows:
        if not r["ok"]:
            lines.append(f"### {r['cell']}")
            lines.append("```json")
            lines.append(json.dumps(r.get("ebody") or r.get("emsg"), indent=2,
                                    default=str))
            lines.append("```")
    lines += ["", "## Raw records", "```json",
              json.dumps(rows, indent=2, default=str), "```"]
    out.write_text("\n".join(lines))
    print(f"\nwrote {out}  (cost ${total_cost:.4f}, wall {wall:.1f}s)")


if __name__ == "__main__":
    main()
