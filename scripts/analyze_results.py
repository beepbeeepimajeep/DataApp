#!/usr/bin/env python3
"""
DataApp Phase 3: Analysis and handoff.
Generates dataset_manifest.jsonl with consensus predictions.
Computes statistics and verifies quality thresholds.
"""

import sys
import json
import logging
from pathlib import Path
from collections import Counter

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
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


def main():
    """Run analysis phase."""
    logger.info("=== DataApp Phase 3: Analysis & Handoff ===")

    config = load_config()
    manifest_file = Path(config["paths"]["output_dir"]) / config["paths"]["manifest_file"]

    if not manifest_file.exists():
        logger.error(f"Manifest file not found: {manifest_file}")
        return 1

    # Load manifest
    manifest = read_jsonl(manifest_file)
    logger.info(f"Loaded {len(manifest)} items from manifest")

    if not manifest:
        logger.warning("Manifest is empty")
        return 1

    # Compute statistics
    total_items = len(manifest)
    total_cost = sum(m.get("cost_usd", 0) for m in manifest)
    no_box_count = sum(1 for m in manifest if not m.get("consensus", "").strip())
    full_agreement_count = sum(
        1 for m in manifest if m.get("agreement_rate", 0) >= 0.999
    )

    avg_agreement = sum(m.get("agreement_rate", 0) for m in manifest) / max(
        total_items, 1
    )

    # Stats by type
    by_type = {}
    for entry in manifest:
        item_type = entry.get("type", "unknown")
        if item_type not in by_type:
            by_type[item_type] = []
        by_type[item_type].append(entry)

    logger.info("\n=== Statistics ===")
    logger.info(f"Total items: {total_items}")
    logger.info(f"Total cost: ${total_cost:.2f}")
    logger.info(f"No-box rate: {no_box_count}/{total_items} ({no_box_count/total_items:.2%})")
    logger.info(f"Full agreement rate: {full_agreement_count}/{total_items} ({full_agreement_count/total_items:.2%})")
    logger.info(f"Avg agreement rate: {avg_agreement:.2%}")

    logger.info("\n=== Stats by Type ===")
    for item_type in sorted(by_type.keys()):
        items_of_type = by_type[item_type]
        count = len(items_of_type)
        cost = sum(m.get("cost_usd", 0) for m in items_of_type)
        no_box = sum(1 for m in items_of_type if not m.get("consensus", "").strip())
        agreement = sum(m.get("agreement_rate", 0) for m in items_of_type) / count
        full_agree = sum(1 for m in items_of_type if m.get("agreement_rate", 0) >= 0.999)

        logger.info(
            f"{item_type:4s}: {count:3d} items, "
            f"${cost:7.2f}, "
            f"{no_box:3d} no-box ({no_box/count:.1%}), "
            f"{full_agree:3d} full-agree ({full_agree/count:.1%}), "
            f"avg-agree {agreement:.2%}"
        )

    # Quality checks
    logger.info("\n=== Quality Checks ===")
    no_box_threshold = config.get("validation", {}).get("max_no_box_rate", 0.05)
    no_box_ok = (no_box_count / total_items) <= no_box_threshold
    logger.info(
        f"No-box rate threshold: {no_box_threshold:.1%} "
        f"({'PASS' if no_box_ok else 'FAIL'})"
    )

    # Distribution check
    type_counts = {t: len(items) for t, items in by_type.items()}
    logger.info(f"\nType distribution:")
    for t in sorted(type_counts.keys()):
        pct = type_counts[t] / total_items * 100
        logger.info(f"  {t}: {type_counts[t]:3d} ({pct:5.1f}%)")

    # Summary for handoff
    logger.info("\n=== Handoff Summary ===")
    summary = {
        "total_items": total_items,
        "total_cost_usd": total_cost,
        "no_box_rate": no_box_count / total_items,
        "full_agreement_rate": full_agreement_count / total_items,
        "avg_agreement_rate": avg_agreement,
        "type_distribution": type_counts,
        "manifest_file": str(manifest_file),
    }
    logger.info(json.dumps(summary, indent=2))

    # Save summary
    summary_file = Path(config["paths"]["output_dir"]) / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"\nSummary saved to {summary_file}")

    logger.info("\n✓ Phase 3 complete.")
    logger.info(f"✓ Manifest ready: {manifest_file}")
    logger.info(f"✓ Output directory: {config['paths']['output_dir']}")
    logger.info("\nHandoff to Rain for SFT training pipeline.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
