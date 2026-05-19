#!/usr/bin/env python3
"""
Regrade manifest using fixed answers_match.

Applies the composed normalization pipeline fix to all manifest entries,
updating agreement_type, which_agreed, consensus_answer, and adding
agreement_via field.

Dry-run mode shows changes without writing.
Apply mode writes atomically with backup.

Usage:
  python3 scripts/regrade_manifest.py --dry-run    # Preview changes
  python3 scripts/regrade_manifest.py --apply      # Apply and write
"""

import json
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import compute_consensus
from src.storage import read_jsonl

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Regrade manifest with fixed answers_match"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes and write manifest",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("ERROR: must specify --dry-run or --apply")
        sys.exit(1)

    manifest_path = Path("dataapp_outputs/dataset_manifest.jsonl")

    # Load existing manifest
    logger.info(f"Loading manifest from {manifest_path}...")
    entries = read_jsonl(manifest_path)
    logger.info(f"Loaded {len(entries)} entries")

    # Regrade each entry
    unchanged = []
    improved = []
    worsened = []

    logger.info("Regrading entries...")
    for entry in entries:
        item_id = entry["id"]
        old_agreement = entry["agreement_type"]

        # Extract raw answers
        extractions = {
            "gpt5_4": entry.get("gpt5_4_answer_raw", ""),
            "gpt_oss": entry.get("gpt_oss_answer_raw", ""),
            "sonnet": entry.get("sonnet_answer_raw", ""),
        }

        # Recompute consensus with fixed function
        new_consensus = compute_consensus(extractions)
        new_agreement = new_consensus["type"]

        # Compare
        old_count = int(old_agreement.split("/")[0])
        new_count = int(new_agreement.split("/")[0])

        if new_count > old_count:
            improved.append({
                "item_id": item_id,
                "old": old_agreement,
                "new": new_agreement,
                "via": new_consensus["agreement_via"],
                "entry": entry,
                "new_consensus": new_consensus,
            })
        elif new_count < old_count:
            worsened.append({
                "item_id": item_id,
                "old": old_agreement,
                "new": new_agreement,
            })
        else:
            unchanged.append({
                "item_id": item_id,
                "agreement": old_agreement,
                "via": new_consensus["agreement_via"],
                "entry": entry,
                "new_consensus": new_consensus,
            })

    # Report
    print("\n" + "=" * 80)
    print("REGRADE SUMMARY")
    print("=" * 80)
    print(f"\nTotal entries: {len(entries)}")
    print(f"Items unchanged (agreement same): {len(unchanged)}")
    print(f"Items improved (agreement increased): {len(improved)}")
    print(f"Items worsened (should be zero): {len(worsened)}")

    if worsened:
        print("\n⚠️  ANOMALY: Items worsened (fix should be monotonic):")
        for item in worsened[:10]:
            print(
                f"  Item {item['item_id']:3d}: "
                f"{item['old']} → {item['new']}"
            )

    if improved:
        print("\nImprovement breakdown:")
        improvements = {}
        for item in improved:
            key = f"{item['old']} → {item['new']}"
            improvements[key] = improvements.get(key, 0) + 1
        for key in sorted(improvements.keys()):
            print(f"  {key}: {improvements[key]}")

    # agreement_via distribution
    via_dist = Counter()
    for item in unchanged + improved:
        via_dist[item["via"]] += 1

    print(
        f"\nagreement_via distribution "
        f"({len(unchanged) + len(improved)} entries):"
    )
    for via_type in sorted(via_dist.keys()):
        count = via_dist[via_type]
        pct = 100 * count / (len(unchanged) + len(improved))
        print(f"  {via_type:15s}: {count:4d} ({pct:5.1f}%)")

    # Sample items
    if improved:
        print(f"\nSample improved items (first 5):")
        for item in improved[:5]:
            old_entry = item["entry"]
            print(
                f"\n  Item {item['item_id']} "
                f"({old_entry.get('question_type')})"
            )
            print(
                f"    Agreement: {item['old']} → {item['new']} "
                f"(via {item['via']})"
            )
            print(f"    gpt5_4:  {old_entry.get('gpt5_4_answer_raw')!r}")
            print(f"    gpt_oss: {old_entry.get('gpt_oss_answer_raw')!r}")
            print(f"    sonnet:  {old_entry.get('sonnet_answer_raw')!r}")

    # Apply if requested
    if args.apply:
        print("\n" + "=" * 80)
        print("APPLYING CHANGES")
        print("=" * 80)

        # Build new manifest with updates
        new_entries = []
        for entry in entries:
            item_id = entry["id"]

            # Find if this entry was improved or unchanged
            improved_entry = next(
                (e for e in improved if e["item_id"] == item_id), None
            )
            unchanged_entry = next(
                (e for e in unchanged if e["item_id"] == item_id), None
            )

            if improved_entry:
                # Update agreement fields
                entry["agreement_type"] = improved_entry["new"]
                entry["which_agreed"] = improved_entry["new_consensus"][
                    "which_agreed"
                ]
                entry["consensus_answer"] = improved_entry["new_consensus"][
                    "answer"
                ]
                entry["agreement_via"] = improved_entry["via"]
            elif unchanged_entry:
                # Just add agreement_via field
                entry["agreement_via"] = unchanged_entry["via"]
            # else: worsened (shouldn't happen, keep as-is)

            new_entries.append(entry)

        # Atomic write with backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = manifest_path.with_name(
            f"{manifest_path.stem}.bak.before_regrade_{timestamp}{manifest_path.suffix}"
        )
        manifest_path.rename(backup_path)
        logger.info(f"Backed up original to {backup_path}")

        tmp_path = manifest_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            for entry in new_entries:
                f.write(json.dumps(entry) + "\n")

        tmp_path.rename(manifest_path)
        logger.info(f"Wrote updated manifest to {manifest_path}")

        print(f"\n✓ Regrade complete:")
        print(f"  {len(improved)} items improved")
        print(f"  {len(unchanged)} items unchanged (added agreement_via)")
        print(f"  Total entries: {len(new_entries)}")
        print(f"  Backup: {backup_path}")
    else:
        print("\n[DRY-RUN] No changes written.")
        print("Run with --apply to actually update the manifest.")


if __name__ == "__main__":
    main()
