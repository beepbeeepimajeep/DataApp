#!/usr/bin/env python3
"""
Submit a Batch API job to rerun gpt-5.4 for the 171 RateLimitError items (267-449 range).

Usage:
  python3 scripts/batch_submit_gpt54_retry.py --dry-run   # show what would be submitted
  python3 scripts/batch_submit_gpt54_retry.py             # submit batch

Output:
  dataapp_outputs/gpt54_retry_batch_info.json   -- batch id + submission metadata
  dataapp_outputs/gpt54_retry_batch_input.jsonl -- batch request file (kept for audit)

Collect results later with:
  python3 scripts/batch_collect_gpt54_retry.py
"""

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
BATCH_INPUT = OUTPUTS_DIR / "gpt54_retry_batch_input.jsonl"
BATCH_INFO = OUTPUTS_DIR / "gpt54_retry_batch_info.json"
PRIVATE_JSONL = Path(__file__).parent.parent / "private.jsonl"

MODEL = "gpt-5.4"
TEMPERATURE = 0.6
MAX_TOKENS = 16384


SYSTEM_PROMPT = """You are generating a math solution trace for supervised fine-tuning of a smaller reasoning model.

Your goal: produce a correct, clear, concise solution. Not flashy. Not verbose. Teachable.

Rules:
1. Show essential reasoning steps. Avoid unnecessary verification loops, restarts, or exploration of alternative paths.
2. Use exact symbolic form when natural (fractions, radicals, π). Use decimals only when the problem asks for them.
3. Do not use \\boxed{} anywhere except the final answer.
4. End with exactly one \\boxed{...} containing the final answer.
5. Briefly identify what is being asked before solving."""

SINGLE_SUFFIX = """Problem type: single-answer.

There is exactly one final answer. End with: \\boxed{<your final answer>}"""

MULTI_SUFFIX = """Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \\boxed{...} with comma-separated values

End with: \\boxed{<comma-separated values in requested order>}"""

MCQ_SUFFIX = """Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \\boxed{Letter}"""


def detect_type(item: dict) -> str:
    if isinstance(item.get("options"), list) and len(item["options"]) > 0:
        return "mcq"
    if item.get("question", "").count("[ANS]") > 1:
        return "multi_free"
    return "single_free"


def build_messages(item: dict) -> list[dict]:
    question = item.get("question", "")
    options = item.get("options")
    qtype = detect_type(item)

    if qtype == "mcq":
        opts_text = "\n".join(f"{chr(65+i)}. {opt}" for i, opt in enumerate(options))
        user_content = f"{question}\n\nOptions:\n{opts_text}\n\n{MCQ_SUFFIX}"
    elif qtype == "multi_free":
        user_content = f"{question}\n\n{MULTI_SUFFIX}"
    else:
        user_content = f"{question}\n\n{SINGLE_SUFFIX}"

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def find_failed_items() -> list[int]:
    """Find item ids where gpt5_4_response.md contains RetryError or output_tokens=0."""
    failed = []
    for idx in range(943):
        padded = f"{idx:04d}"
        f = OUTPUTS_DIR / f"item_{padded}" / "gpt5_4_response.md"
        if not f.exists():
            failed.append(idx)
            continue
        content = f.read_text()
        if "RetryError" in content or "Output tokens: 0" in content:
            failed.append(idx)
    return sorted(failed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show plan, no API calls")
    args = parser.parse_args()

    # Load private.jsonl
    items = {}
    with open(PRIVATE_JSONL) as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                items[item["id"]] = item
    print(f"Loaded {len(items)} items from private.jsonl")

    # Find failed items
    failed_ids = find_failed_items()
    print(f"Failed gpt4 items found: {len(failed_ids)}")
    print(f"Range: {min(failed_ids)}-{max(failed_ids)}")

    if not failed_ids:
        print("No failed items. Exiting.")
        return 0

    # Build batch requests
    requests = []
    for item_id in failed_ids:
        item = items.get(item_id)
        if not item:
            print(f"WARNING: item {item_id} not found in private.jsonl")
            continue
        messages = build_messages(item)
        requests.append({
            "custom_id": f"item_{item_id:04d}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "messages": messages,
                "temperature": TEMPERATURE,
                "max_completion_tokens": MAX_TOKENS,
            }
        })

    print(f"Built {len(requests)} batch requests")

    # Estimate cost
    avg_input = 370
    avg_output = 382
    n = len(requests)
    input_cost = (n * avg_input / 1_000_000) * 1.25   # batch 50% off $2.50
    output_cost = (n * avg_output / 1_000_000) * 5.00  # batch 50% off $10.00
    print(f"Estimated cost: ${input_cost + output_cost:.3f} "
          f"(input ${input_cost:.3f} + output ${output_cost:.3f})")

    if args.dry_run:
        print(f"\nDRY RUN — would submit {len(requests)} items. No API calls made.")
        print(f"First 5 custom_ids: {[r['custom_id'] for r in requests[:5]]}")
        return 0

    # Write batch input file
    OUTPUTS_DIR.mkdir(exist_ok=True)
    with open(BATCH_INPUT, "w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")
    print(f"Wrote batch input: {BATCH_INPUT} ({BATCH_INPUT.stat().st_size} bytes)")

    # Submit to Batch API
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    print("Uploading batch input file...")
    with open(BATCH_INPUT, "rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")
    print(f"File uploaded: {uploaded.id}")

    print("Submitting batch...")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": f"gpt54_retry_{len(requests)}_items"},
    )
    print(f"Batch submitted: {batch.id}")
    print(f"Status: {batch.status}")

    # Save batch info
    info = {
        "batch_id": batch.id,
        "input_file_id": uploaded.id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(requests),
        "item_ids": failed_ids,
        "model": MODEL,
        "status": batch.status,
        "estimated_cost_usd": round(input_cost + output_cost, 4),
    }
    with open(BATCH_INFO, "w") as f:
        json.dump(info, f, indent=2)
    print(f"Saved batch info: {BATCH_INFO}")
    print(f"\nBatch ID: {batch.id}")
    print(f"Collect results later with: python3 scripts/batch_collect_gpt54_retry.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
