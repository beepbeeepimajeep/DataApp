#!/usr/bin/env python3
"""
Collect results from the gpt-5.4 retry batch and update the raw response files.

Usage:
  python3 scripts/batch_collect_gpt54_retry.py --status   # check status only
  python3 scripts/batch_collect_gpt54_retry.py            # collect if completed

On success:
  - Writes dataapp_outputs/item_XXXX/gpt5_4_response.md  (overwrites RetryError stubs)
  - Writes dataapp_outputs/item_XXXX/gpt5_4_metadata.json
  - Updates data/teacher_answers_compact.json key "g" for each item
  - Writes dataapp_outputs/gpt54_retry_batch_output.jsonl (raw batch output, kept for audit)

Run build_teacher_answers_compact.py afterward to regenerate full compact store.
"""

import csv
import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUTS_DIR = Path(__file__).parent.parent / "dataapp_outputs"
BATCH_INFO = OUTPUTS_DIR / "gpt54_retry_batch_info.json"
BATCH_OUTPUT = OUTPUTS_DIR / "gpt54_retry_batch_output.jsonl"
COMPACT_JSON = Path(__file__).parent.parent / "data" / "teacher_answers_compact.json"


def extract_last_boxed(text: str) -> str:
    """Extract content of last \\boxed{...}, handling nested braces."""
    import re
    matches = list(re.finditer(r'\\boxed\{', text))
    if not matches:
        return ""
    start = matches[-1].end()
    depth = 1
    pos = start
    while pos < len(text) and depth > 0:
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
        pos += 1
    return text[start:pos - 1].strip()


def format_response_md(item_id: int, response: str, metadata: dict) -> str:
    """Format response into the standard ## Reasoning + Response / ## Metadata wrapper."""
    padded = f"{item_id:04d}"
    lines = [
        f"# item_{padded} — gpt-5.4 retry",
        "",
        "## Reasoning + Response",
        response,
        "",
        "## Metadata",
        f"- Model: {metadata.get('model', 'gpt-5.4')}",
        f"- Input tokens: {metadata.get('input_tokens', 0)}",
        f"- Output tokens: {metadata.get('output_tokens', 0)}",
        f"- Hit token cap: {metadata.get('hit_token_cap', False)}",
        f"- Finish reason: {metadata.get('finish_reason', '')}",
        f"- Generation time: {metadata.get('generation_time_s', 0):.2f}s",
        f"- Request ID: {metadata.get('request_id', '')}",
        f"- Via batch: True",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true", help="Check batch status only")
    args = parser.parse_args()

    if not BATCH_INFO.exists():
        print(f"ERROR: {BATCH_INFO} not found. Run batch_submit_gpt54_retry.py first.")
        return 1

    info = json.loads(BATCH_INFO.read_text())
    batch_id = info["batch_id"]
    print(f"Batch ID: {batch_id}")
    print(f"Submitted at: {info['submitted_at']}")
    print(f"Item count: {info['item_count']}")

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    batch = client.batches.retrieve(batch_id)
    print(f"Status: {batch.status}")
    print(f"Request counts: {batch.request_counts}")

    if args.status:
        return 0

    if batch.status != "completed":
        print(f"Batch not complete yet (status={batch.status}). Try again later.")
        return 1

    # Download output file
    output_file_id = batch.output_file_id
    print(f"Downloading output file: {output_file_id}")
    content = client.files.content(output_file_id)
    BATCH_OUTPUT.write_bytes(content.content)
    print(f"Saved: {BATCH_OUTPUT} ({BATCH_OUTPUT.stat().st_size:,} bytes)")

    # Parse results
    results = {}
    with open(BATCH_OUTPUT) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            custom_id = rec["custom_id"]
            item_id = int(custom_id.replace("item_", ""))
            results[item_id] = rec

    print(f"Parsed {len(results)} results")

    # Load compact store
    compact = json.loads(COMPACT_JSON.read_text())

    # Process each result
    stats = {"ok": 0, "error": 0, "no_box": 0}

    for item_id, rec in sorted(results.items()):
        padded = f"{item_id:04d}"
        key = str(item_id)

        # Check for API-level error
        if rec.get("error"):
            print(f"  item_{padded}: API error: {rec['error']}")
            stats["error"] += 1
            continue

        body = rec.get("response", {}).get("body", {})
        choices = body.get("choices", [])
        if not choices:
            print(f"  item_{padded}: no choices in response")
            stats["error"] += 1
            continue

        choice = choices[0]
        response_text = choice.get("message", {}).get("content") or ""
        finish_reason = choice.get("finish_reason", "")
        usage = body.get("usage", {})

        metadata = {
            "teacher": "gpt5_4",
            "model": "gpt-5.4",
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "hit_token_cap": finish_reason == "length",
            "finish_reason": finish_reason,
            "generation_time_s": 0.0,
            "request_id": body.get("id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": None,
            "via_batch": True,
        }

        # Extract answer
        answer = extract_last_boxed(response_text)
        if not answer:
            stats["no_box"] += 1
            print(f"  item_{padded}: no \\boxed found (finish={finish_reason})")
        else:
            stats["ok"] += 1

        # Write response md
        md_content = format_response_md(item_id, response_text, metadata)
        md_path = OUTPUTS_DIR / f"item_{padded}" / "gpt5_4_response.md"
        md_path.write_text(md_content)

        # Write metadata json
        meta_path = OUTPUTS_DIR / f"item_{padded}" / "gpt5_4_metadata.json"
        meta_path.write_text(json.dumps(metadata, indent=2))

        # Update compact store
        if key not in compact:
            compact[key] = {"s": "", "g": "", "o": "", "x": ""}
        compact[key]["g"] = answer

    # Write updated compact store
    COMPACT_JSON.write_text(json.dumps(compact, ensure_ascii=False, separators=(",", ":")))
    print(f"\nUpdated {COMPACT_JSON}")

    print(f"\n=== Collection Stats ===")
    print(f"  ok (with \\boxed): {stats['ok']}")
    print(f"  no_box: {stats['no_box']}")
    print(f"  error: {stats['error']}")
    print(f"  Total: {sum(stats.values())}")

    # Update batch info with completion timestamp
    info["collected_at"] = datetime.now(timezone.utc).isoformat()
    info["stats"] = stats
    BATCH_INFO.write_text(json.dumps(info, indent=2))

    print(f"\nDone. Re-run build_teacher_answers_compact.py to regenerate full compact store.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
