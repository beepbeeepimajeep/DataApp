#!/usr/bin/env python3
"""
Collect GPT-5.5 responses from gpt55_full directory and populate manifest.

This script:
1. Reads all item_XXXX_gpt5_5_response.md files
2. Extracts answers using DataAppExtractor
3. Updates dataset_manifest.jsonl with gpt5_5_answer_raw field
4. Recomputes 4-teacher consensus
5. Reports completion status
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from src.extraction import DataAppExtractor
from src.orchestrator import compute_consensus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_manifest(manifest_path: str) -> dict:
    """Load manifest into memory (id -> item)."""
    manifest = {}
    with open(manifest_path) as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            manifest[item["id"]] = item
    return manifest


def load_gpt55_response(item_id: int) -> Optional[str]:
    """Load a single GPT-5.5 response file."""
    fpath = f"dataapp_outputs/gpt55_full/item_{item_id:04d}_gpt5_5_response.md"
    if not os.path.exists(fpath):
        return None
    with open(fpath) as f:
        return f.read()


def extract_answer_from_response(response: str) -> str:
    """Extract answer using strict extraction (boxed only)."""
    extractor = DataAppExtractor(strict_extract=False)
    return extractor.extract(response)


def update_manifest_with_gpt55(manifest: dict) -> tuple[dict, list]:
    """
    Populate gpt5_5_answer_raw for all items in manifest.
    Returns: (updated_manifest, errors)
    """
    extractor = DataAppExtractor(strict_extract=False)
    errors = []

    for item_id in sorted(manifest.keys()):
        response = load_gpt55_response(item_id)

        if response is None:
            errors.append(
                {
                    "item_id": item_id,
                    "error": "Response file not found",
                }
            )
            continue

        try:
            answer = extract_answer_from_response(response)
            manifest[item_id]["gpt5_5_answer_raw"] = answer
        except Exception as e:
            errors.append(
                {
                    "item_id": item_id,
                    "error": f"Extraction failed: {str(e)}",
                }
            )
            manifest[item_id]["gpt5_5_answer_raw"] = ""

    return manifest, errors


def recompute_consensus(item: dict) -> dict:
    """Recompute 4-teacher consensus with new gpt5_5_answer_raw."""
    answers = {
        "sonnet": item.get("sonnet_answer_raw", ""),
        "gpt5_4": item.get("gpt5_4_answer_raw", ""),
        "gpt_oss": item.get("gpt_oss_answer_raw", ""),
        "gpt5_5": item.get("gpt5_5_answer_raw", ""),
    }

    # Filter out empty answers
    valid_answers = {k: v for k, v in answers.items() if v}

    if not valid_answers:
        item["consensus_answer"] = ""
        item["agreement_type"] = "0/4"
        item["which_agreed"] = []
        return item

    # Compute consensus
    consensus_result = compute_consensus(answers)

    item["consensus_answer"] = consensus_result.get("answer", "")
    item["agreement_type"] = consensus_result.get("type", "0/4")
    item["which_agreed"] = consensus_result.get("which_agreed", [])

    return item


def save_manifest(manifest: dict, output_path: str) -> None:
    """Save manifest to file with atomic write."""
    import tempfile

    # Write to temp file first
    with tempfile.NamedTemporaryFile(
        mode="w", dir=os.path.dirname(output_path), delete=False
    ) as tmp:
        for item_id in sorted(manifest.keys()):
            json.dump(manifest[item_id], tmp)
            tmp.write("\n")
        tmp_path = tmp.name

    # Atomic rename
    os.rename(tmp_path, output_path)


def main():
    manifest_path = "dataapp_outputs/dataset_manifest.jsonl"

    logger.info("Loading manifest...")
    manifest = load_manifest(manifest_path)
    logger.info(f"Loaded {len(manifest)} items from manifest")

    logger.info("Updating manifest with GPT-5.5 answers...")
    manifest, errors = update_manifest_with_gpt55(manifest)

    logger.info("Recomputing 4-teacher consensus...")
    for item_id in manifest:
        manifest[item_id] = recompute_consensus(manifest[item_id])

    logger.info("Saving updated manifest...")
    save_manifest(manifest, manifest_path)

    # Report
    logger.info(f"Completed collection for {len(manifest)} items")

    if errors:
        logger.warning(f"Encountered {len(errors)} errors during extraction:")
        for err in errors[:10]:
            logger.warning(f"  Item {err['item_id']}: {err['error']}")
        if len(errors) > 10:
            logger.warning(f"  ... and {len(errors) - 10} more")

    # Count 4-teacher agreement
    agreement_counts = {}
    for item in manifest.values():
        atype = item.get("agreement_type", "0/4")
        agreement_counts[atype] = agreement_counts.get(atype, 0) + 1

    logger.info("4-teacher agreement distribution:")
    for atype in sorted(agreement_counts.keys(), reverse=True):
        count = agreement_counts[atype]
        pct = 100 * count / len(manifest)
        logger.info(f"  {atype}: {count} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
