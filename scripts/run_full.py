#!/usr/bin/env python3
"""
DataApp Phase 2: Full pipeline (943 items).
Processes all items with parallel API calls, extraction, and consensus voting.
Resume-capable: skips completed items on restart.
"""

import sys
import json
import logging
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import yaml
from tqdm import tqdm
from src.orchestrator import DataAppOrchestrator
from src.storage import read_jsonl

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


def main():
    """Run full pipeline."""
    logger.info("=== DataApp Phase 2: Full Pipeline (943 items) ===")

    # Load config and data
    config = load_config()
    all_items = load_data(config)

    # Initialize orchestrator
    orchestrator = DataAppOrchestrator(config)

    # Get completed IDs (for resume)
    completed = orchestrator.get_completed_ids()
    logger.info(f"Already completed: {len(completed)} items")

    # Get items to process
    to_process = [i for i in all_items if i["id"] not in completed]
    logger.info(f"To process: {len(to_process)} items")
    logger.info(f"Current spend: ${orchestrator.cost_tracker.total_cost_usd():.2f}")

    # Process with progress bar
    processed = 0
    failed = 0

    with tqdm(to_process, desc="Phase 2", unit="item", dynamic_ncols=True) as pbar:
        for item in pbar:
            item_id = item.get("id")
            try:
                entry = orchestrator.run_item(item)
                processed += 1
                pbar.set_postfix(
                    id=item_id,
                    ok=processed,
                    fail=failed,
                    cost=f"${orchestrator.cost_tracker.total_cost_usd():.2f}",
                )
            except Exception as e:
                logger.error(f"Item {item_id} failed: {e}")
                failed += 1
                pbar.set_postfix(
                    id=item_id,
                    ok=processed,
                    fail=failed,
                    cost=f"${orchestrator.cost_tracker.total_cost_usd():.2f}",
                )

    # Final summary
    logger.info("\n=== Phase 2 Complete ===")
    logger.info(f"Processed: {processed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total cost: ${orchestrator.cost_tracker.total_cost_usd():.2f}")

    # Load manifest for stats
    manifest_path = Path(config["paths"]["output_dir"]) / config["paths"]["manifest_file"]
    manifest = read_jsonl(manifest_path)
    logger.info(f"Total items in manifest: {len(manifest)}")

    # Stats by type
    if manifest:
        by_type = {}
        for entry in manifest:
            qt = entry.get("question_type", "unknown")
            if qt not in by_type:
                by_type[qt] = []
            by_type[qt].append(entry)

        logger.info("\nStats by type:")
        for qt in sorted(by_type.keys()):
            items_of_type = by_type[qt]
            count = len(items_of_type)
            full_agree = sum(1 for m in items_of_type if m.get("agreement_type") == "3/3")
            logger.info(
                f"  {qt}: {count} items, {full_agree}/3 agreement: {full_agree/max(count,1):.1%}"
            )

    logger.info(f"\n✓ Phase 2 complete.")
    logger.info(f"[FROM CLAUDE_DATAAPP] Full run done. Outputs in {config['paths']['output_dir']}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
