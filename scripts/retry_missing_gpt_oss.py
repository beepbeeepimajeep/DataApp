#!/usr/bin/env python3
"""
Retry GPT-OSS (TritonAI) for items where it failed (gpt_oss_answer_raw is empty).

Target items: 95, 405, 498, 506, 525 have empty gpt_oss_answer_raw.
This script resubmits via GPTOSSClient (TritonAI, $0 cost for UCSD) and
updates manifest in-place.

Manifest rewrite is atomic: read full file, update entry, temp+rename.

Usage:
  python3 scripts/retry_missing_gpt_oss.py --dry-run
  python3 scripts/retry_missing_gpt_oss.py --max-items 2 --dry-run  # smoke test
  python3 scripts/retry_missing_gpt_oss.py --max-items 2             # run smoke
  python3 scripts/retry_missing_gpt_oss.py                            # full retry
  python3 scripts/retry_missing_gpt_oss.py --item-ids "95,405,498"   # specific items
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

from src.api_clients import GPTOSSClient
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


def get_missing_gpt_oss_items(manifest_path: Path) -> list[dict]:
    """
    Identify items where gpt_oss_answer_raw is empty.

    Returns list of manifest entries.
    """
    missing = []
    with open(manifest_path) as f:
        for line in f:
            entry = json.loads(line)
            if not entry.get('gpt_oss_answer_raw'):  # Empty string or missing
                missing.append(entry)
    return missing


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def call_gpt_oss(client: GPTOSSClient, messages: list[dict], max_tokens: int) -> dict:
    """Call GPT-OSS (TritonAI) with tenacity retry."""
    import time
    start = time.time()
    resp = client.call(messages, max_tokens=max_tokens, temperature=0.6)
    elapsed = time.time() - start

    return {
        "response": resp.get("response") or "",
        "input_tokens": resp.get("input_tokens", 0),
        "output_tokens": resp.get("output_tokens", 0),
        "hit_token_cap": resp.get("hit_token_cap", False),
        "finish_reason": resp.get("finish_reason", "stop"),
        "generation_time_s": elapsed,
        "model": "gpt-oss",
        "request_id": resp.get("request_id", ""),
        "error": resp.get("error"),
        "route": "tritonai",
    }


def retry_item(
    item_id: int,
    item: dict,
    client: GPTOSSClient,
    extractor: DataAppExtractor,
    dry_run: bool = False,
) -> dict:
    """
    Retry single item: call GPT-OSS and return result dict.

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
        result = call_gpt_oss(client, messages, max_tokens)

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

        # Update gpt_oss fields
        entry_to_update["gpt_oss_answer_raw"] = retry_result["extracted"]
        entry_to_update["gpt_oss_metadata"] = {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "hit_token_cap": result.get("hit_token_cap", False),
            "finish_reason": result.get("finish_reason"),
            "generation_time_s": result.get("generation_time_s", 0),
        }
        entry_to_update["route_gpt_oss"] = result.get("route", "tritonai")

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
        # Retry failed — mark error but keep gpt5_4 and sonnet
        entry_to_update["gpt_oss_answer_raw"] = ""
        entry_to_update["gpt_oss_metadata"] = {
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
    """Retry GPT-OSS (TritonAI) for missing items."""
    parser = argparse.ArgumentParser(description="Retry GPT-OSS for missing items (TritonAI, $0 cost)")
    parser.add_argument("--dry-run", action="store_true", help="Identify items, no API calls")
    parser.add_argument("--max-items", type=int, default=None, help="Limit to N items")
    parser.add_argument("--item-ids", type=str, default=None, help="Comma-separated item IDs to retry (overrides max-items)")
    args = parser.parse_args()

    logger.info("=== GPT-OSS Retry for Missing Items (TritonAI, $0 cost) ===")

    config = load_config()
    output_dir = Path(config["paths"]["output_dir"])
    manifest_path = output_dir / config["paths"]["manifest_file"]
    all_items = load_data(config)

    # Find items to retry
    missing = get_missing_gpt_oss_items(manifest_path)
    logger.info(f"Items with missing GPT-OSS: {len(missing)}")

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
    client = GPTOSSClient()
    extractor = DataAppExtractor(strict_extract=False)

    # Retry each item sequentially (manifest rewrite is read-modify-write,
    # unsafe under concurrency without locking. Sequential is safe + acceptable
    # for ~5 items @ ~5-10s per item = ~1 min wall-clock)
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
    logger.info("RETRY COMPLETE (TritonAI, $0 cost)")
    logger.info("="*80)
    logger.info(f"Retried: {len(missing)} items")
    logger.info(f"Success: {success_count}")
    logger.info(f"Failed: {error_count}")
    logger.info(f"Total input tokens: {total_input_tokens:,}")
    logger.info(f"Total output tokens: {total_output_tokens:,}")
    logger.info(f"Estimated cost: $0.00 (TritonAI is free for UCSD)")
    logger.info("="*80 + "\n")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
