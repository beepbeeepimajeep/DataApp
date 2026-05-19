#!/usr/bin/env python3
"""
4-way agreement analysis: Phase 1 consensus (Sonnet, GPT-5.4, GPT-OSS) + GPT-5.5.

Reads:
  - dataapp_outputs/dataset_manifest.jsonl (45 Phase 1 items with 3-teacher answers)
  - dataapp_outputs/smoke_gpt55_phase1_redo/*.md (45 GPT-5.5 response files)

Extracts GPT-5.5 answers using DataAppExtractor (strict_extract=False, same as Phase 1).
Calls compute_consensus(extractions) with 4 teachers per item.
Reports canonical 4-way agreement counts and per-item breakdown.

Outputs:
  - Text report to stdout
  - JSON artifact: dataapp_outputs/smoke_gpt55_4way_analysis_<timestamp>.json
  - Script SHA and input paths logged for reproducibility

This script replaces the lost inline analysis from 2026-05-19 smoke test.
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction import DataAppExtractor
from src.orchestrator import compute_consensus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_git_sha():
    """Get current git commit SHA."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        return result.stdout.strip()
    except Exception as e:
        logger.warning(f"Could not get git SHA: {e}")
        return "unknown"


def load_manifest(manifest_path):
    """Load Phase 1 manifest."""
    items = {}
    with open(manifest_path) as f:
        for line in f:
            if line.strip():
                entry = json.loads(line.strip())
                items[entry["id"]] = entry
    return items


def load_gpt55_responses(smoke_dir):
    """Load all GPT-5.5 response files."""
    responses = {}
    for md_file in sorted(smoke_dir.glob("item_*_gpt5_5_response.md")):
        # Extract item ID from filename: item_0174_gpt5_5_response.md -> 174
        item_id = int(md_file.name.split("_")[1])
        with open(md_file) as f:
            responses[item_id] = f.read()
    return responses


def main():
    parser = argparse.ArgumentParser(
        description="Analyze 4-way (Sonnet, GPT-5.4, GPT-OSS, GPT-5.5) agreement"
    )
    parser.add_argument(
        "--manifest",
        default="dataapp_outputs/dataset_manifest.jsonl",
        help="Path to Phase 1 manifest"
    )
    parser.add_argument(
        "--smoke-dir",
        default="dataapp_outputs/smoke_gpt55_phase1_redo",
        help="Directory containing GPT-5.5 response files"
    )
    parser.add_argument(
        "--output-dir",
        default="dataapp_outputs",
        help="Output directory for JSON artifact"
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    smoke_dir = Path(args.smoke_dir)
    output_dir = Path(args.output_dir)

    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        sys.exit(1)
    if not smoke_dir.exists():
        logger.error(f"Smoke directory not found: {smoke_dir}")
        sys.exit(1)

    # Log inputs
    logger.info(f"Manifest: {manifest_path.absolute()}")
    logger.info(f"Smoke dir: {smoke_dir.absolute()}")
    logger.info(f"Script SHA: {get_git_sha()}")

    # Load data
    manifest_items = load_manifest(manifest_path)
    gpt55_responses = load_gpt55_responses(smoke_dir)

    logger.info(f"Loaded {len(manifest_items)} Phase 1 items")
    logger.info(f"Loaded {len(gpt55_responses)} GPT-5.5 responses")

    # Extract GPT-5.5 answers
    extractor = DataAppExtractor(strict_extract=False)
    gpt55_answers = {}
    for item_id, response_text in gpt55_responses.items():
        extracted = extractor.extract(response_text)
        gpt55_answers[item_id] = extracted

    # Analyze 4-way agreement
    per_item_results = []
    agreement_counts = defaultdict(int)
    breakdowns_by_type = defaultdict(list)

    for item_id in sorted(manifest_items.keys()):
        entry = manifest_items[item_id]

        # Get Phase 1 answers (3 teachers)
        sonnet_ans = entry.get("sonnet_answer_raw", "")
        gpt54_ans = entry.get("gpt5_4_answer_raw", "")
        gpt_oss_ans = entry.get("gpt_oss_answer_raw", "")

        # Get GPT-5.5 answer
        gpt55_ans = gpt55_answers.get(item_id, "")

        # Build extractions dict
        extractions = {
            "sonnet": sonnet_ans,
            "gpt5_4": gpt54_ans,
            "gpt_oss": gpt_oss_ans,
            "gpt5_5": gpt55_ans,
        }

        # Compute 4-way consensus
        consensus = compute_consensus(extractions)

        # Record result
        result = {
            "id": item_id,
            "question_type": entry.get("question_type", ""),
            "agreement_type": consensus["type"],
            "which_agreed": consensus["which_agreed"],
            "consensus_answer": consensus["answer"],
            "sonnet_answer_raw": sonnet_ans,
            "gpt5_4_answer_raw": gpt54_ans,
            "gpt_oss_answer_raw": gpt_oss_ans,
            "gpt5_5_answer_raw": gpt55_ans,
        }
        per_item_results.append(result)
        agreement_counts[consensus["type"]] += 1
        breakdowns_by_type[consensus["type"]].append(item_id)

    # Compute summary statistics
    total_items = len(per_item_results)
    summary = {
        "total_items": total_items,
        "script_sha": get_git_sha(),
        "timestamp": datetime.now().isoformat(),
        "input_manifest": str(manifest_path.absolute()),
        "input_smoke_dir": str(smoke_dir.absolute()),
        "agreement_counts": dict(agreement_counts),
        "agreement_breakdown_by_type": {
            agreement_type: items
            for agreement_type, items in sorted(breakdowns_by_type.items())
        },
    }

    # Compute subsets
    gpt55_broke_unanimity = []
    gpt55_differs_from_consensus = []
    phase1_unanimous_gpt55_agrees = []
    phase1_unanimous_gpt55_disagrees = []

    for result in per_item_results:
        item_id = result["id"]
        entry = manifest_items[item_id]
        prior_agreement = entry.get("agreement_type", "")
        phase1_consensus = entry.get("consensus_answer", "")

        # Check if GPT-5.5 broke 3/3 unanimity
        if prior_agreement == "3/3" and result["agreement_type"] != "4/4":
            gpt55_broke_unanimity.append(item_id)

        # Check if GPT-5.5 differs from Phase 1 consensus
        if result["gpt5_5_answer_raw"] and result["gpt5_5_answer_raw"] != phase1_consensus:
            gpt55_differs_from_consensus.append(item_id)

        # Check if Phase 1 was unanimous and GPT-5.5 agrees
        if prior_agreement == "3/3":
            if result["gpt5_5_answer_raw"] == phase1_consensus:
                phase1_unanimous_gpt55_agrees.append(item_id)
            else:
                phase1_unanimous_gpt55_disagrees.append(item_id)

    summary["gpt55_broke_unanimity"] = gpt55_broke_unanimity
    summary["gpt55_differs_from_consensus"] = gpt55_differs_from_consensus
    summary["phase1_unanimous_gpt55_agrees"] = phase1_unanimous_gpt55_agrees
    summary["phase1_unanimous_gpt55_disagrees"] = phase1_unanimous_gpt55_disagrees

    # Write JSON artifact
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"smoke_gpt55_4way_analysis_{timestamp}.json"
    with open(output_json, "w") as f:
        json.dump({
            "summary": summary,
            "per_item": per_item_results,
        }, f, indent=2)

    logger.info(f"JSON artifact saved: {output_json}")

    # Print text report
    print("\n" + "=" * 80)
    print("4-WAY AGREEMENT ANALYSIS: Phase 1 (Sonnet, GPT-5.4, GPT-OSS) + GPT-5.5")
    print("=" * 80)
    print(f"\nScript SHA: {get_git_sha()}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Manifest: {manifest_path}")
    print(f"Smoke dir: {smoke_dir}")

    print(f"\nTotal items analyzed: {total_items}")
    print("\n" + "-" * 80)
    print("AGREEMENT COUNT SUMMARY")
    print("-" * 80)

    # Sort agreement types for display (4/4, 3/4, 3/3, 2/4, 2/3, ...)
    sorted_types = sorted(
        agreement_counts.items(),
        key=lambda x: (
            int(x[0].split("/")[1]),  # Sort by total teachers (ascending)
            -int(x[0].split("/")[0]),  # Then by agreement count (descending)
        )
    )

    for agreement_type, count in sorted_types:
        pct = 100 * count / total_items
        print(f"  {agreement_type:5s}: {count:3d} items ({pct:5.1f}%)")

    print("\n" + "-" * 80)
    print("DIVERGENCE ANALYSIS")
    print("-" * 80)
    print(f"  GPT-5.5 broke Phase 1 3/3 unanimity: {len(gpt55_broke_unanimity)} items")
    if gpt55_broke_unanimity:
        print(f"    Items: {gpt55_broke_unanimity[:10]}{'...' if len(gpt55_broke_unanimity) > 10 else ''}")

    print(f"  GPT-5.5 differs from Phase 1 consensus: {len(gpt55_differs_from_consensus)} items")
    if gpt55_differs_from_consensus:
        print(f"    Items: {gpt55_differs_from_consensus[:10]}{'...' if len(gpt55_differs_from_consensus) > 10 else ''}")

    print(f"  Phase 1 unanimous (3/3), GPT-5.5 agrees: {len(phase1_unanimous_gpt55_agrees)} items")
    print(f"  Phase 1 unanimous (3/3), GPT-5.5 disagrees: {len(phase1_unanimous_gpt55_disagrees)} items")

    print("\n" + "=" * 80)
    print(f"Full results saved to: {output_json}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
