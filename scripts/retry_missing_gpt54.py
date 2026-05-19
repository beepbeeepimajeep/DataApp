#!/usr/bin/env python3
"""
Retry GPT-5.4 for items where it failed (gpt5_4_answer_raw is empty).

During Phase 2, GPT-5.4 hit quota exhaustion starting at item 267.
gpt_oss and sonnet continued. This script fixes items 267-449 by
resubmitting GPT-5.4 and updating manifest in-place.

Manifest rewrite is atomic: read full file, update entry, temp+rename.

Usage:
  python3 scripts/retry_missing_gpt54.py --dry-run
  python3 scripts/retry_missing_gpt54.py --max-items 2 --dry-run  # smoke test
  python3 scripts/retry_missing_gpt54.py --max-items 2             # run smoke
  python3 scripts/retry_missing_gpt54.py                            # full retry
"""

import sys
import json
import logging
import argparse
import tempfile
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential

from src.api_clients import GPT54Client
from src.prompts import build_messages, detect_question_type
from src.extraction import DataAppExtractor
from src.storage import read_jsonl
from src.orchestrator import compute_consensus

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load config.yaml."""
    config_file = Path(__file__).parent.parent / "config.yaml"
    with open(config_file) as f:
        return yaml.safe_load(f)


def load_data(config: dict) -> dict:
    """Load private.jsonl as {item_id: item_dict}."""
    data_dir = Path(config["paths"]["data_dir"])
    data_file = data_dir / config["paths"]["input_file"]
    items = read_jsonl(data_file)
    return {item["id"]: item for item in items}


def get_missing_gpt54_items(manifest_path: Path) -> list[dict]:
    """
    Identify items where gpt5_4_answer_raw is empty.

    Returns list of (manifest_entry, item_id) tuples.
    """
    missing = []
    with open(manifest_path) as f:
        for line in f:
            entry = json.loads(line)
            if not entry.get('gpt5_4_answer_raw'):  # Empty string or missing
                missing.append(entry)
    return missing


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def call_gpt54(client: GPT54Client, messages: list[dict], max_tokens: int) -> dict:
    """Call GPT-5.4 with tenacity retry."""
    import time
    start = time.time()
    resp = client.openai_client.chat.completions.create(
        model=client.model,
        messages=messages,
        temperature=0.6,
        max_completion_tokens=max_tokens,
    )
    elapsed = time.time() - start

    return {
        "response": resp.choices[0].message.content or "",
        "input_tokens": resp.usage.prompt_tokens,
        "output_tokens": resp.usage.completion_tokens,
        "hit_token_cap": resp.choices[0].finish_reason == "length",
        "finish_reason": resp.choices[0].finish_reason,
        "generation_time_s": elapsed,
        "model": "gpt-5.4",
        "request_id": resp.id,
        "error": None,
        "route": "openai",
    }


def retry_item(
    item_id: int,
    item: dict,
    client: GPT54Client,
    extractor: DataAppExtractor,
    dry_run: bool = False,
) -> dict:
    """
    Retry single item: call GPT-5.4 and return result dict.

    Returns:
        {
            "item_id": int,
            "success": bool,
            "error": str or None,
            "result": response_dict or None,
            "extracted": str,
            "input_tokens": int,
            "output_tokens": int,
        }
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would retry item {item_id}")
        return {
            "item_id": item_id,
            "success": True,
            "error": None,
            "result": None,
            "extracted": "",
            "input_tokens": 0,
            "output_tokens": 0,
        }

    question = item.get("question", "")
    options = item.get("options")
    question_type = detect_question_type(item)
    messages = build_messages(question, question_type, options)
    max_tokens = 16384

    try:
        result = call_gpt54(client, messages, max_tokens)

        # Extract answer
        extracted = ""
        if result.get("response"):
            extracted = extractor.extract(result["response"])

        logger.info(
            f"Item {item_id}: success, tokens={result['output_tokens']}, "
            f"extracted={extracted[:50] if extracted else 'NONE'}"
        )

        return {
            "item_id": item_id,
            "success": True,
            "error": None,
            "result": result,
            "extracted": extracted,
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
        }

    except Exception as e:
        logger.error(f"Item {item_id} failed: {e}")
        return {
            "item_id": item_id,
            "success": False,
            "error": str(e),
            "result": None,
            "extracted": "",
            "input_tokens": 0,
            "output_tokens": 0,
        }


def update_manifest_entry(manifest_path: Path, item_id: int, retry_result: dict) -> bool:
    """
    Update manifest entry for item_id with retry result.
    Uses atomic write (temp+rename).

    Returns True on success.
    """
    # Read entire manifest
    entries = []
    entry_to_update = None
    with open(manifest_path) as f:
        for line in f:
            entry = json.loads(line)
            if entry["id"] == item_id:
                entry_to_update = entry
            entries.append(entry)

    if entry_to_update is None:
        logger.error(f"Item {item_id} not found in manifest")
        return False

    # If retry succeeded, update the entry
    if retry_result["success"] and retry_result["result"]:
        result = retry_result["result"]

        # Update gpt5_4 fields
        entry_to_update["gpt5_4_answer_raw"] = retry_result["extracted"]
        entry_to_update["gpt5_4_metadata"] = {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "hit_token_cap": result.get("hit_token_cap", False),
            "finish_reason": result.get("finish_reason"),
            "generation_time_s": result.get("generation_time_s", 0),
        }
        entry_to_update["route_gpt5_4"] = result.get("route", "openai")

        # Recompute consensus with all 3 teachers
        extractions = {
            "gpt5_4": entry_to_update.get("gpt5_4_answer_raw", ""),
            "gpt_oss": entry_to_update.get("gpt_oss_answer_raw", ""),
            "sonnet": entry_to_update.get("sonnet_answer_raw", ""),
        }
        consensus = compute_consensus(extractions)

        entry_to_update["agreement_type"] = consensus["type"]
        entry_to_update["which_agreed"] = consensus["which_agreed"]
        entry_to_update["consensus_answer"] = consensus["answer"]

        # Check for errors (any teacher now has error)
        any_errors = any(
            entry_to_update.get(f"{t}_metadata", {}).get("finish_reason") is None
            for t in ["gpt5_4", "gpt_oss", "sonnet"]
        ) or any(
            result.get("error") for t in ["gpt5_4", "gpt_oss", "sonnet"]
            if (result := entry_to_update.get(f"{t}_metadata", {}))
        )
        entry_to_update["any_errors"] = any_errors

        logger.info(
            f"Item {item_id}: updated. New agreement={consensus['type']}, "
            f"consensus={consensus['answer'][:50] if consensus['answer'] else 'NONE'}"
        )
    else:
        # Retry failed — mark error but keep gpt_oss and sonnet
        entry_to_update["gpt5_4_answer_raw"] = ""
        entry_to_update["gpt5_4_metadata"] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "hit_token_cap": False,
            "finish_reason": "error",
            "generation_time_s": 0,
        }
        entry_to_update["any_errors"] = True
        logger.warning(f"Item {item_id}: retry failed, marked with error")

    # Atomic write: temp + rename
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=manifest_path.parent, delete=False, suffix=".jsonl"
        ) as tmp:
            for entry in entries:
                json.dump(entry, tmp)
                tmp.write("\n")
            tmp_path = tmp.name

        Path(tmp_path).rename(manifest_path)
        return True

    except Exception as e:
        logger.error(f"Failed to write manifest: {e}")
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()
        return False


def main():
    """Retry GPT-5.4 for missing items."""
    parser = argparse.ArgumentParser(description="Retry GPT-5.4 for missing items")
    parser.add_argument("--dry-run", action="store_true", help="Identify items, no API calls")
    parser.add_argument("--max-items", type=int, default=None, help="Limit to N items")
    parser.add_argument("--item-ids", type=str, default=None, help="Comma-separated item IDs to retry (overrides max-items)")
    args = parser.parse_args()

    logger.info("=== GPT-5.4 Retry for Missing Items ===")

    config = load_config()
    output_dir = Path(config["paths"]["output_dir"])
    manifest_path = output_dir / config["paths"]["manifest_file"]
    all_items = load_data(config)

    # Find items to retry
    missing = get_missing_gpt54_items(manifest_path)
    logger.info(f"Items with missing GPT-5.4: {len(missing)}")

    if not missing:
        logger.info("No items to retry. Exiting.")
        return 0

    # Filter by specific IDs if requested
    if args.item_ids:
        target_ids = set(int(x.strip()) for x in args.item_ids.split(","))
        missing = [e for e in missing if e["id"] in target_ids]
        logger.info(f"Filtered to {len(missing)} items by ID: {sorted(target_ids)}")
    # Filter by max-items if requested
    elif args.max_items:
        missing = missing[:args.max_items]
        logger.info(f"Limited to {args.max_items} items")

    # Report what will be retried
    logger.info(f"\nItems to retry (by ID):")
    for entry in missing[:10]:
        logger.info(f"  {entry['id']}")
    if len(missing) > 10:
        logger.info(f"  ... and {len(missing) - 10} more")

    if args.dry_run:
        logger.info(f"\nDRY RUN: Would retry {len(missing)} items")
        return 0

    # Initialize clients
    client = GPT54Client()
    extractor = DataAppExtractor(strict_extract=False)

    # Retry each item sequentially (manifest rewrite is read-modify-write,
    # unsafe under concurrency without locking. Sequential is safe + acceptable
    # for 171 items @ ~5-10s per item = ~30 min wall-clock)
    results = []
    success_count = 0
    error_count = 0
    total_input_tokens = 0
    total_output_tokens = 0

    for i, entry in enumerate(missing, 1):
        item_id = entry["id"]
        item = all_items.get(item_id)

        if not item:
            logger.error(f"Item {item_id} not found in private.jsonl")
            error_count += 1
            continue

        logger.info(f"[{i}/{len(missing)}] Retrying item {item_id}...")

        try:
            result = retry_item(item_id, item, client, extractor, dry_run=False)
            results.append(result)

            if result["success"]:
                success_count += 1
                total_input_tokens += result["input_tokens"]
                total_output_tokens += result["output_tokens"]

                # Update manifest
                if not update_manifest_entry(manifest_path, item_id, result):
                    error_count += 1
            else:
                error_count += 1
                # Still update manifest with error
                update_manifest_entry(manifest_path, item_id, result)

        except Exception as e:
            logger.error(f"Item {item_id} exception: {e}")
            error_count += 1

    # Summary
    logger.info("\n" + "="*80)
    logger.info("RETRY COMPLETE")
    logger.info("="*80)
    logger.info(f"Retried: {len(missing)} items")
    logger.info(f"Success: {success_count}")
    logger.info(f"Failed: {error_count}")
    logger.info(f"Total input tokens: {total_input_tokens:,}")
    logger.info(f"Total output tokens: {total_output_tokens:,}")

    # Estimate cost (GPT-5.4: $2.50 per 1M input, $15 per 1M output per OpenAI pricing)
    input_cost = (total_input_tokens / 1_000_000) * 2.50
    output_cost = (total_output_tokens / 1_000_000) * 15
    total_cost = input_cost + output_cost
    logger.info(f"Estimated cost: ${total_cost:.2f} (input ${input_cost:.2f} + output ${output_cost:.2f})")
    logger.info("="*80 + "\n")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
