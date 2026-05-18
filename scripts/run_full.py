#!/usr/bin/env python3
"""
DataApp Phase 2: Full pipeline (943 items).
Processes all items with parallel API calls, extraction, and voting.
Resume-capable: skips completed items on restart.
"""

import sys
import json
import logging
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from tqdm import tqdm
from src.orchestrator import DataAppOrchestrator
from src.storage import read_jsonl

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
    data_file = Path(config["paths"]["data_dir"]) / config["paths"]["data_file"]
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
    to_process = orchestrator.get_items_to_process(all_items, skip_completed=True)
    logger.info(f"To process: {len(to_process)} items")

    # Process with progress bar
    processed = 0
    failed = 0
    total_cost = 0.0
    total_agreement = 0.0

    with tqdm(to_process, desc="Phase 2", unit="q", dynamic_ncols=True) as pbar:
        for item in pbar:
            item_id = item.get("id")
            try:
                entry = orchestrator.process_item(item)
                processed += 1
                total_cost += entry.get("cost_usd", 0)
                total_agreement += entry.get("agreement_rate", 0)

                pbar.set_postfix(
                    id=item_id,
                    ok=processed,
                    fail=failed,
                    cost=f"${total_cost:.2f}",
                    agree=f"{(total_agreement / max(processed, 1)):.2%}",
                )
            except Exception as e:
                logger.error(f"Item {item_id} failed: {e}")
                failed += 1
                pbar.set_postfix(
                    id=item_id,
                    ok=processed,
                    fail=failed,
                    cost=f"${total_cost:.2f}",
                )

    # Final summary
    logger.info("\n=== Phase 2 Complete ===")
    logger.info(f"Processed: {processed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total cost: ${total_cost:.2f}")
    logger.info(f"Avg agreement rate: {(total_agreement / max(processed, 1)):.2%}")

    # Compute final stats
    manifest = read_jsonl(orchestrator.manifest_file)
    logger.info(f"Total items in manifest: {len(manifest)}")

    if manifest:
        costs_by_type = {}
        agreement_by_type = {}
        for entry in manifest:
            item_type = entry.get("type", "unknown")
            if item_type not in costs_by_type:
                costs_by_type[item_type] = []
                agreement_by_type[item_type] = []
            costs_by_type[item_type].append(entry.get("cost_usd", 0))
            agreement_by_type[item_type].append(entry.get("agreement_rate", 0))

        logger.info("\nStats by type:")
        for item_type in sorted(costs_by_type.keys()):
            avg_cost = sum(costs_by_type[item_type]) / len(costs_by_type[item_type])
            avg_agree = (
                sum(agreement_by_type[item_type]) / len(agreement_by_type[item_type])
            )
            count = len(costs_by_type[item_type])
            logger.info(
                f"  {item_type}: {count} items, "
                f"${avg_cost:.4f} avg, {avg_agree:.2%} agreement"
            )

    logger.info("\n✓ Phase 2 complete. Ready for Phase 3 (analysis).")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
