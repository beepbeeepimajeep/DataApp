#!/usr/bin/env python3
"""
Test reasoning health: verify ≥2/3 models have reasoning in each item.
Load manifest and flag items missing reasoning from all models.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import read_jsonl


def test_reasoning_present():
    """
    Check manifest entries for reasoning presence.
    Flags items where all 3 models have no reasoning.
    """
    manifest_path = Path("dataapp_outputs") / "dataset_manifest.jsonl"

    if not manifest_path.exists():
        print(f"❌ Manifest not found at {manifest_path}")
        return False

    manifest = read_jsonl(manifest_path)
    if not manifest:
        print(f"❌ Manifest is empty")
        return False

    print(f"\n=== Reasoning Presence Health Check ===")
    print(f"Total items: {len(manifest)}")

    no_reasoning_items = []
    weak_reasoning_items = []

    for entry in manifest:
        item_id = entry.get("id")
        reasoning = entry.get("reasoning_present", {})

        # Count how many models have reasoning
        reasoning_count = sum(1 for v in reasoning.values() if v)

        if reasoning_count == 0:
            no_reasoning_items.append(item_id)
        elif reasoning_count == 1:
            weak_reasoning_items.append(item_id)

    # Report results
    print(f"\nItems with ≥2/3 reasoning: {len(manifest) - len(no_reasoning_items) - len(weak_reasoning_items)}")
    print(f"Items with 1/3 reasoning (weak): {len(weak_reasoning_items)}")
    print(f"Items with 0/3 reasoning (critical): {len(no_reasoning_items)}")

    if no_reasoning_items:
        print(f"\n⚠️  CRITICAL: {len(no_reasoning_items)} items have NO reasoning from any model:")
        for item_id in no_reasoning_items[:10]:  # Show first 10
            print(f"  - Item {item_id}")
        if len(no_reasoning_items) > 10:
            print(f"  ... and {len(no_reasoning_items) - 10} more")

    if weak_reasoning_items:
        print(f"\n⚠️  WARNING: {len(weak_reasoning_items)} items have reasoning from only 1 model:")
        for item_id in weak_reasoning_items[:5]:  # Show first 5
            print(f"  - Item {item_id}")
        if len(weak_reasoning_items) > 5:
            print(f"  ... and {len(weak_reasoning_items) - 5} more")

    # Check token cap
    hit_cap_count = sum(1 for entry in manifest if entry.get("any_hit_cap", False))
    if hit_cap_count > 0:
        print(f"\n⚠️  Token cap hit on {hit_cap_count} items")

    passed = len(no_reasoning_items) == 0
    if passed:
        print(f"\n✓ All items have reasoning from ≥1 model")
    else:
        print(f"\n✗ {len(no_reasoning_items)} items need investigation")

    return passed


if __name__ == "__main__":
    success = test_reasoning_present()
    sys.exit(0 if success else 1)
