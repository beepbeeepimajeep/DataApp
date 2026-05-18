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

from dotenv import load_dotenv
import yaml
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


def stratified_sample(items: list[dict], sample_size: int = 45, seed: int = 42) -> list[dict]:
    """
    Stratified sample: 15 MCQ, 15 single-free, 15 multi-free.

    Args:
        items: All items.
        sample_size: Target sample size (must be divisible by 3).
        seed: Random seed for reproducibility.

    Returns:
        List of sampled items.
    """
    import random
    from src.prompts import detect_question_type

    by_type = {"mcq": [], "single_free": [], "multi_free": []}
    for item in items:
        item_type = detect_question_type(item)
        by_type[item_type].append(item)

    logger.info(
        f"Type distribution: "
        f"mcq={len(by_type['mcq'])}, "
        f"single_free={len(by_type['single_free'])}, "
        f"multi_free={len(by_type['multi_free'])}"
    )

    rng = random.Random(seed)
    sample = []
    per_type = sample_size // 3

    for item_type in ["mcq", "single_free", "multi_free"]:
        available = by_type[item_type]
        take = min(per_type, len(available))
        selected = rng.sample(available, take)
        sample.extend(selected)
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

    has_answer = sum(1 for m in manifest if m.get("consensus_answer", "").strip())
    rate = has_answer / len(manifest)

    logger.info(f"Format compliance: {has_answer}/{len(manifest)} ({rate:.1%})")
    return rate >= threshold


def check_multibox_accuracy(
    items: list[dict], manifest: list[dict], threshold: float = 0.90
) -> bool:
    """
    Check that ≥threshold% of multi-answer items have correct answer count.

    Args:
        items: Original items (for question text with [ANS] count).
        manifest: Manifest entries (for consensus answers).
        threshold: Minimum accuracy rate.

    Returns:
        True if passed, False otherwise.
    """
    # Build id -> item map
    item_map = {item.get("id"): item for item in items}

    multi_items = [m for m in manifest if item_map.get(m["id"], {}).get("question_type") == "multi_free"]
    if not multi_items:
        logger.info("No multi-answer items in sample")
        return True

    correct = 0
    for entry in multi_items:
        item = item_map.get(entry["id"], {})
        question = item.get("question", "")

        # Count expected [ANS] placeholders in question
        expected_count = question.count("[ANS]")

        # Count answer values in consensus (depth-aware comma split)
        from src.extraction import count_top_level_answers
        consensus_count = count_top_level_answers(entry.get("consensus_answer", ""))

        if consensus_count == expected_count:
            correct += 1
        else:
            logger.debug(
                f"ID {entry['id']}: expected {expected_count} answers, got {consensus_count}"
            )

    accuracy = correct / len(multi_items) if multi_items else 0
    logger.info(f"Multi-answer accuracy: {correct}/{len(multi_items)} ({accuracy:.1%})")
    return accuracy >= threshold


def check_agreement_rate(manifest: list[dict], threshold: float = 0.40) -> bool:
    """
    Check that ≥threshold% of items have 3/3 model agreement.

    Args:
        manifest: Manifest entries.
        threshold: Minimum rate (0-1).

    Returns:
        True if passed, False otherwise.
    """
    if not manifest:
        logger.warning("No manifest entries")
        return False

    full_agreement = sum(1 for m in manifest if m.get("agreement_type") == "3/3")
    rate = full_agreement / len(manifest)

    logger.info(f"3/3 agreement rate: {full_agreement}/{len(manifest)} ({rate:.1%})")
    return rate >= threshold


def main():
    """Run validation phase."""
    logger.info("=== DataApp Phase 1: Validation (45 items) ===")

    # Load config and data
    config = load_config()
    all_items = load_data(config)

    # Stratified sample: 15 MCQ, 15 single, 15 multi
    validation_items = stratified_sample(all_items, sample_size=45)
    validation_ids = {item["id"] for item in validation_items}
    logger.info(f"Validation set: {len(validation_items)} items")

    # Initialize orchestrator (uses updated config)
    orchestrator = DataAppOrchestrator(config)

    # Process validation items (skip any already completed)
    summary = orchestrator.run_batch(
        [i for i in validation_items if i["id"] not in orchestrator.get_completed_ids()],
        skip_completed=False
    )
    logger.info(f"Batch summary: {json.dumps(summary, indent=2)}")

    # Load and filter manifest to validation items only
    manifest_path = Path(config["paths"]["output_dir"]) / config["paths"]["manifest_file"]
    all_manifest = read_jsonl(manifest_path)
    manifest = [m for m in all_manifest if m["id"] in validation_ids]
    logger.info(f"Validation manifest entries: {len(manifest)}")

    # Check thresholds (per PROMPT_STRATEGY.md)
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

    logger.info("\n=== Phase 1 Validation Results ===")
    logger.info(f"Format compliance ≥95%: {'PASS' if format_ok else 'FAIL'}")
    logger.info(f"Multi-answer count accuracy ≥90%: {'PASS' if multibox_ok else 'FAIL'}")
    logger.info(f"3/3 agreement ≥40%: {'PASS' if agreement_ok else 'FAIL'}")

    if format_ok and multibox_ok and agreement_ok:
        logger.info(f"\n✓ All thresholds PASSED.")
        logger.info(f"[FROM CLAUDE_DATAAPP] Phase 1 validation complete. Cost: ${orchestrator.cost_tracker.total_cost_usd():.2f}")
        logger.info("Waiting for Rain approval before Phase 2.")
        return 0
    else:
        logger.error(f"\n✗ Validation FAILED. Review above.")
        logger.error("Fix prompts/extraction/config and re-run Phase 1.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
