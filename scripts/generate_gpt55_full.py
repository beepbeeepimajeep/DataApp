#!/usr/bin/env python3
"""
GPT-5.5 xhigh reasoning pipeline: full-scale (943 items) with 10-minute timeout.
Parallel sync API with 15 workers, resume-safe, checkpoint every 50 items.
NOT YET EXECUTED — awaiting Ticket 3 smoke validation.
"""

import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent dir to path
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
    logger.info(f"Loaded {len(items)} items from {data_file}")
    return items


def get_completed_gpt55_ids(output_dir: Path) -> set[int]:
    """Get set of already-processed item IDs (check for response files)."""
    gpt55_dir = output_dir / "gpt55_full"
    if not gpt55_dir.exists():
        return set()

    completed = set()
    for item_file in gpt55_dir.glob("item_*_gpt5_5_response.md"):
        try:
            item_id = int(item_file.name.split("_")[1])
            completed.add(item_id)
        except (ValueError, IndexError):
            pass

    return completed


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


def process_item(
    item: dict,
    client: GPT55Client,
    extractor: DataAppExtractor,
    output_dir: Path,
    timeout_seconds: int = 600,
    dry_run: bool = False,
) -> dict:
    """
    Process single item: query GPT-5.5, save response, extract answer.

    Returns dict with: item_id, success, error, output_tokens, cost_usd, wall_time_s, finish_reason
    """
    item_id = item["id"]
    question = item.get("question", "")
    options = item.get("options")

    question_type = detect_question_type(item)
    messages = build_messages(question, question_type, options)
    max_tokens = 65536  # GPT-5.5 budget
    prompt_for_log = messages[-1]["content"]

    start = time.time()

    # Create output directory
    gpt55_dir = output_dir / "gpt55_full"
    gpt55_dir.mkdir(parents=True, exist_ok=True)

    response_path = gpt55_dir / f"item_{int(item_id):04d}_gpt5_5_response.md"

    if dry_run:
        return {
            "item_id": item_id,
            "success": True,
            "error": None,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "wall_time_s": 0.0,
            "finish_reason": "dry_run"
        }

    # Query GPT-5.5 with timeout
    try:
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
            except TimeoutError:
                elapsed = time.time() - start
                logger.warning(f"Item {item_id}: timeout after {elapsed:.1f}s")
                result = {
                    "response": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "hit_token_cap": False,
                    "finish_reason": "timeout",
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

    # Estimate cost: $5 per 1M input, $30 per 1M output
    # GPT-5.5 reasoning tokens billed as output tokens at $30/1M
    input_cost = (result.get("input_tokens", 0) / 1_000_000) * 5
    output_tokens = result.get("output_tokens", 0)
    reasoning_tokens = result.get("reasoning_tokens", 0)
    output_cost = ((output_tokens + reasoning_tokens) / 1_000_000) * 30
    total_cost = input_cost + output_cost

    # Save response to markdown
    md_content = _format_gpt55_response_md(result, prompt_for_log)
    _atomic_write(response_path, md_content)

    # Extract answer
    extracted = ""
    if result.get("response"):
        extracted = extractor.extract(result["response"])

    # Log to cost_log.jsonl
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
        "timestamp": datetime.now().__str__()
    }
    append_jsonl(cost_entry, cost_log_path)

    return {
        "item_id": item_id,
        "success": result.get("error") is None,
        "error": result.get("error"),
        "output_tokens": result.get("output_tokens", 0),
        "reasoning_tokens": result.get("reasoning_tokens", 0),
        "cost_usd": total_cost,
        "wall_time_s": elapsed,
        "finish_reason": result.get("finish_reason"),
        "extracted": extracted,
    }


def main():
    """Run GPT-5.5 pipeline."""
    parser = argparse.ArgumentParser(description="GPT-5.5 xhigh reasoning pipeline")
    parser.add_argument("--limit", type=int, default=None, help="Limit to N items (smoke mode)")
    parser.add_argument("--start-id", type=int, default=None, help="Start at specific item ID")
    parser.add_argument("--workers", type=int, default=15, help="Number of concurrent workers")
    parser.add_argument("--item-ids-file", type=str, default=None, help="JSON file with list of item IDs to process")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done, no API calls")
    args = parser.parse_args()

    logger.info("=== GPT-5.5 xhigh Reasoning Pipeline ===")
    logger.info(f"Config: limit={args.limit}, workers={args.workers}, dry_run={args.dry_run}")

    # Load config and data
    config = load_config()
    all_items = load_data(config)
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get already-completed items
    completed = get_completed_gpt55_ids(output_dir)
    logger.info(f"Already completed: {len(completed)} items")

    # Filter to items to process
    to_process = [i for i in all_items if i["id"] not in completed]

    if args.item_ids_file:
        # Load specific item IDs from file (for smoke tests)
        with open(args.item_ids_file) as f:
            item_ids = json.load(f)
        to_process = [i for i in to_process if i["id"] in item_ids]
        logger.info(f"Filtered to {len(to_process)} items from {args.item_ids_file}")

    if args.start_id:
        to_process = [i for i in to_process if i["id"] >= args.start_id]

    if args.limit:
        to_process = to_process[:args.limit]

    logger.info(f"To process: {len(to_process)} items")

    if args.dry_run:
        logger.info("DRY RUN MODE: no API calls will be made")
        for item in to_process[:3]:
            logger.info(f"  Would process item {item['id']}")
        return 0

    # Initialize clients
    client = GPT55Client(model="gpt-5.5")
    extractor = DataAppExtractor(strict_extract=False)

    # Process items in parallel
    results = []
    completed_count = 0
    error_count = 0
    timeout_count = 0
    cap_hit_count = 0
    total_cost = 0.0
    total_output_tokens = 0
    run_start = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_item, item, client, extractor, output_dir): item
            for item in to_process
        }

        for i, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                result = future.result()
                results.append(result)

                if result["success"]:
                    completed_count += 1
                else:
                    error_count += 1

                if result["finish_reason"] == "timeout":
                    timeout_count += 1

                total_cost += result["cost_usd"]
                total_output_tokens += result["output_tokens"]

                logger.info(
                    f"[{i}/{len(to_process)}] Item {result['item_id']}: "
                    f"finish={result['finish_reason']}, "
                    f"tokens={result['output_tokens']}, "
                    f"cost=${result['cost_usd']:.4f}, "
                    f"wall_time={result['wall_time_s']:.1f}s"
                )

                # Checkpoint every 50 items
                if i % 50 == 0:
                    elapsed = time.time() - run_start
                    if i < len(to_process):
                        rate = elapsed / i
                        remaining = len(to_process) - i
                        eta = rate * remaining
                    else:
                        eta = 0

                    checkpoint = {
                        "completed_count": completed_count,
                        "error_count": error_count,
                        "timeout_count": timeout_count,
                        "cap_hit_count": cap_hit_count,
                        "total_cost_usd_so_far": total_cost,
                        "elapsed_seconds": int(elapsed),
                        "eta_seconds": int(eta),
                    }
                    checkpoint_path = output_dir / "gpt55_full_progress.json"
                    with open(checkpoint_path, "w") as f:
                        json.dump(checkpoint, f, indent=2)
                    logger.info(f"Checkpoint: {completed_count}/{i}, cost=${total_cost:.2f}, ETA={int(eta)}s")

            except Exception as e:
                logger.error(f"Item {item['id']} failed: {e}")
                error_count += 1

    # Final report
    elapsed = time.time() - run_start
    logger.info("\n" + "="*80)
    logger.info("GPT-5.5 Pipeline Complete")
    logger.info("="*80)
    logger.info(f"Processed: {completed_count} items")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Timeouts: {timeout_count}")
    logger.info(f"Total cost: ${total_cost:.2f}")
    logger.info(f"Total output tokens: {total_output_tokens}")
    logger.info(f"Wall clock: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    if completed_count > 0:
        logger.info(f"Avg output tokens: {total_output_tokens/completed_count:.0f}")
        logger.info(f"Avg cost/item: ${total_cost/completed_count:.4f}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
