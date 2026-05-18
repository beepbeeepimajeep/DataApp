#!/usr/bin/env python3
"""
DataApp Phase 1: Validation (45-item stratified sample).
Tests format compliance, multi-answer accuracy, and agreement rate.
"""

import sys
import json
import logging
from pathlib import Path
from collections import Counter

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
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


def stratified_sample(items: list[dict], sample_size: int = 45) -> list[dict]:
    """
    Stratified sample by type (31% MCQ, 32% single-free, 36% multi-free).

    Args:
        items: All items.
        sample_size: Target sample size.

    Returns:
        List of sampled items.
    """
    by_type = {}
    for item in items:
        item_type = item.get("type", "unknown")
        if item_type not in by_type:
            by_type[item_type] = []
        by_type[item_type].append(item)

    logger.info(f"Type distribution: {[(t, len(v)) for t, v in by_type.items()]}")

    sample = []
    type_counts = {
        "MCS": int(sample_size * 0.31),  # MCQ single choice
        "MCM": int(sample_size * 0.05),  # MCQ multiple choice
        "INT": int(sample_size * 0.08),  # Single-free (integers, intervals)
        "NV": int(sample_size * 0.14),   # Single-free (numerical values)
        "EX": int(sample_size * 0.10),   # Single-free (expressions)
        "EQ": int(sample_size * 0.05),   # Multi-free (equations)
        "OL": int(sample_size * 0.13),   # Multi-free (ordered lists)
        "UOL": int(sample_size * 0.15),  # Multi-free (unordered lists)
    }

    for item_type, target_count in type_counts.items():
        if item_type in by_type:
            available = by_type[item_type]
            take = min(target_count, len(available))
            sample.extend(available[:take])
            logger.info(f"{item_type}: taking {take} of {len(available)}")

    logger.info(f"Stratified sample size: {len(sample)}")
    return sample


def check_format_compliance(manifest: list[dict], threshold: float = 0.95) -> bool:
    """
    Check that ≥threshold% of items have boxed answers.

    Args:
        manifest: List of manifest entries.
        threshold: Minimum compliance rate.

    Returns:
        True if passed, False otherwise.
    """
    if not manifest:
        logger.warning("No manifest entries to check")
        return False

    has_boxed = sum(1 for m in manifest if m.get("consensus", "").strip())
    rate = has_boxed / len(manifest)

    logger.info(f"Format compliance: {has_boxed}/{len(manifest)} ({rate:.1%})")
    return rate >= threshold


def check_multibox_accuracy(
    items: list[dict], manifest: list[dict], threshold: float = 0.90
) -> bool:
    """
    Check that ≥threshold% of multi-answer items have correct answer count.

    Args:
        items: Original items (for type/gold).
        manifest: Manifest entries (for consensus answers).
        threshold: Minimum accuracy rate.

    Returns:
        True if passed, False otherwise.
    """
    # Build id -> item map
    item_map = {item.get("id"): item for item in items}

    multi_items = [m for m in manifest if item_map.get(m["id"], {}).get("type") in ["OL", "UOL", "EQ"]]
    if not multi_items:
        logger.info("No multi-answer items in sample")
        return True

    correct = 0
    for entry in multi_items:
        item = item_map.get(entry["id"], {})
        gold = item.get("gold", "")

        # Count answer boxes in consensus (naive: count commas + 1)
        consensus_count = (entry.get("consensus", "").count(",") + 1) if entry.get("consensus") else 0
        gold_count = gold.count(",") + 1 if gold else 0

        if consensus_count == gold_count:
            correct += 1
        else:
            logger.debug(
                f"ID {entry['id']}: expected {gold_count} answers, got {consensus_count}"
            )

    accuracy = correct / len(multi_items)
    logger.info(f"Multi-answer accuracy: {correct}/{len(multi_items)} ({accuracy:.1%})")
    return accuracy >= threshold


def check_agreement_rate(manifest: list[dict], threshold: float = 0.40) -> bool:
    """
    Check that ≥threshold% of items have 3/3 model agreement.

    Args:
        manifest: Manifest entries.
        threshold: Minimum rate.

    Returns:
        True if passed, False otherwise.
    """
    if not manifest:
        logger.warning("No manifest entries")
        return False

    full_agreement = sum(1 for m in manifest if m.get("agreement_rate", 0) >= 0.999)
    rate = full_agreement / len(manifest)

    logger.info(f"3/3 agreement rate: {full_agreement}/{len(manifest)} ({rate:.1%})")
    return rate >= threshold


def main():
    """Run validation phase."""
    logger.info("=== DataApp Phase 1: Validation ===")

    # Load config and data
    config = load_config()
    all_items = load_data(config)

    # Stratified sample
    validation_items = stratified_sample(all_items, sample_size=45)
    logger.info(f"Validation set: {len(validation_items)} items")

    # Initialize orchestrator
    orchestrator = DataAppOrchestrator(config)

    # Get items to process (skip if already done)
    to_process = orchestrator.get_items_to_process(validation_items, skip_completed=True)
    logger.info(f"Processing {len(to_process)} new items")

    # Process batch
    summary = orchestrator.run_batch(to_process)
    logger.info(f"Batch summary: {json.dumps(summary, indent=2)}")

    # Load manifest
    manifest = read_jsonl(orchestrator.manifest_file)
    logger.info(f"Total manifest entries: {len(manifest)}")

    # Check thresholds
    val_config = config.get("validation", {})
    format_ok = check_format_compliance(
        manifest, val_config.get("min_format_compliance", 0.95)
    )
    multibox_ok = check_multibox_accuracy(
        all_items, manifest, val_config.get("min_multibox_accuracy", 0.90)
    )
    agreement_ok = check_agreement_rate(
        manifest, val_config.get("min_agreement_rate", 0.40)
    )

    logger.info("\n=== Validation Results ===")
    logger.info(f"Format compliance: {'PASS' if format_ok else 'FAIL'}")
    logger.info(f"Multi-answer accuracy: {'PASS' if multibox_ok else 'FAIL'}")
    logger.info(f"Agreement rate: {'PASS' if agreement_ok else 'FAIL'}")

    if format_ok and multibox_ok and agreement_ok:
        logger.info("\n✓ Validation PASSED. Ready for Phase 2.")
        return 0
    else:
        logger.error("\n✗ Validation FAILED. Debug and re-run before Phase 2.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
