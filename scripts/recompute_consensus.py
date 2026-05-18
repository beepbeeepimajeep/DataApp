#!/usr/bin/env python3
"""
Recompute consensus on Phase 1 data using normalized comparison.

Does NOT re-run API calls. Reads existing extractions and recomputes agreement.
"""

import json
import logging
from pathlib import Path
from collections import defaultdict

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import compute_consensus
from src.storage import Storage

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    output_dir = Path("dataapp_outputs")
    manifest_path = output_dir / "dataset_manifest.jsonl"
    storage = Storage(str(output_dir), str(manifest_path))

    # Load existing manifest
    old_entries = []
    if manifest_path.exists():
        with open(manifest_path) as f:
            for line in f:
                if line.strip():
                    old_entries.append(json.loads(line))

    logger.info(f"Loaded {len(old_entries)} items from existing manifest")

    # Recompute consensus for each item
    new_entries = []
    agreement_dist_old = defaultdict(int)
    agreement_dist_new = defaultdict(int)

    for entry in old_entries:
        item_id = entry["id"]

        # Load raw extractions from item_*/extractions.json
        item_dir = storage.item_dir(item_id)
        extractions_file = item_dir / "extractions.json"

        if not extractions_file.exists():
            logger.warning(f"Item {item_id}: extractions.json not found, skipping")
            continue

        with open(extractions_file) as f:
            extractions_data = json.load(f)

        # Map teacher keys to extracted answers
        extractions = {}
        for teacher in ["sonnet", "gpt5_4", "gpt_oss"]:
            if teacher in extractions_data:
                extractions[teacher] = extractions_data[teacher].get("extracted_answer", "")

        # Record old agreement type
        agreement_dist_old[entry["agreement_type"]] += 1

        # Recompute consensus with normalized matching
        new_consensus = compute_consensus(extractions)

        # Record new agreement type
        agreement_dist_new[new_consensus["type"]] += 1

        # Build new manifest entry (preserve raw answers and metadata)
        new_entry = {
            "id": item_id,
            "question_type": entry.get("question_type", ""),
            "gpt5_4_answer_raw": extractions.get("gpt5_4", ""),
            "gpt_oss_answer_raw": extractions.get("gpt_oss", ""),
            "sonnet_answer_raw": extractions.get("sonnet", ""),
            "agreement_type": new_consensus["type"],
            "which_agreed": new_consensus["which_agreed"],
            "consensus_answer": new_consensus["answer"],
            "any_errors": entry.get("any_errors", False),
            "reasoning_present": entry.get("reasoning_present", {}),
            "gpt5_4_metadata": entry.get("gpt5_4_metadata", {}),
            "gpt_oss_metadata": entry.get("gpt_oss_metadata", {}),
            "sonnet_metadata": entry.get("sonnet_metadata", {}),
            "route_gpt5_4": entry.get("route_gpt5_4", "tritonai"),
            "any_hit_cap": entry.get("any_hit_cap", False),
        }
        new_entries.append(new_entry)

    # Write new manifest
    backup_path = manifest_path.with_stem(manifest_path.stem + "_backup")
    if manifest_path.exists():
        manifest_path.rename(backup_path)
        logger.info(f"Backed up old manifest to {backup_path}")

    with open(manifest_path, "w") as f:
        for entry in new_entries:
            f.write(json.dumps(entry) + "\n")

    logger.info(f"Wrote new manifest with {len(new_entries)} items")

    # Report agreement distribution
    logger.info("\n" + "=" * 70)
    logger.info("CONSENSUS RECOMPUTATION RESULTS")
    logger.info("=" * 70)
    logger.info("\nOld agreement distribution (exact string match):")
    for atype in ["3/3", "2/3", "1/3", "0/3"]:
        count = agreement_dist_old[atype]
        pct = count / len(old_entries) * 100 if old_entries else 0
        logger.info(f"  {atype}: {count} ({pct:.1f}%)")

    logger.info("\nNew agreement distribution (normalized matching):")
    for atype in ["3/3", "2/3", "1/3", "0/3"]:
        count = agreement_dist_new[atype]
        pct = count / len(old_entries) * 100 if old_entries else 0
        logger.info(f"  {atype}: {count} ({pct:.1f}%)")

    old_3_3 = agreement_dist_old["3/3"] / len(old_entries) * 100 if old_entries else 0
    new_3_3 = agreement_dist_new["3/3"] / len(old_entries) * 100 if old_entries else 0
    logger.info(f"\n3/3 Agreement Rate: {old_3_3:.1f}% → {new_3_3:.1f}%")
    logger.info(f"Improvement: +{new_3_3 - old_3_3:.1f}%")

    # Find items where agreement improved
    improved = 0
    for old, new in zip(old_entries, new_entries):
        if old["agreement_type"] != new["agreement_type"]:
            old_level = int(old["agreement_type"][0])
            new_level = int(new["agreement_type"][0])
            if new_level > old_level:
                improved += 1

    logger.info(f"Items with improved agreement: {improved}")
    logger.info("=" * 70 + "\n")


if __name__ == "__main__":
    main()
