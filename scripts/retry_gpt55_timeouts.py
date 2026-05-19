#!/usr/bin/env python3
"""
Retry GPT-5.5 items that timed out or errored during parallel run.
Sequential processing with 30-minute budget per item.
To execute AFTER Ticket 4 (full parallel run) completes.
"""

import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import yaml
from src.api_clients import GPT55Client
from src.prompts import build_messages, detect_question_type
from src.extraction import DataAppExtractor
from src.storage import read_jsonl, append_jsonl, _atomic_write

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


def load_data(config: dict) -> list[dict]:
    """Load private.jsonl."""
    data_dir = Path(config["paths"]["data_dir"])
    data_file = data_dir / config["paths"]["input_file"]
    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        raise FileNotFoundError(f"private.jsonl not found at {data_file}")

    items = read_jsonl(data_file)
    logger.info(f"Loaded {len(items)} items from private.jsonl")
    return items


def get_retry_candidates(cost_log_path: Path, response_dir: Path) -> set[int]:
    """
    Identify items that need retry:
    - finish_reason == "timeout"
    - finish_reason == "error"
    - No response file exists
    - Response file is empty
    """
    candidates = set()

    # Check cost log for timeouts/errors
    if cost_log_path.exists():
        for entry in read_jsonl(cost_log_path):
            item_id = entry.get("item_id")
            finish_reason = entry.get("finish_reason")

            if finish_reason in ["timeout", "error"]:
                candidates.add(item_id)
                logger.info(f"Candidate from cost log: item {item_id} ({finish_reason})")

    # Check for missing response files
    if response_dir.exists():
        all_items = set(int(f.name.split("_")[1]) for f in response_dir.glob("item_*_gpt5_5_response.md"))
    else:
        all_items = set()

    # Find items in cost log that don't have response files
    if cost_log_path.exists():
        for entry in read_jsonl(cost_log_path):
            item_id = entry.get("item_id")
            if item_id and item_id not in all_items:
                candidates.add(item_id)
                logger.info(f"Candidate from missing file: item {item_id}")

    # Check for empty response files
    for resp_file in response_dir.glob("item_*_gpt5_5_response.md"):
        item_id = int(resp_file.name.split("_")[1])
        try:
            with open(resp_file) as f:
                content = f.read()
            # Check if response section is empty
            if "## Reasoning + Response" in content:
                section_start = content.find("## Reasoning + Response") + len("## Reasoning + Response")
                section_end = content.find("##", section_start)
                if section_end == -1:
                    section_end = len(content)
                response_section = content[section_start:section_end].strip()
                if not response_section or response_section == "":
                    candidates.add(item_id)
                    logger.info(f"Candidate from empty content: item {item_id}")
        except Exception as e:
            logger.warning(f"Error reading {resp_file}: {e}")

    return candidates


def _format_gpt55_response_md(response_data: dict, prompt: str) -> str:
    """Format GPT-5.5 response as markdown with metadata footer."""
    finish_reason = response_data.get("finish_reason", "unknown")
    reasoning_tokens = response_data.get("reasoning_tokens", 0)
    error_note = f"\n\n**ERROR:** {response_data.get('error')}" if response_data.get("error") else ""
    timeout_note = "\n\n**TIMEOUT:** Item exceeded 10-minute hard limit." if finish_reason == "timeout" else ""

    return f"""# GPT-5.5 xhigh Response

## Prompt
```
{prompt}
```

## Reasoning + Response
{response_data.get('response', '')}

## Metadata
- Model: {response_data.get('model', 'gpt-5.5')}
- Input tokens: {response_data.get('input_tokens', 0)}
- Output tokens: {response_data.get('output_tokens', 0)}
- Reasoning tokens: {reasoning_tokens}
- Hit token cap: {response_data.get('hit_token_cap', False)}
- Finish reason: {finish_reason}
- Generation time: {response_data.get('generation_time_s', 0):.2f}s
- Request ID: {response_data.get('request_id', 'N/A')}{error_note}{timeout_note}
"""


def retry_item(
    item: dict,
    client: GPT55Client,
    extractor: DataAppExtractor,
    output_dir: Path,
    timeout_seconds: int = 1800,
    dry_run: bool = False,
) -> dict:
    """
    Retry single item with longer timeout (30 min for retries).

    Returns dict with: item_id, success, error, output_tokens, cost_usd, wall_time_s, finish_reason, retry_attempt
    """
    item_id = item["id"]
    question = item.get("question", "")
    options = item.get("options")

    question_type = detect_question_type(item)
    messages = build_messages(question, question_type, options)
    max_tokens = 65536
    prompt_for_log = messages[-1]["content"]

    response_dir = output_dir / "gpt55_full"
    response_path = response_dir / f"item_{int(item_id):04d}_gpt5_5_response.md"

    start = time.time()

    if dry_run:
        logger.info(f"[DRY RUN] Would retry item {item_id}")
        return {
            "item_id": item_id,
            "success": True,
            "error": None,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "wall_time_s": 0.0,
            "finish_reason": "dry_run",
            "retry_attempt": 1,
        }

    # Call GPT-5.5 with longer timeout
    try:
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.call,
                messages,
                temperature=1.0,
                max_tokens=max_tokens,
                reasoning_effort="xhigh"
            )
            try:
                result = future.result(timeout=timeout_seconds)
            except FutureTimeoutError:
                elapsed = time.time() - start
                logger.warning(f"Item {item_id}: timeout after {elapsed:.1f}s (30-min budget)")
                result = {
                    "response": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "hit_token_cap": False,
                    "finish_reason": "timeout_retry",
                    "generation_time_s": elapsed,
                    "model": client.model,
                    "request_id": None,
                    "error": f"Timeout after {timeout_seconds}s",
                    "route": "openai"
                }
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"Item {item_id}: API error: {e}")
        result = {
            "response": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "hit_token_cap": False,
            "finish_reason": "error",
            "generation_time_s": elapsed,
            "model": client.model,
            "request_id": None,
            "error": str(e),
            "route": "openai"
        }

    elapsed = time.time() - start

    # Estimate cost
    input_cost = (result.get("input_tokens", 0) / 1_000_000) * 5
    output_cost = (result.get("output_tokens", 0) / 1_000_000) * 30
    total_cost = input_cost + output_cost

    # Save response (overwrite existing)
    md_content = _format_gpt55_response_md(result, prompt_for_log)
    _atomic_write(response_path, md_content)

    # Extract answer
    extracted = ""
    if result.get("response"):
        extracted = extractor.extract(result["response"])

    # Append to cost log with retry marker
    cost_log_path = output_dir / "gpt55_full_cost_log.jsonl"
    cost_entry = {
        "item_id": item_id,
        "model": result.get("model", "gpt-5.5"),
        "input_tokens": result.get("input_tokens", 0),
        "output_tokens": result.get("output_tokens", 0),
        "reasoning_tokens": result.get("reasoning_tokens", 0),
        "cost_usd": total_cost,
        "wall_time_s": elapsed,
        "finish_reason": result.get("finish_reason"),
        "error": result.get("error"),
        "retry_attempt": 1,
        "timestamp": datetime.now().__str__()
    }
    append_jsonl(cost_entry, cost_log_path)

    logger.info(
        f"Item {item_id}: finish={result['finish_reason']}, "
        f"tokens={result['output_tokens']}, "
        f"cost=${total_cost:.4f}, "
        f"wall_time={elapsed:.1f}s"
    )

    return {
        "item_id": item_id,
        "success": result.get("error") is None,
        "error": result.get("error"),
        "output_tokens": result.get("output_tokens", 0),
        "cost_usd": total_cost,
        "wall_time_s": elapsed,
        "finish_reason": result.get("finish_reason"),
        "retry_attempt": 1,
    }


def main():
    """Retry GPT-5.5 timeout/error items."""
    parser = argparse.ArgumentParser(description="Retry GPT-5.5 timeout/error items")
    parser.add_argument("--dry-run", action="store_true", help="List items to retry, no API calls")
    parser.add_argument("--max-items", type=int, default=None, help="Limit retries to N items")
    args = parser.parse_args()

    logger.info("=== GPT-5.5 Retry Script (Sequential, 30-min timeout) ===")

    # Load config and data
    config = load_config()
    all_items = load_data(config)
    output_dir = Path(config["paths"]["output_dir"])
    cost_log_path = output_dir / "gpt55_full_cost_log.jsonl"
    response_dir = output_dir / "gpt55_full"

    # Find retry candidates
    retry_ids = get_retry_candidates(cost_log_path, response_dir)
    logger.info(f"Retry candidates identified: {len(retry_ids)}")

    if not retry_ids:
        logger.info("No items need retry. Exiting.")
        return 0

    # Filter to actual items
    to_retry = [i for i in all_items if i["id"] in retry_ids]

    if args.max_items:
        to_retry = to_retry[:args.max_items]
        logger.info(f"Limited to {args.max_items} items")

    if args.dry_run:
        logger.info(f"DRY RUN: Would retry {len(to_retry)} items:")
        for item in to_retry:
            print(f"  Item {item['id']}: {item.get('question', '')[:60]}...")
        return 0

    # Sequential retry (30-min per item)
    logger.info(f"Starting sequential retry of {len(to_retry)} items (30-min budget each)")

    client = GPT55Client(model="gpt-5.5")
    extractor = DataAppExtractor(strict_extract=False)

    results = []
    success_count = 0
    error_count = 0
    total_cost = 0.0

    for i, item in enumerate(to_retry, 1):
        logger.info(f"[{i}/{len(to_retry)}] Retrying item {item['id']}...")
        try:
            result = retry_item(item, client, extractor, output_dir, timeout_seconds=1800, dry_run=False)
            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                error_count += 1

            total_cost += result["cost_usd"]

        except Exception as e:
            logger.error(f"Item {item['id']} retry failed: {e}")
            error_count += 1

    # Summary
    logger.info("\n" + "="*80)
    logger.info("RETRY COMPLETE")
    logger.info("="*80)
    logger.info(f"Retried: {len(to_retry)} items")
    logger.info(f"Success: {success_count}")
    logger.info(f"Failed: {error_count}")
    logger.info(f"Total retry cost: ${total_cost:.2f}")
    logger.info("="*80 + "\n")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
