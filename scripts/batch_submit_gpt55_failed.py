#!/usr/bin/env python3
"""
Submit batch job for GPT-5.5 xhigh failed items.

Reads gpt55_full_cost_log.jsonl, identifies failures, builds batch JSONL,
uploads via Files API, submits Batch API job.

Usage:
  python3 scripts/batch_submit_gpt55_failed.py --dry-run    # Write JSONL only
  python3 scripts/batch_submit_gpt55_failed.py               # Submit batch
  python3 scripts/batch_submit_gpt55_failed.py --max-items 5 --item-ids-file /tmp/ids.json
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import yaml
from openai import OpenAI
from src.prompts import build_messages, detect_question_type
from src.storage import read_jsonl

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config():
    """Load config.yaml"""
    config_file = Path(__file__).parent.parent / "config.yaml"
    with open(config_file) as f:
        return yaml.safe_load(f)


def load_data(config):
    """Load private.jsonl"""
    data_dir = Path(config["paths"]["data_dir"])
    data_file = data_dir / config["paths"]["input_file"]
    items = read_jsonl(data_file)
    logger.info(f"Loaded {len(items)} items from private.jsonl")
    return {item["id"]: item for item in items}


def get_failed_items(cost_log_path, response_dir, item_ids_filter=None):
    """Identify items needing retry"""
    failed_ids = set()

    # Check cost log for failures
    if cost_log_path.exists():
        for entry in read_jsonl(cost_log_path):
            item_id = entry.get("item_id")
            finish_reason = entry.get("finish_reason")

            if finish_reason in [None, "None_error", "timeout", "error"]:
                failed_ids.add(item_id)

    # Check for missing response files
    if response_dir.exists():
        all_items = set(
            int(f.name.split("_")[1])
            for f in response_dir.glob("item_*_gpt5_5_response.md")
        )
    else:
        all_items = set()

    # Find items in cost log that don't have response files
    if cost_log_path.exists():
        for entry in read_jsonl(cost_log_path):
            item_id = entry.get("item_id")
            if item_id and item_id not in all_items:
                failed_ids.add(item_id)

    # Filter by item_ids_filter if provided
    if item_ids_filter:
        failed_ids = failed_ids.intersection(set(item_ids_filter))

    return sorted(list(failed_ids))


def build_batch_jsonl(failed_items_dict, all_items_dict):
    """Build batch API JSONL lines"""
    lines = []

    for item_id in sorted(failed_items_dict.keys()):
        item = all_items_dict.get(item_id)
        if not item:
            continue

        question = item.get("question", "")
        options = item.get("options")
        question_type = detect_question_type(item)

        messages = build_messages(question, question_type, options)

        batch_request = {
            "custom_id": f"item_{int(item_id):04d}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5.5",
                "messages": messages,
                "reasoning_effort": "xhigh",
                "max_completion_tokens": 65536,
                "temperature": 1.0,
            },
        }

        lines.append(json.dumps(batch_request))

    return lines


def main():
    parser = argparse.ArgumentParser(description="Submit batch job for GPT-5.5 failed items")
    parser.add_argument("--dry-run", action="store_true", help="Write JSONL only, no upload")
    parser.add_argument("--max-items", type=int, default=None, help="Limit to N items")
    parser.add_argument("--item-ids-file", type=str, default=None, help="JSON file with item IDs to retry")
    parser.add_argument("--output-info-suffix", type=str, default=None, help="Suffix for batch_info filename (e.g., 'phase1' → gpt55_phase1_batch_info.json)")
    args = parser.parse_args()

    logger.info("=== GPT-5.5 xhigh Batch Submit ===")

    config = load_config()
    output_dir = Path(config["paths"]["output_dir"])
    cost_log_path = output_dir / "gpt55_full_cost_log.jsonl"
    response_dir = output_dir / "gpt55_full"

    # Load data
    all_items_dict = load_data(config)

    # Parse item filter if provided
    item_ids_filter = None
    if args.item_ids_file:
        with open(args.item_ids_file) as f:
            item_ids_filter = json.load(f)
        logger.info(f"Filtering to {len(item_ids_filter)} items from --item-ids-file")

    # Get failed items
    failed_ids = get_failed_items(cost_log_path, response_dir, item_ids_filter)
    logger.info(f"Failed items identified: {len(failed_ids)}")

    if not failed_ids:
        logger.info("No items to retry. Exiting.")
        return 0

    # Limit if requested
    if args.max_items:
        failed_ids = failed_ids[:args.max_items]
        logger.info(f"Limited to {args.max_items} items")

    # Build batch JSONL
    failed_items_dict = {item_id: all_items_dict.get(item_id) for item_id in failed_ids}
    batch_lines = build_batch_jsonl(failed_items_dict, all_items_dict)

    logger.info(f"Built batch: {len(batch_lines)} requests")

    # Write to file
    batch_input_path = output_dir / "gpt55_batch_input.jsonl"
    with open(batch_input_path, "w") as f:
        for line in batch_lines:
            f.write(line + "\n")
    logger.info(f"Wrote batch input: {batch_input_path}")

    if args.dry_run:
        logger.info("DRY RUN: Batch not submitted")
        logger.info(f"\nSample request (first item):")
        print(batch_lines[0] if batch_lines else "(none)")
        logger.info(f"\nEstimated cost: ${len(batch_lines) * 0.114:.2f} (@ $0.114/item Batch rate)")
        return 0

    # Upload file
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    logger.info("Uploading batch input file...")

    with open(batch_input_path, "rb") as f:
        file_response = client.files.create(file=f, purpose="batch")

    file_id = file_response.id
    logger.info(f"File uploaded: {file_id}")

    # Submit batch
    logger.info("Submitting batch job...")
    batch_response = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    batch_id = batch_response.id
    logger.info(f"Batch submitted: {batch_id}")
    logger.info(f"Status: {batch_response.status}")

    # Save batch info
    batch_info = {
        "batch_id": batch_id,
        "file_id": file_id,
        "item_count": len(batch_lines),
        "estimated_cost_usd": len(batch_lines) * 0.114,
        "submitted_at": datetime.now().isoformat(),
    }

    # Per-phase filename support — pass --output-info-suffix=phase1 to write
    # gpt55_phase1_batch_info.json. Defaults to gpt55_batch_info.json.
    suffix = f"_{args.output_info_suffix}" if args.output_info_suffix else ""
    batch_info_path = output_dir / f"gpt55{suffix}_batch_info.json"
    with open(batch_info_path, "w") as f:
        json.dump(batch_info, f, indent=2)
    logger.info(f"Batch info saved: {batch_info_path}")

    print("\n" + "="*70)
    print("BATCH SUBMITTED")
    print("="*70)
    print(f"Batch ID: {batch_id}")
    print(f"File ID: {file_id}")
    print(f"Items: {len(batch_lines)}")
    print(f"Estimated cost: ${len(batch_lines) * 0.114:.2f}")
    print(f"Completion window: 24h")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    import os
    sys.exit(main())
