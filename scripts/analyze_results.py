#!/usr/bin/env python3
"""
DataApp Phase 3: Analysis and handoff.
Reads dataset_manifest.jsonl and cost_log.jsonl.
Computes agreement distribution, token stats, cost breakdown, no-box rate.
Reports findings without recommending pipeline/lineup decisions.
"""

import sys
import json
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime

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


def load_cost_log(cost_log_path: Path) -> dict:
    """Load cost_log.jsonl and aggregate by model and item."""
    cost_by_item = defaultdict(float)
    cost_by_model = defaultdict(float)
    total_cost = 0.0

    if not cost_log_path.exists():
        logger.warning(f"Cost log not found: {cost_log_path}")
        return {"by_item": cost_by_item, "by_model": cost_by_model, "total": total_cost}

    for entry in read_jsonl(cost_log_path):
        item_id = entry.get("item_id")
        model = entry.get("model", "unknown")
        cost = entry.get("cost_usd", 0)
        if item_id is not None:
            cost_by_item[item_id] += cost
        cost_by_model[model] += cost
        total_cost += cost

    return {
        "by_item": cost_by_item,
        "by_model": cost_by_model,
        "total": total_cost,
    }


def main():
    """Run Phase 3 analysis."""
    logger.info("=== DataApp Phase 3: Analysis & Handoff ===")

    config = load_config()
    output_dir = Path(config["paths"]["output_dir"])
    manifest_file = output_dir / config["paths"]["manifest_file"]
    cost_log_path = output_dir / "cost_log.jsonl"

    if not manifest_file.exists():
        logger.error(f"Manifest file not found: {manifest_file}")
        return 1

    # Load data
    manifest = read_jsonl(manifest_file)
    logger.info(f"Loaded {len(manifest)} items from manifest")

    if not manifest:
        logger.warning("Manifest is empty")
        return 1

    costs = load_cost_log(cost_log_path)

    # Compute statistics
    total_items = len(manifest)
    no_box_count = sum(1 for m in manifest if not m.get("consensus_answer", "").strip())
    error_count = sum(1 for m in manifest if m.get("any_errors", False))
    cap_hit_count = sum(1 for m in manifest if m.get("any_hit_cap", False))

    # Agreement type distribution
    agreement_dist = defaultdict(int)
    for entry in manifest:
        agreement_type = entry.get("agreement_type", "0/0")
        agreement_dist[agreement_type] += 1

    # Stats by question type
    by_type = defaultdict(list)
    for entry in manifest:
        q_type = entry.get("question_type", "unknown")
        by_type[q_type].append(entry)

    # Token statistics
    all_tokens_per_teacher = defaultdict(list)
    for entry in manifest:
        for teacher in ["sonnet", "gpt5_4", "gpt_oss"]:
            meta_key = f"{teacher}_metadata"
            meta = entry.get(meta_key, {})
            output_tokens = meta.get("output_tokens", 0)
            if output_tokens > 0:
                all_tokens_per_teacher[teacher].append(output_tokens)

    # Reasoning presence
    reasoning_count = defaultdict(int)
    for entry in manifest:
        reasoning_dict = entry.get("reasoning_present", {})
        for teacher, present in reasoning_dict.items():
            if present:
                reasoning_count[teacher] += 1

    # Print report
    print("\n" + "=" * 80)
    print("DATAAPP PHASE 3: ANALYSIS & HANDOFF")
    print("=" * 80)
    print(f"\nManifest: {manifest_file}")
    print(f"Cost log: {cost_log_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    print(f"\n{'-' * 80}")
    print("SUMMARY")
    print(f"{'-' * 80}")
    print(f"Total items processed: {total_items}")
    print(f"Total cost: ${costs['total']:.2f}")
    print(f"Errors (any_errors=True): {error_count}/{total_items} ({error_count/total_items:.1%})")
    print(f"Cap hits (any_hit_cap=True): {cap_hit_count}/{total_items} ({cap_hit_count/total_items:.1%})")
    print(f"No-box rate (empty consensus): {no_box_count}/{total_items} ({no_box_count/total_items:.1%})")

    print(f"\n{'-' * 80}")
    print("AGREEMENT TYPE DISTRIBUTION")
    print(f"{'-' * 80}")
    for agreement_type in sorted(agreement_dist.keys(),
                                  key=lambda x: (int(x.split('/')[1]),
                                                 -int(x.split('/')[0]))):
        count = agreement_dist[agreement_type]
        pct = 100 * count / total_items
        print(f"  {agreement_type:5s}: {count:3d} items ({pct:5.1f}%)")

    print(f"\n{'-' * 80}")
    print("COST BREAKDOWN BY MODEL")
    print(f"{'-' * 80}")
    for model in sorted(costs["by_model"].keys()):
        cost = costs["by_model"][model]
        pct = 100 * cost / max(costs["total"], 1)
        print(f"  {model:20s}: ${cost:7.2f} ({pct:5.1f}%)")

    print(f"\n{'-' * 80}")
    print("TOKEN STATISTICS BY TEACHER")
    print(f"{'-' * 80}")
    for teacher in sorted(all_tokens_per_teacher.keys()):
        tokens = all_tokens_per_teacher[teacher]
        if tokens:
            median = sorted(tokens)[len(tokens) // 2]
            p95 = sorted(tokens)[int(0.95 * len(tokens))]
            mean = sum(tokens) / len(tokens)
            print(f"  {teacher:15s}: median={median:5d}, p95={p95:5d}, mean={mean:7.1f}")

    print(f"\n{'-' * 80}")
    print("REASONING PRESENCE BY TEACHER")
    print(f"{'-' * 80}")
    for teacher in sorted(reasoning_count.keys()):
        count = reasoning_count[teacher]
        pct = 100 * count / total_items
        print(f"  {teacher:15s}: {count:3d} items ({pct:5.1f}%)")

    print(f"\n{'-' * 80}")
    print("STATS BY QUESTION TYPE")
    print(f"{'-' * 80}")
    for q_type in sorted(by_type.keys()):
        items = by_type[q_type]
        count = len(items)
        type_cost = sum(costs["by_item"].get(m["id"], 0) for m in items)
        no_box = sum(1 for m in items if not m.get("consensus_answer", "").strip())
        errors = sum(1 for m in items if m.get("any_errors", False))
        caps = sum(1 for m in items if m.get("any_hit_cap", False))

        print(f"  {q_type:15s}: {count:3d} items, ${type_cost:7.2f}, "
              f"{no_box:3d} no-box ({no_box/count:.1%}), "
              f"{errors:3d} errors ({errors/count:.1%}), "
              f"{caps:3d} cap-hits ({caps/count:.1%})")

    # Quality checks
    print(f"\n{'-' * 80}")
    print("QUALITY THRESHOLDS (from config.yaml)")
    print(f"{'-' * 80}")
    validation_config = config.get("validation", {})
    max_no_box = validation_config.get("max_no_box_rate", 0.05)
    no_box_ok = (no_box_count / total_items) <= max_no_box
    print(f"  Max no-box rate: {max_no_box:.1%} → {no_box_count/total_items:.1%} "
          f"({'PASS' if no_box_ok else 'WARN'})")

    # Build summary artifact
    summary = {
        "total_items": total_items,
        "total_cost_usd": costs["total"],
        "no_box_rate": no_box_count / total_items,
        "error_rate": error_count / total_items,
        "cap_hit_rate": cap_hit_count / total_items,
        "agreement_distribution": dict(agreement_dist),
        "cost_by_model": dict(costs["by_model"]),
        "type_distribution": {t: len(items) for t, items in by_type.items()},
        "token_stats": {
            teacher: {
                "count": len(tokens),
                "median": sorted(tokens)[len(tokens) // 2],
                "p95": sorted(tokens)[int(0.95 * len(tokens))],
                "mean": sum(tokens) / len(tokens),
            }
            for teacher, tokens in all_tokens_per_teacher.items()
        },
        "reasoning_presence": dict(reasoning_count),
        "manifest_file": str(manifest_file.absolute()),
    }

    # Save summary JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = output_dir / f"phase3_analysis_{timestamp}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary artifact saved: {summary_file}")

    print(f"\n{'=' * 80}")
    print(f"Analysis complete. Summary artifact: {summary_file}")
    print(f"Handoff ready: manifest at {manifest_file}")
    print("=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
